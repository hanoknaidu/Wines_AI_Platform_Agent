"""Declarative base and portable column types.

PostgreSQL is the production engine. The same models also run on SQLite
(aiosqlite) so unit/API tests need no infrastructure; the type decorators
below make both engines behave the same:

* UTCDateTime  -> TIMESTAMPTZ on PG; always returns tz-aware UTC datetimes
* JSONType     -> JSONB on PG, JSON on SQLite
* BigId        -> BIGINT on PG, INTEGER on SQLite (rowid alias)
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, Integer, MetaData, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

BigId = BigInteger().with_variant(Integer(), "sqlite")
JSONType = JSON().with_variant(JSONB(), "postgresql")


class UTCDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        value = value.astimezone(UTC)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

    def process_result_value(self, value: Any, dialect) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, str):  # defensive: raw SQLite text
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def in_(column: str, values: tuple[str, ...] | list[str]) -> str:
    """SQL text for an enum-style CHECK constraint: col IN ('a','b')."""
    quoted = ",".join("'" + v.replace("'", "''") + "'" for v in values)
    return f"{column} IN ({quoted})"
