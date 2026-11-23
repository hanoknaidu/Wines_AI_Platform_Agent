"""Orders. orders.status = fulfillment lifecycle; orders.payment_status = money
summary (refunded / partially_refunded live there, contract decision 2)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, UTCDateTime, in_
from app.models.customer import Customer
from app.models.organization import Store

ORDER_STATUSES = (
    "placed", "age_verification_pending", "confirmed", "picking", "substitution_pending",
    "ready_for_pickup", "out_for_delivery", "label_created", "in_transit", "partially_fulfilled",
    "delivery_exception", "delivered", "picked_up", "delivery_failed", "redelivery_scheduled",
    "returned_to_store", "returned_to_sender", "on_hold", "cancelled", "completed",
)
PAYMENT_STATUSES = (
    "pending", "authorized", "partially_paid", "paid", "partially_refunded", "refunded", "voided", "failed",
)
CANCEL_REASONS = (
    "customer_request", "out_of_stock", "pricing_error", "fraud", "age_verification_failed",
    "pickup_not_collected", "failed_delivery", "store_decision",
)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(in_("status", ORDER_STATUSES), name="status"),
        CheckConstraint(in_("payment_status", PAYMENT_STATUSES), name="payment_status"),
        CheckConstraint(in_("fulfillment_type", ("local_delivery", "pickup", "shipping")), name="fulfillment_type"),
        CheckConstraint(
            "grand_total_cents = items_subtotal_cents - discount_total_cents + shipping_fee_cents"
            " + tip_cents + tax_total_cents",
            name="grand_total",
        ),
        CheckConstraint("(status = 'on_hold') = (hold_reason IS NOT NULL)", name="hold_reason"),
        CheckConstraint(
            "(status = 'cancelled') = (cancelled_at IS NOT NULL AND cancel_reason IS NOT NULL)", name="cancelled"
        ),
        Index("ix_orders_customer_placed", "customer_id", "placed_at"),
        Index("ix_orders_status_placed", "status", "placed_at"),
    )

    order_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.store_id"))
    channel: Mapped[str] = mapped_column(String(20), default="web")
    status: Mapped[str] = mapped_column(String(30), default="placed")
    hold_reason: Mapped[str | None] = mapped_column(String(30))
    payment_status: Mapped[str] = mapped_column(String(30), default="pending")
    fulfillment_type: Mapped[str] = mapped_column(String(20))
    pickup_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.warehouse_id"))
    alternate_pickup_name: Mapped[str | None] = mapped_column(String(120))
    delivery_zone: Mapped[int | None] = mapped_column(Integer)
    delivery_window_start: Mapped[datetime | None] = mapped_column(UTCDateTime)
    delivery_window_end: Mapped[datetime | None] = mapped_column(UTCDateTime)
    substitution_preference: Mapped[str] = mapped_column(String(30), default="contact_me")
    is_gift: Mapped[bool] = mapped_column(Boolean, default=False)
    gift_message: Mapped[str | None] = mapped_column(Text)
    customer_note: Mapped[str | None] = mapped_column(Text)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    items_subtotal_cents: Mapped[int] = mapped_column(Integer, default=0)
    discount_total_cents: Mapped[int] = mapped_column(Integer, default=0)
    shipping_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    tip_cents: Mapped[int] = mapped_column(Integer, default=0)
    tax_total_cents: Mapped[int] = mapped_column(Integer, default=0)
    grand_total_cents: Mapped[int] = mapped_column(Integer, default=0)
    tax_rate_ppm: Mapped[int] = mapped_column(Integer)
    tax_jurisdiction: Mapped[str] = mapped_column(String(120))
    replacement_for_order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.order_id"))
    placed_at: Mapped[datetime] = mapped_column(UTCDateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    cancel_reason: Mapped[str | None] = mapped_column(String(30))
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    customer: Mapped[Customer] = relationship(lazy="raise_on_sql")
    store: Mapped[Store] = relationship(lazy="raise_on_sql")
    items: Mapped[list[OrderItem]] = relationship(lazy="raise_on_sql", order_by="OrderItem.line_number")
    replacement_for: Mapped[Order | None] = relationship(lazy="raise_on_sql", remote_side="Order.order_id")
    addresses: Mapped[list[OrderAddress]] = relationship(lazy="raise_on_sql")
    discounts: Mapped[list[OrderDiscount]] = relationship(lazy="raise_on_sql")
    status_history: Mapped[list[OrderStatusHistory]] = relationship(
        lazy="raise_on_sql", order_by=lambda: (OrderStatusHistory.changed_at, OrderStatusHistory.history_id)
    )
    shipments: Mapped[list[Shipment]] = relationship(lazy="raise_on_sql", order_by="Shipment.shipment_id")  # noqa: F821
    payments: Mapped[list[Payment]] = relationship(lazy="raise_on_sql", order_by="Payment.refund_priority")  # noqa: F821
    refunds: Mapped[list[Refund]] = relationship(lazy="raise_on_sql", order_by="Refund.refund_id")  # noqa: F821
    returns: Mapped[list[ReturnRequest]] = relationship(  # noqa: F821
        lazy="raise_on_sql", order_by="ReturnRequest.return_id", foreign_keys="ReturnRequest.order_id"
    )

    def address(self, role: str) -> OrderAddress | None:
        return next((a for a in self.addresses if a.address_role == role), None)


class OrderAddress(Base):
    __tablename__ = "order_addresses"
    __table_args__ = (
        CheckConstraint("address_role <> 'shipping' OR state_code IN ('NJ','NY')", name="ship_state"),  # A-02
        CheckConstraint(
            "address_role <> 'shipping' OR address_type NOT IN ('po_box','school','dormitory')",
            name="ship_restricted",
        ),  # A-20
    )

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), primary_key=True)
    address_role: Mapped[str] = mapped_column(String(10), primary_key=True)
    source_address_id: Mapped[int | None] = mapped_column(ForeignKey("customer_addresses.address_id"))
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


class OrderItem(Base):
    """Immutable snapshot of what was bought and the price paid."""

    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "line_number"),
        CheckConstraint("line_subtotal_cents = unit_price_cents * quantity", name="line_subtotal"),
        CheckConstraint(
            "line_total_cents = line_subtotal_cents - discount_cents + tax_cents", name="line_total"
        ),
        CheckConstraint("quantity_cancelled >= 0 AND quantity_cancelled <= quantity", name="qty_cancelled"),
    )

    order_item_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    line_number: Mapped[int] = mapped_column(Integer)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.variant_id"), index=True)
    price_id: Mapped[int | None] = mapped_column(ForeignKey("product_prices.price_id"))
    sku: Mapped[str] = mapped_column(String(40))
    product_name: Mapped[str] = mapped_column(String(200))
    brand_name: Mapped[str] = mapped_column(String(160))
    vintage_year: Mapped[int | None] = mapped_column(Integer)
    size_ml: Mapped[int] = mapped_column(Integer)
    pack_quantity: Mapped[int] = mapped_column(Integer, default=1)
    is_final_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vintage_specific: Mapped[bool] = mapped_column(Boolean, default=False)
    unit_regular_price_cents: Mapped[int] = mapped_column(Integer)
    unit_price_cents: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    line_subtotal_cents: Mapped[int] = mapped_column(Integer)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    tax_cents: Mapped[int] = mapped_column(Integer, default=0)
    line_total_cents: Mapped[int] = mapped_column(Integer)
    quantity_cancelled: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)

    variant: Mapped[ProductVariant] = relationship(lazy="raise_on_sql")  # noqa: F821

    def unit_net_cents(self, quantity: int) -> int:
        """Money for `quantity` units: price net of allocated discount, plus tax,
        prorated from the frozen line totals (never re-priced)."""
        if quantity <= 0:
            return 0
        return (self.line_total_cents * quantity * 2 + self.quantity) // (2 * self.quantity)


class OrderDiscount(Base):
    __tablename__ = "order_discounts"

    order_discount_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    promotion_id: Mapped[int | None] = mapped_column(ForeignKey("promotions.promotion_id"))
    discount_type: Mapped[str] = mapped_column(String(30))
    code_used: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    amount_cents: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class OrderStatusHistory(Base):
    """Append-only timeline."""

    __tablename__ = "order_status_history"
    __table_args__ = (Index("ix_order_status_history_order", "order_id", "changed_at"),)

    history_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"))
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    actor_type: Mapped[str] = mapped_column(String(20))
    actor_ref: Mapped[str | None] = mapped_column(String(60))
    note: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(UTCDateTime)


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"
    __table_args__ = (
        CheckConstraint("(status = 'active') = (closed_at IS NULL)", name="closed_at"),
        Index("ix_reservations_stock", "warehouse_id", "variant_id", "status"),
    )

    reservation_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.order_item_id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.warehouse_id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.variant_id"))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
