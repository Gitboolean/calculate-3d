"""Application entry point: `create_app()` wires core and every module router."""

import uvicorn
from fastapi import FastAPI

from calculate3d.core.config import get_settings
from calculate3d.core.errors import register_error_handlers
from calculate3d.modules.health.router import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="calculate-3d", version="0.1.0")
    register_error_handlers(app)
    app.include_router(health_router)
    return app


def run() -> None:
    settings = get_settings()
    uvicorn.run("calculate3d.main:create_app", factory=True, host=settings.host, port=settings.port)
