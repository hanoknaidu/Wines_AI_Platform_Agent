from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, UTCDateTime, in_
from app.models.organization import Store

CUSTOMER_STATUSES = ("active", "locked", "suspended", "closed", "anonymized")
ADDRESS_TYPES = ("residential", "business", "hotel", "po_box", "school", "dormitory")
RESTRICTED_ADDRESS_TYPES = ("po_box", "school", "dormitory")  # A-20


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint(in_("status", CUSTOMER_STATUSES), name="status"),
        CheckConstraint("status = 'active' OR status_reason IS NOT NULL", name="status_reason"),
    )

    customer_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    customer_number: Mapped[str] = mapped_column(String(20), unique=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    phone_e164: Mapped[str | None] = mapped_column(String(20), index=True)
    date_of_birth: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")
    status_reason: Mapped[str | None] = mapped_column(Text)  # internal: never serialized
    home_store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.store_id"), index=True)
    marketing_source: Mapped[str | None] = mapped_column(String(60))
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    home_store: Mapped[Store | None] = relationship(lazy="raise_on_sql")


class AgeVerification(Base):
    __tablename__ = "age_verifications"
    __table_args__ = (
        CheckConstraint(in_("status", ("pending", "verified", "failed", "manual_review")), name="status"),
        Index("ix_age_verifications_customer_started", "customer_id", "started_at"),
    )

    age_verification_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    status: Mapped[str] = mapped_column(String(20))
    method: Mapped[str] = mapped_column(String(30))
    provider: Mapped[str] = mapped_column(String(100))
    provider_reference: Mapped[str | None] = mapped_column(String(100))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"
    __table_args__ = (CheckConstraint(in_("address_type", ADDRESS_TYPES), name="address_type"),)

    address_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    label: Mapped[str | None] = mapped_column(String(60))
    recipient_name: Mapped[str] = mapped_column(String(120))
    line1: Mapped[str] = mapped_column(String(200))
    line2: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    state_code: Mapped[str] = mapped_column(String(2))
    postal_code: Mapped[str] = mapped_column(String(5))
    country_code: Mapped[str] = mapped_column(String(2), default="US")
    phone_e164: Mapped[str | None] = mapped_column(String(20))
    address_type: Mapped[str] = mapped_column(String(20), default="residential")
    delivery_instructions: Mapped[str | None] = mapped_column(Text)
    is_default_shipping: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default_billing: Mapped[bool] = mapped_column(Boolean, default=False)
    validated_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    @property
    def is_restricted_destination(self) -> bool:
        return self.address_type in RESTRICTED_ADDRESS_TYPES


class CustomerPaymentMethod(Base):
    """Tokenized only. processor_token is never serialized (A-74)."""

    __tablename__ = "customer_payment_methods"

    payment_method_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    method_type: Mapped[str] = mapped_column(String(20))
    processor: Mapped[str] = mapped_column(String(40))
    processor_token: Mapped[str] = mapped_column(String(200), unique=True)
    card_brand: Mapped[str] = mapped_column(String(20))
    card_last4: Mapped[str] = mapped_column(String(4))
    exp_month: Mapped[int] = mapped_column(Integer)
    exp_year: Mapped[int] = mapped_column(Integer)
    billing_address_id: Mapped[int | None] = mapped_column(ForeignKey("customer_addresses.address_id"))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    removed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
