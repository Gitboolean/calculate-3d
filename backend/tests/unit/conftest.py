from collections.abc import Iterator

import pytest
from sqlalchemy import Connection

import calculate3d.modules.catalog.tables
import calculate3d.modules.pricing.tables  # noqa: F401 — register tables on the shared metadata
from calculate3d.core.db import create_db_engine, metadata


@pytest.fixture
def conn() -> Iterator[Connection]:
    """In-memory SQLite with every module's tables — no file I/O."""
    engine = create_db_engine("sqlite://")
    with engine.begin() as connection:
        metadata.create_all(connection)
        yield connection
    engine.dispose()
