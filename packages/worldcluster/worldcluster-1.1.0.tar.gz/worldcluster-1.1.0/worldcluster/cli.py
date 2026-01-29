import argparse
import sys
import json
from .worldcluster import Cluster

cluster_instance = None

def get_cluster():
    global cluster_instance
    if cluster_instance is None:
        cluster_instance = Cluster()
    return cluster_instance

def cmd_start(args):
    cluster = Cluster(max_workers=args.workers, enabled=not args.disabled)
    print(f"Cluster node started on {cluster.host}:{cluster.port}")
    print(f"Workers: {args.workers}")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        cluster.stop()
        print("Node stopped.")

def cmd_status(args):
    cluster = get_cluster()
    peers = cluster.registry.list()
    print("Your node:", cluster.host, cluster.port)
    print("Donating CPU:", cluster.enabled_flag["enabled"])
    print("Max workers:", cluster.max_workers)
    print("Peers:")
    for host, port in peers:
        print("  -", host, port)

def cmd_enable(args):
    cluster = get_cluster()
    cluster.set_enabled(True)
    print("CPU donation enabled.")

def cmd_disable(args):
    cluster = get_cluster()
    cluster.set_enabled(False)
    print("CPU donation disabled.")

def cmd_run(args):
    cluster = get_cluster()

    # Define a simple function registry for CLI use
    def square(x): return x * x
    def cube(x): return x * x * x

    functions = {
        "square": square,
        "cube": cube,
    }

    if args.func not in functions:
        print("Unknown function:", args.func)
        print("Available:", ", ".join(functions.keys()))
        sys.exit(1)

    func = functions[args.func]
    values = [json.loads(v) for v in args.values]

    print("Running distributed job...")
    results = cluster.map(func, values)
    print("Results:", results)

def main():
    parser = argparse.ArgumentParser(prog="lancluster")
    sub = parser.add_subparsers(dest="cmd")

    # start
    p = sub.add_parser("start", help="Start a cluster node")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--disabled", action="store_true")
    p.set_defaults(func=cmd_start)

    # status
    p = sub.add_parser("status", help="Show cluster status")
    p.set_defaults(func=cmd_status)

    # enable
    p = sub.add_parser("enable", help="Enable CPU donation")
    p.set_defaults(func=cmd_enable)

    # disable
    p = sub.add_parser("disable", help="Disable CPU donation")
    p.set_defaults(func=cmd_disable)

    # run
    p = sub.add_parser("run", help="Run a distributed function")
    p.add_argument("func", help="Function name")
    p.add_argument("values", nargs="+", help="Values to process")
    p.set_defaults(func=cmd_run)

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        return

    args.func(args)

if __name__ == "__main__":
    main()
