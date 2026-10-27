from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import Engine

from calculate3d.core.config import Settings
from calculate3d.core.errors import AppError
from calculate3d.main import create_app

PROBLEM_KEYS = {"type", "title", "status", "detail", "code"}


class ItemIn(BaseModel):
    qty: int


def build_app(engine: Engine, tmp_path: Path) -> FastAPI:
    app = create_app(Settings(database_url=str(engine.url), web_dist_dir=tmp_path / "missing"))

    @app.get("/api/_test/boom")
    def boom() -> None:
        raise RuntimeError("secret detail")

    @app.post("/api/_test/items")
    def items(body: ItemIn) -> dict[str, int]:
        return {"qty": body.qty}

    @app.get("/api/_test/odd")
    def odd() -> None:
        raise AppError("odd", "Odd status", status=499)

    return app


def test_unhandled_exception_returns_problem_json_without_leaking_detail(
    engine: Engine, tmp_path: Path
) -> None:
    client = TestClient(build_app(engine, tmp_path), raise_server_exceptions=False)

    response = client.get("/api/_test/boom")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body.keys() >= PROBLEM_KEYS
    assert body["code"] == "internal_error"
    assert body["status"] == 500
    assert "secret detail" not in response.text


def test_invalid_body_returns_validation_problem_json(engine: Engine, tmp_path: Path) -> None:
    client = TestClient(build_app(engine, tmp_path))

    response = client.post("/api/_test/items", json={"qty": "not-a-number"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body.keys() >= PROBLEM_KEYS
    assert body["code"] == "validation_error"
    assert body["status"] == 422
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) > 0


def test_method_not_allowed_keeps_allow_header(engine: Engine, tmp_path: Path) -> None:
    client = TestClient(build_app(engine, tmp_path))

    response = client.post("/api/health")

    assert response.status_code == 405
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "GET" in response.headers["allow"]


def test_app_error_with_non_http_status_renders_problem_json(
    engine: Engine, tmp_path: Path
) -> None:
    client = TestClient(build_app(engine, tmp_path), raise_server_exceptions=False)

    response = client.get("/api/_test/odd")

    assert response.status_code == 499
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["title"] == "Error"
    assert body["code"] == "odd"
