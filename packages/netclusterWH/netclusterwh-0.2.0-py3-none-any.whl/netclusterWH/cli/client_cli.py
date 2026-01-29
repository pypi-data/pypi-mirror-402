import argparse
import asyncio
import json
from netclusterWH.client.worker import start_client, upload_function_file

def main():
    parser = argparse.ArgumentParser(prog="netclusterwh-client")
    parser.add_argument("uri", help="ws://yourserver:8765")

    sub = parser.add_subparsers(dest="cmd")

    # Upload a function file
    p = sub.add_parser("upload", help="Upload a Python file as a function")
    p.add_argument("file", help="Path to the .py file")
    p.add_argument("func", help="Function name inside the file")

    args = parser.parse_args()

    if args.cmd == "upload":
        asyncio.run(upload_function_file(args.uri, args.file, args.func))
        return

    # Default: run as worker
    asyncio.run(start_client(args.uri))

