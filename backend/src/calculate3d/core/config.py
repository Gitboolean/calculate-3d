"""Application settings, read from `CALC3D_*` environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[3]
REPO_DIR = BACKEND_DIR.parent
# The server binds 127.0.0.1 only (ADR 0004); browsers may address it by either name.
LOCAL_NAMES = ("127.0.0.1", "localhost")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CALC3D_")

    database_url: str = f"sqlite:///{BACKEND_DIR / 'var' / 'calculate3d.db'}"
    port: int = 8000
    # Vite dev server port (`make dev`); its proxy forwards the browser's Host/Origin unchanged.
    vite_port: int = 5173
    # Extra `Host` values the request guard accepts — empty in real runs; tests add `testserver`.
    extra_allowed_hosts: tuple[str, ...] = ()
    # Built web UI served at `/` by `make run`; skipped when absent (API-only / `make dev`).
    web_dist_dir: Path = REPO_DIR / "web" / "dist"

    @property
    def allowed_hosts(self) -> frozenset[str]:
        """`Host` values the request guard accepts (ADR 0007 of cost-calculator)."""
        local = {f"{name}:{port}" for name in LOCAL_NAMES for port in (self.port, self.vite_port)}
        return frozenset(local | set(self.extra_allowed_hosts))

    @property
    def allowed_origins(self) -> frozenset[str]:
        return frozenset(f"http://{host}" for host in self.allowed_hosts)


@lru_cache
def get_settings() -> Settings:
    return Settings()
