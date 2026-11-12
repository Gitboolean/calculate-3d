from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.factories import make_filament_mapping, make_plastic, make_price_settings
from tests.fixtures.slicer import LITTLE_TREES, VTULKA_PROJECT, VTULKA_SLICED

PARSE = "/api/importing/parse"
OCTET = {"Content-Type": "application/octet-stream"}
PLA = "Bambu PLA Basic @BBL A1M"
MAX_BODY = 100_000_000


@pytest.fixture
def white(engine: Engine) -> str:
    """Price settings + «PLA білий», mapped from the vtulka filament (AC-01 precondition)."""
    with engine.begin() as conn:
        make_price_settings(conn)
        plastic = make_plastic(conn, name="PLA білий", price_per_kg_kop=40000)
        make_filament_mapping(conn, plastic_id=plastic)
    return plastic


def _parse(client: TestClient, body: bytes) -> Any:
    return client.post(PARSE, content=body, headers=OCTET)


def test_sliced_vtulka_parses_with_the_remembered_plastic(client: TestClient, white: str) -> None:
    response = _parse(client, VTULKA_SLICED.read_bytes())

    assert response.status_code == 200
    assert response.json() == {
        "plate": {"index": 1, "name": ""},
        "print_time_s": 5880,
        "filaments": [
            {
                "filament_name": PLA,
                "filament_type": "PLA",
                "filament_color": "#FFFFFF",
                "usage_mg": 11540,
                "plastic_id": white,
            }
        ],
    }


def test_little_trees_names_its_plate_and_three_used_filaments(
    client: TestClient, white: str
) -> None:
    response = _parse(client, LITTLE_TREES.read_bytes())

    assert response.status_code == 200
    body = response.json()
    assert body["plate"] == {"index": 1, "name": "mini christmas tree"}
    assert body["print_time_s"] == 5460
    assert [(f["filament_color"], f["usage_mg"], f["plastic_id"]) for f in body["filaments"]] == [
        ("#3F8E43", 15490, None),
        ("#000000", 2230, None),
        ("#FEC600", 2360, None),
    ]


def test_without_settings_the_file_is_not_parsed(client: TestClient) -> None:
    response = _parse(client, VTULKA_SLICED.read_bytes())

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "importing.settings_missing"
    assert response.json()["missing"] == ["plastics", "price_settings"]


def test_unsliced_project_is_422_not_sliced(client: TestClient, white: str) -> None:
    response = _parse(client, VTULKA_PROJECT.read_bytes())

    assert response.status_code == 422
    assert response.json()["code"] == "importing.not_sliced"


def test_body_over_the_limit_is_413_by_content_length(client: TestClient, white: str) -> None:
    response = _parse(client, bytes(MAX_BODY + 1))

    assert response.status_code == 413
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "importing.file_too_large"


def test_chunked_body_over_the_limit_is_413(client: TestClient, white: str) -> None:
    def chunks() -> Iterator[bytes]:
        for _ in range(100):
            yield bytes(1_000_000)
        yield b"\0"

    response = client.post(PARSE, content=chunks(), headers=OCTET)

    assert response.status_code == 413
    assert response.json()["code"] == "importing.file_too_large"


def test_body_of_exactly_the_limit_reaches_the_parser_by_content_length(
    client: TestClient, white: str
) -> None:
    # PRD §6: ≤ 100 MB is accepted — zeros are no archive, so the parser rejects it, not the size.
    response = _parse(client, bytes(MAX_BODY))

    assert response.status_code == 422
    assert response.json()["code"] == "importing.not_slicer_project"


def test_chunked_body_of_exactly_the_limit_reaches_the_parser(
    client: TestClient, white: str
) -> None:
    def chunks() -> Iterator[bytes]:
        for _ in range(100):
            yield bytes(1_000_000)

    response = client.post(PARSE, content=chunks(), headers=OCTET)

    assert response.status_code == 422
    assert response.json()["code"] == "importing.not_slicer_project"


def test_oversized_content_length_is_rejected_before_settings(client: TestClient) -> None:
    # Size is checked before settings readiness (contract order: 413 before 409).
    response = _parse(client, bytes(MAX_BODY + 1))

    assert response.status_code == 413


def test_same_origin_octet_stream_reaches_the_parser(client: TestClient, white: str) -> None:
    response = client.post(
        PARSE,
        content=VTULKA_SLICED.read_bytes(),
        headers={**OCTET, "Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"},
    )

    assert response.status_code == 200


def test_openapi_describes_a_binary_octet_stream_body_and_problem_errors(
    client: TestClient,
) -> None:
    operation = client.get("/openapi.json").json()["paths"][PARSE]["post"]

    assert operation["operationId"] == "parseSlicerFile"
    body = operation["requestBody"]
    assert body["required"] is True
    assert body["content"]["application/octet-stream"]["schema"] == {
        "type": "string",
        "format": "binary",
        "maxLength": MAX_BODY,
    }
    for status in ("409", "413", "415", "422"):
        assert set(operation["responses"][status]["content"]) == {"application/problem+json"}
