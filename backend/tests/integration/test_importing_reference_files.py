"""QG-1: every reference file → parse → the same quote as manual input, to the kopeck."""

from collections import defaultdict
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.factories import make_filament_mapping, make_plastic, make_price_settings
from tests.fixtures.slicer import LITTLE_TREES, VTULKA_SLICED

PARSE = "/api/importing/parse"
PLA = "Bambu PLA Basic @BBL A1M"


def parse(client: TestClient, body: bytes) -> dict[str, Any]:
    response = client.post(
        PARSE, content=body, headers={"Content-Type": "application/octet-stream"}
    )
    assert response.status_code == 200, response.text
    parsed: dict[str, Any] = response.json()
    return parsed


def compose(parsed: dict[str, Any]) -> dict[str, Any]:
    """Quote rows the way the web composes them (ADR 0004): Σ mg per plastic → ceil(/10) cg."""
    mg: dict[str, int] = defaultdict(int)
    for filament in parsed["filaments"]:
        mg[filament["plastic_id"]] += filament["usage_mg"]
    return {
        "plastics": [{"plastic_id": p, "usage_cg": -(-total // 10)} for p, total in mg.items()],
        "print_time_s": parsed["print_time_s"],
    }


def quote(client: TestClient, parsed: dict[str, Any]) -> dict[str, Any]:
    response = client.post("/api/costing/quote", json=compose(parsed))
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    return result


LITTLE_TREES_PLASTICS = (
    ("#3F8E43", "PLA зелений"),
    ("#000000", "PLA чорний"),
    ("#FEC600", "PLA жовтий"),
)


@pytest.fixture
def white(engine: Engine) -> str:
    with engine.begin() as conn:
        make_price_settings(conn)
        plastic = make_plastic(conn, name="PLA білий", price_per_kg_kop=40000)
        make_filament_mapping(conn, plastic_id=plastic)
    return plastic


def test_vtulka_quotes_18_82_with_the_ac01_breakdown(client: TestClient, white: str) -> None:
    parsed = parse(client, VTULKA_SLICED.read_bytes())

    assert compose(parsed) == {
        "plastics": [{"plastic_id": white, "usage_cg": 1154}],
        "print_time_s": 5880,  # 1 h 38 min
    }
    assert quote(client, parsed) == {
        "min_donation_kop": 1882,
        "breakdown": {
            "plastic_kop": 462,
            "electricity_kop": 106,
            "wear_kop": 1143,
            "scrap_kop": 171,
        },
    }


def test_vtulka_follows_a_plastic_price_change(client: TestClient, white: str) -> None:
    response = client.put(
        f"/api/pricing/plastics/{white}", json={"name": "PLA білий", "price_per_kg_kop": 65000}
    )
    assert response.status_code == 200, response.text

    assert quote(client, parse(client, VTULKA_SLICED.read_bytes()))["min_donation_kop"] == 2200


def test_little_trees_rows_are_the_slicer_grams_with_purge(
    client: TestClient, engine: Engine
) -> None:
    with engine.begin() as conn:
        make_price_settings(conn)
        rows = {}
        for color, name in LITTLE_TREES_PLASTICS:
            rows[color] = make_plastic(conn, name=name, price_per_kg_kop=40000)
            make_filament_mapping(conn, plastic_id=rows[color], filament_color=color)

    parsed = parse(client, LITTLE_TREES.read_bytes())

    assert parsed["plate"] == {"index": 1, "name": "mini christmas tree"}
    assert compose(parsed) == {
        "plastics": [
            {"plastic_id": rows["#3F8E43"], "usage_cg": 1549},
            {"plastic_id": rows["#000000"], "usage_cg": 223},
            {"plastic_id": rows["#FEC600"], "usage_cg": 236},
        ],
        "print_time_s": 5460,  # 1 h 31 min
    }
    assert quote(client, parsed)["min_donation_kop"] > 0
