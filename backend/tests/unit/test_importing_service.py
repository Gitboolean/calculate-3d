import pytest
from sqlalchemy import Connection

from calculate3d.modules.importing import repo, service
from calculate3d.modules.importing.service import FilamentMappingInput
from calculate3d.modules.pricing import service as pricing
from calculate3d.modules.pricing.schemas import PlasticInput

PLA = "Bambu PLA Basic @BBL A1M"
PETG = "Bambu PETG Basic @BBL A1M"


def mapping(name: str, color: str, plastic_id: str) -> FilamentMappingInput:
    return FilamentMappingInput(filament_name=name, filament_color=color, plastic_id=plastic_id)


@pytest.fixture
def plastic(conn: Connection) -> str:
    return pricing.create_plastic(conn, PlasticInput(name="PLA білий", price_per_kg_kop=40000)).id


def test_remember_mappings_stores_and_replaces_choices(conn: Connection, plastic: str) -> None:
    other = pricing.create_plastic(conn, PlasticInput(name="PETG чорний", price_per_kg_kop=65000))

    service.remember_mappings(conn, [mapping(PLA, "#FFFFFF", plastic)])
    service.remember_mappings(
        conn, [mapping(PLA, "#FFFFFF", other.id), mapping(PETG, "#000000", other.id)]
    )

    assert repo.find_mappings(conn, [(PLA, "#FFFFFF"), (PETG, "#000000")]) == {
        (PLA, "#FFFFFF"): other.id,
        (PETG, "#000000"): other.id,
    }


def test_no_mappings_writes_nothing(conn: Connection) -> None:
    service.remember_mappings(conn, [])

    assert repo.find_mappings(conn, [(PLA, "#FFFFFF")]) == {}


def test_unknown_plastic_is_a_domain_error_pointing_at_its_mapping(
    conn: Connection, plastic: str
) -> None:
    with pytest.raises(service.ImportPlasticNotFound) as err:
        service.remember_mappings(
            conn, [mapping(PLA, "#FFFFFF", plastic), mapping(PETG, "#000000", "gone")]
        )

    assert (err.value.code, err.value.status) == ("importing.plastic_not_found", 422)
    assert err.value.field == "filament_mappings.1.plastic_id"
    assert repo.find_mappings(conn, [(PLA, "#FFFFFF")]) == {}


def test_plastic_vanishing_after_the_pre_check_maps_the_repo_exception(
    conn: Connection, plastic: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The pre-check sees the plastic; the FK backstop then rejects the write (SAD §6 flow 6).
    monkeypatch.setattr(
        service.pricing_service,
        "list_plastics_by_ids",
        lambda _conn, ids: [pricing.Plastic(id=i, name="x", price_per_kg_kop=1) for i in ids],
    )

    with pytest.raises(service.ImportPlasticNotFound) as err:
        service.remember_mappings(conn, [mapping(PLA, "#FFFFFF", "gone")])

    assert isinstance(err.value.__cause__, repo.MappingPlasticMissing)
    assert err.value.field == "filament_mappings.0.plastic_id"


@pytest.mark.parametrize(
    ("name", "color"),
    [
        ("", "#FFFFFF"),
        (f" {PLA}", "#FFFFFF"),
        ("x" * 201, "#FFFFFF"),
        (PLA, "#ffffff"),
        (PLA, "#FFF"),
    ],
)
def test_mapping_input_accepts_only_canonical_keys(name: str, color: str) -> None:
    with pytest.raises(ValueError):
        mapping(name, color, "p")
