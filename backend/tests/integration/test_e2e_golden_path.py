"""test-plan § E2E (API): the author's golden path, every step checked in kopecks."""

from fastapi.testclient import TestClient

AC04 = {
    "tariff_per_kwh_kop": 432,
    "printer_power_w": 150,
    "printer_price_kop": 3_000_000,
    "printer_lifetime_h": 5000,
    "parts_per_hour_kop": 100,
    "scrap_rate_permille": 100,
}


def test_golden_path_from_settings_to_catalog_and_back(client: TestClient) -> None:
    settings = client.put("/api/pricing/settings", json=AC04).json()
    assert settings["wear_per_hour_kop"] == 700

    petg = client.post(
        "/api/pricing/plastics", json={"name": "PETG чорний", "price_per_kg_kop": 65000}
    ).json()
    usage = {"plastics": [{"plastic_id": petg["id"], "usage_cg": 12000}], "print_time_s": 12600}

    quote = client.post("/api/costing/quote", json=usage).json()
    assert quote["min_donation_kop"] == 11525

    item = client.post("/api/catalog/items", json={"name": "Брелок-тризуб", **usage}).json()
    assert "min_donation_kop" not in item
    assert client.get("/api/catalog/items").json()["items"] == [
        {"id": item["id"], "name": "Брелок-тризуб", "min_donation_kop": 11525}
    ]

    refused = client.delete(f"/api/pricing/plastics/{petg['id']}")
    assert refused.status_code == 409
    assert refused.json()["items"] == ["Брелок-тризуб"]

    client.put(
        f"/api/pricing/plastics/{petg['id']}",
        json={"name": "PETG чорний", "price_per_kg_kop": 80000},
    )
    assert client.get("/api/catalog/items").json()["items"][0]["min_donation_kop"] == 13505

    assert client.delete(f"/api/catalog/items/{item['id']}").status_code == 204
    assert client.get("/api/catalog/items").json() == {"items": []}
    assert client.delete(f"/api/pricing/plastics/{petg['id']}").status_code == 204
    assert client.get("/api/pricing/plastics").json() == {"items": []}
