"""catalog persistence — items with their plastic usage rows, read in fixed-size batches."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Connection, delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from calculate3d.modules.catalog.tables import item_plastics, items

# Lets the service type the connection without importing SQLAlchemy.
DbConnection = Connection


class NameKeyTaken(Exception):
    """The UNIQUE name_key index rejected a write (the service pre-checks; this is the backstop)."""


@dataclass(frozen=True, order=True)
class UsageRecord:
    plastic_id: str
    usage_cg: int


@dataclass(frozen=True)
class ItemRecord:
    id: str
    name: str
    print_time_s: int
    usage: tuple[UsageRecord, ...]


_ITEM_COLUMNS = (items.c.id, items.c.name, items.c.print_time_s)
_USAGE_ORDER = (item_plastics.c.item_id, item_plastics.c.plastic_id)


def find_item_id_by_name_key(conn: Connection, name_key: str) -> str | None:
    return conn.execute(select(items.c.id).where(items.c.name_key == name_key)).scalar()


def insert_item(conn: Connection, record: ItemRecord, name_key: str) -> None:
    values = {"name": record.name, "name_key": name_key, "print_time_s": record.print_time_s}
    try:
        conn.execute(insert(items).values(id=record.id, **values))
    except IntegrityError as exc:
        raise NameKeyTaken from exc


def update_item(conn: Connection, record: ItemRecord, name_key: str) -> None:
    values = {"name": record.name, "name_key": name_key, "print_time_s": record.print_time_s}
    try:
        conn.execute(update(items).where(items.c.id == record.id).values(**values))
    except IntegrityError as exc:
        raise NameKeyTaken from exc


def replace_usage(conn: Connection, item_id: str, rows: Sequence[UsageRecord]) -> None:
    """Rewrite all usage rows of an item; the caller's transaction makes it atomic."""
    conn.execute(delete(item_plastics).where(item_plastics.c.item_id == item_id))
    conn.execute(
        insert(item_plastics),
        [{"item_id": item_id, "plastic_id": r.plastic_id, "usage_cg": r.usage_cg} for r in rows],
    )


def get_item(conn: Connection, item_id: str) -> ItemRecord | None:
    row = conn.execute(select(*_ITEM_COLUMNS).where(items.c.id == item_id)).first()
    if row is None:
        return None
    usage = conn.execute(
        select(item_plastics.c.plastic_id, item_plastics.c.usage_cg)
        .where(item_plastics.c.item_id == item_id)
        .order_by(*_USAGE_ORDER)
    )
    return ItemRecord(*row, usage=tuple(UsageRecord(*u) for u in usage))


def list_items_with_usage(conn: Connection) -> list[ItemRecord]:
    """The whole catalog in two queries, whatever its size (ADR 0003)."""
    item_rows = conn.execute(select(*_ITEM_COLUMNS)).all()
    usage: defaultdict[str, list[UsageRecord]] = defaultdict(list)
    usage_rows = conn.execute(
        select(
            item_plastics.c.item_id, item_plastics.c.plastic_id, item_plastics.c.usage_cg
        ).order_by(*_USAGE_ORDER)
    )
    for item_id, plastic_id, usage_cg in usage_rows:
        usage[item_id].append(UsageRecord(plastic_id, usage_cg))
    return [ItemRecord(*row, usage=tuple(usage[row.id])) for row in item_rows]


def delete_item(conn: Connection, item_id: str) -> bool:
    return conn.execute(delete(items).where(items.c.id == item_id)).rowcount > 0


def item_names_using_plastic(conn: Connection, plastic_id: str) -> list[str]:
    stmt = (
        select(items.c.name)
        .join(item_plastics, item_plastics.c.item_id == items.c.id)
        .where(item_plastics.c.plastic_id == plastic_id)
    )
    return list(conn.execute(stmt).scalars())
