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


@pytest.mark.parametrize("name", ["\u200b", "\u200b\u200d", " \u200b "])
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
        ("\u200b", "String should have at least 1 character"),
        (EXPANDING_CHAR * 100, "String should have at most 100 characters"),
    ],
)
def test_name_bound_errors_keep_the_string_length_message(
    client: TestClient, name: str, msg: str
) -> None:
    response = client.post("/api/pricing/plastics", json={"name": name, "price_per_kg_kop": 65000})

    assert [error["msg"] for error in response.json()["errors"]] == [msg]


# T46 (R5-3): the 100 cap counts code points of the normalised name, on both name-bearing endpoints.
# An emoji is one code point (two UTF-16 units, four UTF-8 bytes); Cf (U+200B, U+00AD) at the edges
# is trimmed before the length is measured.
NAME_ENDPOINTS = ["/api/pricing/plastics", "/api/catalog/items"]


def _post_named(client: TestClient, path: str, plastic_id: str, name: str) -> Any:
    body: dict[str, Any] = {"name": name}
    if path == "/api/pricing/plastics":
        body["price_per_kg_kop"] = 65000
    else:
        body["plastics"] = [{"plastic_id": plastic_id, "usage_cg": 100}]
        body["print_time_s"] = 12600
    return client.post(path, json=body)


def _names(client: TestClient, path: str) -> list[str]:
    return [item["name"] for item in client.get(path).json()["items"]]


@pytest.mark.parametrize("path", NAME_ENDPOINTS)
def test_name_of_100_emoji_is_saved_and_101_is_a_422_on_name(
    client: TestClient, seeded: str, path: str
) -> None:
    ok = _post_named(client, path, seeded, "\U0001f600" * 100)
    over = _post_named(client, path, seeded, "\U0001f600" * 101)

    assert ok.status_code == 201, ok.text
    assert ok.json()["name"] == "\U0001f600" * 100
    _assert_422_on(over, "name")
    assert "\U0001f600" * 101 not in _names(client, path)
    assert _names(client, path).count("\U0001f600" * 100) == 1


@pytest.mark.parametrize("path", NAME_ENDPOINTS)
def test_name_of_100_letters_and_a_trailing_zero_width_space_is_saved_as_100_chars(
    client: TestClient, seeded: str, path: str
) -> None:
    response = _post_named(client, path, seeded, "a" * 100 + "\u200b")

    assert response.status_code == 201, response.text
    assert response.json()["name"] == "a" * 100
    assert "a" * 100 in _names(client, path)
    assert all("\u200b" not in name for name in _names(client, path))


@pytest.mark.parametrize("path", NAME_ENDPOINTS)
def test_name_of_100_letters_and_a_trailing_soft_hyphen_is_accepted(
    client: TestClient, seeded: str, path: str
) -> None:
    response = _post_named(client, path, seeded, "b" * 100 + "\u00ad")

    assert response.status_code == 201, response.text
    assert response.json()["name"] == "b" * 100


# T42 (R4-1): the caps are hard-coded from PRD AC-02/AC-05/AC-07 on purpose - importing the MAX_*
# constants would follow a loosened `le=` instead of catching it. Cap is accepted, cap + 1 is a 422.
PLASTIC_PRICE_CAP = 1_000_000_000
SETTINGS_CAPS = {
    "tariff_per_kwh_kop": 1_000_000,
    "printer_power_w": 1_000_000,
    "printer_price_kop": 10_000_000_000,
    "printer_lifetime_h": 1_000_000,
    "parts_per_hour_kop": 100_000_000,
    "scrap_rate_permille": 1000,
}
USAGE_CAP_CG = 100_000_000
PRINT_TIME_CAP_S = 360_000_000
PLASTICS_CAP = 32


def test_plastic_price_cap_is_accepted_and_one_more_is_a_422(client: TestClient) -> None:
    ok = client.post(
        "/api/pricing/plastics", json={"name": "Cap", "price_per_kg_kop": PLASTIC_PRICE_CAP}
    )
    over = client.post(
        "/api/pricing/plastics", json={"name": "Over", "price_per_kg_kop": PLASTIC_PRICE_CAP + 1}
    )

    assert ok.status_code == 201, ok.text
    _assert_422_on(over, "price_per_kg_kop")


@pytest.mark.parametrize("field", SETTINGS_FIELDS)
def test_price_setting_cap_is_accepted_and_one_more_is_a_422(
    client: TestClient, field: str
) -> None:
    cap = SETTINGS_CAPS[field]

    ok = client.put("/api/pricing/settings", json={**AC04_SETTINGS, field: cap})
    over = client.put("/api/pricing/settings", json={**AC04_SETTINGS, field: cap + 1})

    assert ok.status_code == 200, ok.text
    assert ok.json()[field] == cap
    _assert_422_on(over, field)
    assert client.get("/api/pricing/settings").json()[field] == cap


def test_usage_cap_is_accepted_and_one_more_is_a_422_in_quote_and_item(
    client: TestClient, seeded: str
) -> None:
    def post(usage_cg: int) -> tuple[Any, Any]:
        plastics = [{"plastic_id": seeded, "usage_cg": usage_cg}]
        quote = client.post("/api/costing/quote", json={"plastics": plastics, "print_time_s": 3600})
        item = client.post(
            "/api/catalog/items",
            json={"name": f"U{usage_cg}", "plastics": plastics, "print_time_s": 3600},
        )
        return quote, item

    quote, item = post(USAGE_CAP_CG)
    assert quote.status_code == 200, quote.text
    assert item.status_code == 201, item.text

    quote, item = post(USAGE_CAP_CG + 1)
    _assert_422_on(quote, "usage_cg")
    _assert_422_on(item, "usage_cg")


def test_print_time_cap_is_accepted_and_one_minute_more_is_a_422_in_quote_and_item(
    client: TestClient, seeded: str
) -> None:
    plastics = [{"plastic_id": seeded, "usage_cg": 100}]

    def post(print_time_s: int) -> tuple[Any, Any]:
        quote = client.post(
            "/api/costing/quote", json={"plastics": plastics, "print_time_s": print_time_s}
        )
        item = client.post(
            "/api/catalog/items",
            json={"name": f"T{print_time_s}", "plastics": plastics, "print_time_s": print_time_s},
        )
        return quote, item

    quote, item = post(PRINT_TIME_CAP_S)
    assert quote.status_code == 200, quote.text
    assert item.status_code == 201, item.text

    quote, item = post(PRINT_TIME_CAP_S + 60)  # a whole minute, so only the cap can reject it
    _assert_422_on(quote, "print_time_s")
    _assert_422_on(item, "print_time_s")


def test_32_distinct_plastics_are_accepted_and_33_is_a_422_in_quote_and_item(
    client: TestClient, engine: Engine
) -> None:
    with engine.begin() as conn:
        make_price_settings(conn)
        ids = [make_plastic(conn, name=f"Cap-{n}") for n in range(PLASTICS_CAP + 1)]

    def post(count: int) -> tuple[Any, Any]:
        plastics = [{"plastic_id": pid, "usage_cg": 100} for pid in ids[:count]]
        quote = client.post("/api/costing/quote", json={"plastics": plastics, "print_time_s": 3600})
        item = client.post(
            "/api/catalog/items",
            json={"name": f"P{count}", "plastics": plastics, "print_time_s": 3600},
        )
        return quote, item

    quote, item = post(PLASTICS_CAP)
    assert quote.status_code == 200, quote.text
    assert item.status_code == 201, item.text

    quote, item = post(PLASTICS_CAP + 1)
    _assert_422_on(quote, "plastics")
    _assert_422_on(item, "plastics")
