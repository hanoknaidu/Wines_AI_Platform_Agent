"""Money crosses the API boundary as a decimal string ("52.18"); the database
stores integer cents (KB tool contract §1). Never use floats for money."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import PlainSerializer


def cents_to_str(cents: int | None) -> str | None:
    if cents is None:
        return None
    sign = "-" if cents < 0 else ""
    cents = abs(int(cents))
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def str_to_cents(value: str | Decimal) -> int:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(amount * 100)


def pct_of(cents: int, bps: int) -> int:
    """Basis-point share of an amount, rounded half-up (1000 bps = 10%)."""
    return (cents * bps + 5000) // 10000


def prorate(total: int, part: int, whole: int) -> int:
    """total * part / whole, rounded half-up, in integers."""
    if whole <= 0:
        return 0
    return (total * part * 2 + whole) // (2 * whole)


# Pydantic field type: an int of cents in Python, a "12.34" string in JSON.
Money = Annotated[int, PlainSerializer(cents_to_str, return_type=str, when_used="always")]
MoneyOpt = Annotated[int | None, PlainSerializer(cents_to_str, return_type=str | None, when_used="always")]
