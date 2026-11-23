from __future__ import annotations

from datetime import date

from app.core.money import Money
from app.schemas.common import ApiModel, UtcDateTime


class StoreRef(ApiModel):
    store_code: str
    name: str
    state_code: str


class CustomerProfile(ApiModel):
    customer_id: str
    first_name: str
    last_name: str
    email_masked: str
    phone_masked: str | None
    status: str
    home_store: StoreRef | None
    member_since: date
    age_verification_status: str  # not_started | pending | verified | failed | manual_review


class Address(ApiModel):
    address_id: int
    label: str | None
    recipient_name: str
    line1: str
    line2: str | None
    city: str
    state_code: str
    postal_code: str
    address_type: str
    is_default_shipping: bool
    is_default_billing: bool
    restricted_destination: bool  # PO box / school / dorm: never shipped to (A-20)
    deliverable_state: bool  # NJ/NY only (A-02)


class SavedPaymentMethod(ApiModel):
    method_type: str
    card_brand: str
    card_last4: str
    exp_month: int
    exp_year: int
    is_default: bool
    status: str


class LoyaltyReward(ApiModel):
    value: Money
    expires_at: UtcDateTime


class LoyaltySummary(ApiModel):
    enrolled: bool
    tier: str | None
    points: int
    available_rewards: list[LoyaltyReward]


class AccountSummary(ApiModel):
    customer_id: str
    status: str
    age_verification_status: str
    loyalty: LoyaltySummary
    store_credit_balance: Money
    payment_methods: list[SavedPaymentMethod]
    open_orders: int
    open_tickets: int
