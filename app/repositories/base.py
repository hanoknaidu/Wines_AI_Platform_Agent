from __future__ import annotations

import uuid
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

M = TypeVar("M")


class Repository:
    """Repositories hold every SQL query. They never commit: the service that
    owns the unit of work decides when a transaction ends."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @property
    def dialect(self) -> str:
        return self.session.bind.dialect.name if self.session.bind else "unknown"

    async def add(self, obj: M) -> M:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def add_with_public_number(self, obj: M, attr: str, prefix: str, base: int, pk_attr: str) -> M:
        """Insert, then derive the public number (RF-400008) from the DB-assigned
        surrogate key: race-free under concurrency, no MAX()+1 queries. Public
        numbers are sequential, so ownership checks (404 for non-owners) are what
        stop enumeration."""
        setattr(obj, attr, f"~{uuid.uuid4().hex[:18]}")  # fits the narrowest number column (20)
        await self.add(obj)
        setattr(obj, attr, f"{prefix}-{base + getattr(obj, pk_attr)}")
        await self.session.flush()
        return obj
