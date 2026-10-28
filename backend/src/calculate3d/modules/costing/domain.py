"""The cost formula — pure, no I/O (cost-calculator ADR 0002). One place for quote and catalog.

The minimum donation is the ceiling of the exact sum; each breakdown row is rounded half up on
its own, so the rows may differ from the donation by a few kopecks (AC-08).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

from calculate3d.core.money import ceil_kop, round_half_up_kop, wear_per_hour_kop

SECONDS_PER_HOUR = 3600
CG_PER_KG = 100_000
W_PER_KW = 1000
PERMILLE = 1000


@dataclass(frozen=True)
class PlasticUsage:
    price_per_kg_kop: int
    usage_cg: int


@dataclass(frozen=True)
class CostSettings:
    tariff_per_kwh_kop: int
    printer_power_w: int
    printer_price_kop: int
    printer_lifetime_h: int
    parts_per_hour_kop: int
    scrap_rate_permille: int


@dataclass(frozen=True)
class Breakdown:
    plastic_kop: int
    electricity_kop: int
    wear_kop: int
    scrap_kop: int


@dataclass(frozen=True)
class Quote:
    min_donation_kop: int
    breakdown: Breakdown


def compute_quote(
    usages: Sequence[PlasticUsage], print_time_s: int, settings: CostSettings
) -> Quote:
    hours = Fraction(print_time_s, SECONDS_PER_HOUR)
    plastic = sum(
        (Fraction(u.price_per_kg_kop * u.usage_cg, CG_PER_KG) for u in usages), Fraction()
    )
    electricity = Fraction(settings.tariff_per_kwh_kop * settings.printer_power_w, W_PER_KW) * hours
    wear = (
        wear_per_hour_kop(
            settings.printer_price_kop, settings.printer_lifetime_h, settings.parts_per_hour_kop
        )
        * hours
    )
    # Scrap is a share of everything printed, failed prints included.
    scrap = (plastic + electricity + wear) * Fraction(settings.scrap_rate_permille, PERMILLE)
    return Quote(
        min_donation_kop=ceil_kop(plastic + electricity + wear + scrap),
        breakdown=Breakdown(
            plastic_kop=round_half_up_kop(plastic),
            electricity_kop=round_half_up_kop(electricity),
            wear_kop=round_half_up_kop(wear),
            scrap_kop=round_half_up_kop(scrap),
        ),
    )
