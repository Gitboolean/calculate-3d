"""Application settings, read from `CALC3D_*` environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CALC3D_")

    database_url: str = f"sqlite:///{BACKEND_DIR / 'var' / 'calculate3d.db'}"
    # Local-only (ADR 0004): never bind to a public interface by default.
    host: str = "127.0.0.1"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
