from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from sqlalchemy import Connection, Engine, delete, event, func, select
from sqlalchemy.exc import IntegrityError

from calculate3d.modules.catalog import repo
from calculate3d.modules.catalog.tables import item_plastics, items
from calculate3d.modules.pricing.tables import plastics
from tests.factories import make_item, make_plastic, seed_catalog_volume


@contextmanager
def count_queries(conn: Connection) -> Iterator[list[str]]:
    statements: list[str] = []

    def record(*args: Any) -> None:
        statements.append(args[2])

    event.listen(conn, "before_cursor_execute", record)
    try:
        yield statements
    finally:
        event.remove(conn, "before_cursor_execute", record)


@pytest.fixture
def conn(engine: Engine) -> Iterator[Connection]:
    with engine.begin() as connection:
        yield connection


def test_item_is_written_with_its_usage_rows(conn: Connection) -> None:
    petg = make_plastic(conn, name="PETG чорний")
    pla = make_plastic(conn, name="PLA білий")

    repo.insert_item(conn, repo.ItemRecord("i1", "Брелок-тризуб", 12600, ()), "брелок-тризуб")
    repo.replace_usage(conn, "i1", [repo.UsageRecord(petg, 12000), repo.UsageRecord(pla, 500)])

    item = repo.get_item(conn, "i1")
    assert item is not None
    assert (item.name, item.print_time_s) == ("Брелок-тризуб", 12600)
    assert sorted(item.usage) == sorted([repo.UsageRecord(petg, 12000), repo.UsageRecord(pla, 500)])
    assert repo.find_item_id_by_name_key(conn, "брелок-тризуб") == "i1"
    assert repo.find_item_id_by_name_key(conn, "інше") is None


def test_update_and_replace_usage_overwrite_the_item(conn: Connection) -> None:
    petg = make_plastic(conn, name="PETG чорний")
    pla = make_plastic(conn, name="PLA білий")
    item_id = make_item(conn, name="Підставка", usage={petg: 1000})

    repo.update_item(conn, repo.ItemRecord(item_id, "Підставка нова", 7200, ()), "підставка нова")
    repo.replace_usage(conn, item_id, [repo.UsageRecord(pla, 300)])

    assert repo.get_item(conn, item_id) == repo.ItemRecord(
        item_id, "Підставка нова", 7200, (repo.UsageRecord(pla, 300),)
    )


def test_name_key_conflict_raises_the_repo_error(conn: Connection) -> None:
    make_item(conn, name="Брелок-тризуб", usage={make_plastic(conn): 100})

    with pytest.raises(repo.NameKeyTaken):
        repo.insert_item(conn, repo.ItemRecord("i2", "брелок-тризуб", 60, ()), "брелок-тризуб")


def test_unknown_item_is_none(conn: Connection) -> None:
    assert repo.get_item(conn, "missing") is None
    assert repo.delete_item(conn, "missing") is False


def test_deleting_an_item_cascades_its_usage_rows(conn: Connection) -> None:
    petg = make_plastic(conn)
    item_id = make_item(conn, usage={petg: 100})

    assert repo.delete_item(conn, item_id) is True

    assert conn.execute(select(func.count()).select_from(item_plastics)).scalar() == 0
    assert conn.execute(select(func.count()).select_from(items)).scalar() == 0


def test_a_used_plastic_cannot_be_deleted_at_the_db_level(conn: Connection) -> None:
    petg = make_plastic(conn)
    make_item(conn, usage={petg: 100})

    with pytest.raises(IntegrityError):
        conn.execute(delete(plastics).where(plastics.c.id == petg))


def test_item_names_using_a_plastic(conn: Connection) -> None:
    pla = make_plastic(conn, name="PLA білий")
    petg = make_plastic(conn, name="PETG чорний")
    make_item(conn, name="Підставка", usage={pla: 100})
    make_item(conn, name="Органайзер", usage={pla: 200, petg: 50})
    make_item(conn, name="Брелок", usage={petg: 50})

    assert sorted(repo.item_names_using_plastic(conn, pla)) == ["Органайзер", "Підставка"]
    assert repo.item_names_using_plastic(conn, make_plastic(conn, name="Новий")) == []


def test_listing_the_whole_catalog_takes_two_queries(conn: Connection) -> None:
    seed_catalog_volume(conn, items=1000, plastics=50, seed=7)

    with count_queries(conn) as statements:
        listed = repo.list_items_with_usage(conn)

    assert len(statements) == 2
    assert len(listed) == 1000
    assert all(item.usage for item in listed)
    total_rows = conn.execute(select(func.count()).select_from(item_plastics)).scalar()
    assert sum(len(item.usage) for item in listed) == total_rows


def test_empty_catalog_lists_nothing(conn: Connection) -> None:
    assert repo.list_items_with_usage(conn) == []
