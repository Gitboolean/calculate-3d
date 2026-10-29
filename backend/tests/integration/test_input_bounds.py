"""T24 (S2-1): every scaled-integer input has an upper bound; huge values are a 422, not a 500."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.factories import AC04_SETTINGS, make_plastic, make_price_settings

JS_SAFE_MAX = 2**53 - 1
HUGE = [2**63, 10**60]

SETTINGS_FIELDS = [
    "tariff_per_kwh_kop",
    "printer_power_w",
    "printer_price_kop",
    "printer_lifetime_h",
    "parts_per_hour_kop",
    "scrap_rate_permille",
]


@pytest.fixture
def seeded(engine: Engine) -> str:
    with engine.begin() as conn:
        make_price_settings(conn)
        return make_plastic(conn, name="PETG", price_per_kg_kop=65000)


def _assert_422_on(response: Any, field: str) -> None:
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["code"] == "validation_error"
    assert any(field in error["loc"] for error in body["errors"]), body["errors"]


@pytest.mark.parametrize("huge", HUGE)
def test_huge_plastic_price_is_a_422_on_the_field(client: TestClient, huge: int) -> None:
    response = client.post("/api/pricing/plastics", json={"name": "PETG", "price_per_kg_kop": huge})

    _assert_422_on(response, "price_per_kg_kop")
    assert client.get("/api/pricing/plastics").json() == {"items": []}


@pytest.mark.parametrize("huge", HUGE)
@pytest.mark.parametrize("field", SETTINGS_FIELDS)
def test_huge_price_setting_is_a_422_on_the_field(
    client: TestClient, field: str, huge: int
) -> None:
    response = client.put("/api/pricing/settings", json={**AC04_SETTINGS, field: huge})

    _assert_422_on(response, field)


@pytest.mark.parametrize("huge", HUGE)
def test_huge_usage_is_a_422_on_the_field_in_quote_and_item(
    client: TestClient, seeded: str, huge: int
) -> None:
    usage = [{"plastic_id": seeded, "usage_cg": huge}]

    quote = client.post("/api/costing/quote", json={"plastics": usage, "print_time_s": 12600})
    item = client.post(
        "/api/catalog/items", json={"name": "X", "plastics": usage, "print_time_s": 12600}
    )

    _assert_422_on(quote, "usage_cg")
    _assert_422_on(item, "usage_cg")


@pytest.mark.parametrize("huge", HUGE)
def test_huge_print_time_is_a_422_on_the_field_in_quote_and_item(
    client: TestClient, seeded: str, huge: int
) -> None:
    huge -= huge % 60  # keep it a whole number of minutes so only the bound can reject it
    plastics = [{"plastic_id": seeded, "usage_cg": 100}]

    quote = client.post("/api/costing/quote", json={"plastics": plastics, "print_time_s": huge})
    item = client.post(
        "/api/catalog/items", json={"name": "X", "plastics": plastics, "print_time_s": huge}
    )

    _assert_422_on(quote, "print_time_s")
    _assert_422_on(item, "print_time_s")


def test_realistic_large_values_still_work(client: TestClient, seeded: str) -> None:
    plastics = [{"plastic_id": seeded, "usage_cg": 1_000_000}]  # 10 kg
    print_time_s = 1000 * 3600  # 1000 h

    quote = client.post(
        "/api/costing/quote", json={"plastics": plastics, "print_time_s": print_time_s}
    )
    item = client.post(
        "/api/catalog/items",
        json={"name": "Великий", "plastics": plastics, "print_time_s": print_time_s},
    )

    assert quote.status_code == 200, quote.text
    assert item.status_code == 201, item.text


def _maximum(schemas: dict[str, Any], schema: str, field: str) -> int:
    prop = schemas[schema]["properties"][field]
    assert "maximum" in prop, f"{schema}.{field} has no upper bound"
    maximum: int = prop["maximum"]
    return maximum


def test_quote_at_every_maximum_stays_within_js_safe_integer(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    settings = {f: _maximum(schemas, "PriceSettingsInput", f) for f in SETTINGS_FIELDS}
    settings["printer_lifetime_h"] = 1  # worst case: the whole printer price wears off per hour
    price = _maximum(schemas, "PlasticInput", "price_per_kg_kop")
    usage = _maximum(schemas, "PlasticUsage", "usage_cg")
    print_time = _maximum(schemas, "QuoteInput", "print_time_s")

    assert client.put("/api/pricing/settings", json=settings).status_code == 200
    plastic = client.post("/api/pricing/plastics", json={"name": "Max", "price_per_kg_kop": price})
    assert plastic.status_code == 201, plastic.text

    response = client.post(
        "/api/costing/quote",
        json={
            "plastics": [{"plastic_id": plastic.json()["id"], "usage_cg": usage}],
            "print_time_s": print_time - print_time % 60,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["min_donation_kop"] <= JS_SAFE_MAX


@pytest.mark.parametrize("name", ["​", "​‍", " ​ "])
def test_name_of_only_invisible_characters_is_a_422_on_name(client: TestClient, name: str) -> None:
    response = client.post("/api/pricing/plastics", json={"name": name, "price_per_kg_kop": 65000})

    _assert_422_on(response, "name")


# T33 (R2-4): the 1..100 name bound is measured on the NFC-normalised value. U+0344 is
# composition-excluded: NFC expands it to U+0308 U+0301, so 100 of them become 200 characters.
EXPANDING_CHAR = "\u0344"


def test_plastic_name_that_exceeds_100_chars_after_nfc_is_a_422_on_name(client: TestClient) -> None:
    response = client.post(
        "/api/pricing/plastics",
        json={"name": EXPANDING_CHAR * 100, "price_per_kg_kop": 65000},
    )

    _assert_422_on(response, "name")
    assert any(error["loc"][-1] == "name" for error in response.json()["errors"])
    assert client.get("/api/pricing/plastics").json() == {"items": []}


def test_item_name_that_exceeds_100_chars_after_nfc_is_a_422_on_name(
    client: TestClient, seeded: str
) -> None:
    response = client.post(
        "/api/catalog/items",
        json={
            "name": EXPANDING_CHAR * 100,
            "plastics": [{"plastic_id": seeded, "usage_cg": 100}],
            "print_time_s": 12600,
        },
    )

    _assert_422_on(response, "name")
    assert any(error["loc"][-1] == "name" for error in response.json()["errors"])


def test_plastic_name_of_exactly_100_chars_after_nfc_is_accepted(client: TestClient) -> None:
    response = client.post(
        "/api/pricing/plastics",
        json={"name": EXPANDING_CHAR * 50, "price_per_kg_kop": 65000},
    )

    assert response.status_code == 201, response.text
    assert len(response.json()["name"]) == 100


@pytest.mark.parametrize(
    ("name", "msg"),
    [
        ("   ", "String should have at least 1 character"),
        ("​", "String should have at least 1 character"),
        (EXPANDING_CHAR * 100, "String should have at most 100 characters"),
    ],
)
def test_name_bound_errors_keep_the_string_length_message(
    client: TestClient, name: str, msg: str
) -> None:
    response = client.post("/api/pricing/plastics", json={"name": name, "price_per_kg_kop": 65000})

    assert [error["msg"] for error in response.json()["errors"]] == [msg]
