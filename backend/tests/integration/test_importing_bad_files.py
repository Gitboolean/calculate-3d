import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select

from calculate3d.modules.importing.tables import filament_mappings
from tests.factories import make_plastic, make_price_settings
from tests.fixtures.slicer.bad_files import BAD_FILES, BadFile


@pytest.fixture
def ready(engine: Engine) -> None:
    with engine.begin() as conn:
        make_price_settings(conn)
        make_plastic(conn)


@pytest.mark.usefixtures("ready")
@pytest.mark.parametrize("case", BAD_FILES, ids=lambda c: c.name)
def test_bad_file_is_rejected_with_its_code_fast_and_changes_nothing(
    client: TestClient, engine: Engine, case: BadFile
) -> None:
    started = time.perf_counter()
    response = client.post(
        "/api/importing/parse",
        content=case.body,
        headers={"Content-Type": "application/octet-stream"},
    )
    elapsed = time.perf_counter() - started

    assert response.status_code == 422, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == case.expected_code
    assert elapsed < 5
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(filament_mappings)).scalar() == 0
