import re

import pytest
from sqlalchemy import Connection

from calculate3d.core.errors import AppError
from calculate3d.modules.importing import parser, repo, service
from calculate3d.modules.importing.service import FilamentMappingInput
from calculate3d.modules.pricing import service as pricing
from calculate3d.modules.pricing.schemas import PlasticInput, PriceSettingsInput
from tests.fixtures.slicer import LITTLE_TREES, VTULKA_PROJECT, VTULKA_SLICED

AC04 = PriceSettingsInput(
    tariff_per_kwh_kop=432,
    printer_power_w=150,
    printer_price_kop=3_000_000,
    printer_lifetime_h=5000,
    parts_per_hour_kop=100,
    scrap_rate_permille=100,
)

# ImportRejected responses of contracts/openapi.yaml: parser code → HTTP status.
REJECTIONS = {
    "importing.not_slicer_project": 422,
    "importing.not_sliced": 422,
    "importing.multiple_sliced_plates": 422,
    "importing.corrupted_file": 422,
    "importing.print_time_out_of_range": 422,
    "importing.no_filament_usage": 422,
}

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


@pytest.fixture
def ready(conn: Connection, plastic: str) -> str:
    """Settings are complete (AC-04 precondition); returns the «PLA білий» id."""
    pricing.replace_settings(conn, AC04)
    return plastic


@pytest.fixture
def parse_calls(monkeypatch: pytest.MonkeyPatch) -> list[bytes]:
    calls: list[bytes] = []
    real = parser.parse

    def spy(body: bytes) -> parser.ParsedFile:
        calls.append(body)
        return real(body)

    monkeypatch.setattr(service.parser, "parse", spy)
    return calls


@pytest.mark.parametrize(
    ("plastics", "settings", "missing"),
    [
        (False, False, ["plastics", "price_settings"]),
        (False, True, ["plastics"]),
        (True, False, ["price_settings"]),
    ],
)
def test_missing_settings_reject_the_import_before_parsing(
    conn: Connection,
    parse_calls: list[bytes],
    plastics: bool,
    settings: bool,
    missing: list[str],
) -> None:
    if plastics:
        pricing.create_plastic(conn, PlasticInput(name="PLA білий", price_per_kg_kop=40000))
    if settings:
        pricing.replace_settings(conn, AC04)

    with pytest.raises(service.ImportSettingsMissing) as err:
        service.parse_slicer_file(conn, VTULKA_SLICED.read_bytes())

    assert (err.value.code, err.value.status) == ("importing.settings_missing", 409)
    assert err.value.missing == missing
    assert parse_calls == []


@pytest.mark.parametrize(("code", "status"), REJECTIONS.items())
def test_each_parser_rejection_is_its_own_app_error(
    conn: Connection, ready: str, monkeypatch: pytest.MonkeyPatch, code: str, status: int
) -> None:
    def reject(_body: bytes) -> parser.ParsedFile:
        raise parser.ParseError(code)

    monkeypatch.setattr(service.parser, "parse", reject)

    with pytest.raises(AppError) as err:
        service.parse_slicer_file(conn, b"whatever")

    assert (err.value.code, err.value.status) == (code, status)
    assert type(err.value) is not AppError


def test_a_real_unsliced_project_is_rejected_as_not_sliced(conn: Connection, ready: str) -> None:
    with pytest.raises(AppError) as err:
        service.parse_slicer_file(conn, VTULKA_PROJECT.read_bytes())

    assert err.value.code == "importing.not_sliced"


def test_file_too_large_is_413() -> None:
    err = service.FileTooLarge()
    assert (err.code, err.status) == ("importing.file_too_large", 413)


def test_parse_substitutes_only_a_remembered_plastic(conn: Connection, ready: str) -> None:
    service.remember_mappings(conn, [mapping(PLA, "#FFFFFF", ready)])

    parsed = service.parse_slicer_file(conn, VTULKA_SLICED.read_bytes())

    assert parsed.model_dump() == {
        "plate": {"index": 1, "name": ""},
        "print_time_s": 5880,
        "filaments": [
            {
                "filament_name": PLA,
                "filament_type": "PLA",
                "filament_color": "#FFFFFF",
                "usage_mg": 11540,
                "plastic_id": ready,
            }
        ],
    }


def test_same_preset_in_another_color_is_not_substituted(conn: Connection, ready: str) -> None:
    # Only green is mapped; black and yellow share the preset but not the color (AC-09).
    service.remember_mappings(conn, [mapping(PLA, "#3F8E43", ready)])

    parsed = service.parse_slicer_file(conn, LITTLE_TREES.read_bytes())

    assert parsed.plate.model_dump() == {"index": 1, "name": "mini christmas tree"}
    assert [(f.filament_color, f.plastic_id) for f in parsed.filaments] == [
        ("#3F8E43", ready),
        ("#000000", None),
        ("#FEC600", None),
    ]


def test_parsing_writes_nothing(conn: Connection, ready: str) -> None:
    service.parse_slicer_file(conn, VTULKA_SLICED.read_bytes())

    assert repo.find_mappings(conn, [(PLA, "#FFFFFF")]) == {}


def _importing_errors() -> list[AppError]:
    classes: list[type[AppError]] = []
    pending = list(AppError.__subclasses__())
    while pending:
        cls = pending.pop()
        pending.extend(cls.__subclasses__())
        if cls.__module__ == service.__name__:
            classes.append(cls)
    errors = []
    for cls in classes:
        if cls is service.ImportSettingsMissing:
            errors.append(cls(["plastics"]))
        elif cls is service.ImportPlasticNotFound:
            errors.append(cls(0))
        else:
            errors.append(cls())
    return errors


def test_every_importing_message_is_ukrainian() -> None:
    errors = _importing_errors()

    assert {e.code for e in errors} == {
        *REJECTIONS,
        "importing.settings_missing",
        "importing.file_too_large",
        "importing.plastic_not_found",
    }
    for error in errors:
        assert re.search(r"[а-яіїєґ]{3,}", error.message, re.IGNORECASE), error.message
