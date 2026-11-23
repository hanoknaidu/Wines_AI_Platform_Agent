from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, UTCDateTime, in_


class Store(Base):
    __tablename__ = "stores"
    __table_args__ = (CheckConstraint(in_("state_code", ("NJ", "NY")), name="state_code"),)

    store_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    store_code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    legal_name: Mapped[str] = mapped_column(String(200))
    state_code: Mapped[str] = mapped_column(String(2))
    license_type: Mapped[str] = mapped_column(String(120))
    license_number: Mapped[str] = mapped_column(String(60), unique=True)
    address_line1: Mapped[str] = mapped_column(String(200))
    address_line2: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(5))
    phone_e164: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(60), default="America/New_York")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    hours: Mapped[list[StoreHours]] = relationship(lazy="raise_on_sql", order_by="StoreHours.day_of_week")
    exceptions: Mapped[list[StoreHoursException]] = relationship(
        lazy="raise_on_sql", order_by="StoreHoursException.exception_date"
    )


class StoreHours(Base):
    __tablename__ = "store_hours"

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.store_id"), primary_key=True)
    day_of_week: Mapped[int] = mapped_column(Integer, primary_key=True)  # 0 = Sunday
    opens_at: Mapped[str] = mapped_column(String(5))
    closes_at: Mapped[str] = mapped_column(String(5))


class StoreHoursException(Base):
    __tablename__ = "store_hours_exceptions"

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.store_id"), primary_key=True)
    exception_date: Mapped[date] = mapped_column(Date, primary_key=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    opens_at: Mapped[str | None] = mapped_column(String(5))
    closes_at: Mapped[str | None] = mapped_column(String(5))
    note: Mapped[str | None] = mapped_column(Text)


class Warehouse(Base):
    __tablename__ = "warehouses"

    warehouse_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.store_id"), index=True)
    state_code: Mapped[str] = mapped_column(String(2))
    warehouse_code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    warehouse_type: Mapped[str] = mapped_column(String(40))
    is_pickup_point: Mapped[bool] = mapped_column(Boolean, default=False)
    ships_by_carrier: Mapped[bool] = mapped_column(Boolean, default=False)
    runs_local_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    address_line1: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(5))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class StaffUser(Base):
    __tablename__ = "staff_users"

    staff_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200))  # internal only: never serialized
    role: Mapped[str] = mapped_column(String(30))
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.store_id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
