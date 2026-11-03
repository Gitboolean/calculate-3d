from typing import Any

import pytest
from pydantic import ValidationError

from calculate3d.core.errors import AppError
from calculate3d.modules.costing import service
from calculate3d.modules.costing.schemas import QuoteInput
from calculate3d.modules.pricing.schemas import Plastic, PriceSettings

AC04 = PriceSettings(
    tariff_per_kwh_kop=432,
    printer_power_w=150,
    printer_price_kop=3_000_000,
    printer_lifetime_h=5000,
    parts_per_hour_kop=100,
    scrap_rate_permille=100,
    wear_per_hour_kop=700,
)
PETG = Plastic(id="petg", name="PETG чорний", price_per_kg_kop=65000)
PLA = Plastic(id="pla", name="PLA білий", price_per_kg_kop=40000)
CONN: Any = object()


class FakePricing:
    def __init__(self, settings: PriceSettings | None, plastics: list[Plastic]) -> None:
        self.settings = settings
        self.plastics = plastics
        self.calls: list[str] = []

    def get_settings(self, conn: object) -> PriceSettings | None:
        self.calls.append("get_settings")
        return self.settings

    def plastics_exist(self, conn: object) -> bool:
        self.calls.append("plastics_exist")
        return bool(self.plastics)

    def list_plastics_by_ids(self, conn: object, ids: object) -> list[Plastic]:
        self.calls.append("list_plastics_by_ids")
        assert isinstance(ids, set | frozenset | list | tuple)
        return [p for p in self.plastics if p.id in ids]


@pytest.fixture
def pricing(monkeypatch: pytest.MonkeyPatch) -> FakePricing:
    fake = FakePricing(AC04, [PETG, PLA])
    for name in ("get_settings", "plastics_exist", "list_plastics_by_ids"):
        monkeypatch.setattr(service.pricing_service, name, getattr(fake, name))
    return fake


def quote_input(*usages: tuple[str, int], print_time_s: int) -> QuoteInput:
    return QuoteInput.model_validate(
        {
            "plastics": [{"plastic_id": pid, "usage_cg": cg} for pid, cg in usages],
            "print_time_s": print_time_s,
        }
    )


def test_quote_uses_current_prices_and_settings(pricing: FakePricing) -> None:
    quote = service.quote(CONN, quote_input(("petg", 12000), print_time_s=12600))

    assert quote.min_donation_kop == 11525
    assert quote.breakdown.model_dump() == {
        "plastic_kop": 7800,
        "electricity_kop": 227,
        "wear_kop": 2450,
        "scrap_kop": 1048,
    }


def test_quote_sums_every_plastic(pricing: FakePricing) -> None:
    quote = service.quote(CONN, quote_input(("pla", 8000), ("petg", 4000), print_time_s=7200))

    assert (quote.min_donation_kop, quote.breakdown.plastic_kop) == (8063, 5800)


@pytest.mark.parametrize(
    ("settings", "plastics", "missing"),
    [
        (None, [PETG], ["price_settings"]),
        (AC04, [], ["plastics"]),
        (None, [], ["plastics", "price_settings"]),
    ],
)
def test_missing_settings_or_plastics_is_a_409_naming_what_is_missing(
    pricing: FakePricing,
    settings: PriceSettings | None,
    plastics: list[Plastic],
    missing: list[str],
) -> None:
    pricing.settings, pricing.plastics = settings, plastics

    with pytest.raises(AppError) as exc:
        service.quote(CONN, quote_input(("petg", 12000), print_time_s=3600))

    assert (exc.value.code, exc.value.status, exc.value.missing) == (
        "costing.settings_missing",
        409,
        missing,
    )


def test_unknown_plastic_is_a_422_on_its_row(pricing: FakePricing) -> None:
    with pytest.raises(AppError) as exc:
        service.quote(CONN, quote_input(("petg", 100), ("gone", 100), print_time_s=60))

    assert (exc.value.code, exc.value.status, exc.value.field) == (
        "costing.plastic_not_found",
        422,
        "plastics.1.plastic_id",
    )


def test_quote_many_reads_pricing_a_fixed_number_of_times(pricing: FakePricing) -> None:
    inputs = [quote_input(("petg", 100 + i), print_time_s=60 * (i + 1)) for i in range(50)]

    quotes = service.quote_many(CONN, inputs)

    assert len(quotes) == 50
    assert quotes[0] == service.quote(CONN, inputs[0])
    assert pricing.calls[:3] == ["get_settings", "plastics_exist", "list_plastics_by_ids"]
    assert len(pricing.calls) == 6  # 3 for the batch of 50, 3 for the single quote


def test_quote_many_of_nothing_touches_nothing(pricing: FakePricing) -> None:
    pricing.settings = None

    assert service.quote_many(CONN, []) == []
    assert pricing.calls == []


@pytest.mark.parametrize(
    "payload",
    [
        {"plastics": [], "print_time_s": 3600},
        {"plastics": [{"plastic_id": "a", "usage_cg": 0}], "print_time_s": 3600},
        {"plastics": [{"plastic_id": "a", "usage_cg": -5}], "print_time_s": 3600},
        {"plastics": [{"plastic_id": "a", "usage_cg": 12.5}], "print_time_s": 3600},
        {"plastics": [{"plastic_id": "a", "usage_cg": 1}], "print_time_s": 0},
        {"plastics": [{"plastic_id": "a", "usage_cg": 1}], "print_time_s": 90},
        {
            "plastics": [{"plastic_id": "a", "usage_cg": 1}, {"plastic_id": "a", "usage_cg": 2}],
            "print_time_s": 60,
        },
    ],
)
def test_invalid_quote_input_is_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        QuoteInput.model_validate(payload)
