from __future__ import annotations

from app.core.masking import mask_email, mask_phone, mask_street
from app.repositories.customer_repo import CustomerRepository
from app.schemas.customer import (
    AccountSummary,
    Address,
    CustomerProfile,
    LoyaltyReward,
    LoyaltySummary,
    SavedPaymentMethod,
    StoreRef,
)
from app.services.context import ServiceContext


class CustomerService:
    def __init__(self, ctx: ServiceContext) -> None:
        self.ctx = ctx
        self.repo = CustomerRepository(ctx.session)

    async def profile(self, customer_number: str) -> CustomerProfile:
        c = await self.ctx.owned_customer(customer_number)
        store = c.home_store
        return CustomerProfile(
            customer_id=c.customer_number,
            first_name=c.first_name,
            last_name=c.last_name,
            email_masked=mask_email(c.email) or "",
            phone_masked=mask_phone(c.phone_e164),
            status=c.status,  # status_reason is internal (e.g., fraud notes) and never returned
            home_store=StoreRef(store_code=store.store_code, name=store.name, state_code=store.state_code)
            if store else None,
            member_since=c.created_at.date(),
            age_verification_status=await self.repo.age_verification_status(c.customer_id),
        )

    async def addresses(self, customer_number: str) -> list[Address]:
        c = await self.ctx.owned_customer(customer_number)
        agent_view = self.ctx.principal.role == "agent"
        return [
            Address(
                address_id=a.address_id,
                label=a.label,
                recipient_name=a.recipient_name,
                line1=mask_street(a.line1) if agent_view else a.line1,
                line2=None if agent_view else a.line2,
                city=a.city,
                state_code=a.state_code,
                postal_code=a.postal_code,
                address_type=a.address_type,
                is_default_shipping=a.is_default_shipping,
                is_default_billing=a.is_default_billing,
                restricted_destination=a.is_restricted_destination,
                deliverable_state=a.state_code in ("NJ", "NY"),
            )
            for a in await self.repo.list_addresses(c.customer_id)
        ]

    async def account(self, customer_number: str) -> AccountSummary:
        c = await self.ctx.owned_customer(customer_number)
        loyalty = await self.repo.loyalty_account(c.customer_id)
        rewards = await self.repo.available_rewards(c.customer_id, self.ctx.now) if loyalty else []
        return AccountSummary(
            customer_id=c.customer_number,
            status=c.status,
            age_verification_status=await self.repo.age_verification_status(c.customer_id),
            loyalty=LoyaltySummary(
                enrolled=loyalty is not None,
                tier=loyalty.tier if loyalty else None,
                points=await self.repo.loyalty_points(c.customer_id) if loyalty else 0,
                available_rewards=[LoyaltyReward(value=r.value_cents, expires_at=r.expires_at) for r in rewards],
            ),
            store_credit_balance=await self.repo.store_credit_balance(c.customer_id),
            payment_methods=[
                SavedPaymentMethod(
                    method_type=pm.method_type, card_brand=pm.card_brand, card_last4=pm.card_last4,
                    exp_month=pm.exp_month, exp_year=pm.exp_year, is_default=pm.is_default, status=pm.status,
                )
                for pm in await self.repo.list_payment_methods(c.customer_id)
            ],
            open_orders=await self.repo.count_open_orders(c.customer_id),
            open_tickets=await self.repo.count_open_tickets(c.customer_id),
        )
