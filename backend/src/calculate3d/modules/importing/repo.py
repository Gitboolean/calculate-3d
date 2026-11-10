"""importing persistence — filament mappings on the caller's Connection (data-model.md)."""

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from sqlalchemy import Connection, select, tuple_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError

from calculate3d.core.ids import new_id
from calculate3d.modules.importing.tables import filament_mappings

# Lets the service type the connection without importing SQLAlchemy.
DbConnection = Connection

FilamentKey = tuple[str, str]  # (filament_name, filament_color), both already normalized


class MappingPlasticMissing(Exception):
    """The FK on filament_mappings.plastic_id rejected a write (the service pre-checks)."""


@dataclass(frozen=True)
class MappingRecord:
    filament_name: str
    filament_color: str
    plastic_id: str


def find_mappings(conn: Connection, keys: Collection[FilamentKey]) -> dict[FilamentKey, str]:
    """Remembered plastic of each stored key — one query on uq_filament_mappings_name_color."""
    if not keys:
        return {}
    c = filament_mappings.c
    rows = conn.execute(
        select(c.filament_name, c.filament_color, c.plastic_id).where(
            tuple_(c.filament_name, c.filament_color).in_(list(keys))
        )
    )
    return {(name, color): plastic_id for name, color, plastic_id in rows}


def upsert_mappings(conn: Connection, records: Sequence[MappingRecord]) -> None:
    """Insert new keys, repoint existing ones; `id` and `created_at` of a known key stay."""
    stmt = sqlite_insert(filament_mappings)
    stmt = stmt.on_conflict_do_update(
        index_elements=[filament_mappings.c.filament_name, filament_mappings.c.filament_color],
        set_={"plastic_id": stmt.excluded.plastic_id},
    )
    try:
        conn.execute(
            stmt,
            [
                {
                    "id": new_id(),
                    "filament_name": r.filament_name,
                    "filament_color": r.filament_color,
                    "plastic_id": r.plastic_id,
                }
                for r in records
            ],
        )
    except IntegrityError as exc:
        raise MappingPlasticMissing from exc
