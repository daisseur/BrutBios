from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
import atexit
import os
import json
from fastapi import FastAPI
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

app = FastAPI()
setup_filename = "server_setup.json"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Middleware to log requests
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Log the request method, path, and body
        logger.info(f"Request: {request.method} {request.url.path}")
        logger.info(f"Request Body: {await request.body()}")

        # Call the next middleware or endpoint
        response = await call_next(request)

        return response

app.add_middleware(RequestLoggingMiddleware)

class Mask(BaseModel):
    masks: list[int]

async def aprint(*args, **kwargs):
    logger.info(*args, **kwargs)


def get_setup_dict() -> dict:
    if os.path.isfile(setup_filename):
        return json.loads(open(setup_filename, 'r').read())
    else:
        return {}

def replace_setup_dict(new_setup):
    try:
        open(setup_filename, 'w').write(json.dumps(new_setup))
    except Exception as error:
        raise error
    else:
        print("Setup saved")
        return True


global_setup = get_setup_dict()


@app.post("/setup/replace/")
async def load_setup(setup_data: dict):
    global global_setup
    global_setup = setup_data
    return {"message": "Setup loaded from request body"}

@app.get("/setup/status/")
async def status_setup():
    if os.path.exists(setup_filename):
        return {"message": "Setup found"}
    else:
        return {"message": "No setup found"}

@app.delete("/setup/clear/")
async def clear_setup():
    os.remove(setup_filename)
    os.remove("combinations.hcmask")
    os.remove("selected_mask.hcmask")
    return {"message": "Setup cleared"}

@app.get("/setup/data/")
async def data_setup():
    global global_setup
    return global_setup

@app.post("/setup/update/password_length/")
async def update_password_length(password_length: int):
    global global_setup
    global_setup['password_length'] = password_length
    return {"message": f"Password length updated to {password_length}"}

@app.put("/setup/update/bad_masks/")
async def update_bad_masks(bad_masks: Mask):
    global global_setup
    for i in bad_masks:
        if i not in global_setup["bad_masks"]:
            global_setup["bad_masks"].append(i)
    return {"message": "Bad masks updated"}

@app.post("/setup/update/checkpoint_filename/")
async def update_checkpoint_filename(checkpoint_filename: str):
    global global_setup
    global_setup['checkpoint_filename'] = checkpoint_filename
    return {"message": "Checkpoint filename updated"}

@app.put("/setup/update/running_masks/{action}")
async def _running_masks(action: str, running_masks: Mask):
    global global_setup
    await aprint(f"RECEIVED {action}: {running_masks}")
    running_masks = running_masks.masks
    if action == "add":
        for i in running_masks:
            i = int(i)
            if i not in global_setup["running_masks"]:
                global_setup["running_masks"].append(i)
        return {"message": "Running masks updated"}
    elif action == "remove":
        for i in running_masks:
            i = int(i)
            if i in global_setup["running_masks"]:
                global_setup["running_masks"].remove(i)
        return {"message": "Running masks removed"}
    else:
        return {"message": "Malformed request"}



if __name__ == "__main__":
    atexit.register(lambda: replace_setup_dict(global_setup))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
