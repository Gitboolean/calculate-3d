"""Health checks — no FastAPI/SQL imports, so it stays unit-testable."""

from collections.abc import Callable
from typing import Literal

from calculate3d.modules.health import repo


def db_status(ping: Callable[[], bool]) -> Literal["ok", "down"]:
    return "ok" if ping() else "down"


def check_db(engine: repo.DbEngine) -> Literal["ok", "down"]:
    return db_status(lambda: repo.ping(engine))
