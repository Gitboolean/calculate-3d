from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from calculate3d.core.config import BACKEND_DIR
from calculate3d.core.db import create_db_engine, get_engine
from calculate3d.main import create_app


def alembic_config(database_url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


@pytest.fixture(scope="session")
def engine(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Engine]:
    """A real temporary SQLite file, migrated to head once per test session."""
    db_path: Path = tmp_path_factory.mktemp("db") / "test.db"
    url = f"sqlite:///{db_path}"
    command.upgrade(alembic_config(url), "head")
    eng = create_db_engine(url)
    yield eng
    eng.dispose()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_engine] = lambda: engine
    with TestClient(app) as c:
        yield c
