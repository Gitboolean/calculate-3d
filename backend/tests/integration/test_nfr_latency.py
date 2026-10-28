"""QG-2: server response time and query count of the hot paths on NFR-sized data."""

import os
import time
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, select

from calculate3d.modules.pricing.tables import plastics
from tests.factories import make_price_settings, seed_catalog_volume

SAMPLES = 60


def _p95(call: Callable[[], Any]) -> float:
    call()  # warm-up
    durations = []
    for _ in range(SAMPLES):
        start = time.perf_counter()
        response = call()
        durations.append(time.perf_counter() - start)
        assert response.status_code == 200
    return sorted(durations)[int(0.95 * SAMPLES) - 1]


@pytest.fixture
def seeded(engine: Engine) -> Iterator[None]:
    with engine.begin() as conn:
        make_price_settings(conn)
        seed_catalog_volume(conn, items=1000, plastics=50, seed=2026)
    yield


on_ci = pytest.mark.skipif(
    bool(os.environ.get("CI")), reason="wall-clock latency is measured on the author's machine"
)


@on_ci
def test_quote_p95_is_within_300_ms(client: TestClient, engine: Engine, seeded: None) -> None:
    with engine.connect() as conn:
        plastic_id = conn.execute(select(plastics.c.id).limit(1)).scalar_one()
    payload = {"plastics": [{"plastic_id": plastic_id, "usage_cg": 12000}], "print_time_s": 12600}

    assert _p95(lambda: client.post("/api/costing/quote", json=payload)) <= 0.300


@on_ci
def test_catalog_p95_is_within_500_ms(client: TestClient, seeded: None) -> None:
    assert _p95(lambda: client.get("/api/catalog/items")) <= 0.500


def _queries_per_catalog_read(client: TestClient) -> int:
    app_engine: Engine = client.app.state.engine  # type: ignore[attr-defined]
    statements: list[str] = []

    def record(*args: Any) -> None:
        statements.append(args[2])

    event.listen(app_engine, "before_cursor_execute", record)
    try:
        assert client.get("/api/catalog/items").status_code == 200
    finally:
        event.remove(app_engine, "before_cursor_execute", record)
    return len(statements)


@pytest.mark.parametrize("items", [10, 1000])
def test_catalog_read_takes_a_fixed_number_of_queries(
    client: TestClient, engine: Engine, items: int
) -> None:
    with engine.begin() as conn:
        make_price_settings(conn)
        seed_catalog_volume(conn, items=items, plastics=50, seed=items)

    # items + usage rows, settings, «any plastic?», prices of the referenced plastics.
    assert _queries_per_catalog_read(client) == 5
