"""QG-1 (3): the quote, the catalog list and the item page agree on every item's price."""

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.factories import make_price_settings, seed_catalog_volume


def test_quote_list_and_item_report_the_same_minimum_donation(
    client: TestClient, engine: Engine
) -> None:
    with engine.begin() as conn:
        make_price_settings(conn)
        seed_catalog_volume(conn, items=30, plastics=10, seed=31)

    listed = client.get("/api/catalog/items").json()["items"]

    assert len(listed) == 30
    for summary in listed:
        detail = client.get(f"/api/catalog/items/{summary['id']}").json()
        quote = client.post(
            "/api/costing/quote",
            json={"plastics": detail["plastics"], "print_time_s": detail["print_time_s"]},
        ).json()
        assert summary["min_donation_kop"] == detail["quote"]["min_donation_kop"]
        assert quote == detail["quote"]
