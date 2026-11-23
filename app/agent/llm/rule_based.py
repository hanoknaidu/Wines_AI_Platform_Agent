"""Deterministic planner implementing the LLMClient interface.

Used when no LLM is configured (local dev, CI, demos) and as a degraded-mode
fallback if the LLM is unavailable. It still selects tools step by step from
intent, entities and the results observed so far in the turn (it is not one
fixed sequence), and it reads the same Anthropic-format message history, so
it exercises the exact same LangGraph nodes, tool executor and Tool APIs.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from typing import Any

from app.agent.llm.base import AssistantTurn, PlannerContext, ToolCall

OPEN_STATUSES = ("placed", "age_verification_pending", "confirmed", "picking", "substitution_pending",
                 "ready_for_pickup", "on_hold", "out_for_delivery", "label_created", "in_transit",
                 "partially_fulfilled", "delivery_exception", "redelivery_scheduled")
REASON_LABEL = {
    "damaged_in_transit": "damaged in transit", "broken_on_arrival": "broken bottle", "leaking": "leaking bottle",
    "corked_or_flawed": "corked or flawed wine", "wrong_item": "wrong item", "missing_item": "missing item",
    "change_of_mind": "change of mind", "late_delivery": "late delivery",
}
INTENT_REASON = {"claim.flawed_wine": "corked_or_flawed", "claim.damaged": "broken_on_arrival",
                 "return.change_of_mind": "change_of_mind"}


def _date(value: str | None) -> str:
    if not value:
        return "an unknown date"
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return f"{d:%B} {d.day}, {d.year}"
    except ValueError:
        return value


class _Turn:
    """Observations gathered since the customer's latest message."""

    def __init__(self, messages: list[dict]) -> None:
        self.user_text = ""
        self.results: dict[str, list[Any]] = {}
        self.errors: dict[str, dict] = {}
        start = 0
        for idx, msg in enumerate(messages):
            if msg["role"] == "user" and _has_text(msg):
                start = idx
                self.user_text = _text_of(msg)
        names: dict[str, str] = {}
        for msg in messages[start:]:
            for block in _blocks(msg):
                btype = _get(block, "type")
                if btype == "tool_use":
                    names[_get(block, "id")] = _get(block, "name")
                elif btype == "tool_result":
                    name = names.get(_get(block, "tool_use_id"), "?")
                    try:
                        data = json.loads(_get(block, "content") or "null")
                    except (TypeError, ValueError):
                        data = None
                    if _get(block, "is_error"):
                        self.errors[name] = data or {}
                    self.results.setdefault(name, []).append(data)

    def done(self, name: str) -> bool:
        return name in self.results

    def get(self, name: str) -> Any:
        return self.results.get(name, [None])[-1]


def _blocks(msg: dict) -> list:
    content = msg.get("content")
    return content if isinstance(content, list) else [{"type": "text", "text": content or ""}]


def _get(block, key):
    return block.get(key) if isinstance(block, dict) else getattr(block, key, None)


def _has_text(msg: dict) -> bool:
    return any(_get(b, "type") == "text" and (_get(b, "text") or "").strip() for b in _blocks(msg))


def _text_of(msg: dict) -> str:
    return " ".join(_get(b, "text") for b in _blocks(msg)
                    if _get(b, "type") == "text" and not (_get(b, "text") or "").startswith("<context>"))


class RuleBasedPlanner:
    provider = "rule_based"
    model = "rule-based-planner-v1"

    async def complete(self, system: str, messages: list[dict], tools: list[dict],
                       context: PlannerContext) -> AssistantTurn:
        turn = _Turn(messages)
        step = self._plan(context, turn)
        if isinstance(step, str):
            return AssistantTurn(text=step, tool_calls=[], stop_reason="end_turn",
                                 raw_content=[{"type": "text", "text": step}], model=self.model)
        calls = [ToolCall(f"toolu_rb_{uuid.uuid4().hex[:20]}", name, args) for name, args in step]
        raw = [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.input} for c in calls]
        return AssistantTurn(text="", tool_calls=calls, stop_reason="tool_use", raw_content=raw, model=self.model,
                             tool_selection_note=f"rule plan for {context.intent}: {', '.join(c.name for c in calls)}")

    # ------------------------------------------------------------------ planning
    def _plan(self, ctx: PlannerContext, t: _Turn):
        e = ctx.entities
        if ctx.executed_action is not None:
            return self._after_action(ctx.executed_action)
        if ctx.action_declined:
            return "No problem, I haven't made any changes. Is there anything else I can help with?"
        intent = ctx.intent
        if intent == "chitchat":
            return ("Hi! I can help with your orders, deliveries, returns and refunds, and I can suggest wines. "
                    "What can I do for you?")
        if intent in ("order.status",):
            return self._order_status(ctx, t)
        if intent in ("refund.request", "claim.damaged", "claim.flawed_wine"):
            return self._refund_flow(ctx, t)
        if intent == "claim.wrong_or_missing":
            return self._wrong_item(ctx, t)
        if intent == "return.change_of_mind":
            return self._return_flow(ctx, t)
        if intent == "refund.status":
            return self._refund_status(ctx, t)
        if intent == "policy.returns_refunds":
            return self._kb_answer(t, "returns", "refund return policy rules windows methods")
        if intent == "order.cancel":
            return self._cancel_flow(ctx, t)
        if intent == "payment.invoice":
            return self._payment(ctx, t)
        if intent == "loyalty.balance":
            if not t.done("get_account_summary"):
                return [("get_account_summary", {})]
            return self._account(t.get("get_account_summary"))
        if intent == "account.update_profile":
            if not t.done("get_customer_addresses"):
                return [("get_customer_addresses", {})]
            return self._addresses(t.get("get_customer_addresses"))
        if intent == "delivery.eligibility":
            if not e.get("postal_code"):
                return "Sure! What's the 5-digit ZIP code you'd like us to deliver to? We serve New Jersey and New York."
            if not t.done("get_delivery_estimate"):
                return [("get_delivery_estimate", {"postal_code": e["postal_code"]})]
            return self._delivery(t.get("get_delivery_estimate"))
        if intent == "store.info":
            if not t.done("get_store_info"):
                code = {"NJ": "NJ-HOB", "NY": "NY-CHE"}.get(e.get("location"))
                return [("get_store_info", {"store_code": code} if code else {})]
            return self._stores(t.get("get_store_info"))
        if intent.startswith("recommend"):
            return self._products(ctx, t)
        if intent == "human.request":
            return self._human(ctx, t)
        return self._kb_answer(t, None, t.user_text)

    # --- order resolution -----------------------------------------------------------
    def _resolve_order(self, ctx: PlannerContext, t: _Turn, prefer: str):
        """Return an order number, a tool step to look one up, or None."""
        if ctx.entities.get("order_ids"):
            return ctx.entities["order_ids"][0]
        if not t.done("list_customer_orders"):
            return [("list_customer_orders", {"limit": 10})]
        page = t.get("list_customer_orders") or {}
        orders = page.get("items", []) if isinstance(page, dict) else []
        if not orders:
            return None
        if prefer == "delivered":
            pick = [o for o in orders if o.get("delivered_at")]
        elif prefer == "open":
            pick = [o for o in orders if o["status"] in OPEN_STATUSES]
        elif prefer == "refunded":
            pick = [o for o in orders if o["payment_status"] in ("refunded", "partially_refunded")]
        else:
            pick = [o for o in orders if o["status"] != "cancelled"]
        return (pick or orders)[0]["order_id"]

    # --- flows ------------------------------------------------------------------------
    def _order_status(self, ctx, t):
        order = self._resolve_order(ctx, t, "open")
        if isinstance(order, list):
            return order
        if order is None:
            return "I couldn't find any orders on your account. Is it possible it was placed under another email?"
        if not t.done("get_order_status"):
            return [("get_order_status", {"order_id": order})]
        status = t.get("get_order_status")
        if "get_order_status" in t.errors:
            return self._tool_error(t.errors["get_order_status"])
        shipped = status.get("shipments") and status["status"] not in ("placed", "confirmed", "picking",
                                                                       "age_verification_pending")
        if shipped and not t.done("get_order_tracking"):
            return [("get_order_tracking", {"order_id": order})]
        return self._compose_status(status, t.get("get_order_tracking"))

    def _refund_flow(self, ctx, t):
        e = ctx.entities
        reason = e.get("reason_code") or INTENT_REASON.get(ctx.intent)
        order = self._resolve_order(ctx, t, "delivered")
        if isinstance(order, list):
            return order
        if order is None:
            return "I couldn't find an order on your account to refund. Could you share the order number (WA-…)?"
        steps = []
        if not t.done("get_order"):
            steps.append(("get_order", {"order_id": order}))
        if not t.done("search_kb"):
            steps.append(("search_kb", {"query": f"refund policy {REASON_LABEL.get(reason, '')} window evidence",
                                        "category": "returns"}))
        if not t.done("check_refund_eligibility"):
            steps.append(("check_refund_eligibility", {"order_id": order, **({"reason_code": reason} if reason else {})}))
        if steps:
            return steps
        if "get_order" in t.errors:
            return self._tool_error(t.errors["get_order"])
        elig = t.get("check_refund_eligibility") or {}
        if "check_refund_eligibility" in t.errors:
            return self._tool_error(t.errors["check_refund_eligibility"])
        wants = e.get("wants_action")
        if wants and reason and elig.get("eligible") and not t.done("request_refund") \
                and not t.done("create_return_request"):
            approvals = elig.get("approval_reasons", [])
            if "evidence_required" in approvals:
                items = [{"line_number": i["line_number"], "quantity": i["refundable_quantity"]}
                         for i in elig.get("eligible_items", [])]
                return [("create_return_request", {"order_id": order, "reason_code": reason, "items": items})]
            return [("request_refund", {"order_id": order, "reason_code": reason,
                                        "method": e.get("refund_method", "original_payment")})]
        gated = t.get("request_refund") or t.get("create_return_request")
        return self._compose_eligibility(order, elig, reason, gated, t.get("search_kb"))

    def _wrong_item(self, ctx, t):
        if ctx.entities.get("wants_action"):
            # Explicit "please refund me": eligibility -> gated refund instead of a ticket.
            return self._refund_flow(ctx, t)
        reason = ctx.entities.get("reason_code", "wrong_item")
        order = self._resolve_order(ctx, t, "delivered")
        if isinstance(order, list):
            return order
        if order is None:
            return "Which order was this? Please share the order number (WA-…) and I'll sort it out."
        steps = []
        if not t.done("get_order"):
            steps.append(("get_order", {"order_id": order}))
        if not t.done("get_order_items"):
            steps.append(("get_order_items", {"order_id": order}))
        if not t.done("check_refund_eligibility"):
            steps.append(("check_refund_eligibility", {"order_id": order, "reason_code": reason}))
        if steps:
            return steps
        elig = t.get("check_refund_eligibility") or {}
        if not t.done("create_support_ticket"):
            if not elig.get("eligible"):
                return self._compose_eligibility(order, elig, reason, None, None)
            items = t.get("get_order_items") or []
            lines = "; ".join(f"line {i['line_number']}: {i['quantity']} x {i['product_name']}" for i in items[:6])
            return [("create_support_ticket", {
                "category": "wrong_or_missing_item", "priority": "P3", "order_id": order,
                "subject": f"{REASON_LABEL[reason].capitalize()} reported on {order}",
                "summary": f"Customer reports a {REASON_LABEL[reason]} on {order}. Order lines: {lines}. "
                           f"Eligibility: {elig.get('decision')} (window ends {elig.get('window_ends_at')}). "
                           "Arrange correction: redelivery or refund, free return pickup for wrong items (A-31).",
            })]
        ticket = t.get("create_support_ticket") or {}
        if "create_support_ticket" in t.errors:
            return self._tool_error(t.errors["create_support_ticket"])
        return (f"I'm sorry about the {REASON_LABEL[reason]} on order {order}. I've opened ticket "
                f"{ticket.get('ticket_number')} so our team can make it right at no cost: we can redeliver the "
                f"correct wine or refund it (up to ${elig.get('max_refundable_amount')}), and a wrong bottle is "
                f"picked up free. You'll hear back by {_date(ticket.get('sla_due_at'))}. Would you prefer a "
                "redelivery or a refund?")

    def _return_flow(self, ctx, t):
        reason = ctx.entities.get("reason_code") or "change_of_mind"
        order = self._resolve_order(ctx, t, "delivered")
        if isinstance(order, list):
            return order
        if order is None:
            return "Which order would you like to return? Please share the order number (WA-…)."
        steps = []
        if not t.done("get_order"):
            steps.append(("get_order", {"order_id": order}))
        if not t.done("check_return_eligibility"):
            steps.append(("check_return_eligibility", {"order_id": order, "reason_code": reason}))
        if not t.done("search_kb"):
            steps.append(("search_kb", {"query": "return policy change of mind unopened restocking fee",
                                        "category": "returns"}))
        if steps:
            return steps
        return self._compose_eligibility(order, t.get("check_return_eligibility") or {}, reason, None,
                                         t.get("search_kb"), noun="return")

    def _refund_status(self, ctx, t):
        order = self._resolve_order(ctx, t, "refunded")
        if isinstance(order, list):
            return order
        if order is None:
            return "I couldn't find a refund on your account. Could you share the order number?"
        steps = []
        if not t.done("get_order_refunds"):
            steps.append(("get_order_refunds", {"order_id": order}))
        if not t.done("get_order_returns"):
            steps.append(("get_order_returns", {"order_id": order}))
        if not t.done("search_kb"):
            steps.append(("search_kb", {"query": "refund timing posting rejected claim ineligible window",
                                        "category": "returns"}))
        if steps:
            return steps
        refunds = t.get("get_order_refunds") or []
        returns = t.get("get_order_returns") or []
        rejected = [r for r in returns if r.get("status") == "rejected" or r.get("eligibility") == "ineligible"]
        parts = []
        for r in refunds:
            line = f"- {r['refund_id']}: ${r['amount']} ({r['customer_facing_reason'].lower()}), status {r['status']}"
            if r["status"] == "pending_approval":
                line += " (waiting for a team member's approval)"
            elif r.get("expected_posting"):
                line += f". {r['expected_posting']}"
            parts.append(line)
        for r in rejected:
            parts.append(f"- Claim {r['rma_number']} was not approved: {r.get('ineligible_reason') or 'outside policy'}.")
        if not parts:
            return f"There are no refunds or claims on order {order} yet. Would you like me to check refund options?"
        return (f"Here's what I see for order {order}:\n" + "\n".join(parts)
                + "\nIf a card refund hasn't posted within 10 business days, I can ask our finance team for a trace.")

    def _cancel_flow(self, ctx, t):
        order = self._resolve_order(ctx, t, "open")
        if isinstance(order, list):
            return order
        if order is None:
            return "I don't see any open orders to cancel. Could you share the order number?"
        if not t.done("check_cancellation_eligibility"):
            return [("check_cancellation_eligibility", {"order_id": order})]
        elig = t.get("check_cancellation_eligibility") or {}
        if "check_cancellation_eligibility" in t.errors:
            return self._tool_error(t.errors["check_cancellation_eligibility"])
        if elig.get("eligible") and ctx.entities.get("wants_action") and not t.done("cancel_order"):
            return [("cancel_order", {"order_id": order})]
        reason = (elig.get("reasons") or [{}])[0].get("message", "")
        if t.done("cancel_order"):
            refund = elig.get("refund_preview") or "0.00"
            return (f"Order {order} hasn't started packing, so it can be cancelled free of charge. "
                    f"{'You will be refunded $' + refund + ' to your original payment. ' if refund != '0.00' else 'The pending card authorization will simply be released. '}"
                    "Shall I go ahead and cancel it? Please reply \"yes\" to confirm.")
        if elig.get("eligible"):
            return f"Good news: order {order} can still be cancelled free of charge. {reason} Would you like me to cancel it?"
        return f"I'm afraid order {order} can't be cancelled right now. {reason}"

    def _payment(self, ctx, t):
        order = self._resolve_order(ctx, t, "any")
        if isinstance(order, list):
            return order
        if order is None:
            return "Which order is this about? Please share the order number."
        wants_invoice = bool(re.search(r"invoice|receipt", t.user_text, re.I))
        tool = "get_invoice" if wants_invoice else "get_order_payment"
        if not t.done(tool):
            return [(tool, {"order_id": order})]
        data = t.get(tool) or {}
        if wants_invoice:
            return (f"Here's the receipt summary for {order}: items ${data['items_subtotal']}, discounts "
                    f"-${data['discount_total']}, delivery ${data['shipping_fee']}, tax ${data['tax_total']}, "
                    f"total ${data['grand_total']}. Seller of record: {data['seller_of_record']['legal_name']}.")
        tenders = ", ".join(f"{p['card_brand'] or p['tender_type']} {('ending ' + p['card_last4']) if p['card_last4'] else ''}"
                            f" ${p['amount']}".replace("  ", " ") for p in data.get("tenders", []))
        return (f"Order {order} total ${data['grand_total']}, paid with {tenders}. Captured so far: "
                f"${data['captured_total']}; refunded: ${data['refunded_total']}."
                + (" A card dispute is open on this order, so our finance team is handling it." if data.get("chargeback_open") else ""))

    def _products(self, ctx, t):
        text = t.user_text.lower()
        args: dict[str, Any] = {}
        for color in ("red", "white", "rose", "orange"):
            if re.search(rf"\b{color}\b", text) or (color == "rose" and "rosé" in text):
                args["color"] = color
        if re.search(r"sparkling|champagne|prosecco|bubbl", text):
            args["wine_type"] = "sparkling"
        if "non-alcoholic" in text or "non alcoholic" in text or "alcohol-free" in text:
            args["is_non_alcoholic"] = True
        if "organic" in text:
            args["certification"] = "usda_organic"
        m = re.search(r"under \$?(\d{1,4})", text)
        location = ctx.entities.get("location")
        if not location:
            if not t.done("get_customer_profile"):
                return [("get_customer_profile", {})]
            profile = t.get("get_customer_profile") or {}
            location = (profile.get("home_store") or {}).get("state_code", "NJ")
        args["location"] = location
        if m:
            args["price_max"] = m.group(1)
        for grape in ("cabernet", "pinot noir", "pinot grigio", "chardonnay", "sauvignon blanc", "malbec",
                      "riesling", "merlot", "syrah", "tempranillo"):
            if grape in text:
                args["grape"] = grape
        if not t.done("search_products"):
            return [("search_products", args)]
        page = t.get("search_products") or {}
        items = page.get("items", [])
        if not items:
            return ("I couldn't find a match for that right now. I can set up a back-in-stock alert or suggest "
                    "something close. What style do you usually enjoy?")
        lines = []
        for p in items[:4]:
            price = p.get("price") or {}
            avail = (p.get("availability") or {}).get("stock_status", "unknown").replace("_", " ")
            name = p["name"] if p["name"].startswith(p["brand"]) else f"{p['brand']} {p['name']}"
            lines.append(f"- {name} {p.get('vintage') or 'NV'} ({p['size_ml']} ml): "
                         f"${price.get('unit_price', '?')}, {avail}")
        intro = ("We sell wine from around the world (still, sparkling, dessert, organic and non-alcoholic), "
                 "plus some spirits. A few picks" if not args.keys() - {"location"} else "Here are a few options")
        return f"{intro} from our {location} store:\n" + "\n".join(lines) + \
            "\nWould you like details on any of these, or a different style or budget?"

    def _human(self, ctx, t):
        if not t.done("create_support_ticket"):
            return [("create_support_ticket", {
                "category": "general", "priority": "P2", "reason_code": "customer_requested_human",
                "subject": "Customer asked to speak with a person",
                "summary": f"Customer: {ctx.customer_number}. Intent: human.request. Message: {t.user_text[:500]}. "
                           "Why escalated: customer requested a human.",
            })]
        ticket = t.get("create_support_ticket") or {}
        return (f"Of course. I've passed this to our support team (ticket {ticket.get('ticket_number')}). "
                f"Someone will reach out by {_date(ticket.get('sla_due_at'))}; our team is available 9 am-9 pm ET, "
                "and they'll see everything we've discussed.")

    def _kb_answer(self, t, category, query):
        if not t.done("search_kb"):
            return [("search_kb", {"query": query[:300], **({"category": category} if category else {})})]
        hits = (t.get("search_kb") or {}).get("results", [])
        if not hits:
            return ("I don't have a confirmed answer for that. Would you like me to open a ticket so our team can "
                    "follow up?")
        # KB docs are written for agents; prefer customer-facing rule sections.
        top = next((h for h in hits if re.search(r"rule|polic|method|what|window", h["section"], re.I)), hits[0])
        text = re.sub(r"\((?:[a-z]+_[a-z_]+[^)]*)\)", "", top["text"])  # drop internal tool names
        excerpt = re.sub(r"\s+", " ", re.sub(r"[#*|`>]", "", text)).strip()[:700]
        return f"Here's what our policy says ({top['title']}, {top['section']}):\n{excerpt}"

    # --- composition ------------------------------------------------------------------
    @staticmethod
    def _tool_error(err: dict) -> str:
        if err.get("error_code") in ("ORDER_NOT_FOUND", "NOT_FOUND"):
            return "I couldn't find that order on your account. Could you double-check the order number?"
        return ("I couldn't confirm that right now. I don't want to guess, so would you like me to try again or "
                "open a ticket for our team?")

    @staticmethod
    def _compose_status(status: dict, tracking: dict | None) -> str:
        text = f"Your order {status['order_id']} is **{status['status'].replace('_', ' ')}**: {status['status_description']}"
        if status.get("eta_window_start") and status["status"] in ("out_for_delivery", "redelivery_scheduled"):
            text += f" Expected between {status['eta_window_start'][11:16]} and {status['eta_window_end'][11:16]} UTC."
        if tracking:
            for s in tracking.get("shipments", []):
                last = (s.get("events") or [{}])[-1]
                bit = f"\n- Shipment {s['shipment_number']} ({s['carrier'] or s['method']}): {s['status'].replace('_', ' ')}"
                if last.get("description"):
                    bit += f"; latest update: {last['description']}"
                if s.get("tracking_url"):
                    bit += f" (track: {s['tracking_url']})"
                if s.get("weather_hold"):
                    bit += " (held for weather to protect the wine)"
                text += bit
        return text + "\nAn adult 21+ with ID needs to receive it."

    @staticmethod
    def _compose_eligibility(order, elig: dict, reason, gated, kb, noun: str = "refund") -> str:
        reasons = [r["message"] for r in elig.get("reasons", [])]
        if gated and gated.get("status") == "confirmation_required":
            amount = elig.get("max_refundable_amount")
            extra = (" A team member will need to approve it before it's paid out."
                     if elig.get("requires_human_approval") else "")
            return (f"Order {order} is eligible: {reasons[0] if reasons else ''} I can {gated['summary']}"
                    f"{' for $' + amount if amount and noun == 'refund' else ''}.{extra} "
                    "Shall I go ahead? Please reply \"yes\" to confirm.")
        decision = elig.get("decision")
        if decision == "cancel_instead":
            return f"Order {order} hasn't been delivered yet, so it can be cancelled instead of refunded. Would you like me to check that?"
        if not elig.get("eligible"):
            body = " ".join(reasons) or f"This order isn't eligible for a {noun}."
            steps = elig.get("next_steps") or []
            hint = " If something else went wrong (damaged, faulty or wrong item), let me know." if reason == "change_of_mind" else ""
            return f"I checked order {order}. {body}{hint}" + (f" {steps[0]}" if steps and "escalate" in steps[0].lower() else "")
        if reason is None:
            options = [o["reason_code"].replace("_", " ") for o in elig.get("reason_options", []) if o["eligible"]]
            return (f"I can help with order {order}. Refund options depend on what happened. Right now these are "
                    f"still open: {', '.join(options)}. What went wrong with the order?")
        amount = elig.get("max_refundable_amount")
        msg = f"Good news: order {order} is eligible for a {noun} for the {REASON_LABEL.get(reason, reason)}"
        msg += f", up to ${amount}." if amount else "."
        if elig.get("requires_human_approval"):
            why = {"refund_over_limit": "it's over $150", "evidence_required": "we need photos of the issue first",
                   "claim_review": "it's a second claim within 60 days", "collectible_dispute": "it's a collectible vintage"}
            msg += " A team member will need to approve it because " + " and ".join(
                why.get(a, a) for a in elig.get("approval_reasons", [])) + "."
        if elig.get("restocking_fee_bps"):
            msg += " You can choose full value as store credit, or a refund to your card minus a 15% restocking fee."
        return msg + f" Would you like me to start the {noun}?"

    @staticmethod
    def _after_action(action: dict) -> str:
        result, tool, ok = action.get("result") or {}, action.get("tool"), action.get("ok")
        if not ok:
            msg = result.get("message", "it couldn't be completed")
            return (f"I wasn't able to complete that: {msg} Nothing was changed. Would you like me to open a ticket "
                    "for our team?")
        if tool == "request_refund":
            refund = result.get("refund", {})
            if result.get("requires_human_approval"):
                return (f"I've submitted refund {refund.get('refund_id')} for ${refund.get('amount')}. It needs a "
                        f"team member's approval (ticket {result.get('ticket_number')}), and you'll hear back within "
                        "4 business hours.")
            return (f"Done: refund {refund.get('refund_id')} for ${refund.get('amount')} has been issued. "
                    f"{refund.get('expected_posting', '')}")
        if tool == "create_return_request":
            rma = result.get("rma", {})
            steps = " ".join(result.get("next_steps", [])[:2])
            return f"Your claim {rma.get('rma_number')} is open ({result.get('eligibility', '').replace('_', ' ')}). {steps}"
        if tool == "cancel_order":
            refund = result.get("refund_amount", "0.00")
            tail = (f"A refund of ${refund} is on its way ({result.get('expected_posting')})" if refund != "0.00"
                    else result.get("expected_posting", ""))
            return f"Order {result.get('order_id')} is cancelled. {tail}"
        return "Done."

    @staticmethod
    def _account(a: dict) -> str:
        loyalty = a.get("loyalty", {})
        rewards = loyalty.get("available_rewards", [])
        text = (f"You have {loyalty.get('points', 0)} Rewards points ({loyalty.get('tier') or 'not enrolled'} tier) "
                f"and ${a.get('store_credit_balance')} in store credit.")
        if rewards:
            text += " Available rewards: " + ", ".join(f"${r['value']} (expires {_date(r['expires_at'])})" for r in rewards) + "."
        return text

    @staticmethod
    def _addresses(items: list) -> str:
        if not items:
            return "You don't have any saved addresses yet."
        lines = [f"- {a.get('label') or 'Address'}: {a['line1']}, {a['city']}, {a['state_code']} {a['postal_code']}"
                 + (" (can't be used for delivery)" if a["restricted_destination"] or not a["deliverable_state"] else "")
                 for a in items]
        return "Here are your saved addresses:\n" + "\n".join(lines) + "\nYou can edit them in your account settings."

    @staticmethod
    def _delivery(d: dict) -> str:
        if not d.get("serviceable"):
            return d.get("reason") or "Sorry, we can only deliver within New Jersey and New York."
        parts = []
        for o in d.get("options", []):
            fee = "free" if o.get("fee") in ("0.00", None) else f"${o['fee']}"
            parts.append(f"- {o['type'].replace('_', ' ').title()}: {fee}; {o['estimate']}")
        return (f"Yes, {d['postal_code']} is served by our {d['fulfilling_store']} store:\n" + "\n".join(parts)
                + "\nSomeone 21+ with ID must receive alcohol deliveries.")

    @staticmethod
    def _stores(data) -> str:
        stores = data if isinstance(data, list) else [data]
        out = []
        for s in stores:
            hours = "; ".join(f"{h['day'][:3]} {h['opens_at']}-{h['closes_at']}" for h in s.get("hours", []))
            exc = "; ".join(f"{x['date']}: {'closed' if x['is_closed'] else x['opens_at'] + '-' + x['closes_at']}"
                            f" ({x['note']})" for x in s.get("upcoming_exceptions", [])[:3])
            out.append(f"**{s['name']}**, {s['address']}. Hours: {hours}." + (f" Upcoming: {exc}." if exc else ""))
        return "\n".join(out)
