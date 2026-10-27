from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Engine

from calculate3d.core.db import get_engine
from calculate3d.modules.health import service
from calculate3d.modules.health.schemas import HealthOut

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def get_health(engine: Annotated[Engine, Depends(get_engine)]) -> HealthOut:
    return HealthOut(status="ok", db=service.check_db(engine))
