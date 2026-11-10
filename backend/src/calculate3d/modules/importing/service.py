"""importing — slicer-file parsing and filament mappings. No FastAPI/SQL imports; `catalog` calls
`remember_mappings` inside its item-save transaction, never `repo`/`tables` (ADR 0003, ADR 0005).
"""

from collections.abc import Sequence

from calculate3d.core.errors import AppError
from calculate3d.modules.importing import repo
from calculate3d.modules.importing.schemas import FilamentMappingInput
from calculate3d.modules.pricing import service as pricing_service

__all__ = ["FilamentMappingInput", "ImportPlasticNotFound", "remember_mappings"]


class ImportPlasticNotFound(AppError):
    def __init__(self, index: int) -> None:
        super().__init__(
            "importing.plastic_not_found",
            "Plastic not found",
            422,
            field=f"filament_mappings.{index}.plastic_id",
        )


def _first_unknown(conn: repo.DbConnection, mappings: Sequence[FilamentMappingInput]) -> int | None:
    ids = {m.plastic_id for m in mappings}
    known = {p.id for p in pricing_service.list_plastics_by_ids(conn, ids)}
    return next((i for i, m in enumerate(mappings) if m.plastic_id not in known), None)


def remember_mappings(conn: repo.DbConnection, mappings: Sequence[FilamentMappingInput]) -> None:
    """Upsert on the caller's Connection — no transaction of its own (ADR 0003)."""
    if not mappings:
        return
    if (index := _first_unknown(conn, mappings)) is not None:
        raise ImportPlasticNotFound(index)
    records = [
        repo.MappingRecord(m.filament_name, m.filament_color, m.plastic_id) for m in mappings
    ]
    try:
        repo.upsert_mappings(conn, records)
    except repo.MappingPlasticMissing as exc:
        # A plastic vanished after the pre-check; point at the first one that is gone now.
        raise ImportPlasticNotFound(_first_unknown(conn, mappings) or 0) from exc
