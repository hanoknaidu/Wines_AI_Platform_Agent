"""Copy the fictional seed data from the SQLite reference build (_DB/ecommerce.db,
produced by scripts/initialize_db.py) into the API database (PostgreSQL in
production-like environments, SQLite in tests).

The SQLite build stays the single source of truth for seed scenarios; this
loader converts types column by column using the ORM metadata:
ISO text -> TIMESTAMPTZ/DATE, 0/1 -> BOOLEAN, REAL -> NUMERIC, JSON text -> JSONB.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import Boolean, Date, Numeric, text
from sqlalchemy.ext.asyncio import AsyncEngine

import app.models  # noqa: F401  (registers tables)
from app.db.base import JSON, Base, UTCDateTime

# Tables owned by the API/agent layer: nothing to copy from the reference DB.
API_OWNED_TABLES = {
    "agent_sessions", "agent_messages", "agent_runs", "agent_run_events", "agent_tool_calls", "idempotency_records",
}


def _converter(column):
    t = column.type
    if isinstance(t, UTCDateTime):
        return lambda v: None if v is None else datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    if isinstance(t, Date):
        return lambda v: None if v is None else date.fromisoformat(str(v)[:10])
    if isinstance(t, Boolean):
        return lambda v: None if v is None else bool(v)
    if isinstance(t, Numeric):
        return lambda v: None if v is None else Decimal(str(v))
    if isinstance(t, JSON) or "JSON" in type(t).__name__.upper():
        return lambda v: json.loads(v) if isinstance(v, str) else v
    return lambda v: v


def read_reference_rows(sqlite_path: Path) -> dict[str, list[dict]]:
    if not sqlite_path.exists():
        raise FileNotFoundError(f"{sqlite_path} not found: run `python scripts/initialize_db.py --force` first")
    src = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    try:
        existing = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        data: dict[str, list[dict]] = {}
        for table in Base.metadata.sorted_tables:
            if table.name in API_OWNED_TABLES or table.name not in existing:
                continue
            src_cols = {r[1] for r in src.execute(f'PRAGMA table_info("{table.name}")')}
            cols = [c for c in table.columns if c.name in src_cols]
            convs = {c.name: _converter(c) for c in cols}
            pk = ", ".join(c.name for c in table.primary_key.columns)
            rows = src.execute(f'SELECT {", ".join(c.name for c in cols)} FROM "{table.name}" ORDER BY {pk}')
            data[table.name] = [{k: convs[k](row[k]) for k in convs} for row in rows]
        return data
    finally:
        src.close()


async def load_seed(engine: AsyncEngine, sqlite_path: Path, *, recreate: bool = False) -> dict[str, int]:
    data = read_reference_rows(sqlite_path)
    counts: dict[str, int] = {}
    async with engine.begin() as conn:
        if recreate:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        for table in Base.metadata.sorted_tables:
            rows = data.get(table.name)
            if not rows:
                continue
            for i in range(0, len(rows), 500):
                await conn.execute(table.insert(), rows[i : i + 500])
            counts[table.name] = len(rows)
        if conn.dialect.name == "postgresql":
            await _reset_pg_sequences(conn)
    return counts


async def _reset_pg_sequences(conn) -> None:
    """Explicit IDs were inserted; move each identity/serial sequence past them."""
    for table in Base.metadata.sorted_tables:
        pk_cols = list(table.primary_key.columns)
        if len(pk_cols) != 1 or not pk_cols[0].autoincrement:
            continue
        col = pk_cols[0].name
        seq = (await conn.execute(text("SELECT pg_get_serial_sequence(:t, :c)"), {"t": table.name, "c": col})).scalar()
        if seq:
            await conn.execute(
                text(f'SELECT setval(:s, COALESCE((SELECT MAX({col}) FROM "{table.name}"), 0) + 1, false)'),
                {"s": seq},
            )
