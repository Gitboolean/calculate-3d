"""Test-data helpers writing through SQLAlchemy Core (data-model.md § Test fixtures)."""

import random

from sqlalchemy import Connection, insert

from calculate3d.core.ids import new_id
from calculate3d.core.text import name_key
from calculate3d.modules.catalog.tables import item_plastics
from calculate3d.modules.catalog.tables import items as items_table
from calculate3d.modules.pricing.repo import SETTINGS_ID
from calculate3d.modules.pricing.tables import plastics as plastics_table
from calculate3d.modules.pricing.tables import price_settings

# AC-04: 4,32 ₴/кВт·год, 150 Вт, 30 000 ₴, 5 000 год, 1,00 ₴/год, брак 10 %.
AC04_SETTINGS = {
    "tariff_per_kwh_kop": 432,
    "printer_power_w": 150,
    "printer_price_kop": 3_000_000,
    "printer_lifetime_h": 5000,
    "parts_per_hour_kop": 100,
    "scrap_rate_permille": 100,
}


def make_plastic(
    conn: Connection, *, name: str = "PETG чорний", price_per_kg_kop: int = 65000
) -> str:
    plastic_id = new_id()
    conn.execute(
        insert(plastics_table).values(
            id=plastic_id, name=name, name_key=name_key(name), price_per_kg_kop=price_per_kg_kop
        )
    )
    return plastic_id


def make_price_settings(conn: Connection, **overrides: int) -> None:
    conn.execute(insert(price_settings).values(id=SETTINGS_ID, **{**AC04_SETTINGS, **overrides}))


def make_item(
    conn: Connection,
    *,
    name: str = "Брелок-тризуб",
    print_time_s: int = 12600,
    usage: dict[str, int],
) -> str:
    """An item with its usage rows; `usage` maps plastic_id → usage_cg."""
    item_id = new_id()
    conn.execute(
        insert(items_table).values(
            id=item_id, name=name, name_key=name_key(name), print_time_s=print_time_s
        )
    )
    conn.execute(
        insert(item_plastics),
        [{"item_id": item_id, "plastic_id": p, "usage_cg": cg} for p, cg in usage.items()],
    )
    return item_id


def seed_catalog_volume(conn: Connection, *, items: int, plastics: int, seed: int) -> None:
    """Deterministic NFR volume: `plastics` plastics and `items` items of 1–3 plastics each."""
    rng = random.Random(seed)
    plastic_rows = [
        {"id": new_id(), "name": f"Plastic-{n}", "name_key": f"plastic-{n}"}
        | {"price_per_kg_kop": rng.randint(20_000, 150_000)}
        for n in range(plastics)
    ]
    conn.execute(insert(plastics_table), plastic_rows)
    item_rows, usage_rows = [], []
    for n in range(items):
        item_id = new_id()
        item_rows.append(
            {"id": item_id, "name": f"Item-{n}", "name_key": f"item-{n}"}
            | {"print_time_s": 60 * rng.randint(1, 3000)}
        )
        for plastic in rng.sample(plastic_rows, rng.randint(1, 3)):
            usage_rows.append(
                {
                    "item_id": item_id,
                    "plastic_id": plastic["id"],
                    "usage_cg": rng.randint(1, 50_000),
                }
            )
    conn.execute(insert(items_table), item_rows)
    conn.execute(insert(item_plastics), usage_rows)
