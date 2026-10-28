from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import Engine

from calculate3d.core.config import Settings
from calculate3d.main import create_app


class EchoIn(BaseModel):
    value: int


def _app(engine: Engine, dist: Path) -> FastAPI:
    app = create_app(
        Settings(database_url=str(engine.url), web_dist_dir=dist, extra_allowed_hosts=())
    )

    @app.post("/api/_test/echo")
    def echo(body: EchoIn) -> dict[str, int]:
        return {"value": body.value}

    @app.delete("/api/_test/thing", status_code=204)
    def delete_thing() -> None:
        return None

    return app


@pytest.fixture
def guarded(engine: Engine, tmp_path: Path) -> Iterator[TestClient]:
    # No UI here: test routes are added after create_app(), so a `/` mount would shadow them.
    with TestClient(_app(engine, tmp_path / "missing"), base_url="http://127.0.0.1:8000") as c:
        yield c


@pytest.fixture
def with_ui(engine: Engine, tmp_path: Path) -> Iterator[TestClient]:
    (tmp_path / "index.html").write_text("<!doctype html><title>calculate-3d</title>")
    with TestClient(_app(engine, tmp_path), base_url="http://127.0.0.1:8000") as c:
        yield c


def _assert_problem(response: object, status: int, code: str) -> None:
    from httpx import Response

    assert isinstance(response, Response)
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == code


@pytest.mark.parametrize(
    "host",
    ["evil.example.test", "evil.example.test:8000", "127.0.0.1:9999", "192.168.1.20:8000", ""],
)
def test_foreign_host_is_rejected_with_400(guarded: TestClient, host: str) -> None:
    _assert_problem(guarded.get("/api/health", headers={"host": host}), 400, "host_not_allowed")


def test_foreign_host_is_rejected_for_the_ui_too(with_ui: TestClient) -> None:
    response = with_ui.get("/", headers={"host": "rebind.example.test:8000"})

    _assert_problem(response, 400, "host_not_allowed")


@pytest.mark.parametrize(
    "host", ["127.0.0.1:8000", "localhost:8000", "127.0.0.1:5173", "localhost:5173"]
)
def test_allowed_hosts_on_both_ports_pass(guarded: TestClient, host: str) -> None:
    response = guarded.get("/api/health", headers={"host": host})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_foreign_origin_is_rejected_with_403(guarded: TestClient) -> None:
    response = guarded.post(
        "/api/_test/echo", json={"value": 1}, headers={"origin": "https://evil.example.test"}
    )

    _assert_problem(response, 403, "cross_origin_forbidden")


@pytest.mark.parametrize("site", ["cross-site", "same-site"])
def test_cross_site_fetch_metadata_is_rejected_with_403(guarded: TestClient, site: str) -> None:
    response = guarded.get("/api/health", headers={"sec-fetch-site": site})

    _assert_problem(response, 403, "cross_origin_forbidden")


@pytest.mark.parametrize(
    "headers",
    [
        {"origin": "http://127.0.0.1:8000", "sec-fetch-site": "same-origin"},
        {
            "origin": "http://localhost:5173",
            "sec-fetch-site": "same-origin",
            "host": "localhost:5173",
        },
        {"sec-fetch-site": "none"},
    ],
)
def test_same_origin_requests_pass(guarded: TestClient, headers: dict[str, str]) -> None:
    response = guarded.post("/api/_test/echo", json={"value": 7}, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"value": 7}


def test_cross_site_navigation_to_the_ui_is_not_blocked(with_ui: TestClient) -> None:
    response = with_ui.get("/", headers={"sec-fetch-site": "cross-site"})

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("content", "content_type"),
    [
        ('{"value": 1}', "text/plain"),
        ("value=1", "application/x-www-form-urlencoded"),
        ("--b\r\n\r\n--b--", "multipart/form-data; boundary=b"),
        ("", "application/x-www-form-urlencoded"),
    ],
)
def test_non_json_mutation_is_rejected_with_415(
    guarded: TestClient, content: str, content_type: str
) -> None:
    response = guarded.post(
        "/api/_test/echo", content=content, headers={"content-type": content_type}
    )

    _assert_problem(response, 415, "unsupported_media_type")


def test_json_with_charset_is_accepted(guarded: TestClient) -> None:
    response = guarded.post(
        "/api/_test/echo",
        content='{"value": 3}',
        headers={"content-type": "application/json; charset=utf-8"},
    )

    assert response.status_code == 200


def test_bodyless_delete_is_accepted(guarded: TestClient) -> None:
    assert guarded.delete("/api/_test/thing").status_code == 204


def test_settings_derive_allowed_hosts_from_app_and_vite_ports() -> None:
    settings = Settings(port=8100, vite_port=5200, extra_allowed_hosts=())

    assert settings.allowed_hosts == frozenset(
        {"127.0.0.1:8100", "localhost:8100", "127.0.0.1:5200", "localhost:5200"}
    )
    assert "http://localhost:5200" in settings.allowed_origins
