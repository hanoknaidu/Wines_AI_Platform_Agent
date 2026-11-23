"""Read-only order views. GET endpoints never mutate business state; reads of
payment and invoice data add an audit row (sensitive-read logging)."""
from __future__ import annotations

from app.core.masking import mask_street
from app.core.money import cents_to_str
from app.models import Order, Payment
from app.repositories.order_repo import OrderFilters, OrderRepository
from app.schemas.common import Page, PageParams
from app.schemas.order import (
    DiscountOut,
    Invoice,
    InvoiceLine,
    OrderAddressOut,
    OrderDetail,
    OrderLine,
    OrderPayment,
    OrderStatusOut,
    OrderSummary,
    OrderTotals,
    OrderTracking,
    PaymentTender,
    ShipmentStatus,
    ShipmentSummary,
    ShipmentTracking,
    StatusHistoryEntry,
    TrackingEvent,
)
from app.services.context import ServiceContext
from app.services.order_facts import compute_facts

STATUS_DESCRIPTIONS = {
    "placed": "Order received; payment authorized.",
    "age_verification_pending": "Waiting for ID verification before the first order can be released.",
    "confirmed": "Confirmed and waiting to be packed.",
    "picking": "The store is packing the order.",
    "substitution_pending": "Waiting for your answer on a proposed substitution.",
    "ready_for_pickup": "Ready for pickup at the store (bring a valid 21+ ID).",
    "out_for_delivery": "With the driver and on the way.",
    "label_created": "Shipping label created; waiting for carrier pickup.",
    "in_transit": "With the carrier and in transit.",
    "partially_fulfilled": "Part of the order has been delivered; the rest is on the way.",
    "delivery_exception": "The carrier reported a delivery problem.",
    "delivered": "Delivered.",
    "picked_up": "Picked up at the store.",
    "delivery_failed": "Delivery attempt failed.",
    "redelivery_scheduled": "A redelivery has been scheduled.",
    "returned_to_store": "Returned to the store after failed delivery attempts.",
    "returned_to_sender": "Returned to the sender by the carrier.",
    "on_hold": "On hold.",
    "cancelled": "Cancelled.",
    "completed": "Completed.",
}
# Customer-safe hold categories: fraud screening logic is never revealed (OC-R6).
HOLD_CATEGORY = {
    "weather": "weather", "fraud_review": "account_review", "bulk_review": "order_review",
    "address_verification": "address_verification", "age_verification": "age_verification",
    "payment_issue": "payment_issue",
}


def _addr(order: Order, mask: bool) -> OrderAddressOut | None:
    a = order.address("shipping")
    if a is None:
        return None
    return OrderAddressOut(
        recipient_name=a.recipient_name, line1=mask_street(a.line1) if mask else a.line1,
        line2=None if mask else a.line2, city=a.city, state_code=a.state_code, postal_code=a.postal_code,
        address_type=a.address_type,
    )


def _tender(p: Payment) -> PaymentTender:
    pm = p.payment_method
    return PaymentTender(
        tender_type=p.tender_type, card_brand=pm.card_brand if pm else None, card_last4=pm.card_last4 if pm else None,
        gift_card_last4=p.gift_card.code_last4 if p.gift_card else None, amount=p.amount_cents, status=p.status,
        authorized=p.authorized_cents, captured=p.captured_cents, voided=p.voided_cents, refunded=p.refunded_cents,
    )


class OrderService:
    def __init__(self, ctx: ServiceContext) -> None:
        self.ctx = ctx
        self.repo = OrderRepository(ctx.session)

    @property
    def _mask(self) -> bool:
        return self.ctx.principal.role == "agent"

    async def list_for_customer(
        self, customer_number: str, filters: OrderFilters, page: PageParams
    ) -> Page[OrderSummary]:
        customer = await self.ctx.owned_customer(customer_number)
        orders, total = await self.repo.list_for_customer(customer.customer_id, filters, page.offset, page.page_size)
        items = []
        for o in orders:
            delivered = [s.delivered_at for s in o.shipments if s.is_handed_off and s.delivered_at]
            items.append(OrderSummary(
                order_id=o.order_number, status=o.status, payment_status=o.payment_status,
                fulfillment_type=o.fulfillment_type, store_code=o.store.store_code, state_code=o.store.state_code,
                item_count=sum(i.quantity for i in o.items), grand_total=o.grand_total_cents, placed_at=o.placed_at,
                delivered_at=max(delivered) if delivered else None,
            ))
        return Page(items=items, page=page.page, page_size=page.page_size, total=total,
                    has_more=page.offset + len(items) < total)

    def _lines(self, order: Order) -> list[OrderLine]:
        facts = compute_facts(order)
        out = []
        for i in order.items:
            lf = facts.lines[i.order_item_id]
            out.append(OrderLine(
                line_number=i.line_number, sku=i.sku, product_name=i.product_name, brand_name=i.brand_name,
                vintage_year=i.vintage_year, size_ml=i.size_ml, quantity=i.quantity, unit_price=i.unit_price_cents,
                unit_regular_price=i.unit_regular_price_cents, discount=i.discount_cents, tax=i.tax_cents,
                line_total=i.line_total_cents, is_final_sale=i.is_final_sale, is_vintage_specific=i.is_vintage_specific,
                quantity_cancelled=i.quantity_cancelled, quantity_shipped=lf.shipped, quantity_delivered=lf.delivered,
                quantity_returned=lf.returned, quantity_refunded=lf.refunded_qty,
            ))
        return out

    async def detail(self, order_number: str) -> OrderDetail:
        o = await self.ctx.owned_order(order_number)
        facts = compute_facts(o)
        return OrderDetail(
            order_id=o.order_number, customer_id=o.customer.customer_number, status=o.status,
            payment_status=o.payment_status, hold_reason_category=HOLD_CATEGORY.get(o.hold_reason or ""),
            fulfillment_type=o.fulfillment_type, store_code=o.store.store_code, state_code=o.store.state_code,
            placed_at=o.placed_at, delivered_at=facts.delivered_at, cancelled_at=o.cancelled_at,
            cancel_reason=o.cancel_reason, delivery_window_start=o.delivery_window_start,
            delivery_window_end=o.delivery_window_end, substitution_preference=o.substitution_preference,
            is_gift=o.is_gift, shipping_address=_addr(o, self._mask),
            pickup_location=o.store.name if o.fulfillment_type == "pickup" else None,
            totals=OrderTotals(
                items_subtotal=o.items_subtotal_cents, discount_total=o.discount_total_cents,
                shipping_fee=o.shipping_fee_cents, tip=o.tip_cents, tax_total=o.tax_total_cents,
                grand_total=o.grand_total_cents, refunded_total=facts.succeeded_refunds_cents,
            ),
            discounts=[DiscountOut(discount_type=d.discount_type, code_used=d.code_used, description=d.description,
                                   amount=d.amount_cents) for d in o.discounts],
            lines=self._lines(o),
            shipments=[ShipmentSummary(
                shipment_number=s.shipment_number, method=s.method, carrier=s.carrier, status=s.status,
                tracking_url=s.tracking_url, delivered_at=s.delivered_at, estimated_delivery_at=s.estimated_delivery_at,
            ) for s in o.shipments],
        )

    async def status(self, order_number: str) -> OrderStatusOut:
        o = await self.ctx.owned_order(order_number)
        last = o.status_history[-1].changed_at if o.status_history else o.updated_at
        return OrderStatusOut(
            order_id=o.order_number, status=o.status, status_description=STATUS_DESCRIPTIONS.get(o.status, o.status),
            payment_status=o.payment_status, hold_reason_category=HOLD_CATEGORY.get(o.hold_reason or ""),
            fulfillment_type=o.fulfillment_type, eta_window_start=o.delivery_window_start,
            eta_window_end=o.delivery_window_end, last_updated_at=last,
            shipments=[ShipmentStatus(
                shipment_number=s.shipment_number, status=s.status, carrier=s.carrier, tracking_url=s.tracking_url,
                eta_window_start=s.delivery_window_start, eta_window_end=s.delivery_window_end,
                estimated_delivery_at=s.estimated_delivery_at, weather_hold=s.weather_hold,
            ) for s in o.shipments],
        )

    async def tracking(self, order_number: str) -> OrderTracking:
        o = await self.ctx.owned_order(order_number)
        lines = {i.order_item_id: i for i in o.items}
        shipments = [ShipmentTracking(
            shipment_number=s.shipment_number, method=s.method, carrier=s.carrier, service_level=s.service_level,
            tracking_number=s.tracking_number, tracking_url=s.tracking_url, status=s.status,
            attempt_count=s.attempt_count, weather_hold=s.weather_hold,
            requires_adult_signature=s.requires_adult_signature, shipped_at=s.shipped_at,
            delivered_at=s.delivered_at, estimated_delivery_at=s.estimated_delivery_at,
            items=[{"line_number": lines[si.order_item_id].line_number, "sku": lines[si.order_item_id].sku,
                    "quantity": si.quantity} for si in s.items if si.order_item_id in lines],
            events=[TrackingEvent(
                event_code=e.event_code, description=e.description,
                location=", ".join(x for x in (e.location_city, e.location_state) if x) or None,
                occurred_at=e.occurred_at,
            ) for e in s.events],
        ) for s in o.shipments]
        note = None if shipments else "Nothing has shipped yet; tracking appears once the order is dispatched."
        return OrderTracking(order_id=o.order_number, status=o.status, fulfillment_type=o.fulfillment_type,
                             shipments=shipments, note=note)

    async def items(self, order_number: str) -> list[OrderLine]:
        return self._lines(await self.ctx.owned_order(order_number))

    async def history(self, order_number: str) -> list[StatusHistoryEntry]:
        o = await self.ctx.owned_order(order_number)
        # Staff codes / service names in actor_ref are internal: expose the actor type only.
        return [StatusHistoryEntry(from_status=h.from_status, to_status=h.to_status, actor_type=h.actor_type,
                                   changed_at=h.changed_at) for h in o.status_history]

    async def payment(self, order_number: str) -> OrderPayment:
        o = await self.ctx.owned_order(order_number)
        self.ctx.audit("payment.read", "order", o.order_number, customer_id=o.customer_id)
        await self.ctx.session.commit()
        return OrderPayment(
            order_id=o.order_number, payment_status=o.payment_status, grand_total=o.grand_total_cents,
            captured_total=sum(p.captured_cents for p in o.payments),
            refunded_total=sum(p.refunded_cents for p in o.payments),
            open_authorization_total=sum(p.open_authorization_cents for p in o.payments),
            chargeback_open=any(p.chargeback_cents > 0 for p in o.payments),
            tenders=[_tender(p) for p in o.payments],
        )

    async def invoice(self, order_number: str) -> Invoice:
        o = await self.ctx.owned_order(order_number)
        facts = compute_facts(o)
        self.ctx.audit("invoice.read", "order", o.order_number, customer_id=o.customer_id)
        await self.ctx.session.commit()
        bill = o.address("billing") or o.address("shipping")
        store = o.store
        return Invoice(
            invoice_number=f"INV-{o.order_number}", order_id=o.order_number, issued_at=o.placed_at,
            seller_of_record={"legal_name": store.legal_name, "license_type": store.license_type,
                              "address": f"{store.address_line1}, {store.city}, "
                                         f"{store.state_code} {store.postal_code}"},
            bill_to={"name": f"{o.customer.first_name} {o.customer.last_name}",
                     "city": bill.city if bill else None, "state_code": bill.state_code if bill else None},
            lines=[InvoiceLine(
                line_number=i.line_number,
                description=f"{i.brand_name} {i.product_name} {i.vintage_year or 'NV'} ({i.size_ml} ml)",
                sku=i.sku, quantity=i.quantity, unit_price=i.unit_price_cents, discount=i.discount_cents,
                tax=i.tax_cents, line_total=i.line_total_cents,
            ) for i in o.items],
            discounts=[DiscountOut(discount_type=d.discount_type, code_used=d.code_used, description=d.description,
                                   amount=d.amount_cents) for d in o.discounts],
            items_subtotal=o.items_subtotal_cents, discount_total=o.discount_total_cents,
            shipping_fee=o.shipping_fee_cents, tip=o.tip_cents, tax_total=o.tax_total_cents,
            tax_jurisdiction=o.tax_jurisdiction, grand_total=o.grand_total_cents,
            payments=[{"tender_type": t.tender_type, "card_brand": t.card_brand, "card_last4": t.card_last4,
                       "amount": t.model_dump(mode="json")["amount"]} for t in map(_tender, o.payments)],
            refunds=[{"refund_id": f.refund_number, "status": f.status, "amount": cents_to_str(f.amount_cents)}
                     for f in o.refunds],
            balance_after_refunds=o.grand_total_cents - facts.succeeded_refunds_cents,
        )
