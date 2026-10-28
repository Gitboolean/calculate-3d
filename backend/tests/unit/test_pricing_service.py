from collections.abc import Callable

import pytest
from pydantic import ValidationError
from sqlalchemy import Connection, func, select

from calculate3d.core.errors import AppError
from calculate3d.modules.pricing import service
from calculate3d.modules.pricing.schemas import PlasticInput, PriceSettingsInput
from calculate3d.modules.pricing.tables import plastics, price_settings

AC04 = PriceSettingsInput(
    tariff_per_kwh_kop=432,
    printer_power_w=150,
    printer_price_kop=3_000_000,
    printer_lifetime_h=5000,
    parts_per_hour_kop=100,
    scrap_rate_permille=100,
)


def no_items(_: str) -> list[str]:
    return []


def items_named(*names: str) -> Callable[[str], list[str]]:
    return lambda _: list(names)


def test_created_plastic_is_listed_with_its_price(conn: Connection) -> None:
    created = service.create_plastic(conn, PlasticInput(name="PETG чорний", price_per_kg_kop=65000))

    assert created.name == "PETG чорний"
    assert created.price_per_kg_kop == 65000
    assert [p.model_dump() for p in service.list_plastics(conn)] == [created.model_dump()]


def test_plastic_name_is_stored_trimmed(conn: Connection) -> None:
    created = service.create_plastic(
        conn, PlasticInput(name="  PLA білий ", price_per_kg_kop=40000)
    )

    assert created.name == "PLA білий"
    assert conn.execute(select(plastics.c.name, plastics.c.name_key)).one() == (
        "PLA білий",
        "pla білий",
    )


@pytest.mark.parametrize("duplicate", ["petg чорний", "PETG чорний ", " Petg Чорний"])
def test_duplicate_name_after_trim_and_casefold_is_rejected(
    conn: Connection, duplicate: str
) -> None:
    service.create_plastic(conn, PlasticInput(name="PETG чорний", price_per_kg_kop=65000))

    with pytest.raises(AppError) as exc:
        service.create_plastic(conn, PlasticInput(name=duplicate, price_per_kg_kop=1))

    assert (exc.value.code, exc.value.status, exc.value.field) == (
        "pricing.name_taken",
        409,
        "name",
    )
    assert conn.execute(select(func.count()).select_from(plastics)).scalar() == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "price_per_kg_kop": 65000},
        {"name": "   ", "price_per_kg_kop": 65000},
        {"name": "x" * 101, "price_per_kg_kop": 65000},
        {"name": "PETG", "price_per_kg_kop": 0},
        {"name": "PETG", "price_per_kg_kop": -1},
        {"name": "PETG", "price_per_kg_kop": 649.995},
        {"name": "PETG", "price_per_kg_kop": "65000"},
        {"name": "PETG", "price_per_kg_kop": 65000, "extra": 1},
    ],
)
def test_invalid_plastic_input_is_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        PlasticInput.model_validate(payload)


def test_update_changes_name_and_price_and_may_keep_own_name(conn: Connection) -> None:
    created = service.create_plastic(conn, PlasticInput(name="PETG чорний", price_per_kg_kop=65000))

    same_name = service.update_plastic(
        conn, created.id, PlasticInput(name="petg ЧОРНИЙ", price_per_kg_kop=80000)
    )

    assert (same_name.name, same_name.price_per_kg_kop) == ("petg ЧОРНИЙ", 80000)


def test_update_to_another_plastics_name_is_rejected(conn: Connection) -> None:
    service.create_plastic(conn, PlasticInput(name="PLA білий", price_per_kg_kop=40000))
    petg = service.create_plastic(conn, PlasticInput(name="PETG чорний", price_per_kg_kop=65000))

    with pytest.raises(AppError) as exc:
        service.update_plastic(conn, petg.id, PlasticInput(name="pla білий", price_per_kg_kop=1))

    assert exc.value.code == "pricing.name_taken"


@pytest.mark.parametrize("action", ["update", "delete"])
def test_unknown_plastic_is_not_found(conn: Connection, action: str) -> None:
    with pytest.raises(AppError) as exc:
        if action == "update":
            service.update_plastic(conn, "missing", PlasticInput(name="X", price_per_kg_kop=1))
        else:
            service.delete_plastic(conn, "missing", no_items)

    assert (exc.value.code, exc.value.status) == ("pricing.plastic_not_found", 404)


def test_plastic_used_by_items_is_not_deleted_and_items_are_named(conn: Connection) -> None:
    pla = service.create_plastic(conn, PlasticInput(name="PLA білий", price_per_kg_kop=40000))

    with pytest.raises(AppError) as exc:
        service.delete_plastic(conn, pla.id, items_named("Підставка", "Органайзер"))

    assert (exc.value.code, exc.value.status) == ("pricing.plastic_in_use", 409)
    assert exc.value.items == ["Органайзер", "Підставка"]
    assert [p.id for p in service.list_plastics(conn)] == [pla.id]
    # AC-03: its price can still change.
    updated = service.update_plastic(
        conn, pla.id, PlasticInput(name="PLA білий", price_per_kg_kop=45000)
    )
    assert updated.price_per_kg_kop == 45000


def test_unused_plastic_is_deleted(conn: Connection) -> None:
    pla = service.create_plastic(conn, PlasticInput(name="PLA білий", price_per_kg_kop=40000))

    service.delete_plastic(conn, pla.id, no_items)

    assert service.list_plastics(conn) == []


def test_plastics_are_listed_in_ukrainian_order(conn: Connection) -> None:
    for name in ["Ялинка", "єнот", "Benchy", "ґава", "гава"]:
        service.create_plastic(conn, PlasticInput(name=name, price_per_kg_kop=1))

    assert [p.name for p in service.list_plastics(conn)] == [
        "Benchy",
        "гава",
        "ґава",
        "єнот",
        "Ялинка",
    ]


def test_list_plastics_by_ids_returns_only_the_requested(conn: Connection) -> None:
    a = service.create_plastic(conn, PlasticInput(name="A", price_per_kg_kop=1))
    service.create_plastic(conn, PlasticInput(name="B", price_per_kg_kop=2))
    c = service.create_plastic(conn, PlasticInput(name="C", price_per_kg_kop=3))

    found = service.list_plastics_by_ids(conn, [c.id, a.id, "missing"])

    assert sorted(p.id for p in found) == sorted([a.id, c.id])


def test_settings_are_not_set_until_first_save(conn: Connection) -> None:
    assert service.get_settings(conn) is None


def test_saved_settings_report_wear_per_hour(conn: Connection) -> None:
    saved = service.replace_settings(conn, AC04)

    assert saved.wear_per_hour_kop == 700
    assert service.get_settings(conn) == saved
    assert saved.model_dump(exclude={"wear_per_hour_kop"}) == AC04.model_dump()


def test_replacing_settings_overwrites_all_fields_in_one_row(conn: Connection) -> None:
    service.replace_settings(conn, AC04)
    zeroes = PriceSettingsInput(
        tariff_per_kwh_kop=0,
        printer_power_w=0,
        printer_price_kop=0,
        printer_lifetime_h=1,
        parts_per_hour_kop=0,
        scrap_rate_permille=0,
    )

    saved = service.replace_settings(conn, zeroes)

    assert saved.model_dump(exclude={"wear_per_hour_kop"}) == zeroes.model_dump()
    assert saved.wear_per_hour_kop == 0
    assert conn.execute(select(func.count()).select_from(price_settings)).scalar() == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tariff_per_kwh_kop", -1),
        ("printer_power_w", -1),
        ("printer_power_w", 152.5),
        ("printer_price_kop", -1),
        ("printer_lifetime_h", 0),
        ("printer_lifetime_h", 2.5),
        ("parts_per_hour_kop", -1),
        ("scrap_rate_permille", -1),
        ("scrap_rate_permille", 1001),
        ("tariff_per_kwh_kop", None),
    ],
)
def test_invalid_settings_input_is_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        PriceSettingsInput.model_validate({**AC04.model_dump(), field: value})


def test_settings_cannot_be_cleared_by_omitting_fields() -> None:
    payload = AC04.model_dump()
    del payload["scrap_rate_permille"]

    with pytest.raises(ValidationError):
        PriceSettingsInput.model_validate(payload)
