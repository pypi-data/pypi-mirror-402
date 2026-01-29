import argparse
import asyncio
from netclusterWH.client.worker import start_client

def main():
    parser = argparse.ArgumentParser(prog="netclusterwh-client")
    parser.add_argument("uri", help="ws://yourserver:8765")
    parser.add_argument("--submit-example", action="store_true")
    args = parser.parse_args()

    asyncio.run(start_client(args.uri, args.submit_example))
