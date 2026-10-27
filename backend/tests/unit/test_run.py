from collections.abc import Iterator
from typing import Any

import pytest

from calculate3d import main
from calculate3d.core.config import Settings, get_settings


@pytest.fixture
def fresh_settings() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_run_binds_loopback_even_when_host_env_is_set(
    monkeypatch: pytest.MonkeyPatch, fresh_settings: None
) -> None:
    monkeypatch.setenv("CALC3D_HOST", "0.0.0.0")
    get_settings.cache_clear()
    recorded: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> None:
        recorded.update(kwargs)

    monkeypatch.setattr("calculate3d.main.uvicorn.run", fake_run)

    main.run()

    assert recorded["host"] == "127.0.0.1"


def test_settings_has_no_host_field() -> None:
    assert "host" not in Settings.model_fields
