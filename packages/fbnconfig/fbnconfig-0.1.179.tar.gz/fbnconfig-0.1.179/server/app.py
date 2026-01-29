import pathlib

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

import fbnconfig
from fbnconfig import log as deployment_log
from fbnconfig import schemagen
from fbnconfig.load_module import load_module


def get_examples_path():
    return pathlib.Path(__file__).parent.parent / "public_examples" / "examples"


async def homepage(_: Request):
    return JSONResponse({"message": "Hello, Banana!", "status": "success"})


async def health_check(_: Request):
    return JSONResponse({"status": "healthy", "service": "fbnconfg-api"})


async def get_schema(_):
    return JSONResponse(SCHEMA)


async def list_examples(request: Request) -> JSONResponse:
    example_folder = get_examples_path()
    files = example_folder.glob("*.py")
    res = [
        {"name": str(f.stem), "path": request.url_for("get_example", example_name=str(f.stem)).path}
        for f in files
    ]
    return JSONResponse(res)


async def get_example(request: Request):
    example_folder = get_examples_path()
    example_name = request.path_params["example_name"] + ".py"
    script_path = example_folder / example_name
    module = load_module(script_path, str(example_folder))
    if getattr(module, "configure", None) is None:
        raise HTTPException(status_code=400, detail="No configure found in " + example_name)
    deployment = module.configure({})
    dump = fbnconfig.dump_deployment(deployment)
    return JSONResponse(dump)


def create_client(lusid_env, token):
    if lusid_env is None or token is None:
        raise HTTPException(status_code=401, detail="No auth header or no X-LUSID-Host")
    client = fbnconfig.create_client(lusid_env, token)
    return client


async def get_log(request: Request):
    client = create_client(request.state.lusid_env, request.state.token)
    deployment_name = request.path_params["deployment_name"]
    log = []
    for line in deployment_log.list_resources_for_deployment(client, deployment_id=deployment_name):
        d = line._asdict()
        d["state"] = vars(d["state"])
        log.append(d)
    return JSONResponse(log)


SCHEMA = schemagen.cmd_deployment_schema()


class PassThruAuth(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            request.state.token = auth.split(" ")[1]
        else:
            request.state.token = None
        host = request.headers.get("X-LUSID-Host")
        request.state.lusid_env = host if host else None
        return await call_next(request)


middleware = [Middleware(x) for x in [PassThruAuth]]
routes = [
    Route("/", homepage),
    Route("/examples/", list_examples),
    Route("/examples/{example_name}", get_example),
    Route("/log/{deployment_name}", get_log),

    Route("/schema", get_schema, methods=["GET"]),
]

# the fbnconfig application
cfg_app = Starlette(routes=routes, middleware=middleware)

# the app that will be run to mount the cfg app
app = Starlette(routes=[
    Mount("/api/fbnconfig", cfg_app)
])
