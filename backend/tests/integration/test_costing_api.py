from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.factories import make_plastic, make_price_settings


@pytest.fixture
def plastics(engine: Engine) -> dict[str, str]:
    with engine.begin() as conn:
        make_price_settings(conn)
        return {
            "petg": make_plastic(conn, name="PETG чорний", price_per_kg_kop=65000),
            "pla": make_plastic(conn, name="PLA білий", price_per_kg_kop=40000),
        }


def _quote(client: TestClient, usages: list[tuple[str, int]], print_time_s: int) -> Any:
    return client.post(
        "/api/costing/quote",
        json={
            "plastics": [{"plastic_id": pid, "usage_cg": cg} for pid, cg in usages],
            "print_time_s": print_time_s,
        },
    )


@pytest.mark.parametrize(
    ("usages", "print_time_s", "expected"),
    [
        pytest.param(
            [("petg", 12000)],
            12600,
            {
                "min_donation_kop": 11525,
                "breakdown": {
                    "plastic_kop": 7800,
                    "electricity_kop": 227,
                    "wear_kop": 2450,
                    "scrap_kop": 1048,
                },
            },
            id="AC-06",
        ),
        pytest.param(
            [("pla", 8000), ("petg", 4000)],
            7200,
            {
                "min_donation_kop": 8063,
                "breakdown": {
                    "plastic_kop": 5800,
                    "electricity_kop": 130,
                    "wear_kop": 1400,
                    "scrap_kop": 733,
                },
            },
            id="AC-06b",
        ),
        pytest.param(
            [("petg", 10000)],
            10800,
            {
                "min_donation_kop": 9674,
                "breakdown": {
                    "plastic_kop": 6500,
                    "electricity_kop": 194,
                    "wear_kop": 2100,
                    "scrap_kop": 879,
                },
            },
            id="AC-08b",
        ),
    ],
)
def test_quote_returns_the_minimum_donation_and_breakdown(
    client: TestClient,
    plastics: dict[str, str],
    usages: list[tuple[str, int]],
    print_time_s: int,
    expected: dict[str, Any],
) -> None:
    response = _quote(client, [(plastics[k], cg) for k, cg in usages], print_time_s)

    assert response.status_code == 200
    assert response.json() == expected
    # AC-06: a quote is a calculation only; nothing lands in the catalog.
    assert client.get("/api/catalog/items").json() == {"items": []}


@pytest.mark.parametrize(
    ("usages", "print_time_s"),
    [
        ([], 3600),
        ([("petg", 0)], 3600),
        ([("petg", -100)], 3600),
        ([("petg", 100), ("petg", 200)], 3600),
        ([("petg", 100)], 0),
        ([("petg", 100)], 90),
    ],
    ids=["no-plastic", "zero-usage", "negative-usage", "duplicate", "zero-time", "seconds"],
)
def test_invalid_quote_is_a_422(
    client: TestClient,
    plastics: dict[str, str],
    usages: list[tuple[str, int]],
    print_time_s: int,
) -> None:
    response = _quote(client, [(plastics[k], cg) for k, cg in usages], print_time_s)

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "validation_error"


def test_unknown_plastic_is_a_422_on_the_row(client: TestClient, plastics: dict[str, str]) -> None:
    response = _quote(client, [(plastics["petg"], 100), ("01900000-dead", 100)], 60)

    assert response.status_code == 422
    assert response.json()["code"] == "costing.plastic_not_found"
    assert response.json()["field"] == "plastics.1.plastic_id"


def test_missing_settings_is_a_409_with_missing(client: TestClient, engine: Engine) -> None:
    with engine.begin() as conn:
        petg = make_plastic(conn)

    response = _quote(client, [(petg, 12000)], 3600)

    assert response.status_code == 409
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "costing.settings_missing"
    assert response.json()["missing"] == ["price_settings"]


def test_no_plastics_and_no_settings_are_both_reported(client: TestClient) -> None:
    response = _quote(client, [("01900000-0000-7000-8000-00000000a001", 12000)], 3600)

    assert response.status_code == 409
    assert response.json()["missing"] == ["plastics", "price_settings"]


def test_openapi_declares_quote_cost(client: TestClient) -> None:
    operation = client.get("/openapi.json").json()["paths"]["/api/costing/quote"]["post"]

    assert operation["operationId"] == "quoteCost"
    assert {s for s in operation["responses"] if s[0] in "45"} == {
        "400",
        "403",
        "409",
        "415",
        "422",
        "500",
    }


def test_duplicate_plastic_is_a_422_on_the_second_occurrence(
    client: TestClient, plastics: dict[str, str]
) -> None:
    pid = plastics["petg"]
    response = _quote(client, [(pid, 100), (pid, 200)], 3600)

    assert response.status_code == 422, response.text
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["errors"][0]["loc"] == ["body", "plastics", 1, "plastic_id"]
