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
    try:
        assert "alembic_version" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_fresh_connection_has_foreign_keys_and_wal(tmp_path: Path) -> None:
    engine = create_db_engine(f"sqlite:///{tmp_path / 'p.db'}")
    try:
        with engine.connect() as conn:
            assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
            assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
    finally:
        engine.dispose()


def test_head_schema_has_feature_tables_indexes_and_fk_actions(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 's.db'}"
    command.upgrade(alembic_config(url), "head")

    engine = create_db_engine(url)
    try:
        insp = inspect(engine)
        assert {"plastics", "price_settings", "items", "item_plastics"} <= set(
            insp.get_table_names()
        )
        with engine.connect() as conn:
            fks = conn.execute(text("PRAGMA foreign_key_list(item_plastics)")).mappings().all()
            indexes = set(
                conn.execute(text("SELECT name FROM sqlite_master WHERE type = 'index'")).scalars()
            )
        on_delete = {fk["table"]: fk["on_delete"] for fk in fks}
        assert on_delete == {"plastics": "RESTRICT", "items": "CASCADE"}
        assert {"uq_plastics_name_key", "uq_items_name_key", "idx_item_plastics_plastic_id"} <= (
            indexes
        )
    finally:
        engine.dispose()
