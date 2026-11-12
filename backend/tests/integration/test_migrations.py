from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import Engine, delete, inspect, select, text
from sqlalchemy.exc import IntegrityError

from calculate3d.core.db import create_db_engine
from calculate3d.modules.importing.tables import filament_mappings
from calculate3d.modules.pricing.tables import plastics
from tests.conftest import alembic_config
from tests.factories import make_filament_mapping, make_plastic


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
        assert {"plastics", "price_settings", "items", "item_plastics", "filament_mappings"} <= set(
            insp.get_table_names()
        )
        with engine.connect() as conn:
            fks = conn.execute(text("PRAGMA foreign_key_list(item_plastics)")).mappings().all()
            indexes = set(
                conn.execute(text("SELECT name FROM sqlite_master WHERE type = 'index'")).scalars()
            )
            mapping_fks = (
                conn.execute(text("PRAGMA foreign_key_list(filament_mappings)")).mappings().all()
            )
        on_delete = {fk["table"]: fk["on_delete"] for fk in fks}
        assert on_delete == {"plastics": "RESTRICT", "items": "CASCADE"}
        assert {(fk["table"], fk["on_delete"]) for fk in mapping_fks} == {("plastics", "CASCADE")}
        assert {
            "uq_plastics_name_key",
            "uq_items_name_key",
            "idx_item_plastics_plastic_id",
            "uq_filament_mappings_name_color",
            "idx_filament_mappings_plastic_id",
        } <= indexes
    finally:
        engine.dispose()


def test_deleting_a_plastic_cascades_to_its_filament_mappings(engine: Engine) -> None:
    with engine.begin() as conn:
        kept = make_plastic(conn, name="PLA білий", price_per_kg_kop=40000)
        gone = make_plastic(conn)
        make_filament_mapping(conn, plastic_id=kept)
        make_filament_mapping(
            conn,
            plastic_id=gone,
            filament_name="Bambu PETG Basic @BBL A1M",
            filament_color="#000000",
        )

        conn.execute(delete(plastics).where(plastics.c.id == gone))

        rows = conn.execute(select(filament_mappings.c.plastic_id)).scalars().all()
    assert rows == [kept]


def test_duplicate_filament_name_and_color_is_rejected(engine: Engine) -> None:
    with engine.connect() as conn:
        plastic_id = make_plastic(conn)
        make_filament_mapping(conn, plastic_id=plastic_id)
        with pytest.raises(IntegrityError):
            make_filament_mapping(conn, plastic_id=plastic_id)
