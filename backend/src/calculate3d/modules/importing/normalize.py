"""Exact numbers and filament keys from slicer text (SAD §8 «Джерело чисел», «Нормалізація»).

Each function returns `None` for a value the parser must reject as a corrupted file. Numbers are
plain decimals parsed through `Decimal`: no sign, exponent, NaN or infinity ever matches.
"""

import re
from decimal import ROUND_CEILING, Decimal

MAX_NAME_CODE_POINTS = 200
MAX_SAFE_INTEGER = 2**53 - 1  # usage_mg stays exact as a JS number (ADR 0004)
MG_PER_G = 1000
S_PER_MIN = 60

_COLOR = re.compile(r"#([0-9A-Fa-f]{6})([0-9A-Fa-f]{2})?")
_GRAMS = re.compile(r"[0-9]{1,16}(?:\.[0-9]{1,3})?")
_SECONDS = re.compile(r"[0-9]{1,12}(?:\.[0-9]{1,6})?")


def filament_color(raw: str) -> str | None:
    """`#RRGGBB` upper case; an 8-digit `#RRGGBBAA` loses its alpha (AC-09)."""
    match = _COLOR.fullmatch(raw)
    return f"#{match.group(1).upper()}" if match else None


def filament_name(raw: str) -> str | None:
    """Only trimmed — case kept, no NFC — so a mapping matches exactly (AC-09)."""
    name = raw.strip()
    if not 1 <= len(name) <= MAX_NAME_CODE_POINTS or not name.isprintable():
        return None
    return name


def usage_mg(raw: str) -> int | None:
    """Grams with at most 3 decimals → exact milligrams (11.54 → 11 540; ADR 0004)."""
    if not _GRAMS.fullmatch(raw):
        return None
    mg = int(Decimal(raw) * MG_PER_G)
    return mg if mg <= MAX_SAFE_INTEGER else None


def print_time_s(raw: str) -> int | None:
    """Seconds rounded up to a whole minute (5 828 → 5 880; 5 820 stays — AC-03)."""
    if not _SECONDS.fullmatch(raw):
        return None
    minutes = (Decimal(raw) / S_PER_MIN).to_integral_value(rounding=ROUND_CEILING)
    return int(minutes) * S_PER_MIN
