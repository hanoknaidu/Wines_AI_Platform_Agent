"""Returns (RMA) and refunds. A refund is the business decision; money moves in
payment_transactions / store_credit_transactions / gift_card_transactions."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, UTCDateTime, in_

RETURN_REASON_CODES = (
    "damaged_in_transit", "broken_on_arrival", "corked_or_flawed", "leaking",
    "wrong_item", "missing_item", "change_of_mind", "late_delivery",
)
REFUND_REASON_CODES = RETURN_REASON_CODES + (
    "order_cancelled", "item_out_of_stock", "price_adjustment", "price_match", "failed_delivery", "duplicate_charge",
)
REFUND_STATUSES = ("pending_approval", "approved", "processing", "succeeded", "failed", "rejected", "cancelled")
INACTIVE_REFUND_STATUSES = ("failed", "rejected", "cancelled")
INACTIVE_RETURN_STATUSES = ("rejected", "cancelled")


class ReturnRequest(Base):
    __tablename__ = "returns"
    __table_args__ = (
        CheckConstraint(in_("eligibility", ("auto_approved", "needs_review", "ineligible")), name="eligibility"),
        CheckConstraint("(eligibility = 'ineligible') = (ineligible_reason IS NOT NULL)", name="ineligible_reason"),
        Index("ix_returns_customer", "customer_id", "requested_at"),
    )

    return_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    rma_number: Mapped[str] = mapped_column(String(20), unique=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    status: Mapped[str] = mapped_column(String(20), default="requested")
    eligibility: Mapped[str] = mapped_column(String(20))
    ineligible_reason: Mapped[str | None] = mapped_column(Text)
    remedy: Mapped[str | None] = mapped_column(String(30))
    return_method: Mapped[str] = mapped_column(String(30))
    initiated_via: Mapped[str] = mapped_column(String(20))
    customer_notes: Mapped[str | None] = mapped_column(Text)
    decided_by_type: Mapped[str | None] = mapped_column(String(20))
    decided_by_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff_users.staff_id"))
    replacement_order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.order_id"))
    requested_at: Mapped[datetime] = mapped_column(UTCDateTime)
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    received_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    items: Mapped[list[ReturnItem]] = relationship(lazy="raise_on_sql", order_by="ReturnItem.return_item_id")
    evidence: Mapped[list[ReturnEvidence]] = relationship(lazy="raise_on_sql")

    @property
    def is_active(self) -> bool:
        return self.status not in INACTIVE_RETURN_STATUSES


class ReturnItem(Base):
    __tablename__ = "return_items"
    __table_args__ = (
        UniqueConstraint("return_id", "order_item_id"),
        CheckConstraint(in_("reason_code", RETURN_REASON_CODES), name="reason_code"),
        CheckConstraint("reason_code = 'change_of_mind' OR restocking_fee_bps = 0", name="restocking_fee"),  # A-34
    )

    return_item_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    return_id: Mapped[int] = mapped_column(ForeignKey("returns.return_id"), index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"))
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.order_item_id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    reason_code: Mapped[str] = mapped_column(String(30))
    item_condition: Mapped[str | None] = mapped_column(String(20))
    disposition: Mapped[str] = mapped_column(String(30), default="pending")
    restocking_fee_bps: Mapped[int] = mapped_column(Integer, default=0)
    inspection_notes: Mapped[str | None] = mapped_column(Text)  # internal: never serialized


class ReturnEvidence(Base):
    __tablename__ = "return_evidence"

    evidence_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    return_id: Mapped[int] = mapped_column(ForeignKey("returns.return_id"), index=True)
    return_item_id: Mapped[int | None] = mapped_column(ForeignKey("return_items.return_item_id"))
    evidence_type: Mapped[str] = mapped_column(String(20))
    storage_ref: Mapped[str] = mapped_column(String(300), unique=True)
    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime)


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = (
        CheckConstraint(in_("reason_code", REFUND_REASON_CODES), name="reason_code"),
        CheckConstraint(in_("method", ("original_payment", "store_credit")), name="method"),
        CheckConstraint(in_("status", REFUND_STATUSES), name="status"),
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint(
            "amount_cents = items_amount_cents + tax_amount_cents + shipping_amount_cents"
            " + tip_amount_cents - restocking_fee_cents",
            name="amount_breakdown",
        ),
        CheckConstraint(
            "restocking_fee_cents = 0 OR (reason_code = 'change_of_mind' AND method = 'original_payment')",
            name="restocking_fee",
        ),  # A-34
        # A-60 / A-62: the AI agent may not complete a refund over $150 on its own.
        CheckConstraint(
            "initiated_by_type <> 'ai_agent' OR amount_cents <= 15000 OR requires_human_approval",
            name="agent_refund_cap",
        ),
        CheckConstraint(
            "NOT requires_human_approval OR status IN ('pending_approval','rejected','cancelled')"
            " OR approved_by_staff_id IS NOT NULL",
            name="human_approval",
        ),
        Index("ix_refunds_status", "status"),
    )

    refund_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    refund_number: Mapped[str] = mapped_column(String(40), unique=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    return_id: Mapped[int | None] = mapped_column(ForeignKey("returns.return_id"))
    reason_code: Mapped[str] = mapped_column(String(30))
    method: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending_approval")
    items_amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    tax_amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    shipping_amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    tip_amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    restocking_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    amount_cents: Mapped[int] = mapped_column(Integer)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff_users.staff_id"))
    initiated_by_type: Mapped[str] = mapped_column(String(20))
    initiated_by_ref: Mapped[str | None] = mapped_column(String(60))
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True)
    note: Mapped[str | None] = mapped_column(Text)  # internal: never serialized
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    approved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    items: Mapped[list[RefundItem]] = relationship(lazy="raise_on_sql")
    return_request: Mapped[ReturnRequest | None] = relationship(lazy="raise_on_sql")

    @property
    def is_active(self) -> bool:
        return self.status not in INACTIVE_REFUND_STATUSES


class RefundItem(Base):
    __tablename__ = "refund_items"

    refund_id: Mapped[int] = mapped_column(ForeignKey("refunds.refund_id"), primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.order_item_id"), primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"))
    quantity: Mapped[int] = mapped_column(Integer)  # 0 = price-only adjustment
    amount_cents: Mapped[int] = mapped_column(Integer)
