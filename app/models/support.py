"""Support tickets, the append-only audit log and API idempotency records."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, JSONType, UTCDateTime, in_

TICKET_CATEGORIES = (
    "order_status", "delivery_issue", "pickup_issue", "damaged_item", "flawed_wine", "wrong_or_missing_item",
    "return_request", "refund_status", "pricing_dispute", "price_match", "promo_code", "loyalty",
    "account_access", "age_verification", "privacy_request", "payment_issue", "product_question",
    "product_request", "bulk_or_event_order", "complaint", "compliance", "fraud", "general",
)
TICKET_REASON_CODES = (
    "handoff_compliance_incident", "underage_risk", "legal_matter", "safety_crisis", "fraud_signal",
    "account_takeover", "refund_over_limit", "claim_review", "policy_exception_request", "price_match",
    "pricing_dispute", "fulfillment_delay", "bulk_order", "account_recovery", "privacy_request",
    "id_verification_failure", "pre_arrival_issue", "product_request", "conduct_complaint", "kb_gap",
    "customer_requested_human", "tool_failure", "refund_trace",
)
TICKET_STATUSES = ("new", "open", "pending_customer", "pending_internal", "escalated", "resolved", "closed")


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = (
        CheckConstraint(in_("category", TICKET_CATEGORIES), name="category"),
        CheckConstraint(in_("priority", ("P1", "P2", "P3")), name="priority"),
        CheckConstraint(f"reason_code IS NULL OR {in_('reason_code', TICKET_REASON_CODES)}", name="reason_code"),
        CheckConstraint(in_("status", TICKET_STATUSES), name="status"),
        CheckConstraint("priority <> 'P1' OR reason_code IS NOT NULL", name="p1_reason"),
        Index("ix_tickets_customer", "customer_id", "created_at"),
        Index("ix_tickets_queue", "status", "priority", "sla_due_at"),
    )

    ticket_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String(40), unique=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.customer_id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.order_id"), index=True)
    return_id: Mapped[int | None] = mapped_column(ForeignKey("returns.return_id"))
    conversation_id: Mapped[str | None] = mapped_column(String(100), index=True)
    channel: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(30))
    priority: Mapped[str] = mapped_column(String(2))
    reason_code: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="new")
    subject: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    customer_sentiment: Mapped[str | None] = mapped_column(String(20))
    assigned_team: Mapped[str | None] = mapped_column(String(20))
    assigned_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff_users.staff_id"))
    sla_due_at: Mapped[datetime] = mapped_column(UTCDateTime)
    first_response_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    csat_score: Mapped[int | None] = mapped_column(Integer)
    created_by_type: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    messages: Mapped[list[TicketMessage]] = relationship(lazy="raise_on_sql", order_by="TicketMessage.created_at")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    __table_args__ = (Index("ix_ticket_messages_ticket", "ticket_id", "created_at"),)

    message_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("support_tickets.ticket_id"))
    author_type: Mapped[str] = mapped_column(String(20))
    author_customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.customer_id"))
    author_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff_users.staff_id"))
    visibility: Mapped[str] = mapped_column(String(10), default="public")
    body: Mapped[str] = mapped_column(Text)
    attachment_refs: Mapped[list | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class AuditLog(Base):
    """Append-only (PG: REVOKE UPDATE, DELETE + trigger in migration 0001)."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            in_("actor_type", ("customer", "ai_agent", "staff", "system", "carrier", "payment_processor")),
            name="actor_type",
        ),
        CheckConstraint(in_("outcome", ("success", "denied", "failed", "requires_approval")), name="outcome"),
        Index("ix_audit_entity", "entity_type", "entity_id", "occurred_at"),
        Index("ix_audit_customer", "customer_id", "occurred_at"),
        Index("ix_audit_action", "action", "occurred_at"),
    )

    audit_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    actor_type: Mapped[str] = mapped_column(String(20))
    actor_ref: Mapped[str] = mapped_column(String(60))
    action: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(60))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.customer_id"))
    outcome: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(Text)
    conversation_id: Mapped[str | None] = mapped_column(String(100))
    request_id: Mapped[str | None] = mapped_column(String(128))
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    before_state: Mapped[dict | None] = mapped_column(JSONType)
    after_state: Mapped[dict | None] = mapped_column(JSONType)
    ip_address: Mapped[str | None] = mapped_column(String(45))


class IdempotencyRecord(Base):
    """Stores the first response for (principal, Idempotency-Key) so a retried
    refund/cancellation/return returns the same result instead of acting twice."""

    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("principal_ref", "idempotency_key"),)

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    principal_ref: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(300))
    request_hash: Mapped[str] = mapped_column(String(64))
    status_code: Mapped[int] = mapped_column(Integer)
    response_body: Mapped[dict] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)


__all__ = ["SupportTicket", "TicketMessage", "AuditLog", "IdempotencyRecord"]
