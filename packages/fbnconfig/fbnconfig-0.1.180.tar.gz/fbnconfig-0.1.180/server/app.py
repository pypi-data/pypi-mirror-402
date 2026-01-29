import json
import logging
import os
import pathlib
import time
import uuid
from datetime import datetime, timezone

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

logger = logging.getLogger("fbnconfig.server")


def _get_request_ids(request: Request) -> tuple[str, str | None]:
    """Return (request_id, correlation_id).

    Uses LUSID Web API header convention: CorrelationId.
    """
    correlation_id = request.headers.get("CorrelationId")
    request_id = f"page:fbnconfig-api,pageInstance:{uuid.uuid4()}" # Mimic LUSID's style for pageInstance
    return request_id, correlation_id


def _configure_logging(level_name: str = "INFO") -> None:
    level = logging.getLevelNamesMapping().get(level_name.upper().strip(), logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers: # Checking if handlers is none, to avoid adding duplicate logging handlers
        logging.basicConfig(level=level)
    else:
        root_logger.setLevel(level)


_configure_logging(os.getenv("LOG_LEVEL", "INFO"))


# Startup tracking for readiness probe
_app_started_at = None


def _json_log(level: int, event: str, **fields):
    log_data = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
    logger.log(level, json.dumps(log_data))


def get_examples_path():
    return pathlib.Path(__file__).parent.parent / "public_examples" / "examples"


async def homepage(_: Request):
    return JSONResponse({"message": "Hello, Banana!", "status": "success"})


async def health_check(_: Request):
    return JSONResponse({"status": "healthy", "service": "fbnconfig-api"})


async def ready_check(_: Request):
    # Returns 503 until startup event completes, then 200
    if _app_started_at is None:
        return JSONResponse({"status": "not_ready", "service": "fbnconfig-api"}, status_code=503)
    return JSONResponse({
        "status": "ready","service": "fbnconfig-api","started_at": _app_started_at.isoformat()
    })


async def get_schema(_):
    return JSONResponse(SCHEMA)


async def invoke(request: Request) -> JSONResponse:
    # Minimal callable endpoint to validate POST routing, JSON parsing, Middleware and Error logging.
    try:
        payload = await request.json()
    except Exception as exc:
        payload = None
        _json_log(
            logging.WARNING,
            "json_parse_failed",
            request_id=getattr(request.state, "request_id", None),
            correlation_id=getattr(request.state, "correlation_id", None),
            error=str(exc),
        )
    return JSONResponse({"status": "ok", "received": payload})

# Lists available Python example files with their API paths
async def list_examples(request: Request) -> JSONResponse:
    example_folder = get_examples_path()
    if not example_folder.exists():
        _json_log(
            logging.WARNING,
            "examples_folder_missing",
            path=str(example_folder)
        )
        return JSONResponse(
            {"examples": [], "message": "No examples folder found."},
            status_code=404
        )
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

    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f'Example "{example_name}" not found')

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


class RequestLogger(BaseHTTPMiddleware):

    # Constants for duration calculation
    MS_IN_SECOND = 1000
    DURATION_PRECISION = 3

    async def dispatch(self, request: Request, call_next):

        # Extract existing IDs from headers or generate new ones for traceability
        request_id, correlation_id = _get_request_ids(request)
        
        # Store IDs in request state so downstream handlers can access them
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        # Record start time for duration calculation
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            # Log the error before re-raising so we capture failed requests
            self._log_request(
                level=logging.ERROR,
                event="request_error",
                request=request,
                request_id=request_id,
                correlation_id=correlation_id,
                error=str(exc),
                start_time=start_time
            )
            raise

        # Add correlation ID to response headers for client-side tracing
        if correlation_id:
            response.headers["CorrelationId"] = correlation_id

        # Log successful request completions 
        self._log_request(
            level=logging.INFO,
            event="request_complete",
            request=request,
            request_id=request_id,
            correlation_id=correlation_id,
            status=response.status_code,
            start_time=start_time
        )
        return response

    def _log_request(self, *, level, event, request, request_id, correlation_id, start_time, **extra):
        """Log request details in structured JSON for observability."""
        duration_ms = round((time.perf_counter() - start_time) * self.MS_IN_SECOND, self.DURATION_PRECISION)
        _json_log(
            level,
            event,
            request_id=request_id,
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
            **extra
        )

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


middleware = [Middleware(RequestLogger), Middleware(PassThruAuth)]
routes = [
    Route("/", homepage),
    Route("/health", health_check),
    Route("/ready", ready_check),
    Route("/invoke", invoke, methods=["POST"]),
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


@app.router.on_event("startup")
async def startup():
    """Record startup time and log structured event for observability."""
    global _app_started_at
    _app_started_at = datetime.now(timezone.utc)
    try:
        _json_log(
            logging.INFO,
            "app_startup",
            timestamp=_app_started_at.isoformat(),
            version=getattr(fbnconfig, "__version__", "unknown")
        )
    except Exception as exc:
        logger.error(f"Startup logging failed: {exc}")

@app.router.on_event("shutdown")
async def shutdown():
    """Log structured shutdown event for observability."""
    try:
        _json_log(
            logging.INFO,
            "app_shutdown",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception as exc:
        logger.error(f"Shutdown logging failed: {exc}")