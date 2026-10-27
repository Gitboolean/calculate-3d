"""SQLite engine with the pragmas every connection needs, and the per-request connection."""

from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Connection, Engine, MetaData, create_engine, event

from calculate3d.core.config import get_settings

# Shared MetaData for every module's `tables.py`.
metadata = MetaData()


def _set_sqlite_pragmas(dbapi_conn: Any, _record: Any) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def create_db_engine(url: str) -> Engine:
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_db_engine(get_settings().database_url)
    return _engine


def get_connection(engine: Annotated[Engine, Depends(get_engine)]) -> Iterator[Connection]:
    """FastAPI dependency: one transaction per request, committed on success."""
    with engine.begin() as conn:
        yield conn
