"""Derived per-order facts (quantities across shipments, returns and refunds),
computed from a fully loaded Order. Mirrors _DB view v_order_item_fulfillment."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.models import Order, OrderItem


@dataclass
class LineFacts:
    item: OrderItem
    shipped: int = 0
    delivered: int = 0
    returned: int = 0
    refunded_qty: int = 0
    refunded_cents: int = 0

    @property
    def open_quantity(self) -> int:
        """Units neither cancelled nor shipped yet."""
        return max(self.item.quantity - self.item.quantity_cancelled - self.shipped, 0)

    @property
    def remaining_line_cents(self) -> int:
        return max(self.item.line_total_cents - self.refunded_cents, 0)


@dataclass
class OrderFacts:
    order: Order
    lines: dict[int, LineFacts] = field(default_factory=dict)  # by order_item_id
    delivered_at: datetime | None = None
    active_refunds_cents: int = 0
    succeeded_refunds_cents: int = 0
    captured_cents: int = 0
    chargeback_open: bool = False

    @property
    def state_code(self) -> str:
        return self.order.store.state_code

    @property
    def collected_cents(self) -> int:
        """What the customer actually paid: captures (partial captures happen when
        units are cancelled before shipping, e.g. a declined substitution)."""
        return min(self.order.grand_total_cents, self.captured_cents)

    @property
    def remaining_refundable_cents(self) -> int:
        return max(self.collected_cents - self.active_refunds_cents, 0)

    @property
    def delivered_units(self) -> int:
        return sum(lf.delivered for lf in self.lines.values())

    def by_line_number(self) -> dict[int, LineFacts]:
        return {lf.item.line_number: lf for lf in self.lines.values()}

    @property
    def fee_tax_cents(self) -> int:
        """Tax charged on the delivery/shipping fee (order tax minus line taxes)."""
        return max(self.order.tax_total_cents - sum(i.tax_cents for i in self.order.items), 0)


def compute_facts(order: Order) -> OrderFacts:
    facts = OrderFacts(order=order, lines={i.order_item_id: LineFacts(i) for i in order.items})
    delivered_times = []
    for shipment in order.shipments:
        if shipment.status == "cancelled":
            continue
        for si in shipment.items:
            lf = facts.lines.get(si.order_item_id)
            if lf:
                lf.shipped += si.quantity
                if shipment.is_handed_off:
                    lf.delivered += si.quantity
        if shipment.is_handed_off and shipment.delivered_at:
            delivered_times.append(shipment.delivered_at)
    facts.delivered_at = max(delivered_times) if delivered_times else None

    for rma in order.returns:
        if not rma.is_active:
            continue
        for ri in rma.items:
            if ri.order_item_id in facts.lines:
                facts.lines[ri.order_item_id].returned += ri.quantity

    for refund in order.refunds:
        if not refund.is_active:
            continue
        facts.active_refunds_cents += refund.amount_cents
        if refund.status == "succeeded":
            facts.succeeded_refunds_cents += refund.amount_cents
        for fi in refund.items:
            if fi.order_item_id in facts.lines:
                facts.lines[fi.order_item_id].refunded_qty += fi.quantity
                facts.lines[fi.order_item_id].refunded_cents += fi.amount_cents

    facts.captured_cents = sum(p.captured_cents for p in order.payments)
    facts.chargeback_open = any(p.chargeback_cents > 0 for p in order.payments)
    return facts
