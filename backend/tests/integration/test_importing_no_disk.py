import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.factories import make_plastic, make_price_settings
from tests.fixtures.slicer import VTULKA_PROJECT, VTULKA_SLICED


def _files(*roots: Path) -> set[str]:
    return {os.path.join(d, f) for root in roots for d, _, fs in os.walk(root) for f in fs}


def test_import_leaves_no_bytes_on_disk(
    client: TestClient, engine: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A private temp dir: the machine-wide one is shared with other processes.
    private_tmp = tmp_path / "tmp"
    private_tmp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(private_tmp))
    db_dir = Path(str(engine.url.database)).parent
    with engine.begin() as conn:
        make_price_settings(conn)
        make_plastic(conn)
    client.get("/api/health")  # settle the WAL / shm files of the DB first
    before = _files(private_tmp, db_dir)
    db_size = sum(Path(p).stat().st_size for p in before if p.endswith(".db"))

    for body in (VTULKA_SLICED.read_bytes(), VTULKA_PROJECT.read_bytes(), b"not a zip"):
        client.post(
            "/api/importing/parse",
            content=body,
            headers={"Content-Type": "application/octet-stream"},
        )

    assert _files(private_tmp, db_dir) == before
    assert sum(Path(p).stat().st_size for p in before if p.endswith(".db")) == db_size
