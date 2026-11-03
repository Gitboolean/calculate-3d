"""T25 / S2-2: check-then-write is serialized by an eager write lock; FK errors become 4xx."""

import sqlite3
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from calculate3d.core.db import get_connection
from calculate3d.modules.catalog import service as catalog_service
from tests.factories import make_item, make_plastic, make_price_settings


def _problem(response: Any, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    assert response.headers["content-type"] == "application/problem+json"
    body: dict[str, Any] = response.json()
    assert body["code"] == code
    return body


def test_request_connection_holds_the_write_lock_after_a_read_only_statement(
    engine: Engine,
) -> None:
    """AC-03/AC-14b: the pre-check read and the write share one BEGIN IMMEDIATE transaction."""
    path = engine.url.database
    assert path is not None
    request_scope = get_connection(engine)
    conn = next(request_scope)
    other = sqlite3.connect(path, timeout=0.1, isolation_level=None)
    try:
        conn.exec_driver_sql("SELECT 1").all()  # a pre-check read, no write yet

        with pytest.raises(sqlite3.OperationalError, match="locked"):
            other.execute("BEGIN IMMEDIATE")
    finally:
        other.close()
        request_scope.close()


def test_in_use_plastic_that_slips_past_the_precheck_is_a_409_not_a_500(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-03: a race hides the usage from the pre-check; the FK RESTRICT must still be a 409."""
    with engine.begin() as conn:
        petg = make_plastic(conn)
        make_price_settings(conn)
        make_item(conn, name="Підставка", usage={petg: 100})
        make_item(conn, name="Органайзер", usage={petg: 200})

    real = catalog_service.item_names_using_plastic
    calls: list[str] = []

    def stale_first(conn: Any, plastic_id: str) -> list[str]:
        calls.append(plastic_id)
        return [] if len(calls) == 1 else real(conn, plastic_id)

    monkeypatch.setattr(catalog_service, "item_names_using_plastic", stale_first)

    response = client.delete(f"/api/pricing/plastics/{petg}")

    body = _problem(response, 409, "pricing.plastic_in_use")
    assert body["items"] == ["Органайзер", "Підставка"]
    assert any(p["id"] == petg for p in client.get("/api/pricing/plastics").json()["items"])


def test_item_with_a_vanished_plastic_is_a_422_not_a_500(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-14b: the plastic is gone between pre-check and insert; the FK violation is a 422."""
    with engine.begin() as conn:
        make_price_settings(conn)
    ghost = "01900000-0000-7000-8000-00000000dead"

    # The pre-check reads a stale snapshot in which the plastic still exists ...
    monkeypatch.setattr(
        catalog_service.pricing_service,
        "list_plastics_by_ids",
        lambda conn, ids: [SimpleNamespace(id=ghost)],
    )
    # ... and the AC-10 quote is stubbed so the FK insert is reached.
    monkeypatch.setattr(catalog_service.costing_service, "quote", lambda conn, data: None)

    response = client.post(
        "/api/catalog/items",
        json={
            "name": "Брелок",
            "plastics": [{"plastic_id": ghost, "usage_cg": 100}],
            "print_time_s": 600,
        },
    )

    body = _problem(response, 422, "catalog.plastic_not_found")
    assert body["field"] == "plastics.0.plastic_id"
    assert client.get("/api/catalog/items").json() == {"items": []}
