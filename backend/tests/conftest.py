import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from calculate3d.core.config import BACKEND_DIR, Settings
from calculate3d.core.db import create_db_engine
from calculate3d.main import create_app

# TestClient sends `Host: testserver`; let the request guard accept it in every test-built Settings.
os.environ.setdefault("CALC3D_EXTRA_ALLOWED_HOSTS", '["testserver"]')


def alembic_config(database_url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


@pytest.fixture(scope="session")
def migrated_db_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A SQLite file migrated to head once per session; every test copies it."""
    db_path: Path = tmp_path_factory.mktemp("template") / "template.db"
    url = f"sqlite:///{db_path}"
    command.upgrade(alembic_config(url), "head")
    # WAL may still hold pages: fold them into the main file so a plain copy is complete.
    eng = create_db_engine(url)
    # Raw connection: pooled ones open BEGIN IMMEDIATE, which blocks a checkpoint.
    raw = eng.raw_connection()
    try:
        raw.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        raw.close()
    eng.dispose()
    return db_path


@pytest.fixture
def engine(migrated_db_template: Path, tmp_path: Path) -> Iterator[Engine]:
    """A private, migrated SQLite file per test — no data leaks between tests."""
    db_path = tmp_path / "test.db"
    shutil.copyfile(migrated_db_template, db_path)
    eng = create_db_engine(f"sqlite:///{db_path}")
    yield eng
    eng.dispose()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    app = create_app(Settings(database_url=str(engine.url)))
    with TestClient(app) as c:
        yield c
