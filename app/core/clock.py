"""Injectable clock. Business windows (48 h damage claims, 14-day returns...) are
time-dependent, so tests and demos freeze "now" via REFERENCE_NOW."""
from __future__ import annotations

from datetime import UTC, datetime


class Clock:
    def __init__(self, frozen: datetime | None = None) -> None:
        if frozen is not None and frozen.tzinfo is None:
            frozen = frozen.replace(tzinfo=UTC)
        self._frozen = frozen

    def now(self) -> datetime:
        return self._frozen or datetime.now(UTC)

    @property
    def is_frozen(self) -> bool:
        return self._frozen is not None


def to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def iso(value: datetime | None) -> str | None:
    value = to_utc(value)
    return value.strftime("%Y-%m-%dT%H:%M:%SZ") if value else None
