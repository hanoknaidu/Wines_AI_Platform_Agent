from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, JSONType, UTCDateTime

HANDED_OFF_STATUSES = ("delivered", "picked_up")


class Shipment(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        # Compliance: no handoff without a 21+ ID check.
        CheckConstraint(
            "status NOT IN ('delivered','picked_up') OR (delivered_at IS NOT NULL AND id_verified "
            "AND handed_to_name IS NOT NULL AND id_check_method IS NOT NULL)",
            name="handoff_id_check",
        ),
        CheckConstraint("attempt_count BETWEEN 0 AND 3", name="attempts"),
    )

    shipment_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    shipment_number: Mapped[str] = mapped_column(String(20), unique=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.store_id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.warehouse_id"))
    method: Mapped[str] = mapped_column(String(20))
    carrier: Mapped[str | None] = mapped_column(String(30))
    service_level: Mapped[str | None] = mapped_column(String(60))
    tracking_number: Mapped[str | None] = mapped_column(String(60), unique=True)
    tracking_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    requires_adult_signature: Mapped[bool] = mapped_column(Boolean, default=True)
    weather_hold: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    delivery_window_start: Mapped[datetime | None] = mapped_column(UTCDateTime)
    delivery_window_end: Mapped[datetime | None] = mapped_column(UTCDateTime)
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    shipping_cost_cents: Mapped[int | None] = mapped_column(Integer)  # internal cost: never serialized
    shipped_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    handed_to_name: Mapped[str | None] = mapped_column(String(120))
    id_check_method: Mapped[str | None] = mapped_column(String(40))
    id_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    items: Mapped[list[ShipmentItem]] = relationship(lazy="raise_on_sql")
    events: Mapped[list[ShipmentTrackingEvent]] = relationship(
        lazy="raise_on_sql", order_by="ShipmentTrackingEvent.occurred_at"
    )

    @property
    def is_handed_off(self) -> bool:
        return self.status in HANDED_OFF_STATUSES


class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.shipment_id"), primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.order_item_id"), primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"))
    quantity: Mapped[int] = mapped_column(Integer)


class ShipmentTrackingEvent(Base):
    __tablename__ = "shipment_tracking_events"
    __table_args__ = (Index("ix_tracking_shipment", "shipment_id", "occurred_at"),)

    tracking_event_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.shipment_id"))
    event_code: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    location_city: Mapped[str | None] = mapped_column(String(100))
    location_state: Mapped[str | None] = mapped_column(String(2))
    source: Mapped[str] = mapped_column(String(30))
    carrier_event_ref: Mapped[str | None] = mapped_column(String(100), unique=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONType)  # never serialized
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime)

