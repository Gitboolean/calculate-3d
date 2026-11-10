"""PRD §6 «Збереженість зіставлень»: a saved mapping survives a restart; a deleted plastic is
forgotten (AC-11)."""

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from calculate3d.core.config import Settings
from calculate3d.main import create_app
from tests.fixtures.slicer import VTULKA_SLICED
from tests.integration.test_nfr_durability import AC04

PLA = "Bambu PLA Basic @BBL A1M"


def _parse(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/importing/parse",
        content=VTULKA_SLICED.read_bytes(),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200, response.text
    filament: dict[str, object] = response.json()["filaments"][0]
    return filament


def test_mapping_survives_a_restart_and_dies_with_its_plastic(engine: Engine) -> None:
    url = str(engine.url)
    engine.dispose()

    with TestClient(create_app(Settings(database_url=url))) as first_run:
        first_run.put("/api/pricing/settings", json=AC04)
        white = first_run.post(
            "/api/pricing/plastics", json={"name": "PLA білий", "price_per_kg_kop": 40000}
        ).json()["id"]
        assert _parse(first_run)["plastic_id"] is None
        saved = first_run.post(
            "/api/catalog/items",
            json={
                "name": "Втулка A",
                "plastics": [{"plastic_id": white, "usage_cg": 1154}],
                "print_time_s": 5880,
                "filament_mappings": [
                    {"filament_name": PLA, "filament_color": "#FFFFFF", "plastic_id": white}
                ],
            },
        )
        assert saved.status_code == 201, saved.text

    with TestClient(create_app(Settings(database_url=url))) as second_run:
        assert _parse(second_run)["plastic_id"] == white
        # Only items block a plastic's deletion; the mapping just goes with it (AC-11).
        assert second_run.delete(f"/api/catalog/items/{saved.json()['id']}").status_code == 204
        assert second_run.delete(f"/api/pricing/plastics/{white}").status_code == 204
        assert (
            second_run.post(
                "/api/pricing/plastics", json={"name": "PLA інший", "price_per_kg_kop": 40000}
            ).status_code
            == 201
        )
        assert _parse(second_run)["plastic_id"] is None
