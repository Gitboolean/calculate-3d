"""Application settings, read from `CALC3D_*` environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[3]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CALC3D_")

    database_url: str = f"sqlite:///{BACKEND_DIR / 'var' / 'calculate3d.db'}"
    port: int = 8000
    # Built web UI served at `/` by `make run`; skipped when absent (API-only / `make dev`).
    web_dist_dir: Path = REPO_DIR / "web" / "dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
