from fastapi.testclient import TestClient

from calculate3d.core.db import create_db_engine, get_engine
from calculate3d.main import create_app


def test_health_reports_api_and_db_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_unknown_route_returns_problem_json(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "Not Found"
    assert body["code"] == "not_found"
    assert {"type", "detail"} <= body.keys()


def test_health_reports_db_down_when_database_unreachable() -> None:
    engine = create_db_engine("sqlite:////nonexistent-dir/x.db")
    app = create_app()
    app.dependency_overrides[get_engine] = lambda: engine
    with TestClient(app) as c:
        response = c.get("/api/health")

    engine.dispose()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "down"}
