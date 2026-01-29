import asyncio
import json
import websockets
from collections import deque

workers = set()
pending_jobs = {}
job_queue = deque()
job_counter = 0
lock = asyncio.Lock()
worker_ids = {}
worker_uploaded_functions = {}  # worker_id -> set(func_names)
next_worker_id = 1

async def register_worker(ws):
    global next_worker_id
    worker_id = next_worker_id
    next_worker_id += 1

    worker_ids[ws] = worker_id
    worker_uploaded_functions[worker_id] = set()

    workers.add(ws)
    print(f"Worker {worker_id} connected")


async def unregister_worker(ws):
    worker_id = worker_ids.get(ws)
    if worker_id:
        funcs = worker_uploaded_functions.get(worker_id, set())

        # Tell all workers to delete these functions
        for w in workers:
            await w.send(json.dumps({
                "type": "delete_functions",
                "names": list(funcs)
            }))

        del worker_uploaded_functions[worker_id]
        del worker_ids[ws]

    workers.discard(ws)
    print("Worker disconnected")


async def assign_jobs():
    while True:
        await asyncio.sleep(0.01)
        async with lock:
            if not job_queue or not workers:
                continue

            job_id, payload, client_ws = job_queue.popleft()
            worker = next(iter(workers))

            await worker.send(json.dumps({
                "type": "job",
                "job_id": job_id,
                "payload": payload
            }))

async def handle_client(ws):
    global job_counter
    await register_worker(ws)

    try:
        async for msg in ws:
            data = json.loads(msg)

            if data["type"] == "submit":
                func = data["func"]
                items = data["data"]

                job_id = job_counter
                job_counter += 1

                pending_jobs[job_id] = {
                    "client": ws,
                    "results": None
                }

                job_queue.append((job_id, {"func": func, "data": items}, ws))

            elif data["type"] == "result":
                job_id = data["job_id"]
                results = data["results"]

                job = pending_jobs.pop(job_id, None)
                if job:
                    client_ws = job["client"]
                    await client_ws.send(json.dumps({
                        "type": "done",
                        "job_id": job_id,
                        "results": results
                    }))
            elif data["type"] == "upload_function":
                name = data["name"]
                code = data["code"]

                # Broadcast to all workers
            for w in workers:
                await w.send(json.dumps({
                    "type": "upload_function",
                    "name": name,
                    "code": code
                }))

            await ws.send(json.dumps({"type": "upload_ok"}))


    finally:
        await unregister_worker(ws)

async def start_server(host="0.0.0.0", port=8765):
    asyncio.create_task(assign_jobs())
    print(f"Server running on ws://{host}:{port}")
    async with websockets.serve(handle_client, host, port):
        await asyncio.Future()
