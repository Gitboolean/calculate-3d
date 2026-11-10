"""QG-4: server time to parse a slicer file, p95 ≤ 5 s up to the 100 MB size limit."""

import time
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.factories import make_filament_mapping, make_plastic, make_price_settings
from tests.fixtures.slicer import LITTLE_TREES, VTULKA_SLICED
from tests.fixtures.slicer.bad_files import padded_to
from tests.integration.test_nfr_latency import on_ci

SAMPLES = 20
LIMIT = 100_000_000


def _p95(call: Callable[[], int]) -> float:
    durations = []
    for _ in range(SAMPLES):
        start = time.perf_counter()
        status = call()
        durations.append(time.perf_counter() - start)
        assert status == 200
    return sorted(durations)[int(0.95 * SAMPLES) - 1]


@pytest.fixture
def ready(engine: Engine) -> None:
    with engine.begin() as conn:
        make_price_settings(conn)
        make_filament_mapping(conn, plastic_id=make_plastic(conn))


def _post(client: TestClient, body: bytes) -> Callable[[], int]:
    def call() -> int:
        return client.post(
            "/api/importing/parse",
            content=body,
            headers={"Content-Type": "application/octet-stream"},
        ).status_code

    return call


@on_ci
@pytest.mark.usefixtures("ready")
@pytest.mark.parametrize("path", [VTULKA_SLICED, LITTLE_TREES], ids=lambda p: p.name)
def test_reference_file_p95_is_within_5_s(client: TestClient, path: Path) -> None:
    assert _p95(_post(client, path.read_bytes())) <= 5


@on_ci
@pytest.mark.usefixtures("ready")
def test_file_of_exactly_100_mb_p95_is_within_5_s(client: TestClient) -> None:
    body = padded_to(LIMIT)

    assert len(body) == LIMIT
    assert _p95(_post(client, body)) <= 5
