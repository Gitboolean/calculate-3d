from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy import Connection

from calculate3d.core.errors import AppError
from calculate3d.modules.catalog import service
from calculate3d.modules.catalog.schemas import ItemInput
from calculate3d.modules.pricing import service as pricing
from calculate3d.modules.pricing.schemas import PlasticInput, PriceSettingsInput

AC04 = PriceSettingsInput(
    tariff_per_kwh_kop=432,
    printer_power_w=150,
    printer_price_kop=3_000_000,
    printer_lifetime_h=5000,
    parts_per_hour_kop=100,
    scrap_rate_permille=100,
)


@pytest.fixture
def ids(conn: Connection) -> dict[str, str]:
    pricing.replace_settings(conn, AC04)
    return {
        "petg": pricing.create_plastic(
            conn, PlasticInput(name="PETG чорний", price_per_kg_kop=65000)
        ).id,
        "pla": pricing.create_plastic(
            conn, PlasticInput(name="PLA білий", price_per_kg_kop=40000)
        ).id,
    }


def item(name: str, *usages: tuple[str, int], print_time_s: int = 12600) -> ItemInput:
    return ItemInput.model_validate(
        {
            "name": name,
            "plastics": [{"plastic_id": pid, "usage_cg": cg} for pid, cg in usages],
            "print_time_s": print_time_s,
        }
    )


def test_saved_item_keeps_exactly_the_entered_parameters(
    conn: Connection, ids: dict[str, str]
) -> None:
    saved = service.create_item(conn, item(" Брелок-тризуб ", (ids["petg"], 12000)))

    assert saved.name == "Брелок-тризуб"
    assert [p.model_dump() for p in saved.plastics] == [
        {"plastic_id": ids["petg"], "usage_cg": 12000}
    ]
    assert saved.print_time_s == 12600
    assert "min_donation_kop" not in saved.model_dump()
    assert service.get_item(conn, saved.id).model_dump(exclude={"quote"}) == saved.model_dump()


@pytest.mark.parametrize("duplicate", ["брелок-тризуб", "Брелок-тризуб  ", "БРЕЛОК-ТРИЗУБ"])
def test_duplicate_item_name_is_rejected(
    conn: Connection, ids: dict[str, str], duplicate: str
) -> None:
    service.create_item(conn, item("Брелок-тризуб", (ids["petg"], 12000)))

    with pytest.raises(AppError) as exc:
        service.create_item(conn, item(duplicate, (ids["pla"], 100)))

    assert (exc.value.code, exc.value.status, exc.value.field) == (
        "catalog.name_taken",
        409,
        "name",
    )
    assert len(service.list_items(conn, None)) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "  ", "plastics": [{"plastic_id": "a", "usage_cg": 1}], "print_time_s": 60},
        {"name": "X", "plastics": [], "print_time_s": 60},
        {"name": "X", "plastics": [{"plastic_id": "a", "usage_cg": 0}], "print_time_s": 60},
        {"name": "X", "plastics": [{"plastic_id": "a", "usage_cg": 1}], "print_time_s": 0},
        {
            "name": "X",
            "plastics": [{"plastic_id": "a", "usage_cg": 1}, {"plastic_id": "a", "usage_cg": 1}],
            "print_time_s": 60,
        },
    ],
)
def test_invalid_item_input_is_rejected(payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ItemInput.model_validate(payload)


def test_unknown_plastic_is_a_422_on_its_row(conn: Connection, ids: dict[str, str]) -> None:
    with pytest.raises(AppError) as exc:
        service.create_item(conn, item("Нове", (ids["petg"], 100), ("gone", 100)))

    assert (exc.value.code, exc.value.status, exc.value.field) == (
        "catalog.plastic_not_found",
        422,
        "plastics.1.plastic_id",
    )
    assert service.list_items(conn, None) == []


def test_catalog_search_filters_and_sorts_in_ukrainian_order(
    conn: Connection, ids: dict[str, str]
) -> None:
    for name in [
        "Ялинка-тризуб",
        "Іграшка",
        "Брелок-Тризуб",
        "ґудзик тризуб",
        "Benchy тризуб",
        "гачок",
    ]:
        service.create_item(conn, item(name, (ids["petg"], 12000)))

    found = service.list_items(conn, "тризуб")

    assert [i.name for i in found] == [
        "Benchy тризуб",
        "Брелок-Тризуб",
        "ґудзик тризуб",
        "Ялинка-тризуб",
    ]
    assert {i.min_donation_kop for i in found} == {11525}
    assert len(service.list_items(conn, None)) == 6
    assert len(service.list_items(conn, "  ")) == 6


def test_catalog_price_follows_the_current_plastic_price(
    conn: Connection, ids: dict[str, str]
) -> None:
    service.create_item(conn, item("Брелок-тризуб", (ids["petg"], 12000)))

    pricing.update_plastic(
        conn, ids["petg"], PlasticInput(name="PETG чорний", price_per_kg_kop=80000)
    )

    assert [i.min_donation_kop for i in service.list_items(conn, "тризуб")] == [13505]


def test_opened_item_shows_quote_from_current_settings(
    conn: Connection, ids: dict[str, str]
) -> None:
    saved = service.create_item(conn, item("Підставка", (ids["petg"], 12000)))

    detail = service.get_item(conn, saved.id)

    assert detail.quote.min_donation_kop == 11525
    assert detail.quote.breakdown.model_dump() == {
        "plastic_kop": 7800,
        "electricity_kop": 227,
        "wear_kop": 2450,
        "scrap_kop": 1048,
    }


def test_edited_item_has_new_parameters_and_price(conn: Connection, ids: dict[str, str]) -> None:
    saved = service.create_item(conn, item("Підставка", (ids["petg"], 12000)))

    updated = service.update_item(
        conn, saved.id, item("Підставка XL", (ids["pla"], 8000), print_time_s=7200)
    )

    assert updated.name == "Підставка XL"
    detail = service.get_item(conn, saved.id)
    assert [p.plastic_id for p in detail.plastics] == [ids["pla"]]
    assert detail.print_time_s == 7200
    assert detail.quote.min_donation_kop != 11525
    # The plastic dropped from the only item that used it can be deleted again.
    pricing.delete_plastic(
        conn, ids["petg"], lambda pid: service.item_names_using_plastic(conn, pid)
    )


def test_failed_edit_leaves_the_item_unchanged(conn: Connection, ids: dict[str, str]) -> None:
    saved = service.create_item(conn, item("Підставка", (ids["petg"], 12000)))
    service.create_item(conn, item("Органайзер", (ids["pla"], 100)))
    before = service.get_item(conn, saved.id)

    for bad in (
        item("органайзер", (ids["pla"], 100)),
        item("Підставка", (ids["pla"], 100), ("gone", 1)),
    ):
        with pytest.raises(AppError):
            service.update_item(conn, saved.id, bad)

    assert service.get_item(conn, saved.id) == before


def test_item_may_keep_its_own_name_on_edit(conn: Connection, ids: dict[str, str]) -> None:
    saved = service.create_item(conn, item("Підставка", (ids["petg"], 12000)))

    assert (
        service.update_item(conn, saved.id, item("ПІДСТАВКА", (ids["petg"], 1))).name == "ПІДСТАВКА"
    )


def test_deleted_item_is_gone_and_frees_its_plastics(conn: Connection, ids: dict[str, str]) -> None:
    saved = service.create_item(conn, item("Підставка", (ids["pla"], 100)))
    assert service.item_names_using_plastic(conn, ids["pla"]) == ["Підставка"]

    service.delete_item(conn, saved.id)

    assert service.list_items(conn, None) == []
    assert service.item_names_using_plastic(conn, ids["pla"]) == []


@pytest.mark.parametrize("action", ["get", "update", "delete"])
def test_unknown_item_is_not_found(conn: Connection, ids: dict[str, str], action: str) -> None:
    with pytest.raises(AppError) as exc:
        if action == "get":
            service.get_item(conn, "missing")
        elif action == "update":
            service.update_item(conn, "missing", item("X", (ids["petg"], 1)))
        else:
            service.delete_item(conn, "missing")

    assert (exc.value.code, exc.value.status) == ("catalog.item_not_found", 404)
