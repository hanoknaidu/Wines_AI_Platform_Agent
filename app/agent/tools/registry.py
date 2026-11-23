"""Agent tool catalog. Every tool = typed Pydantic input + description + one
Tool API call. The customer is NEVER an LLM-supplied parameter: it is bound
from the authenticated session, so a prompt cannot redirect a tool to another
customer's data (the Tool API enforces ownership as a second line).

Categories
  kb     in-process Knowledge Base retrieval
  read   GET Tool API (side-effect free)
  write  POST Tool API; `requires_confirmation=True` tools are gated: the LLM
         can only *propose* them, and they execute after the customer
         explicitly confirms on the next turn.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OrderId = Field(..., pattern=r"^WA-\d{6}$", description="Order number, e.g. WA-100101")
ReasonCode = Literal[
    "damaged_in_transit", "broken_on_arrival", "corked_or_flawed", "leaking",
    "wrong_item", "missing_item", "change_of_mind", "late_delivery",
]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NoInput(_In):
    pass


class OrderInput(_In):
    order_id: str = OrderId


class SearchKbInput(_In):
    query: str = Field(..., min_length=2, max_length=300, description="Natural-language policy/product question")
    category: Literal[
        "system", "taste", "region", "brand", "sparkling", "low-calorie", "organic", "non-alcoholic", "stock",
        "pricing", "discounts", "orders", "returns", "account", "general",
    ] | None = Field(None, description="Optional KB category filter (e.g. 'returns' for refund/return policy)")


class ListOrdersInput(_In):
    status: list[str] | None = Field(None, max_length=10, description="Optional order statuses to include")
    limit: int = Field(5, ge=1, le=20)


class EligibilityInput(_In):
    order_id: str = OrderId
    reason_code: ReasonCode | None = Field(None, description="What went wrong; omit to see every option")


class RmaInput(_In):
    rma_number: str = Field(..., pattern=r"^RMA-\d{6}$")


class TicketNumberInput(_In):
    ticket_number: str = Field(..., pattern=r"^TKT-\d{6}$")


class ProductSearchInput(_In):
    query: str | None = Field(None, max_length=100, description="Free text: name, brand, grape, style")
    color: Literal["red", "white", "rose", "orange"] | None = None
    wine_type: Literal["still", "sparkling", "fortified", "dessert"] | None = None
    sweetness: Literal["dry", "off_dry", "medium_sweet", "sweet"] | None = None
    body: Literal["light", "medium", "full"] | None = None
    country: str | None = Field(None, max_length=60)
    grape: str | None = Field(None, max_length=60)
    certification: str | None = Field(None, max_length=40, description="e.g. usda_organic, vegan, kosher")
    is_non_alcoholic: bool | None = None
    location: Literal["NJ", "NY"] | None = Field(None, description="Fulfilling store state; needed for price filters")
    price_max: str | None = Field(None, pattern=r"^\d{1,5}(\.\d{1,2})?$", description="Max unit price, e.g. '30'")
    in_stock_only: bool = False


class SkuInput(_In):
    sku: str = Field(..., pattern=r"^[A-Z0-9][A-Z0-9-]{2,39}$")


class InventoryInput(_In):
    sku: str = Field(..., pattern=r"^[A-Z0-9][A-Z0-9-]{2,39}$")
    location: Literal["NJ", "NY"]


class DeliveryInput(_In):
    postal_code: str = Field(..., pattern=r"^\d{5}$")
    bottles: int = Field(1, ge=1, le=120)
    subtotal: str | None = Field(None, pattern=r"^\d{1,6}(\.\d{1,2})?$")


class StoreInput(_In):
    store_code: Literal["NJ-HOB", "NY-CHE"] | None = Field(None, description="Omit to list both stores")


class TicketInput(_In):
    category: Literal[
        "order_status", "delivery_issue", "pickup_issue", "damaged_item", "flawed_wine", "wrong_or_missing_item",
        "return_request", "refund_status", "pricing_dispute", "price_match", "promo_code", "loyalty",
        "account_access", "age_verification", "privacy_request", "payment_issue", "product_question",
        "product_request", "bulk_or_event_order", "complaint", "compliance", "fraud", "general",
    ]
    priority: Literal["P1", "P2", "P3"] = "P3"
    reason_code: str | None = Field(None, max_length=40, description="Escalation-matrix reason code")
    subject: str = Field(..., min_length=3, max_length=200)
    summary: str = Field(..., min_length=10, max_length=3000, description="Handoff summary (escalation template)")
    order_id: str | None = Field(None, pattern=r"^WA-\d{6}$")
    customer_sentiment: Literal["positive", "neutral", "frustrated", "angry"] | None = None


class LineQty(_In):
    line_number: int = Field(..., ge=1, le=999)
    quantity: int = Field(..., ge=1, le=999)


class RefundInput(_In):
    order_id: str = OrderId
    reason_code: ReasonCode
    method: Literal["original_payment", "store_credit"] = "original_payment"
    items: list[LineQty] | None = Field(None, description="Lines/quantities; omit for all eligible units")
    rma_number: str | None = Field(None, pattern=r"^RMA-\d{6}$")


class ReturnInput(_In):
    order_id: str = OrderId
    reason_code: ReasonCode
    items: list[LineQty] = Field(..., min_length=1)
    remedy: Literal["refund_original_payment", "store_credit", "replacement", "redelivery"] = "refund_original_payment"
    customer_notes: str | None = Field(None, max_length=500)


class CancelInput(_In):
    order_id: str = OrderId


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_model: type[_In]
    category: Literal["kb", "read", "write"]
    method: str = "GET"
    path: Callable[[Any, str], str] | None = None  # (args, customer_number) -> path
    params: Callable[[Any], dict] | None = None
    body: Callable[[Any], dict] | None = None
    requires_confirmation: bool = False
    confirm_summary: Callable[[Any], str] | None = None

    def anthropic_schema(self) -> dict:
        schema = self.input_model.model_json_schema()
        schema.pop("title", None)
        schema.setdefault("properties", {})
        return {"name": self.name, "description": self.description, "input_schema": schema}


def _o(a) -> str:
    return a.order_id


TOOLS: list[ToolSpec] = [
    ToolSpec(
        "search_kb",
        "Search the Knowledge Base for store policy and wine knowledge (refund/return rules and windows, delivery, "
        "pickup, pricing, promotions, account, compliance, wine education). Use before explaining any policy. "
        "Never use it for live data such as prices, stock or order status.",
        SearchKbInput, "kb",
    ),
    ToolSpec("get_customer_profile", "The signed-in customer's profile: name, masked contact, home store, "
             "age-verification status.", NoInput, "read", path=lambda a, c: f"/customers/{c}"),
    ToolSpec("get_customer_addresses", "The customer's saved addresses (street masked), with restricted-destination "
             "flags.", NoInput, "read", path=lambda a, c: f"/customers/{c}/addresses"),
    ToolSpec("get_account_summary", "Loyalty points/tier/rewards, store-credit balance, saved cards (brand + last 4), "
             "open orders and tickets.", NoInput, "read", path=lambda a, c: f"/customers/{c}/account"),
    ToolSpec("list_customer_orders", "List the customer's recent orders, newest first (order number, status, total, "
             "placed and delivered dates). Use to find which order the customer means.", ListOrdersInput, "read",
             path=lambda a, c: f"/customers/{c}/orders",
             params=lambda a: {"status": a.status, "page_size": a.limit, "sort": "-placed_at"}),
    ToolSpec("get_order", "Full order details: lines, totals, discounts, fulfillment type, (masked) address, "
             "shipments, delivered date.", OrderInput, "read", path=lambda a, c: f"/orders/{_o(a)}"),
    ToolSpec("get_order_status", "Current order status with a plain-language description, payment status, ETA "
             "window and per-shipment status.", OrderInput, "read", path=lambda a, c: f"/orders/{_o(a)}/status"),
    ToolSpec("get_order_tracking", "Carrier/driver tracking: shipments, tracking URL, attempts, weather holds and "
             "tracking events.", OrderInput, "read", path=lambda a, c: f"/orders/{_o(a)}/tracking"),
    ToolSpec("get_order_items", "Order lines with ordered, shipped, delivered, returned and refunded quantities.",
             OrderInput, "read", path=lambda a, c: f"/orders/{_o(a)}/items"),
    ToolSpec("get_order_payment", "Payment information: tenders (card brand + last 4), captured, refunded, open "
             "authorization, chargeback flag.", OrderInput, "read", path=lambda a, c: f"/orders/{_o(a)}/payment"),
    ToolSpec("get_order_history", "Order status timeline.", OrderInput, "read",
             path=lambda a, c: f"/orders/{_o(a)}/history"),
    ToolSpec("get_invoice", "Invoice/receipt for an order.", OrderInput, "read",
             path=lambda a, c: f"/orders/{_o(a)}/invoice"),
    ToolSpec("check_refund_eligibility", "Policy decision on whether an order can be refunded and why (window, "
             "amount, evidence, approval needs). Read-only: it never issues a refund. Call it before discussing or "
             "requesting any refund.", EligibilityInput, "read",
             path=lambda a, c: f"/orders/{_o(a)}/refund-eligibility", params=lambda a: {"reason_code": a.reason_code}),
    ToolSpec("check_return_eligibility", "Policy decision on whether items can be returned (state rules, windows, "
             "excluded items). Read-only.", EligibilityInput, "read",
             path=lambda a, c: f"/orders/{_o(a)}/return-eligibility", params=lambda a: {"reason_code": a.reason_code}),
    ToolSpec("check_cancellation_eligibility", "Whether an order can still be cancelled, with the refund/void "
             "preview. Read-only.", OrderInput, "read", path=lambda a, c: f"/orders/{_o(a)}/cancellation-eligibility"),
    ToolSpec("get_order_refunds", "Existing refund records on an order (status incl. pending_approval/rejected, "
             "amount, method, reason).", OrderInput, "read", path=lambda a, c: f"/orders/{_o(a)}/refunds"),
    ToolSpec("get_order_returns", "Existing returns/claims (RMAs) on an order with status, eligibility and remedy.",
             OrderInput, "read", path=lambda a, c: f"/orders/{_o(a)}/returns"),
    ToolSpec("get_return_status", "One return/claim by RMA number.", RmaInput, "read",
             path=lambda a, c: f"/returns/{a.rma_number}"),
    ToolSpec("search_products", "Search sellable products with live price and availability for a location. Use "
             "for recommendations and 'do you have X'. Recommend only products this tool returns.",
             ProductSearchInput, "read", path=lambda a, c: "/products",
             params=lambda a: {"q": a.query, "color": a.color, "wine_type": a.wine_type, "sweetness": a.sweetness,
                               "body": a.body, "country": a.country, "grape": a.grape,
                               "certification": a.certification, "is_non_alcoholic": a.is_non_alcoholic,
                               "location": a.location, "price_max": a.price_max, "in_stock_only": a.in_stock_only,
                               "page_size": 6}),
    ToolSpec("get_product_details", "Full wine information for a SKU: tasting notes, taste profile, grapes, region, "
             "ABV, nutrition (with source), certifications (with evidence), accolades, prices and availability.",
             SkuInput, "read", path=lambda a, c: f"/products/{a.sku}"),
    ToolSpec("check_inventory", "Live stock status for a SKU at NJ or NY.", InventoryInput, "read",
             path=lambda a, c: f"/products/{a.sku}/availability", params=lambda a: {"location": a.location}),
    ToolSpec("get_delivery_estimate", "Pickup, local delivery and shipping options, fees and timing for a ZIP code "
             "(NJ/NY only).", DeliveryInput, "read", path=lambda a, c: "/shipping/estimate",
             params=lambda a: {"postal_code": a.postal_code, "bottles": a.bottles, "subtotal": a.subtotal}),
    ToolSpec("get_store_info", "Store address, phone, weekly hours and upcoming holiday hours.", StoreInput, "read",
             path=lambda a, c: f"/stores/{a.store_code}" if a.store_code else "/stores"),
    ToolSpec("list_support_tickets", "The customer's support tickets.", NoInput, "read",
             path=lambda a, c: f"/customers/{c}/tickets"),
    ToolSpec("get_support_ticket", "One support ticket (public messages only).", TicketNumberInput, "read",
             path=lambda a, c: f"/support/tickets/{a.ticket_number}"),
    ToolSpec("create_support_ticket", "Create a support ticket / human escalation with a handoff summary. Use for "
             "problems needing follow-up, requests for a human, or anything outside your authority. Tell the "
             "customer the ticket number and SLA.", TicketInput, "write", method="POST",
             path=lambda a, c: "/support/tickets",
             body=lambda a: {**a.model_dump(exclude_none=True), "customer_id": None}),
    ToolSpec("request_evidence_upload", "Get a secure, short-lived photo upload link for a damage/defect claim.",
             RmaInput, "write", method="POST", path=lambda a, c: f"/returns/{a.rma_number}/evidence-upload-link"),
    ToolSpec(
        "request_refund",
        "Initiate a refund. ONLY when the customer explicitly asks for the refund to be processed AND "
        "check_refund_eligibility says it is eligible. This does not execute immediately: it records a pending "
        "action and you must ask the customer to confirm amount and method.",
        RefundInput, "write", method="POST", path=lambda a, c: f"/orders/{_o(a)}/refunds",
        body=lambda a: {**a.model_dump(exclude_none=True, exclude={"order_id"}), "confirmed_by_customer": True},
        requires_confirmation=True,
        confirm_summary=lambda a: f"refund order {a.order_id} for {a.reason_code.replace('_', ' ')} "
                                  f"to {'store credit' if a.method == 'store_credit' else 'the original payment'}",
    ),
    ToolSpec(
        "create_return_request",
        "Create a return/claim (RMA). Only after explaining eligibility and the remedy, when the customer wants to "
        "proceed. Gated: requires explicit customer confirmation on the next turn.",
        ReturnInput, "write", method="POST", path=lambda a, c: f"/orders/{_o(a)}/returns",
        body=lambda a: {**a.model_dump(exclude_none=True, exclude={"order_id"}), "confirmed_by_customer": True},
        requires_confirmation=True,
        confirm_summary=lambda a: f"open a {a.reason_code.replace('_', ' ')} claim on order {a.order_id} for "
                                  + ", ".join(f"{i.quantity} x line {i.line_number}" for i in a.items),
    ),
    ToolSpec(
        "cancel_order",
        "Cancel an order. Only when the customer explicitly asks to cancel AND check_cancellation_eligibility says "
        "eligible. Gated: requires explicit customer confirmation on the next turn.",
        CancelInput, "write", method="POST", path=lambda a, c: f"/orders/{_o(a)}/cancellation",
        body=lambda a: {"reason_code": "customer_request", "confirmed_by_customer": True},
        requires_confirmation=True,
        confirm_summary=lambda a: f"cancel order {a.order_id}",
    ),
]

TOOLS_BY_NAME: dict[str, ToolSpec] = {t.name: t for t in TOOLS}


def anthropic_tool_definitions() -> list[dict]:
    """Deterministic order (prompt-cache friendly)."""
    return [t.anthropic_schema() for t in TOOLS]
