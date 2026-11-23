"""Payments (one row per tender), the append-only processor ledger, and the
internal money ledgers (store credit, gift cards, loyalty)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, UTCDateTime, in_
from app.models.customer import CustomerPaymentMethod


class GiftCard(Base):
    __tablename__ = "gift_cards"

    gift_card_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(128), unique=True)  # never serialized
    code_last4: Mapped[str] = mapped_column(String(4))
    card_format: Mapped[str] = mapped_column(String(10))
    initial_value_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")
    purchaser_customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.customer_id"))
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.order_id"))
    recipient_email: Mapped[str | None] = mapped_column(String(254))
    issued_at: Mapped[datetime] = mapped_column(UTCDateTime)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            in_("tender_type", ("card", "apple_pay", "google_pay", "gift_card", "store_credit")), name="tender"
        ),
        CheckConstraint("amount_cents > 0", name="amount_positive"),
    )

    payment_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    tender_type: Mapped[str] = mapped_column(String(20))
    payment_method_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer_payment_methods.payment_method_id")
    )
    gift_card_id: Mapped[int | None] = mapped_column(ForeignKey("gift_cards.gift_card_id"))
    processor: Mapped[str] = mapped_column(String(30))
    processor_payment_ref: Mapped[str | None] = mapped_column(String(100), unique=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    refund_priority: Mapped[int] = mapped_column(Integer, default=1)  # card refunded last
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    payment_method: Mapped[CustomerPaymentMethod | None] = relationship(lazy="raise_on_sql")
    gift_card: Mapped[GiftCard | None] = relationship(lazy="raise_on_sql")
    transactions: Mapped[list[PaymentTransaction]] = relationship(
        lazy="raise_on_sql", order_by="PaymentTransaction.transaction_id"
    )

    def _sum(self, txn_type: str, statuses: tuple[str, ...] = ("succeeded",)) -> int:
        return sum(t.amount_cents for t in self.transactions if t.transaction_type == txn_type and t.status in statuses)

    @property
    def authorized_cents(self) -> int:
        return self._sum("authorization")

    @property
    def captured_cents(self) -> int:
        return self._sum("capture")

    @property
    def voided_cents(self) -> int:
        return self._sum("void")

    @property
    def refunded_cents(self) -> int:
        return self._sum("refund", ("succeeded", "pending"))

    @property
    def chargeback_cents(self) -> int:
        """Disputed amount still open. A dispute is recorded as a *pending*
        chargeback while the bank decides, so pending counts (RF-R5)."""
        disputed = self._sum("chargeback", ("pending", "succeeded"))
        return max(disputed - self._sum("chargeback_reversal"), 0)

    @property
    def open_authorization_cents(self) -> int:
        return max(self.authorized_cents - self.captured_cents - self.voided_cents, 0)

    @property
    def refundable_cents(self) -> int:
        return max(self.captured_cents - self.refunded_cents, 0)


class PaymentTransaction(Base):
    """Append-only: authorization, capture(s), void, refund(s), chargeback."""

    __tablename__ = "payment_transactions"
    __table_args__ = (
        CheckConstraint(
            in_(
                "transaction_type",
                ("authorization", "capture", "void", "refund", "chargeback", "chargeback_reversal"),
            ),
            name="type",
        ),
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint("(transaction_type = 'refund') = (refund_id IS NOT NULL)", name="refund_link"),
        Index("ix_ptx_payment_type", "payment_id", "transaction_type", "status"),
    )

    transaction_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.payment_id"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    transaction_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))
    amount_cents: Mapped[int] = mapped_column(Integer)
    parent_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("payment_transactions.transaction_id"))
    refund_id: Mapped[int | None] = mapped_column(ForeignKey("refunds.refund_id"), index=True)
    shipment_id: Mapped[int | None] = mapped_column(ForeignKey("shipments.shipment_id"))
    processor_reference: Mapped[str | None] = mapped_column(String(100), unique=True)
    failure_code: Mapped[str | None] = mapped_column(String(60))
    failure_message: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    processed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class StoreCreditTransaction(Base):
    """Balance = SUM(amount_cents). Instant, never expires (A-36)."""

    __tablename__ = "store_credit_transactions"
    __table_args__ = (
        CheckConstraint("amount_cents <> 0", name="amount_nonzero"),
        # A-61: AI goodwill credit <= $15
        CheckConstraint(
            "entry_type <> 'issue_goodwill' OR issued_by_type <> 'ai_agent' OR amount_cents <= 1500",
            name="agent_goodwill_cap",
        ),
        Index("ix_sct_customer", "customer_id", "created_at"),
    )

    store_credit_txn_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    entry_type: Mapped[str] = mapped_column(String(20))
    amount_cents: Mapped[int] = mapped_column(Integer)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.order_id"))
    refund_id: Mapped[int | None] = mapped_column(ForeignKey("refunds.refund_id"))
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.payment_id"))
    reason: Mapped[str] = mapped_column(Text)
    issued_by_type: Mapped[str] = mapped_column(String(20))
    issued_by_ref: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class GiftCardTransaction(Base):
    __tablename__ = "gift_card_transactions"

    gift_card_txn_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    gift_card_id: Mapped[int] = mapped_column(ForeignKey("gift_cards.gift_card_id"), index=True)
    entry_type: Mapped[str] = mapped_column(String(20))
    amount_cents: Mapped[int] = mapped_column(Integer)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.payment_id"))
    refund_id: Mapped[int | None] = mapped_column(ForeignKey("refunds.refund_id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"), primary_key=True)
    tier: Mapped[str] = mapped_column(String(20), default="member")
    status: Mapped[str] = mapped_column(String(20), default="active")
    enrolled_at: Mapped[datetime] = mapped_column(UTCDateTime)
    tier_updated_at: Mapped[datetime] = mapped_column(UTCDateTime)


class LoyaltyReward(Base):
    __tablename__ = "loyalty_rewards"

    reward_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("loyalty_accounts.customer_id"), index=True)
    value_cents: Mapped[int] = mapped_column(Integer)
    points_cost: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="available")
    issued_at: Mapped[datetime] = mapped_column(UTCDateTime)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    redeemed_order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.order_id"))
    redeemed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class LoyaltyPointTransaction(Base):
    __tablename__ = "loyalty_point_transactions"
    __table_args__ = (Index("ix_loyalty_txn_customer", "customer_id", "created_at"),)

    loyalty_txn_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("loyalty_accounts.customer_id"))
    entry_type: Mapped[str] = mapped_column(String(30))
    points: Mapped[int] = mapped_column(Integer)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.order_id"))
    reward_id: Mapped[int | None] = mapped_column(ForeignKey("loyalty_rewards.reward_id"))
    reason: Mapped[str] = mapped_column(Text)
    created_by_type: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
