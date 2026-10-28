from typing import Any

import pytest
from fastapi.testclient import TestClient

AC04 = {
    "tariff_per_kwh_kop": 432,
    "printer_power_w": 150,
    "printer_price_kop": 3_000_000,
    "printer_lifetime_h": 5000,
    "parts_per_hour_kop": 100,
    "scrap_rate_permille": 100,
}


def _problem(response: Any, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    assert response.headers["content-type"] == "application/problem+json"
    body: dict[str, Any] = response.json()
    assert body["code"] == code
    return body


def test_added_plastic_appears_in_the_list(client: TestClient) -> None:
    created = client.post(
        "/api/pricing/plastics", json={"name": "PETG чорний", "price_per_kg_kop": 65000}
    )

    assert created.status_code == 201
    plastic = created.json()
    assert plastic["name"] == "PETG чорний"
    assert plastic["price_per_kg_kop"] == 65000
    assert client.get("/api/pricing/plastics").json() == {"items": [plastic]}


@pytest.mark.parametrize("duplicate", ["petg чорний", "PETG чорний "])
def test_duplicate_plastic_name_is_a_409_on_the_name_field(
    client: TestClient, duplicate: str
) -> None:
    client.post("/api/pricing/plastics", json={"name": "PETG чорний", "price_per_kg_kop": 65000})

    response = client.post("/api/pricing/plastics", json={"name": duplicate, "price_per_kg_kop": 1})

    assert _problem(response, 409, "pricing.name_taken")["field"] == "name"
    assert len(client.get("/api/pricing/plastics").json()["items"]) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "   ", "price_per_kg_kop": 65000},
        {"name": "PETG", "price_per_kg_kop": 0},
        {"name": "PETG", "price_per_kg_kop": -100},
        {"name": "PETG", "price_per_kg_kop": 649.995},
        {"name": "PETG", "price_per_kg_kop": "650"},
        {"name": "PETG"},
    ],
)
def test_invalid_plastic_is_a_422_and_nothing_is_saved(
    client: TestClient, payload: dict[str, object]
) -> None:
    response = client.post("/api/pricing/plastics", json=payload)

    assert _problem(response, 422, "validation_error")["errors"]
    assert client.get("/api/pricing/plastics").json() == {"items": []}


def test_plastic_name_and_price_can_be_changed(client: TestClient) -> None:
    plastic = client.post(
        "/api/pricing/plastics", json={"name": "PETG чорний", "price_per_kg_kop": 65000}
    ).json()

    response = client.put(
        f"/api/pricing/plastics/{plastic['id']}",
        json={"name": "PETG чорний", "price_per_kg_kop": 80000},
    )

    assert response.status_code == 200
    assert response.json() == {**plastic, "price_per_kg_kop": 80000}


def test_unused_plastic_is_deleted(client: TestClient) -> None:
    plastic = client.post(
        "/api/pricing/plastics", json={"name": "PLA білий", "price_per_kg_kop": 40000}
    ).json()

    response = client.delete(f"/api/pricing/plastics/{plastic['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/api/pricing/plastics").json() == {"items": []}


@pytest.mark.parametrize("method", ["put", "delete"])
def test_unknown_plastic_is_a_404(client: TestClient, method: str) -> None:
    url = "/api/pricing/plastics/01900000-0000-7000-8000-00000000ffff"
    if method == "put":
        response = client.put(url, json={"name": "X", "price_per_kg_kop": 1})
    else:
        response = client.delete(url)

    _problem(response, 404, "pricing.plastic_not_found")


def test_settings_are_null_until_the_first_save(client: TestClient) -> None:
    response = client.get("/api/pricing/settings")

    assert response.status_code == 200
    assert response.json() is None


def test_saving_settings_stores_all_fields_and_reports_wear_per_hour(client: TestClient) -> None:
    saved = client.put("/api/pricing/settings", json=AC04)

    assert saved.status_code == 200
    assert saved.json() == {**AC04, "wear_per_hour_kop": 700}
    assert client.get("/api/pricing/settings").json() == {**AC04, "wear_per_hour_kop": 700}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tariff_per_kwh_kop", -1),
        ("printer_lifetime_h", 0),
        ("printer_power_w", 152.5),
        ("scrap_rate_permille", 1001),
        ("parts_per_hour_kop", None),
    ],
)
def test_one_invalid_settings_field_saves_nothing(
    client: TestClient, field: str, value: object
) -> None:
    client.put("/api/pricing/settings", json=AC04)
    changed = {**AC04, "tariff_per_kwh_kop": 0, "printer_power_w": 200, field: value}

    response = client.put("/api/pricing/settings", json=changed)

    _problem(response, 422, "validation_error")
    assert client.get("/api/pricing/settings").json() == {**AC04, "wear_per_hour_kop": 700}


def test_zero_is_a_valid_tariff_power_price_parts_and_scrap(client: TestClient) -> None:
    zeroes = {**AC04, "tariff_per_kwh_kop": 0, "printer_power_w": 0, "printer_price_kop": 0}
    zeroes |= {"parts_per_hour_kop": 0, "scrap_rate_permille": 0}

    response = client.put("/api/pricing/settings", json=zeroes)

    assert response.status_code == 200
    assert response.json()["wear_per_hour_kop"] == 0


PRICING_OPERATIONS = {
    ("get", "/api/pricing/plastics"): ("listPlastics", set()),
    ("post", "/api/pricing/plastics"): ("createPlastic", {"409", "415", "422"}),
    ("put", "/api/pricing/plastics/{plastic_id}"): ("updatePlastic", {"404", "409", "415", "422"}),
    ("delete", "/api/pricing/plastics/{plastic_id}"): ("deletePlastic", {"404", "409"}),
    ("get", "/api/pricing/settings"): ("getPriceSettings", set()),
    ("put", "/api/pricing/settings"): ("replacePriceSettings", {"415", "422"}),
}


@pytest.mark.parametrize(("method", "path"), list(PRICING_OPERATIONS))
def test_openapi_declares_pricing_operations_with_problem_json_errors(
    client: TestClient, method: str, path: str
) -> None:
    operation = client.get("/openapi.json").json()["paths"][path][method]
    operation_id, own_errors = PRICING_OPERATIONS[(method, path)]

    assert operation["operationId"] == operation_id
    errors = {status for status in operation["responses"] if status.startswith(("4", "5"))}
    assert errors == own_errors | {"400", "403", "500"}
    for status in errors:
        assert list(operation["responses"][status]["content"]) == ["application/problem+json"]
