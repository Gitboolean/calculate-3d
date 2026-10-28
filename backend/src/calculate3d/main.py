"""Application entry point: `create_app()` wires core and every module router."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.types import Scope

from calculate3d.core.config import Settings, get_settings
from calculate3d.core.db import create_db_engine
from calculate3d.core.errors import register_error_handlers
from calculate3d.core.guard import RequestGuard
from calculate3d.core.problems import use_problem_json_in_openapi
from calculate3d.modules.costing.router import router as costing_router
from calculate3d.modules.health.router import router as health_router
from calculate3d.modules.pricing.router import router as pricing_router

# Local-only, no auth (ADR 0004): the bind address is deliberately not configurable.
HOST = "127.0.0.1"


class SpaStaticFiles(StaticFiles):
    """Built UI: real files as-is, any other non-/api path → index.html (feature ADR 0001)."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or path == "api" or path.startswith("api/"):
                raise
            return await super().get_response("index.html", scope)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = create_db_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(title="calculate-3d", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    register_error_handlers(app)
    # No CORSMiddleware, ever: the API is same-origin only (cost-calculator ADR 0007).
    app.add_middleware(
        RequestGuard,
        allowed_hosts=settings.allowed_hosts,
        allowed_origins=settings.allowed_origins,
    )
    app.include_router(health_router)
    app.include_router(pricing_router)
    app.include_router(costing_router)
    use_problem_json_in_openapi(app)
    # Mounted last so every /api route wins over the static catch-all.
    if settings.web_dist_dir.is_dir():
        app.mount("/", SpaStaticFiles(directory=settings.web_dist_dir, html=True), name="web")
    return app


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "calculate3d.main:create_app",
        factory=True,
        host=HOST,
        port=settings.port,
    )
