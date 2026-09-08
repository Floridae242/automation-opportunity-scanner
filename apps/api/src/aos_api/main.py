import re
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from starlette.concurrency import run_in_threadpool

from aos_api.config import Settings
from aos_api.db import DatabaseProbe, ReadinessProbe
from aos_api.errors import install_error_handlers
from aos_api.routes_analysis import analyses_router, opportunities_router, versions_router
from aos_api.routes_auth import router as auth_router
from aos_api.routes_comments import comments_router
from aos_api.routes_intake import processes_router, projects_router


def create_app(
    probe: ReadinessProbe | None = None,
    settings: Settings | None = None,
    engine: Engine | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        resolved = app.state.settings
        database = probe if probe is not None else DatabaseProbe(resolved or Settings())
        app.state.database = database
        try:
            yield
        finally:
            await run_in_threadpool(database.close)
            if app.state.own_engine is not None:
                app.state.own_engine.dispose()

    app = FastAPI(title="Automation Opportunity Scanner", version="0.1.0", lifespan=lifespan)
    try:
        app.state.settings = settings if settings is not None else Settings()
    except Exception:
        app.state.settings = None
    own_engine = None
    factory = None
    try:
        if engine is not None:
            factory = sessionmaker(bind=engine, expire_on_commit=False)
        elif app.state.settings is not None:
            own_engine = create_engine(
                app.state.settings.database_url.get_secret_value(), pool_pre_ping=True
            )
            factory = sessionmaker(bind=own_engine, expire_on_commit=False)
    except Exception:
        own_engine = None
        factory = None
    app.state.own_engine = own_engine
    app.state.session_factory = factory

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

    install_error_handlers(app)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(processes_router)
    app.include_router(analyses_router)
    app.include_router(versions_router)
    app.include_router(comments_router)
    app.include_router(opportunities_router)

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
