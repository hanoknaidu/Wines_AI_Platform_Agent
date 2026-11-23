from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import (
    InventoryLevel,
    InventoryReservation,
    Order,
    OrderItem,
    OrderStatusHistory,
    Payment,
    ProductListing,
    Refund,
    ReturnItem,
    ReturnRequest,
    Shipment,
)
from app.models.returns import RETURN_REASON_CODES
from app.repositories.base import Repository

ORDER_SORTS = {"placed_at": Order.placed_at, "grand_total": Order.grand_total_cents, "status": Order.status}
CLAIM_REASONS = tuple(r for r in RETURN_REASON_CODES if r not in ("change_of_mind",))


@dataclass
class OrderFilters:
    status: list[str] | None = None
    fulfillment_type: str | None = None
    placed_from: datetime | None = None
    placed_to: datetime | None = None
    sort: str = "-placed_at"


def _full_order_options():
    return (
        selectinload(Order.customer),
        selectinload(Order.store),
        selectinload(Order.items).selectinload(OrderItem.variant),
        selectinload(Order.addresses),
        selectinload(Order.discounts),
        selectinload(Order.status_history),
        selectinload(Order.shipments).selectinload(Shipment.items),
        selectinload(Order.shipments).selectinload(Shipment.events),
        selectinload(Order.payments).selectinload(Payment.transactions),
        selectinload(Order.payments).selectinload(Payment.payment_method),
        selectinload(Order.payments).selectinload(Payment.gift_card),
        selectinload(Order.refunds).selectinload(Refund.items),
        selectinload(Order.refunds).selectinload(Refund.return_request),
        selectinload(Order.returns).selectinload(ReturnRequest.items),
        selectinload(Order.returns).selectinload(ReturnRequest.evidence),
    )


class OrderRepository(Repository):
    async def get_full(self, order_number: str, *, for_update: bool = False) -> Order | None:
        stmt = select(Order).where(Order.order_number == order_number).options(*_full_order_options())
        if for_update and self.dialect == "postgresql":
            # Row lock serializes concurrent refunds/cancellations on one order.
            stmt = stmt.with_for_update(of=Order)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_full_by_id(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.order_id == order_id).options(*_full_order_options())
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def refresh_full(self, order: Order) -> Order:
        """Reload the order graph after writes (populate_existing refreshes
        already-loaded collections; no lazy loads in async code)."""
        order_id = order.order_id
        stmt = (
            select(Order)
            .where(Order.order_id == order_id)
            .options(*_full_order_options())
            .execution_options(populate_existing=True)
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def list_for_customer(
        self, customer_id: int, filters: OrderFilters, offset: int, limit: int
    ) -> tuple[list[Order], int]:
        conds = [Order.customer_id == customer_id]
        if filters.status:
            conds.append(Order.status.in_(filters.status))
        if filters.fulfillment_type:
            conds.append(Order.fulfillment_type == filters.fulfillment_type)
        if filters.placed_from:
            conds.append(Order.placed_at >= filters.placed_from)
        if filters.placed_to:
            conds.append(Order.placed_at < filters.placed_to)
        total = (await self.session.execute(select(func.count()).select_from(Order).where(*conds))).scalar_one()
        desc = filters.sort.startswith("-")
        col = ORDER_SORTS[filters.sort.lstrip("-")]
        stmt = (
            select(Order)
            .where(*conds)
            .options(selectinload(Order.store), selectinload(Order.items), selectinload(Order.shipments))
            .order_by(col.desc() if desc else col.asc(), Order.order_id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars()), int(total)

    async def add_status_history(
        self, order: Order, to_status: str, actor_type: str, actor_ref: str | None, note: str | None, at: datetime
    ) -> None:
        self.session.add(
            OrderStatusHistory(
                order_id=order.order_id,
                from_status=order.status,
                to_status=to_status,
                actor_type=actor_type,
                actor_ref=actor_ref,
                note=note,
                changed_at=at,
            )
        )

    async def active_reservations(self, order_id: int) -> list[InventoryReservation]:
        stmt = select(InventoryReservation).where(
            InventoryReservation.order_id == order_id, InventoryReservation.status == "active"
        )
        return list((await self.session.execute(stmt)).scalars())

    async def inventory_level(self, warehouse_id: int, variant_id: int) -> InventoryLevel | None:
        return await self.session.get(InventoryLevel, (warehouse_id, variant_id))

    async def listings_for(self, store_id: int, variant_ids: list[int]) -> dict[int, ProductListing]:
        stmt = select(ProductListing).where(
            ProductListing.store_id == store_id, ProductListing.variant_id.in_(variant_ids)
        )
        return {pl.variant_id: pl for pl in (await self.session.execute(stmt)).scalars()}

    async def count_recent_claims(self, customer_id: int, since: datetime, exclude_order_id: int | None) -> int:
        """Claims (non change-of-mind returns) on *other* orders in the window (A-60 / A-62)."""
        stmt = (
            select(func.count(func.distinct(ReturnRequest.return_id)))
            .join(ReturnItem, ReturnItem.return_id == ReturnRequest.return_id)
            .where(
                ReturnRequest.customer_id == customer_id,
                ReturnRequest.requested_at >= since,
                ReturnRequest.status.not_in(("cancelled",)),
                ReturnItem.reason_code.in_(CLAIM_REASONS),
            )
        )
        if exclude_order_id:
            stmt = stmt.where(ReturnRequest.order_id != exclude_order_id)
        return int((await self.session.execute(stmt)).scalar_one())
