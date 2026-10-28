import math
import random
from dataclasses import replace
from fractions import Fraction

import pytest

from calculate3d.core.money import round_half_up_kop, wear_per_hour_kop
from calculate3d.modules.costing.domain import (
    Breakdown,
    CostSettings,
    PlasticUsage,
    Quote,
    compute_quote,
)

# AC-04: 4,32 ₴/кВт·год, 150 Вт, 30 000 ₴, 5 000 год, 1,00 ₴/год, брак 10 %.
AC04 = CostSettings(
    tariff_per_kwh_kop=432,
    printer_power_w=150,
    printer_price_kop=3_000_000,
    printer_lifetime_h=5000,
    parts_per_hour_kop=100,
    scrap_rate_permille=100,
)
BARE = CostSettings(
    tariff_per_kwh_kop=0,
    printer_power_w=0,
    printer_price_kop=0,
    printer_lifetime_h=1,
    parts_per_hour_kop=0,
    scrap_rate_permille=0,
)
PETG_120G = [PlasticUsage(price_per_kg_kop=65_000, usage_cg=12_000)]
ONE_KOP_OF_PLASTIC = [PlasticUsage(price_per_kg_kop=1000, usage_cg=100)]

REFERENCE = [
    pytest.param(
        PETG_120G, 12_600, AC04, Quote(11_525, Breakdown(7800, 227, 2450, 1048)), id="AC-06"
    ),
    pytest.param(
        [PlasticUsage(40_000, 8000), PlasticUsage(65_000, 4000)],
        7200,
        AC04,
        Quote(8063, Breakdown(5800, 130, 1400, 733)),
        id="AC-06b",
    ),
    pytest.param(
        [PlasticUsage(65_000, 10_000)],
        10_800,
        AC04,
        Quote(9674, Breakdown(6500, 194, 2100, 879)),
        id="AC-08b",
    ),
    pytest.param(
        [PlasticUsage(80_000, 12_000)],
        12_600,
        AC04,
        Quote(13_505, Breakdown(9600, 227, 2450, 1228)),
        id="AC-13",
    ),
    pytest.param(
        PETG_120G,
        12_600,
        replace(AC04, tariff_per_kwh_kop=0),
        Quote(11_275, Breakdown(7800, 0, 2450, 1025)),
        id="zero-tariff",
    ),
    pytest.param(
        PETG_120G,
        12_600,
        replace(AC04, scrap_rate_permille=0),
        Quote(10_477, Breakdown(7800, 227, 2450, 0)),
        id="scrap-0%",
    ),
    pytest.param(
        PETG_120G,
        12_600,
        replace(AC04, scrap_rate_permille=1000),
        Quote(20_954, Breakdown(7800, 227, 2450, 10_477)),
        id="scrap-100%",
    ),
    pytest.param(
        ONE_KOP_OF_PLASTIC,
        3600,
        replace(BARE, tariff_per_kwh_kop=1, printer_power_w=500),
        Quote(2, Breakdown(1, 1, 0, 0)),
        id="row-half-kop-rounds-up",
    ),
    pytest.param(
        [PlasticUsage(65_000, 1234)],
        60,
        AC04,
        Quote(897, Breakdown(802, 1, 12, 81)),
        id="12.34g-one-minute",
    ),
    pytest.param(
        ONE_KOP_OF_PLASTIC,
        10_800,
        replace(BARE, printer_price_kop=100, printer_lifetime_h=3),
        Quote(101, Breakdown(1, 0, 100, 0)),
        id="repeating-wear-sums-to-whole-kop",
    ),
]


@pytest.mark.parametrize(("usages", "print_time_s", "settings", "expected"), REFERENCE)
def test_quote_matches_reference_table_to_the_kopeck(
    usages: list[PlasticUsage], print_time_s: int, settings: CostSettings, expected: Quote
) -> None:
    assert compute_quote(usages, print_time_s, settings) == expected


@pytest.mark.parametrize(
    ("price_kop", "lifetime_h", "parts_kop", "expected_kop"),
    [(3_000_000, 5000, 100, 700), (1000, 3, 0, 333), (1, 2, 0, 1), (0, 1, 0, 0)],
)
def test_wear_per_hour_is_exact_and_rounds_half_up_for_display(
    price_kop: int, lifetime_h: int, parts_kop: int, expected_kop: int
) -> None:
    exact = wear_per_hour_kop(price_kop, lifetime_h, parts_kop)

    assert exact == Fraction(price_kop, lifetime_h) + parts_kop
    assert round_half_up_kop(exact) == expected_kop


def _exact_total(usages: list[PlasticUsage], print_time_s: int, s: CostSettings) -> Fraction:
    hours = Fraction(print_time_s, 3600)
    plastic = sum((Fraction(u.price_per_kg_kop * u.usage_cg, 100_000) for u in usages), Fraction())
    electricity = Fraction(s.tariff_per_kwh_kop * s.printer_power_w, 1000) * hours
    wear = (Fraction(s.printer_price_kop, s.printer_lifetime_h) + s.parts_per_hour_kop) * hours
    base = plastic + electricity + wear
    return base + base * Fraction(s.scrap_rate_permille, 1000)


def test_min_donation_is_the_ceiling_of_the_exact_cost_for_random_inputs() -> None:
    rng = random.Random(20261028)
    for _ in range(1000):
        usages = [
            PlasticUsage(rng.randint(1, 500_000), rng.randint(1, 200_000))
            for _ in range(rng.randint(1, 4))
        ]
        print_time_s = 60 * rng.randint(1, 6000)
        settings = CostSettings(
            tariff_per_kwh_kop=rng.randint(0, 2000),
            printer_power_w=rng.randint(0, 1500),
            printer_price_kop=rng.randint(0, 20_000_000),
            printer_lifetime_h=rng.randint(1, 20_000),
            parts_per_hour_kop=rng.randint(0, 1000),
            scrap_rate_permille=rng.randint(0, 1000),
        )
        exact = _exact_total(usages, print_time_s, settings)

        donation = compute_quote(usages, print_time_s, settings).min_donation_kop

        assert donation == math.ceil(exact)
        assert exact <= donation < exact + 1
