# Functions this worker can execute
import ast
import asyncio
import json
import websockets

async def upload_function_file(uri, file_path, func_name):
    with open(file_path, "r") as f:
        code = f.read()

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "type": "upload_function",
            "name": func_name,
            "code": code
        }))

        resp = json.loads(await ws.recv())
        if resp.get("type") == "upload_ok":
            print(f"Uploaded function '{func_name}' successfully")
        else:
            print("Upload failed:", resp)

SAFE_BUILTINS = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "range": range,
    "len": len
}

def is_code_safe(code):
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            return False
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ["open", "__import__", "eval", "exec"]:
                return False
        if isinstance(node, ast.Attribute):
            # Prevent things like os.system, subprocess.Popen, etc.
            return False

    return True

def load_dynamic_function(name, code, FUNCTIONS):
    if not is_code_safe(code):
        raise ValueError("Unsafe code detected")

    # Restricted execution environment
    safe_globals = {
        "__builtins__": SAFE_BUILTINS
    }
    safe_locals = {}

    exec(code, safe_globals, safe_locals)

    if name not in safe_locals:
        raise ValueError("Function not found after execution")

    FUNCTIONS[name] = safe_locals[name]

def square(x): return x * x
def cube(x): return x * x * x

FUNCTIONS = {
    "square": square,
    "cube": cube,
}

async def worker_loop(ws):
    async for msg in ws:
        data = json.loads(msg)

        if data["type"] == "job":
            job_id = data["job_id"]
            payload = data["payload"]

            fn_name = payload["func"]
            items = payload["data"]

            if fn_name not in FUNCTIONS:
                results = None
            else:
                fn = FUNCTIONS[fn_name]
                results = [fn(x) for x in items]

            await ws.send(json.dumps({
                "type": "result",
                "job_id": job_id,
                "results": results
            }))
        elif data["type"] == "upload_function":
            name = data["name"]
            code = data["code"]

            try:
                load_dynamic_function(name, code, FUNCTIONS)
                print(f"Loaded dynamic function '{name}'")
            except Exception as e:
                print("Rejected unsafe function:", e)


async def submit_job(ws, func, data):
    await ws.send(json.dumps({
        "type": "submit",
        "func": func,
        "data": data
    }))

    async for msg in ws:
        resp = json.loads(msg)
        if resp["type"] == "done":
            return resp["results"]

async def start_client(uri, submit_example=False):
    async with websockets.connect(uri) as ws:
        asyncio.create_task(worker_loop(ws))

        if submit_example:
            results = await submit_job(ws, "square", range(6))
            print("Job results:", results)

        await asyncio.Future()
