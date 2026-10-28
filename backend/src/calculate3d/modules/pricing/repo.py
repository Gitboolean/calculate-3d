"""pricing persistence — SQLAlchemy Core on the per-request Connection."""

from collections.abc import Collection
from dataclasses import dataclass

from sqlalchemy import Connection, delete, insert, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError

from calculate3d.modules.pricing.tables import plastics, price_settings

# Lets the service type the connection without importing SQLAlchemy.
DbConnection = Connection

# The singleton row's fixed id (data-model.md § price_settings) — not a seed.
SETTINGS_ID = "00000000-0000-7000-8000-000000000001"

SETTINGS_FIELDS = (
    "tariff_per_kwh_kop",
    "printer_power_w",
    "printer_price_kop",
    "printer_lifetime_h",
    "parts_per_hour_kop",
    "scrap_rate_permille",
)


class NameKeyTaken(Exception):
    """The UNIQUE name_key index rejected a write (the service pre-checks; this is the backstop)."""


@dataclass(frozen=True)
class PlasticRecord:
    id: str
    name: str
    price_per_kg_kop: int


_PLASTIC_COLUMNS = (plastics.c.id, plastics.c.name, plastics.c.price_per_kg_kop)


def list_plastics(conn: Connection) -> list[PlasticRecord]:
    return [PlasticRecord(*row) for row in conn.execute(select(*_PLASTIC_COLUMNS))]


def plastics_exist(conn: Connection) -> bool:
    return conn.execute(select(plastics.c.id).limit(1)).first() is not None


def list_plastics_by_ids(conn: Connection, ids: Collection[str]) -> list[PlasticRecord]:
    rows = conn.execute(select(*_PLASTIC_COLUMNS).where(plastics.c.id.in_(ids)))
    return [PlasticRecord(*row) for row in rows]


def get_plastic(conn: Connection, plastic_id: str) -> PlasticRecord | None:
    row = conn.execute(select(*_PLASTIC_COLUMNS).where(plastics.c.id == plastic_id)).first()
    return PlasticRecord(*row) if row else None


def find_plastic_id_by_name_key(conn: Connection, name_key: str) -> str | None:
    return conn.execute(select(plastics.c.id).where(plastics.c.name_key == name_key)).scalar()


def insert_plastic(conn: Connection, record: PlasticRecord, name_key: str) -> None:
    try:
        conn.execute(
            insert(plastics).values(
                id=record.id,
                name=record.name,
                name_key=name_key,
                price_per_kg_kop=record.price_per_kg_kop,
            )
        )
    except IntegrityError as exc:
        raise NameKeyTaken from exc


def update_plastic(conn: Connection, record: PlasticRecord, name_key: str) -> None:
    try:
        conn.execute(
            update(plastics)
            .where(plastics.c.id == record.id)
            .values(name=record.name, name_key=name_key, price_per_kg_kop=record.price_per_kg_kop)
        )
    except IntegrityError as exc:
        raise NameKeyTaken from exc


def delete_plastic(conn: Connection, plastic_id: str) -> None:
    conn.execute(delete(plastics).where(plastics.c.id == plastic_id))


def get_settings(conn: Connection) -> dict[str, int] | None:
    columns = [price_settings.c[name] for name in SETTINGS_FIELDS]
    row = conn.execute(select(*columns).where(price_settings.c.id == SETTINGS_ID)).first()
    return dict(row._mapping) if row else None


def upsert_settings(conn: Connection, values: dict[str, int]) -> None:
    """Replace all six fields at once; `created_at` keeps the first save's time."""
    stmt = sqlite_insert(price_settings).values(id=SETTINGS_ID, **values)
    conn.execute(
        stmt.on_conflict_do_update(
            index_elements=[price_settings.c.id],
            set_={name: stmt.excluded[name] for name in SETTINGS_FIELDS},
        )
    )
