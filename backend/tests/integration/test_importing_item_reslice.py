"""QG-1 AC-05: a re-sliced file replaces «Підставка» — 80,63 ₴ → 60,73 ₴, the name unchanged."""

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.factories import make_filament_mapping, make_item, make_plastic, make_price_settings
from tests.fixtures.slicer.bad_files import vtulka_variant
from tests.integration.test_importing_reference_files import compose, parse


def test_reslice_was_became_and_confirm(client: TestClient, engine: Engine) -> None:
    with engine.begin() as conn:
        make_price_settings(conn)
        white = make_plastic(conn, name="PLA білий", price_per_kg_kop=40000)
        black = make_plastic(conn, name="PETG чорний", price_per_kg_kop=65000)
        make_filament_mapping(conn, plastic_id=white)
        item_id = make_item(
            conn, name="Підставка", print_time_s=7200, usage={white: 8000, black: 4000}
        )
    was = client.get(f"/api/catalog/items/{item_id}").json()
    assert was["quote"]["min_donation_kop"] == 8063

    parsed = parse(client, vtulka_variant(used_g="95.00", prediction="8100"))
    became = compose(parsed)
    assert became == {"plastics": [{"plastic_id": white, "usage_cg": 9500}], "print_time_s": 8100}
    assert client.post("/api/costing/quote", json=became).json()["min_donation_kop"] == 6073

    response = client.put(f"/api/catalog/items/{item_id}", json={"name": was["name"], **became})

    assert response.status_code == 200, response.text
    after = client.get(f"/api/catalog/items/{item_id}").json()
    assert after["name"] == "Підставка"
    assert after["plastics"] == became["plastics"]
    assert after["print_time_s"] == 8100
    assert after["quote"]["min_donation_kop"] == 6073
    listed = client.get("/api/catalog/items").json()["items"]
    assert listed == [{"id": item_id, "name": "Підставка", "min_donation_kop": 6073}]
