"""A failed `BEGIN IMMEDIATE` must surface as a SQLAlchemyError (R2-3)."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from calculate3d.core.config import Settings
from calculate3d.core.db import create_db_engine
from calculate3d.main import create_app

# Short busy timeout so a held lock fails in ~0.1 s instead of the 5 s default.
_FAST_TIMEOUT = "?timeout=0.1"


@contextmanager
def _write_lock_held(engine: Engine) -> Iterator[None]:
    """A second raw connection holds the SQLite write lock on the engine's DB file."""
    other = sqlite3.connect(engine.url.database or "", isolation_level=None)
    try:
        other.execute("BEGIN IMMEDIATE")
        yield
    finally:
        other.close()


def test_begin_failure_surfaces_as_sqlalchemy_operational_error(engine: Engine) -> None:
    locked = create_db_engine(str(engine.url) + _FAST_TIMEOUT)
    try:
        with _write_lock_held(engine), pytest.raises(OperationalError), locked.begin():
            pass
    finally:
        locked.dispose()


def test_health_stays_up_while_another_connection_holds_the_write_lock(engine: Engine) -> None:
    # WAL lets a reader through a held write lock; a busy DB is reachable, not "down".
    app = create_app(Settings(database_url=str(engine.url) + _FAST_TIMEOUT))
    with TestClient(app) as client, _write_lock_held(engine):
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}
