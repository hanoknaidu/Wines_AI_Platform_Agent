#!/usr/bin/env python3
"""Load the fictional seed (from _DB/ecommerce.db) into the API database.

Usage:
  python scripts/load_seed.py                       # DATABASE_URL from env/.env; schema from Alembic
  python scripts/load_seed.py --recreate            # drop + create tables from the ORM first (dev only)
  python scripts/load_seed.py --if-empty            # idempotent (used by docker compose)
  python scripts/load_seed.py --database-url sqlite+aiosqlite:///./local.db --recreate

Production databases are migrated with `alembic upgrade head`, never --recreate.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.seed import load_seed  # noqa: E402
from app.db.session import create_engine  # noqa: E402


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--database-url", help="override DATABASE_URL")
    ap.add_argument("--source", type=Path, default=ROOT / "_DB" / "ecommerce.db")
    ap.add_argument("--recreate", action="store_true", help="drop_all + create_all before loading")
    ap.add_argument("--if-empty", action="store_true", help="skip when the database already has data")
    args = ap.parse_args()

    settings = get_settings()
    if settings.is_production and args.recreate:
        print("refusing --recreate in production", file=sys.stderr)
        return 2
    engine = create_engine(settings, args.database_url)
    if args.if_empty and not args.recreate:
        async with engine.connect() as conn:
            if (await conn.execute(text("SELECT COUNT(*) FROM stores"))).scalar_one():
                print("database already seeded; skipping")
                await engine.dispose()
                return 0
    try:
        counts = await load_seed(engine, args.source, recreate=args.recreate)
    finally:
        await engine.dispose()
    print(f"loaded {sum(counts.values())} rows into {len(counts)} tables")
    for name, n in counts.items():
        print(f"  {name:32s} {n:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
