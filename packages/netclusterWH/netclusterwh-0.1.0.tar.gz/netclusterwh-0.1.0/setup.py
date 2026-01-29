from setuptools import setup, find_packages

setup(
    name="netclusterWH",
    version="0.1.0",
    description="Distributed compute network using WebSockets. Clients are also workers.",
    author="Your Name",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "websockets>=10.0"
    ],
    entry_points={
        "console_scripts": [
            "netcluster-server=netclusterWH.cli.server_cli:main",
            "netcluster-client=netclusterWH.cli.client_cli:main",
        ]
    }
)