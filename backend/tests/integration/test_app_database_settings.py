from pathlib import Path

from alembic import command
from fastapi.testclient import TestClient

from calculate3d.core.config import BACKEND_DIR, Settings
from calculate3d.main import create_app
from tests.conftest import alembic_config

DEFAULT_DB = BACKEND_DIR / "var" / "calculate3d.db"


def _snapshot(path: Path) -> tuple[bool, int | None]:
    return (path.exists(), path.stat().st_mtime_ns if path.exists() else None)


def test_app_uses_database_url_from_settings_passed_to_create_app(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'app.db'}"
    command.upgrade(alembic_config(url), "head")
    before = _snapshot(DEFAULT_DB)

    with TestClient(create_app(Settings(database_url=url))) as c:
        response = c.get("/api/health")

    assert response.json() == {"status": "ok", "db": "ok"}
    assert (tmp_path / "app.db").exists()
    assert _snapshot(DEFAULT_DB) == before


def test_app_reports_db_down_when_settings_database_url_is_unopenable(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'missing-dir' / 'x.db'}"

    with TestClient(create_app(Settings(database_url=url))) as c:
        response = c.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "down"}


def test_two_apps_with_different_database_urls_do_not_share_a_database(tmp_path: Path) -> None:
    good = f"sqlite:///{tmp_path / 'good.db'}"
    command.upgrade(alembic_config(good), "head")
    bad = f"sqlite:///{tmp_path / 'missing-dir' / 'x.db'}"

    with (
        TestClient(create_app(Settings(database_url=good))) as ok_client,
        TestClient(create_app(Settings(database_url=bad))) as down_client,
    ):
        assert ok_client.get("/api/health").json()["db"] == "ok"
        assert down_client.get("/api/health").json()["db"] == "down"
