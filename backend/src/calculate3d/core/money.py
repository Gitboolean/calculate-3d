"""Exact money arithmetic (project ADR 0003): kopecks as `int`, never `float`.

Intermediate amounts are exact rationals (`Fraction`): wear per hour (price ÷ lifetime) and
hourly rates for minutes of printing are repeating fractions that no fixed-precision `Decimal`
holds exactly. Rounding to whole kopecks goes through `Decimal` with a directed context, so the
division can only err in the safe direction and the final rounding mode is the named one.
"""

from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction

# Enough digits that every kopeck amount's integer part is exact.
_PRECISION = 50


def _to_decimal(amount: Fraction, rounding: str) -> Decimal:
    with localcontext(prec=_PRECISION, rounding=rounding):
        return Decimal(amount.numerator) / Decimal(amount.denominator)


def ceil_kop(amount: Fraction) -> int:
    """Round up to a whole kopeck — the minimum donation is never below the exact cost (AC-08)."""
    # Rounding the division up first never crosses past the exact ceiling.
    return int(_to_decimal(amount, ROUND_CEILING).to_integral_value(ROUND_CEILING))


def round_half_up_kop(amount: Fraction) -> int:
    """Round to the nearest kopeck, half a kopeck up — breakdown rows and display values."""
    # Truncating the division first keeps «just below ½» from turning into ½.
    return int(_to_decimal(amount, ROUND_FLOOR).to_integral_value(ROUND_HALF_UP))


def wear_per_hour_kop(
    printer_price_kop: int, printer_lifetime_h: int, parts_per_hour_kop: int
) -> Fraction:
    """Exact printer wear per print hour = price ÷ lifetime + parts (AC-04)."""
    return Fraction(printer_price_kop, printer_lifetime_h) + parts_per_hour_kop
