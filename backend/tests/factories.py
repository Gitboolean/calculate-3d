"""Test-data helpers writing through SQLAlchemy Core (data-model.md § Test fixtures)."""

from sqlalchemy import Connection, insert

from calculate3d.core.ids import new_id
from calculate3d.core.text import name_key
from calculate3d.modules.pricing.repo import SETTINGS_ID
from calculate3d.modules.pricing.tables import plastics, price_settings

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
        insert(plastics).values(
            id=plastic_id, name=name, name_key=name_key(name), price_per_kg_kop=price_per_kg_kop
        )
    )
    return plastic_id


def make_price_settings(conn: Connection, **overrides: int) -> None:
    conn.execute(insert(price_settings).values(id=SETTINGS_ID, **{**AC04_SETTINGS, **overrides}))
