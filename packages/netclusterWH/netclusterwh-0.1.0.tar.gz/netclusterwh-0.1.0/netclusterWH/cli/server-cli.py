import argparse
import asyncio
from netclusterWH.server.server import start_server

def main():
    parser = argparse.ArgumentParser(prog="netclusterwh-server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    asyncio.run(start_server(args.host, args.port))
