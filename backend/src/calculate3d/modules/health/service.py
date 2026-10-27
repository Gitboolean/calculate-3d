"""Health checks — no FastAPI/SQL imports, so it stays unit-testable."""

from collections.abc import Callable
from typing import Literal


def db_status(ping: Callable[[], bool]) -> Literal["ok", "down"]:
    return "ok" if ping() else "down"
