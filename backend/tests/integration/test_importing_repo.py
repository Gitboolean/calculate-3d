from collections.abc import Iterator

import pytest
from sqlalchemy import Connection, Engine, delete, select

from calculate3d.modules.importing import repo
from calculate3d.modules.importing.tables import filament_mappings
from calculate3d.modules.pricing.tables import plastics
from tests.factories import make_filament_mapping, make_plastic

PLA = "Bambu PLA Basic @BBL A1M"
PETG = "Bambu PETG Basic @BBL A1M"


@pytest.fixture
def conn(engine: Engine) -> Iterator[Connection]:
    with engine.begin() as connection:
        yield connection


def _rows(conn: Connection) -> list[tuple[str, ...]]:
    c = filament_mappings.c
    stmt = select(c.id, c.filament_name, c.filament_color, c.plastic_id, c.created_at)
    return [tuple(row) for row in conn.execute(stmt.order_by(c.filament_color))]


def test_find_returns_plastic_ids_only_for_stored_pairs(conn: Connection) -> None:
    white = make_plastic(conn, name="PLA білий", price_per_kg_kop=40000)
    black = make_plastic(conn)
    make_filament_mapping(conn, plastic_id=white)
    make_filament_mapping(conn, plastic_id=black, filament_name=PETG, filament_color="#000000")

    found = repo.find_mappings(
        conn,
        [
            (PLA, "#FFFFFF"),
            (PETG, "#000000"),
            (PLA, "#000000"),  # same preset, another color — another mapping (AC-09)
            (PLA.lower(), "#FFFFFF"),  # name match is case-sensitive (AC-09)
        ],
    )

    assert found == {(PLA, "#FFFFFF"): white, (PETG, "#000000"): black}


def test_find_handles_32_pairs_and_no_pairs(conn: Connection) -> None:
    plastic = make_plastic(conn)
    pairs = [(PLA, f"#0000{n:02X}") for n in range(32)]
    for name, color in pairs[::2]:
        make_filament_mapping(conn, plastic_id=plastic, filament_name=name, filament_color=color)

    assert repo.find_mappings(conn, pairs) == {pair: plastic for pair in pairs[::2]}
    assert repo.find_mappings(conn, []) == {}


def test_upsert_replaces_only_the_plastic_and_keeps_id_and_created_at(conn: Connection) -> None:
    first = make_plastic(conn, name="PLA білий", price_per_kg_kop=40000)
    second = make_plastic(conn)
    repo.upsert_mappings(conn, [repo.MappingRecord(PLA, "#FFFFFF", first)])
    (before,) = _rows(conn)

    repo.upsert_mappings(conn, [repo.MappingRecord(PLA, "#FFFFFF", second)])

    (after,) = _rows(conn)
    assert after == (before[0], PLA, "#FFFFFF", second, before[4])


def test_two_pairs_may_point_at_one_plastic(conn: Connection) -> None:
    plastic = make_plastic(conn)

    repo.upsert_mappings(
        conn,
        [repo.MappingRecord(PLA, "#FFFFFF", plastic), repo.MappingRecord(PETG, "#000000", plastic)],
    )

    assert repo.find_mappings(conn, [(PLA, "#FFFFFF"), (PETG, "#000000")]) == {
        (PLA, "#FFFFFF"): plastic,
        (PETG, "#000000"): plastic,
    }


def test_deleted_plastic_is_never_found_again(conn: Connection) -> None:
    plastic = make_plastic(conn)
    make_filament_mapping(conn, plastic_id=plastic)

    conn.execute(delete(plastics).where(plastics.c.id == plastic))

    assert repo.find_mappings(conn, [(PLA, "#FFFFFF")]) == {}


def test_missing_plastic_becomes_a_repo_exception(engine: Engine) -> None:
    with engine.connect() as conn:
        with pytest.raises(repo.MappingPlasticMissing):
            repo.upsert_mappings(conn, [repo.MappingRecord(PLA, "#FFFFFF", "no-such-plastic")])
        assert _rows(conn) == []
