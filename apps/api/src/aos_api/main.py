import re
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from aos_api.config import Settings
from aos_api.db import DatabaseProbe, ReadinessProbe


def create_app(probe: ReadinessProbe | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = probe if probe is not None else DatabaseProbe(Settings())
        app.state.database = database
        try:
            yield
        finally:
            await run_in_threadpool(database.close)

    app = FastAPI(title="Automation Opportunity Scanner", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get("x-request-id", "")
        identifier = supplied if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", supplied) else str(uuid4())
        request.state.request_id = identifier
        response = await call_next(request)
        response.headers["x-request-id"] = identifier
        return response

    @app.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    def ready(request: Request) -> JSONResponse:
        is_ready = request.app.state.database.check()
        return JSONResponse(
            {"status": "ready" if is_ready else "not_ready"}, status_code=200 if is_ready else 503
        )

    return app
