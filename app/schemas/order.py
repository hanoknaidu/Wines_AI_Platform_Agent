from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.core.money import Money, MoneyOpt
from app.schemas.common import ApiModel, PolicyReason, UtcDateTime


class OrderSummary(ApiModel):
    order_id: str
    status: str
    payment_status: str
    fulfillment_type: str
    store_code: str
    state_code: str
    item_count: int
    grand_total: Money
    placed_at: UtcDateTime
    delivered_at: UtcDateTime | None


class OrderAddressOut(ApiModel):
    recipient_name: str
    line1: str
    line2: str | None
    city: str
    state_code: str
    postal_code: str
    address_type: str


class OrderLine(ApiModel):
    line_number: int
    sku: str
    product_name: str
    brand_name: str
    vintage_year: int | None
    size_ml: int
    quantity: int
    unit_price: Money
    unit_regular_price: Money
    discount: Money
    tax: Money
    line_total: Money
    is_final_sale: bool
    is_vintage_specific: bool
    quantity_cancelled: int
    quantity_shipped: int
    quantity_delivered: int
    quantity_returned: int
    quantity_refunded: int


class OrderTotals(ApiModel):
    items_subtotal: Money
    discount_total: Money
    shipping_fee: Money
    tip: Money
    tax_total: Money
    grand_total: Money
    refunded_total: Money


class DiscountOut(ApiModel):
    discount_type: str
    code_used: str | None
    description: str
    amount: Money


class ShipmentSummary(ApiModel):
    shipment_number: str
    method: str
    carrier: str | None
    status: str
    tracking_url: str | None
    delivered_at: UtcDateTime | None
    estimated_delivery_at: UtcDateTime | None


class OrderDetail(ApiModel):
    order_id: str
    customer_id: str
    status: str
    payment_status: str
    hold_reason_category: str | None
    fulfillment_type: str
    store_code: str
    state_code: str
    placed_at: UtcDateTime
    delivered_at: UtcDateTime | None
    cancelled_at: UtcDateTime | None
    cancel_reason: str | None
    delivery_window_start: UtcDateTime | None
    delivery_window_end: UtcDateTime | None
    substitution_preference: str
    is_gift: bool
    shipping_address: OrderAddressOut | None
    pickup_location: str | None
    totals: OrderTotals
    discounts: list[DiscountOut]
    lines: list[OrderLine]
    shipments: list[ShipmentSummary]


class ShipmentStatus(ApiModel):
    shipment_number: str
    status: str
    carrier: str | None
    tracking_url: str | None
    eta_window_start: UtcDateTime | None
    eta_window_end: UtcDateTime | None
    estimated_delivery_at: UtcDateTime | None
    weather_hold: bool


class OrderStatusOut(ApiModel):
    order_id: str
    status: str
    status_description: str
    payment_status: str
    hold_reason_category: str | None
    fulfillment_type: str
    eta_window_start: UtcDateTime | None
    eta_window_end: UtcDateTime | None
    last_updated_at: UtcDateTime
    shipments: list[ShipmentStatus]


class TrackingEvent(ApiModel):
    event_code: str
    description: str
    location: str | None
    occurred_at: UtcDateTime


class ShipmentTracking(ApiModel):
    shipment_number: str
    method: str
    carrier: str | None
    service_level: str | None
    tracking_number: str | None
    tracking_url: str | None
    status: str
    attempt_count: int
    weather_hold: bool
    requires_adult_signature: bool
    shipped_at: UtcDateTime | None
    delivered_at: UtcDateTime | None
    estimated_delivery_at: UtcDateTime | None
    items: list[dict]
    events: list[TrackingEvent]


class OrderTracking(ApiModel):
    order_id: str
    status: str
    fulfillment_type: str
    shipments: list[ShipmentTracking]
    note: str | None = None


class StatusHistoryEntry(ApiModel):
    from_status: str | None
    to_status: str
    actor_type: str
    changed_at: UtcDateTime


class PaymentTender(ApiModel):
    tender_type: str
    card_brand: str | None
    card_last4: str | None
    gift_card_last4: str | None
    amount: Money
    status: str
    authorized: Money
    captured: Money
    voided: Money
    refunded: Money


class OrderPayment(ApiModel):
    order_id: str
    payment_status: str
    grand_total: Money
    captured_total: Money
    refunded_total: Money
    open_authorization_total: Money
    chargeback_open: bool
    tenders: list[PaymentTender]


class InvoiceLine(ApiModel):
    line_number: int
    description: str
    sku: str
    quantity: int
    unit_price: Money
    discount: Money
    tax: Money
    line_total: Money


class Invoice(ApiModel):
    invoice_number: str
    order_id: str
    issued_at: UtcDateTime
    seller_of_record: dict
    bill_to: dict
    lines: list[InvoiceLine]
    discounts: list[DiscountOut]
    items_subtotal: Money
    discount_total: Money
    shipping_fee: Money
    tip: Money
    tax_total: Money
    tax_jurisdiction: str
    grand_total: Money
    payments: list[dict]
    refunds: list[dict]
    balance_after_refunds: Money


class CancellationEligibility(ApiModel):
    order_id: str
    eligible: bool
    decision: Literal["eligible", "request_only", "ineligible"]
    status: str
    reasons: list[PolicyReason]
    refund_preview: MoneyOpt
    void_preview: MoneyOpt
    policy_refs: list[str]


class CancelOrderRequest(ApiModel):
    reason_code: Literal["customer_request"] = "customer_request"
    confirmed_by_customer: bool = Field(..., description="Must be true: explicit customer confirmation")
    note: str | None = Field(None, max_length=500)


class CancelOrderResult(ApiModel):
    order_id: str
    cancelled: bool
    status: str
    voided_amount: Money
    refund_amount: Money
    refund_id: str | None
    refund_method: str | None
    expected_posting: str | None
