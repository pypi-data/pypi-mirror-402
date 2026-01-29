from setuptools import setup, find_packages

setup(
    name="worldcluster",
    version="1.1.0",
    description="A lightweight distributed parallel processing cluster for LAN/Tailscale/ZeroTier networks.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.8",
    entry_points={
    "console_scripts": [
        "worldcluster=worldcluster.cli:main",
    ]
},
)
