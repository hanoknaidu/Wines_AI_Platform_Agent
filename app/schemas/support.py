from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.core.money import MoneyOpt
from app.models.support import TICKET_CATEGORIES, TICKET_REASON_CODES
from app.schemas.common import ApiModel, UtcDateTime

TicketCategory = Literal[TICKET_CATEGORIES]  # type: ignore[valid-type]
TicketReason = Literal[TICKET_REASON_CODES]  # type: ignore[valid-type]


class TicketCreate(ApiModel):
    customer_id: str | None = Field(None, pattern=r"^C-\d{6}$")
    order_id: str | None = Field(None, pattern=r"^WA-\d{6}$")
    rma_number: str | None = Field(None, pattern=r"^RMA-\d{6}$")
    category: TicketCategory
    priority: Literal["P1", "P2", "P3"] = "P3"
    reason_code: TicketReason | None = None
    subject: str = Field(..., min_length=3, max_length=200)
    summary: str = Field(..., min_length=10, max_length=4000)
    customer_sentiment: Literal["positive", "neutral", "frustrated", "angry"] | None = None
    conversation_id: str | None = Field(None, max_length=100)

    @model_validator(mode="after")
    def _p1_needs_reason(self):
        if self.priority == "P1" and not self.reason_code:
            raise ValueError("P1 tickets require a reason_code from the escalation matrix")
        return self


class TicketMessageOut(ApiModel):
    author_type: str
    body: str
    created_at: UtcDateTime


class TicketSummary(ApiModel):
    ticket_number: str
    category: str
    priority: str
    status: str
    subject: str
    order_id: str | None
    sla_due_at: UtcDateTime
    created_at: UtcDateTime


class TicketDetail(TicketSummary):
    reason_code: str | None
    assigned_team: str | None
    summary: str
    rma_number: str | None
    resolved_at: UtcDateTime | None
    messages: list[TicketMessageOut]


class StoreHoursOut(ApiModel):
    day: str
    opens_at: str
    closes_at: str


class StoreExceptionOut(ApiModel):
    date: str
    is_closed: bool
    opens_at: str | None
    closes_at: str | None
    note: str | None


class StoreInfo(ApiModel):
    store_code: str
    name: str
    state_code: str
    address: str
    phone: str
    timezone: str
    hours: list[StoreHoursOut]
    upcoming_exceptions: list[StoreExceptionOut]


class FulfillmentOption(ApiModel):
    type: Literal["pickup", "local_delivery", "shipping"]
    eligible: bool
    fee: MoneyOpt
    order_minimum: MoneyOpt
    free_threshold: MoneyOpt
    free_delivery_gap: MoneyOpt
    zone: int | None = None
    estimate: str
    notes: list[str]


class DeliveryEstimate(ApiModel):
    postal_code: str
    state_code: str | None
    serviceable: bool
    fulfilling_store: str | None
    options: list[FulfillmentOption]
    reason: str | None
    policy_refs: list[str]
