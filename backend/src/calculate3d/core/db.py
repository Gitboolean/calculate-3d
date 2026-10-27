"""SQLite engine with the pragmas every connection needs, and the per-request connection."""

from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy import Connection, Engine, MetaData, create_engine, event

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


def get_engine(request: Request) -> Engine:
    """FastAPI dependency: the engine `create_app()` stored on `app.state`."""
    engine: Engine = request.app.state.engine
    return engine


def get_connection(engine: Annotated[Engine, Depends(get_engine)]) -> Iterator[Connection]:
    """One transaction per request, committed on success. Inject via `ConnectionDep`."""
    with engine.begin() as conn:
        yield conn


# `scope="function"` finishes the dependency (commit) before the response is sent, so a failed
# commit renders a 500 problem+json instead of a silent 200.
ConnectionDep = Annotated[Connection, Depends(get_connection, scope="function")]
