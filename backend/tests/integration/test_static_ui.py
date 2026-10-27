from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from calculate3d.core.config import Settings
from calculate3d.core.db import get_engine
from calculate3d.main import create_app


def _client(engine: Engine, dist: Path) -> TestClient:
    app = create_app(Settings(web_dist_dir=dist))
    app.dependency_overrides[get_engine] = lambda: engine
    return TestClient(app)


def test_root_serves_built_ui_next_to_the_api(engine: Engine, tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<!doctype html><title>calculate-3d</title>")

    with _client(engine, tmp_path) as client:
        page = client.get("/")
        health = client.get("/api/health")
        missing = client.get("/api/does-not-exist")

    assert page.status_code == 200
    assert "<title>calculate-3d</title>" in page.text
    assert health.json() == {"status": "ok", "db": "ok"}
    assert missing.headers["content-type"] == "application/problem+json"


def test_api_still_starts_when_ui_is_not_built(engine: Engine, tmp_path: Path) -> None:
    with _client(engine, tmp_path / "missing") as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/").status_code == 404
