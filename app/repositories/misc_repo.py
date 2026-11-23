"""Smaller repositories: stores, support tickets, returns, audit, idempotency."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.models import (
    AuditLog,
    FulfillmentRate,
    IdempotencyRecord,
    Order,
    ReturnRequest,
    Store,
    StoreHoursException,
    SupportTicket,
)
from app.repositories.base import Repository


class StoreRepository(Repository):
    async def list(self) -> list[Store]:
        stmt = select(Store).where(Store.is_active.is_(True)).options(
            selectinload(Store.hours), selectinload(Store.exceptions)
        )
        return list((await self.session.execute(stmt.order_by(Store.store_code))).scalars())

    async def get_by_code(self, code: str) -> Store | None:
        stmt = select(Store).where(Store.store_code == code).options(
            selectinload(Store.hours), selectinload(Store.exceptions)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_state(self, state_code: str) -> Store | None:
        stmt = select(Store).where(Store.state_code == state_code, Store.is_active.is_(True)).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def fulfillment_rates(self, store_id: int, on: date) -> list[FulfillmentRate]:
        stmt = select(FulfillmentRate).where(
            FulfillmentRate.store_id == store_id,
            FulfillmentRate.effective_from <= on,
            (FulfillmentRate.effective_to.is_(None)) | (FulfillmentRate.effective_to > on),
        )
        return list((await self.session.execute(stmt.order_by(FulfillmentRate.rate_id))).scalars())

    async def exceptions_between(self, store_id: int, start: date, end: date) -> list[StoreHoursException]:
        stmt = select(StoreHoursException).where(
            StoreHoursException.store_id == store_id,
            StoreHoursException.exception_date >= start,
            StoreHoursException.exception_date <= end,
        )
        return list((await self.session.execute(stmt.order_by(StoreHoursException.exception_date))).scalars())


class SupportRepository(Repository):
    async def get_by_number(self, ticket_number: str) -> SupportTicket | None:
        stmt = (
            select(SupportTicket)
            .where(SupportTicket.ticket_number == ticket_number)
            .options(selectinload(SupportTicket.messages))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_customer(self, customer_id: int, offset: int, limit: int) -> tuple[list[SupportTicket], int]:
        cond = SupportTicket.customer_id == customer_id
        total = (await self.session.execute(select(func.count()).where(cond))).scalar_one()
        stmt = (
            select(SupportTicket)
            .where(cond)
            .order_by(SupportTicket.created_at.desc(), SupportTicket.ticket_id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars()), int(total)

    async def order_numbers(self, order_ids: set[int]) -> dict[int, str]:
        if not order_ids:
            return {}
        stmt = select(Order.order_id, Order.order_number).where(Order.order_id.in_(order_ids))
        rows = await self.session.execute(stmt)
        return dict(rows.all())


class ReturnRepository(Repository):
    async def get_by_rma(self, rma_number: str) -> ReturnRequest | None:
        stmt = (
            select(ReturnRequest)
            .where(ReturnRequest.rma_number == rma_number)
            .options(selectinload(ReturnRequest.items), selectinload(ReturnRequest.evidence))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()


class AuditRepository(Repository):
    def append(self, entry: AuditLog) -> None:
        # Added to the caller's transaction: the audit row commits (or rolls
        # back) atomically with the change it describes.
        self.session.add(entry)


class IdempotencyRepository(Repository):
    async def get(self, principal_ref: str, key: str) -> IdempotencyRecord | None:
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.principal_ref == principal_ref, IdempotencyRecord.idempotency_key == key
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def purge_expired(self, now: datetime) -> int:
        result = await self.session.execute(delete(IdempotencyRecord).where(IdempotencyRecord.expires_at < now))
        return result.rowcount or 0
