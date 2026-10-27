from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from fastapi.testclient import TestClient

from calculate3d.core.config import Settings, get_settings
from calculate3d.main import create_app
from tests.conftest import alembic_config


@pytest.fixture
def unreachable_default_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point the env/default DB URL somewhere unopenable, so any fallback to it reports `down`."""
    monkeypatch.setenv("CALC3D_DATABASE_URL", "sqlite:////nonexistent-dir/sentinel.db")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.usefixtures("unreachable_default_db")
def test_app_uses_database_url_from_settings_passed_to_create_app(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'app.db'}"
    command.upgrade(alembic_config(url), "head")

    with TestClient(create_app(Settings(database_url=url))) as c:
        response = c.get("/api/health")

    assert response.json() == {"status": "ok", "db": "ok"}


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
