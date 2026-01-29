import socket
import threading
import time
import json
import traceback
import queue
import asyncio

# ============================================================
#  CONFIG
# ============================================================

DISCOVERY_PORT = 50100
DISCOVERY_INTERVAL = 3.0
DISCOVERY_TIMEOUT = 10.0

TCP_PORT = 50200
BUFFER = 4096

JOB_RETRIES = 2
JOB_TIMEOUT = 10.0


# ============================================================
#  PEER REGISTRY WITH SIMPLE LOAD METRICS
# ============================================================

class PeerRegistry:
    def __init__(self, self_host, self_port):
        self.self_host = self_host
        self.self_port = self_port
        self._peers = {}      # (host, port) -> last_seen
        self._metrics = {}    # (host, port) -> avg_duration
        self._lock = threading.Lock()

    def update(self, host, port):
        if host == self.self_host and port == self.self_port:
            return
        with self._lock:
            self._peers[(host, port)] = time.time()

    def list(self):
        now = time.time()
        with self._lock:
            dead = [p for p, ts in self._peers.items()
                    if now - ts > DISCOVERY_TIMEOUT]
            for p in dead:
                del self._peers[p]
                self._metrics.pop(p, None)
            return list(self._peers.keys())

    def record_duration(self, host, port, duration):
        key = (host, port)
        with self._lock:
            old = self._metrics.get(key)
            if old is None:
                self._metrics[key] = duration
            else:
                self._metrics[key] = 0.7 * old + 0.3 * duration

    def sorted_workers(self, include_self=True):
        with self._lock:
            peers = list(self._peers.keys())
            if include_self:
                peers = peers + [(self.self_host, self.self_port)]
            def score(p):
                return self._metrics.get(p, 1.0)
            return sorted(peers, key=score)


# ============================================================
#  DISCOVERY (UDP BROADCAST)
# ============================================================

def broadcast_presence(self_port, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = json.dumps({"port": self_port}).encode()

    while not stop_event.is_set():
        try:
            sock.sendto(msg, ("255.255.255.255", DISCOVERY_PORT))
        except OSError:
            pass
        stop_event.wait(DISCOVERY_INTERVAL)

    sock.close()


def listen_for_peers(registry, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))

    while not stop_event.is_set():
        try:
            sock.settimeout(1.0)
            data, addr = sock.recvfrom(1024)
        except socket.timeout:
            continue
        except OSError:
            break

        try:
            msg = json.loads(data.decode())
            registry.update(addr[0], msg["port"])
        except Exception:
            pass

    sock.close()


# ============================================================
#  WORKER SERVER (TCP) + LOCAL WORKER POOL
# ============================================================

def send_json(conn, obj):
    conn.sendall((json.dumps(obj) + "\n").encode())


def recv_json(conn):
    buf = b""
    while b"\n" not in buf:
        chunk = conn.recv(BUFFER)
        if not chunk:
            break
        buf += chunk
    if not buf:
        return None
    return json.loads(buf.decode().strip())


def worker_job_runner(func_registry, job_queue, enabled_flag):
    while True:
        func_name, args, kwargs, conn = job_queue.get()
        if conn is None:
            # shutdown signal
            break
        try:
            if not enabled_flag["enabled"]:
                send_json(conn, {
                    "ok": False,
                    "error": "Node not accepting jobs right now"
                })
                conn.close()
                continue

            if func_name not in func_registry:
                raise ValueError(f"Unknown function: {func_name}")
            fn = func_registry[func_name]
            result = fn(*args, **kwargs)
            send_json(conn, {"ok": True, "result": result})
        except Exception as e:
            send_json(conn, {
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
        finally:
            conn.close()
            job_queue.task_done()


def start_worker_server(host, port, stop_event, func_registry, max_workers, enabled_flag):
    # local queue of incoming jobs
    job_queue = queue.Queue()

    # start local worker threads (processing power control)
    for _ in range(max_workers):
        t = threading.Thread(
            target=worker_job_runner,
            args=(func_registry, job_queue, enabled_flag),
            daemon=True
        )
        t.start()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(50)

    while not stop_event.is_set():
        try:
            s.settimeout(1.0)
            conn, _ = s.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        # enqueue job for local worker threads
        try:
            req = recv_json(conn)
            if not req:
                conn.close()
                continue
            func_name = req["func_name"]
            args = req["args"]
            kwargs = req["kwargs"]
            job_queue.put((func_name, args, kwargs, conn))
        except Exception:
            conn.close()

    # shutdown workers
    for _ in range(max_workers):
        job_queue.put((None, None, None, None))
    s.close()


# ============================================================
#  CLUSTER API + JOB QUEUE + FAULT TOLERANCE
# ============================================================

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    s.close()
    return ip


class Cluster:
    def __init__(self, port=TCP_PORT, max_workers=4, enabled=True):
        """
        max_workers: how many jobs this node will run in parallel.
        enabled: whether this node donates CPU to the cluster.
        """
        self.host = get_local_ip()
        self.port = port
        self.registry = PeerRegistry(self.host, self.port)
        self.stop_event = threading.Event()
        self.func_registry = {}
        self.job_queue = queue.Queue()
        self.results = {}
        self.results_lock = threading.Lock()
        self.job_counter = 0

        self.enabled_flag = {"enabled": bool(enabled)}
        self.max_workers = max_workers

        # discovery
        threading.Thread(
            target=broadcast_presence,
            args=(self.port, self.stop_event),
            daemon=True
        ).start()

        threading.Thread(
            target=listen_for_peers,
            args=(self.registry, self.stop_event),
            daemon=True
        ).start()

        # worker server (this node's donated CPU)
        threading.Thread(
            target=start_worker_server,
            args=(self.host, self.port, self.stop_event,
                  self.func_registry, self.max_workers, self.enabled_flag),
            daemon=True
        ).start()

        # dispatcher for outgoing jobs
        threading.Thread(
            target=self._dispatcher_loop,
            daemon=True
        ).start()

        time.sleep(1)

    # ---------- processing power controls ----------

    def set_enabled(self, enabled: bool):
        """Turn this node's donation on/off."""
        self.enabled_flag["enabled"] = bool(enabled)

    def set_max_workers(self, n: int):
        """
        Change max_workers for *future* runs.
        (Current worker pool size is fixed until restart in this simple version.)
        """
        self.max_workers = int(n)

    # ---------- function registration ----------

    def register(self, func, name=None):
        """Register a function to be callable across the cluster."""
        if name is None:
            name = func.__name__
        self.func_registry[name] = func
        return name

    # ---------- internal networking ----------

    def _send_job_once(self, host, port, func_name, args, kwargs):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(JOB_TIMEOUT)
        s.connect((host, port))
        send_json(s, {
            "func_name": func_name,
            "args": args,
            "kwargs": kwargs
        })
        resp = recv_json(s)
        s.close()
        return resp

    def _run_job_with_retries(self, job_id, func_name, args, kwargs):
        workers = self.registry.sorted_workers(include_self=True)
        if not workers:
            workers = [(self.host, self.port)]

        for attempt in range(JOB_RETRIES + 1):
            for host, port in workers:
                start = time.time()
                try:
                    resp = self._send_job_once(host, port, func_name, args, kwargs)
                    duration = time.time() - start
                    self.registry.record_duration(host, port, duration)

                    if resp and resp.get("ok"):
                        with self.results_lock:
                            self.results[job_id] = resp["result"]
                        return
                except Exception:
                    continue

        with self.results_lock:
            self.results[job_id] = None

    # ---------- dispatcher loop & job queue ----------

    def _dispatcher_loop(self):
        while not self.stop_event.is_set():
            try:
                job = self.job_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            job_id, func_name, args, kwargs = job
            threading.Thread(
                target=self._run_job_with_retries,
                args=(job_id, func_name, args, kwargs),
                daemon=True
            ).start()

    # ---------- public sync API ----------

    def map(self, func, iterable):
        """Parallel map using a registered function."""
        func_name = self.register(func)
        items = list(iterable)
        job_ids = []

        for item in items:
            with self.results_lock:
                job_id = self.job_counter
                self.job_counter += 1
            job_ids.append(job_id)
            self.job_queue.put((job_id, func_name, (item,), {}))

        while True:
            with self.results_lock:
                done = all(jid in self.results for jid in job_ids)
            if done:
                break
            time.sleep(0.01)

        with self.results_lock:
            out = [self.results.pop(jid) for jid in job_ids]
        return out

    # ---------- public async API ----------

    async def amap(self, func, iterable):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.map, func, iterable)

    # ---------- shutdown ----------

    def stop(self):
        self.stop_event.set()
