from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.core.money import Money, MoneyOpt
from app.schemas.common import ApiModel, PolicyReason, UtcDateTime

ClaimReason = Literal[
    "damaged_in_transit", "broken_on_arrival", "corked_or_flawed", "leaking",
    "wrong_item", "missing_item", "change_of_mind", "late_delivery",
]


class EligibleItem(ApiModel):
    line_number: int
    sku: str
    product_name: str
    refundable_quantity: int
    refundable_amount: Money


class ReasonOption(ApiModel):
    reason_code: str
    eligible: bool
    window_ends_at: UtcDateTime | None
    note: str


class EligibilityResult(ApiModel):
    order_id: str
    eligible: bool
    decision: Literal["eligible", "ineligible", "requires_review", "cancel_instead"]
    reason_code: str | None
    reasons: list[PolicyReason]
    window_ends_at: UtcDateTime | None
    max_refundable_amount: Money
    restocking_fee_bps: int = 0
    eligible_items: list[EligibleItem]
    agent_can_issue: bool
    requires_human_approval: bool
    approval_reasons: list[str]
    reason_options: list[ReasonOption]
    next_steps: list[str]
    policy_refs: list[str]


class RefundLineOut(ApiModel):
    line_number: int
    sku: str
    quantity: int
    amount: Money


class RefundOut(ApiModel):
    refund_id: str
    order_id: str
    rma_number: str | None
    reason_code: str
    method: str
    status: str
    customer_facing_reason: str
    items_amount: Money
    tax_amount: Money
    shipping_amount: Money
    tip_amount: Money
    restocking_fee: Money
    amount: Money
    requires_human_approval: bool
    created_at: UtcDateTime
    completed_at: UtcDateTime | None
    expected_posting: str | None
    lines: list[RefundLineOut]


class LineSelection(ApiModel):
    line_number: int = Field(..., ge=1, le=999)
    quantity: int = Field(..., ge=1, le=999)


class RefundRequest(ApiModel):
    reason_code: ClaimReason
    method: Literal["original_payment", "store_credit"] = "original_payment"
    items: list[LineSelection] | None = Field(
        None, max_length=50, description="Lines to refund; omit for every eligible unit"
    )
    rma_number: str | None = Field(None, pattern=r"^RMA-\d{6}$")
    confirmed_by_customer: bool
    customer_note: str | None = Field(None, max_length=1000)

    @model_validator(mode="after")
    def _unique_lines(self):
        if self.items and len({i.line_number for i in self.items}) != len(self.items):
            raise ValueError("each line_number may appear once")
        return self


class RefundResult(ApiModel):
    refund: RefundOut
    status: Literal["succeeded", "processing", "pending_approval"]
    requires_human_approval: bool
    approval_reasons: list[str]
    ticket_number: str | None
    message: str


class ReturnItemOut(ApiModel):
    line_number: int
    sku: str
    product_name: str
    quantity: int
    reason_code: str
    item_condition: str | None
    disposition: str
    restocking_fee_bps: int


class ReturnOut(ApiModel):
    rma_number: str
    order_id: str
    status: str
    eligibility: str
    ineligible_reason: str | None
    remedy: str | None
    return_method: str
    evidence_count: int
    evidence_required: bool
    requested_at: UtcDateTime
    decided_at: UtcDateTime | None
    closed_at: UtcDateTime | None
    items: list[ReturnItemOut]
    refund_ids: list[str]


class ReturnRequestIn(ApiModel):
    reason_code: ClaimReason
    items: list[LineSelection] = Field(..., min_length=1, max_length=50)
    remedy: Literal["refund_original_payment", "store_credit", "replacement", "redelivery"] = "refund_original_payment"
    return_method: Literal["not_required", "courier_pickup", "in_store_dropoff"] | None = None
    item_condition: Literal["unopened", "opened", "broken", "defective", "not_received"] | None = None
    confirmed_by_customer: bool
    customer_notes: str | None = Field(None, max_length=1000)

    @model_validator(mode="after")
    def _unique_lines(self):
        if len({i.line_number for i in self.items}) != len(self.items):
            raise ValueError("each line_number may appear once")
        return self


class ReturnCreated(ApiModel):
    rma: ReturnOut
    eligibility: Literal["auto_approved", "needs_review"]
    evidence_required: bool
    next_steps: list[str]
    estimated_refund: MoneyOpt


class EvidenceUploadLink(ApiModel):
    rma_number: str
    upload_link: str
    expires_at: UtcDateTime
    instructions: str
