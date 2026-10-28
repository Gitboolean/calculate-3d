from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from calculate3d.core.config import Settings
from calculate3d.main import create_app


def _client(engine: Engine, dist: Path) -> TestClient:
    app = create_app(Settings(database_url=str(engine.url), web_dist_dir=dist))
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


def _built_ui(dist: Path) -> None:
    (dist / "index.html").write_text("<!doctype html><title>calculate-3d</title>")
    (dist / "assets").mkdir()
    (dist / "assets" / "app.js").write_text("console.log('app')")


def test_client_side_routes_serve_index_html(engine: Engine, tmp_path: Path) -> None:
    _built_ui(tmp_path)

    with _client(engine, tmp_path) as client:
        settings = client.get("/settings")
        item = client.get("/catalog/0190e7a4-0000-7000-8000-000000000000")
        asset = client.get("/assets/app.js")

    for page in (settings, item):
        assert page.status_code == 200
        assert page.headers["content-type"].startswith("text/html")
        assert "<title>calculate-3d</title>" in page.text
    assert asset.status_code == 200
    assert asset.text == "console.log('app')"


def test_unknown_api_path_stays_a_problem_json_404(engine: Engine, tmp_path: Path) -> None:
    _built_ui(tmp_path)

    with _client(engine, tmp_path) as client:
        for path in ("/api/unknown", "/api", "/api/catalog/items/x/y"):
            response = client.get(path)
            assert response.status_code == 404, path
            assert response.headers["content-type"] == "application/problem+json"
            assert response.json()["code"] == "not_found"
