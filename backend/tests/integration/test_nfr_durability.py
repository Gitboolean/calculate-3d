"""QG-4: everything saved is there after the tool restarts."""

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from calculate3d.core.config import Settings
from calculate3d.main import create_app

AC04 = {
    "tariff_per_kwh_kop": 432,
    "printer_power_w": 150,
    "printer_price_kop": 3_000_000,
    "printer_lifetime_h": 5000,
    "parts_per_hour_kop": 100,
    "scrap_rate_permille": 100,
}


def test_saved_data_survives_a_restart(engine: Engine) -> None:
    url = str(engine.url)
    engine.dispose()

    with TestClient(create_app(Settings(database_url=url))) as first_run:
        first_run.put("/api/pricing/settings", json=AC04)
        plastic = first_run.post(
            "/api/pricing/plastics", json={"name": "PETG чорний", "price_per_kg_kop": 65000}
        ).json()
        item = first_run.post(
            "/api/catalog/items",
            json={
                "name": "Брелок-тризуб",
                "plastics": [{"plastic_id": plastic["id"], "usage_cg": 12000}],
                "print_time_s": 12600,
            },
        ).json()
        before = {
            "settings": first_run.get("/api/pricing/settings").json(),
            "plastics": first_run.get("/api/pricing/plastics").json(),
            "item": first_run.get(f"/api/catalog/items/{item['id']}").json(),
        }

    with TestClient(create_app(Settings(database_url=url))) as second_run:
        after = {
            "settings": second_run.get("/api/pricing/settings").json(),
            "plastics": second_run.get("/api/pricing/plastics").json(),
            "item": second_run.get(f"/api/catalog/items/{item['id']}").json(),
        }

    assert after == before
    assert after["item"]["quote"]["min_donation_kop"] == 11525
