from pathlib import Path

from alembic import command
from sqlalchemy import inspect, text

from calculate3d.core.db import create_db_engine
from tests.conftest import alembic_config


def test_migrations_upgrade_downgrade_upgrade_cleanly(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'm.db'}"
    cfg = alembic_config(url)

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    engine = create_db_engine(url)
    assert "alembic_version" in inspect(engine).get_table_names()


def test_fresh_connection_has_foreign_keys_and_wal(tmp_path: Path) -> None:
    engine = create_db_engine(f"sqlite:///{tmp_path / 'p.db'}")
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
