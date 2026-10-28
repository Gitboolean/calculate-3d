"""pricing — plastics and price settings. No FastAPI/SQL imports; `costing` and `catalog` call
the public functions here, never `repo`/`tables` (cost-calculator ADR 0005).
"""

from collections.abc import Callable, Collection

from calculate3d.core.errors import AppError
from calculate3d.core.ids import new_id
from calculate3d.core.money import round_half_up_kop, wear_per_hour_kop
from calculate3d.core.text import name_key, normalize_name, sort_key
from calculate3d.modules.pricing import repo
from calculate3d.modules.pricing.schemas import (
    Plastic,
    PlasticInput,
    PriceSettings,
    PriceSettingsInput,
)

# Connection type for callers (costing, catalog) that must not import pricing's repo.
DbConnection = repo.DbConnection


class PlasticNameTaken(AppError):
    def __init__(self) -> None:
        super().__init__("pricing.name_taken", "Plastic name is already taken", 409, field="name")


class PlasticNotFound(AppError):
    def __init__(self) -> None:
        super().__init__("pricing.plastic_not_found", "Plastic not found", 404)


class PlasticInUse(AppError):
    def __init__(self, item_names: list[str]) -> None:
        super().__init__(
            "pricing.plastic_in_use", "Plastic is used by catalog items", 409, items=item_names
        )


def _to_schema(record: repo.PlasticRecord) -> Plastic:
    return Plastic(id=record.id, name=record.name, price_per_kg_kop=record.price_per_kg_kop)


def list_plastics(conn: repo.DbConnection) -> list[Plastic]:
    records = sorted(repo.list_plastics(conn), key=lambda r: sort_key(r.name))
    return [_to_schema(r) for r in records]


def plastics_exist(conn: repo.DbConnection) -> bool:
    return repo.plastics_exist(conn)


def list_plastics_by_ids(conn: repo.DbConnection, ids: Collection[str]) -> list[Plastic]:
    return [_to_schema(r) for r in repo.list_plastics_by_ids(conn, ids)]


def _save_plastic(
    conn: repo.DbConnection, plastic_id: str, data: PlasticInput, *, is_new: bool
) -> Plastic:
    record = repo.PlasticRecord(plastic_id, normalize_name(data.name), data.price_per_kg_kop)
    key = name_key(record.name)
    if repo.find_plastic_id_by_name_key(conn, key) not in (None, plastic_id):
        raise PlasticNameTaken
    write = repo.insert_plastic if is_new else repo.update_plastic
    try:
        write(conn, record, key)
    except repo.NameKeyTaken as exc:
        raise PlasticNameTaken from exc
    return _to_schema(record)


def create_plastic(conn: repo.DbConnection, data: PlasticInput) -> Plastic:
    return _save_plastic(conn, new_id(), data, is_new=True)


def update_plastic(conn: repo.DbConnection, plastic_id: str, data: PlasticInput) -> Plastic:
    if repo.get_plastic(conn, plastic_id) is None:
        raise PlasticNotFound
    return _save_plastic(conn, plastic_id, data, is_new=False)


def delete_plastic(
    conn: repo.DbConnection,
    plastic_id: str,
    item_names_using: Callable[[str], list[str]],
) -> None:
    """`item_names_using` comes from the router (catalog), so pricing never imports catalog."""
    if repo.get_plastic(conn, plastic_id) is None:
        raise PlasticNotFound
    if names := item_names_using(plastic_id):
        raise PlasticInUse(sorted(names, key=sort_key))
    repo.delete_plastic(conn, plastic_id)


def _with_wear(values: dict[str, int]) -> PriceSettings:
    wear = wear_per_hour_kop(
        values["printer_price_kop"], values["printer_lifetime_h"], values["parts_per_hour_kop"]
    )
    return PriceSettings(**values, wear_per_hour_kop=round_half_up_kop(wear))


def get_settings(conn: repo.DbConnection) -> PriceSettings | None:
    values = repo.get_settings(conn)
    return _with_wear(values) if values else None


def replace_settings(conn: repo.DbConnection, data: PriceSettingsInput) -> PriceSettings:
    values = data.model_dump()
    repo.upsert_settings(conn, values)
    return _with_wear(values)
