"""SQLite engine with the pragmas every connection needs, and the per-request connection."""

from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy import Column, Connection, Engine, MetaData, Text, create_engine, event, text

# Shared MetaData for every module's `tables.py`.
metadata = MetaData()


def created_at_column() -> Column[str]:
    """Audit column; the DB fills it (UTC ISO-8601), as in every migration."""
    return Column(
        "created_at",
        Text,
        nullable=False,
        server_default=text("(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"),
    )


def _set_sqlite_pragmas(dbapi_conn: Any, _record: Any) -> None:
    # Autocommit at the driver level: pysqlite's implicit BEGIN would defer the write lock.
    # SQLAlchemy emits the explicit BEGIN IMMEDIATE below instead.
    dbapi_conn.isolation_level = None
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def _begin_immediate(conn: Connection) -> None:
    # Take the write lock up front so a pre-check read and its write are one serialized unit.
    # Straight on the driver: not a query, so it stays out of cursor-execute statement counts.
    conn.connection.driver_connection.execute("BEGIN IMMEDIATE")  # type: ignore[union-attr]


def create_db_engine(url: str) -> Engine:
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _set_sqlite_pragmas)
        event.listen(engine, "begin", _begin_immediate)
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
