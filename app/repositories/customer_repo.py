from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import (
    AgeVerification,
    Customer,
    CustomerAddress,
    CustomerPaymentMethod,
    LoyaltyAccount,
    LoyaltyPointTransaction,
    LoyaltyReward,
    Order,
    StoreCreditTransaction,
    SupportTicket,
)
from app.repositories.base import Repository

CLOSED_ORDER_STATUSES = ("completed", "cancelled", "delivered", "picked_up", "returned_to_sender")


class CustomerRepository(Repository):
    async def get_by_number(self, customer_number: str) -> Customer | None:
        stmt = (
            select(Customer)
            .where(Customer.customer_number == customer_number)
            .options(selectinload(Customer.home_store))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def age_verification_status(self, customer_id: int) -> str:
        stmt = (
            select(AgeVerification.status)
            .where(AgeVerification.customer_id == customer_id)
            .order_by(AgeVerification.started_at.desc(), AgeVerification.age_verification_id.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() or "not_started"

    async def list_addresses(self, customer_id: int) -> list[CustomerAddress]:
        stmt = (
            select(CustomerAddress)
            .where(CustomerAddress.customer_id == customer_id, CustomerAddress.deleted_at.is_(None))
            .order_by(CustomerAddress.is_default_shipping.desc(), CustomerAddress.address_id)
        )
        return list((await self.session.execute(stmt)).scalars())

    async def list_payment_methods(self, customer_id: int) -> list[CustomerPaymentMethod]:
        stmt = (
            select(CustomerPaymentMethod)
            .where(CustomerPaymentMethod.customer_id == customer_id, CustomerPaymentMethod.status != "removed")
            .order_by(CustomerPaymentMethod.is_default.desc(), CustomerPaymentMethod.payment_method_id)
        )
        return list((await self.session.execute(stmt)).scalars())

    async def loyalty_account(self, customer_id: int) -> LoyaltyAccount | None:
        return await self.session.get(LoyaltyAccount, customer_id)

    async def loyalty_points(self, customer_id: int) -> int:
        stmt = select(func.coalesce(func.sum(LoyaltyPointTransaction.points), 0)).where(
            LoyaltyPointTransaction.customer_id == customer_id
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def available_rewards(self, customer_id: int, now: datetime) -> list[LoyaltyReward]:
        stmt = (
            select(LoyaltyReward)
            .where(
                LoyaltyReward.customer_id == customer_id,
                LoyaltyReward.status == "available",
                LoyaltyReward.expires_at > now,
            )
            .order_by(LoyaltyReward.expires_at)
        )
        return list((await self.session.execute(stmt)).scalars())

    async def store_credit_balance(self, customer_id: int) -> int:
        stmt = select(func.coalesce(func.sum(StoreCreditTransaction.amount_cents), 0)).where(
            StoreCreditTransaction.customer_id == customer_id
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_open_orders(self, customer_id: int) -> int:
        stmt = select(func.count()).where(
            Order.customer_id == customer_id, Order.status.not_in(CLOSED_ORDER_STATUSES)
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_open_tickets(self, customer_id: int) -> int:
        stmt = select(func.count()).where(
            SupportTicket.customer_id == customer_id, SupportTicket.status.not_in(("resolved", "closed"))
        )
        return int((await self.session.execute(stmt)).scalar_one())
