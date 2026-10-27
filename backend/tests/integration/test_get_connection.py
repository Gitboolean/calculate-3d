from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Connection, text

from calculate3d.core.config import Settings
from calculate3d.core.db import create_db_engine, get_connection
from calculate3d.main import create_app


def _build_app(url: str, tmp_path: Path) -> FastAPI:
    # No web/dist mount: routes added after create_app() must not be shadowed by "/".
    app = create_app(Settings(database_url=url, web_dist_dir=tmp_path / "missing"))

    @app.post("/api/_test/notes/{body}")
    def add(body: str, conn: Annotated[Connection, Depends(get_connection)]) -> None:
        conn.execute(text("INSERT INTO note (body) VALUES (:body)"), {"body": body})

    @app.post("/api/_test/notes/{body}/fail")
    def add_then_fail(body: str, conn: Annotated[Connection, Depends(get_connection)]) -> None:
        conn.execute(text("INSERT INTO note (body) VALUES (:body)"), {"body": body})
        raise RuntimeError("boom after write")

    return app


def _notes(url: str) -> list[str]:
    engine = create_db_engine(url)
    try:
        with engine.connect() as conn:
            return list(conn.execute(text("SELECT body FROM note ORDER BY body")).scalars())
    finally:
        engine.dispose()


def _create_note_table(url: str) -> None:
    engine = create_db_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE note (body TEXT NOT NULL)"))
    finally:
        engine.dispose()


def test_request_transaction_commits_when_handler_succeeds(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'tx.db'}"
    _create_note_table(url)

    with TestClient(_build_app(url, tmp_path)) as client:
        response = client.post("/api/_test/notes/kept")

    assert response.status_code == 200
    assert _notes(url) == ["kept"]


def test_request_transaction_rolls_back_when_handler_raises(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'tx.db'}"
    _create_note_table(url)

    with TestClient(_build_app(url, tmp_path), raise_server_exceptions=False) as client:
        response = client.post("/api/_test/notes/lost/fail")

    assert response.status_code == 500
    assert _notes(url) == []
