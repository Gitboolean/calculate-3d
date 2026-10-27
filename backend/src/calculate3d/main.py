"""Application entry point: `create_app()` wires core and every module router."""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from calculate3d.core.config import Settings, get_settings
from calculate3d.core.errors import register_error_handlers
from calculate3d.modules.health.router import router as health_router

# Local-only, no auth (ADR 0004): the bind address is deliberately not configurable.
HOST = "127.0.0.1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="calculate-3d", version="0.1.0")
    register_error_handlers(app)
    app.include_router(health_router)
    # Mounted last so every /api route wins over the static catch-all.
    if settings.web_dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.web_dist_dir, html=True), name="web")
    return app


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "calculate3d.main:create_app",
        factory=True,
        host=HOST,
        port=settings.port,
    )
