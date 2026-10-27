from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Connection

from calculate3d.core.db import get_connection
from calculate3d.modules.health import service
from calculate3d.modules.health.schemas import HealthOut

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def get_health(conn: Annotated[Connection, Depends(get_connection)]) -> HealthOut:
    return HealthOut(status="ok", db="ok" if service.database_ok(conn) else "down")
