"""catalog — items as parameters only; prices are recomputed on every read (ADR 0003).

Talks to `pricing` and `costing` only through their services (ADR 0005).
"""

from calculate3d.core.errors import AppError
from calculate3d.core.ids import new_id
from calculate3d.core.text import contains, name_key, normalize_name, sort_key
from calculate3d.modules.catalog import repo
from calculate3d.modules.catalog.schemas import Item, ItemDetail, ItemInput, ItemSummary
from calculate3d.modules.costing import service as costing_service
from calculate3d.modules.costing.service import PlasticUsage, QuoteInput
from calculate3d.modules.importing import service as importing_service
from calculate3d.modules.pricing import service as pricing_service


class ItemNameTaken(AppError):
    def __init__(self) -> None:
        super().__init__("catalog.name_taken", "Item name is already taken", 409, field="name")


class ItemNotFound(AppError):
    def __init__(self) -> None:
        super().__init__("catalog.item_not_found", "Item not found", 404)


class PlasticNotFound(AppError):
    def __init__(self, index: int) -> None:
        super().__init__(
            "catalog.plastic_not_found",
            "Plastic not found",
            422,
            field=f"plastics.{index}.plastic_id",
        )


def _to_item(record: repo.ItemRecord) -> Item:
    plastics = [PlasticUsage(plastic_id=u.plastic_id, usage_cg=u.usage_cg) for u in record.usage]
    return Item(id=record.id, name=record.name, plastics=plastics, print_time_s=record.print_time_s)


def _quote_input(record: repo.ItemRecord) -> QuoteInput:
    return QuoteInput(plastics=_to_item(record).plastics, print_time_s=record.print_time_s)


def _save(conn: repo.DbConnection, item_id: str, data: ItemInput, *, is_new: bool) -> Item:
    """Validate everything before the first write, so a rejected edit changes nothing."""
    name = normalize_name(data.name)
    key = name_key(name)
    if repo.find_item_id_by_name_key(conn, key) not in (None, item_id):
        raise ItemNameTaken
    known = {
        p.id
        for p in pricing_service.list_plastics_by_ids(conn, {u.plastic_id for u in data.plastics})
    }
    for index, usage in enumerate(data.plastics):
        if usage.plastic_id not in known:
            raise PlasticNotFound(index)

    # AC-10: an item is saved only if its minimum donation can be computed right now.
    costing_service.quote(
        conn,
        QuoteInput(plastics=list(data.plastics), print_time_s=data.print_time_s),
    )

    usage_rows = tuple(repo.UsageRecord(u.plastic_id, u.usage_cg) for u in data.plastics)
    record = repo.ItemRecord(item_id, name, data.print_time_s, usage_rows)
    write = repo.insert_item if is_new else repo.update_item
    try:
        write(conn, record, key)
    except repo.NameKeyTaken as exc:
        raise ItemNameTaken from exc
    try:
        repo.replace_usage(conn, item_id, usage_rows)
    except repo.PlasticMissing as exc:
        # A plastic vanished after the pre-check; point at the first one that is gone now.
        now_known = {
            p.id
            for p in pricing_service.list_plastics_by_ids(
                conn, {u.plastic_id for u in data.plastics}
            )
        }
        index = next((i for i, u in enumerate(data.plastics) if u.plastic_id not in now_known), 0)
        raise PlasticNotFound(index) from exc
    # Same Connection, same BEGIN IMMEDIATE: a rejected mapping rolls the item back (ADR 0003).
    importing_service.remember_mappings(conn, data.filament_mappings)
    return _to_item(record)


def create_item(conn: repo.DbConnection, data: ItemInput) -> Item:
    return _save(conn, new_id(), data, is_new=True)


def update_item(conn: repo.DbConnection, item_id: str, data: ItemInput) -> Item:
    if repo.get_item(conn, item_id) is None:
        raise ItemNotFound
    return _save(conn, item_id, data, is_new=False)


def get_item(conn: repo.DbConnection, item_id: str) -> ItemDetail:
    record = repo.get_item(conn, item_id)
    if record is None:
        raise ItemNotFound
    quote = costing_service.quote(conn, _quote_input(record))
    return ItemDetail(**_to_item(record).model_dump(), quote=quote)


def list_items(conn: repo.DbConnection, query: str | None) -> list[ItemSummary]:
    records = [r for r in repo.list_items_with_usage(conn) if contains(r.name, query or "")]
    records.sort(key=lambda r: sort_key(r.name))
    quotes = costing_service.quote_many(conn, [_quote_input(r) for r in records])
    return [
        ItemSummary(id=r.id, name=r.name, min_donation_kop=q.min_donation_kop)
        for r, q in zip(records, quotes, strict=True)
    ]


def delete_item(conn: repo.DbConnection, item_id: str) -> None:
    if not repo.delete_item(conn, item_id):
        raise ItemNotFound


def item_names_using_plastic(conn: repo.DbConnection, plastic_id: str) -> list[str]:
    """For the pricing router's in-use check (AC-03) — pricing never imports catalog."""
    return repo.item_names_using_plastic(conn, plastic_id)
