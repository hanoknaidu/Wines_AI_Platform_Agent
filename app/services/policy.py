"""Refund / return / cancellation policy engine.

Pure functions over a fully loaded order (no I/O), so every rule is unit
testable. Each rule cites its KB source:

  A-21 cancellation before picking      A-25 pre-arrival cancellation (14 days)
  A-30 damage: 48 h + photo             A-31 wrong/missing: 7 days
  A-32 defective: 30 days               A-33 older-vintage / collectible: review
  A-34 NJ change of mind: 14 days, unopened, 15% restocking to card
  A-35 NY: no change-of-mind returns    A-60 agent refund limit $150 / order
  A-62 human approval: no evidence, 2nd claim in 60 days, over limit
  RF-R5 open chargeback: no refunds     RTN-R4 never-returnable items
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.core.money import cents_to_str, pct_of, prorate
from app.models import OrderItem, ProductListing
from app.schemas.common import PolicyReason
from app.schemas.order import CancellationEligibility
from app.schemas.refund import EligibilityResult, EligibleItem, ReasonOption
from app.services.order_facts import OrderFacts


@dataclass(frozen=True)
class ClaimRule:
    window: timedelta | None
    policy_ref: str
    evidence_required: bool
    label: str


RULES: dict[str, ClaimRule] = {
    "damaged_in_transit": ClaimRule(timedelta(hours=48), "A-30", True, "damaged in transit"),
    "broken_on_arrival": ClaimRule(timedelta(hours=48), "A-30", True, "broken on arrival"),
    "wrong_item": ClaimRule(timedelta(days=7), "A-31", False, "wrong item"),
    "missing_item": ClaimRule(timedelta(days=7), "A-31", False, "missing item"),
    "corked_or_flawed": ClaimRule(timedelta(days=30), "A-32", True, "corked or flawed wine"),
    "leaking": ClaimRule(timedelta(days=30), "A-32", True, "leaking bottle"),
    "change_of_mind": ClaimRule(timedelta(days=14), "A-34", False, "change of mind (unopened)"),
    "late_delivery": ClaimRule(None, "A-61", False, "late delivery"),
}
CLAIM_REASONS = tuple(r for r in RULES if r not in ("change_of_mind", "late_delivery"))
RESTOCKING_FEE_BPS = 1500  # A-34
SECOND_CLAIM_WINDOW = timedelta(days=60)  # A-60 / A-62
OLDER_VINTAGE_YEARS = 10  # A-33

NOT_DELIVERED_CANCELLABLE = (
    "placed", "age_verification_pending", "confirmed", "substitution_pending", "on_hold", "ready_for_pickup",
)
FREE_CANCEL_STATUSES = ("placed", "age_verification_pending", "confirmed", "substitution_pending", "ready_for_pickup")
STAGED_SHIPMENT_STATUSES = ("pending", "picking", "packed", "ready_for_pickup")
REQUEST_ONLY_STATUSES = ("picking",)
DISPATCHED_STATUSES = (
    "out_for_delivery", "label_created", "in_transit", "partially_fulfilled", "delivery_exception",
    "delivery_failed", "redelivery_scheduled",
)


@dataclass
class QuoteLine:
    item: OrderItem
    quantity: int
    amount_cents: int  # items + tax for this line
    tax_cents: int


@dataclass
class RefundQuote:
    lines: list[QuoteLine] = field(default_factory=list)
    shipping_cents: int = 0  # fee + tax on the fee
    restocking_fee_cents: int = 0

    @property
    def items_cents(self) -> int:
        return sum(ql.amount_cents - ql.tax_cents for ql in self.lines)

    @property
    def tax_cents(self) -> int:
        return sum(ql.tax_cents for ql in self.lines)

    @property
    def total_cents(self) -> int:
        return self.items_cents + self.tax_cents + self.shipping_cents - self.restocking_fee_cents


@dataclass
class ClaimEvaluation:
    result: EligibilityResult
    quote: RefundQuote | None


def _r(code: str, message: str, ref: str | None = None) -> PolicyReason:
    return PolicyReason(code=code, message=message, policy_ref=ref)


class PolicyEngine:
    def __init__(self, now: datetime, agent_refund_limit_cents: int = 15000) -> None:
        self.now = now
        self.limit = agent_refund_limit_cents

    # ------------------------------------------------------------------ helpers
    def _excluded_for_change_of_mind(self, item: OrderItem, listing: ProductListing | None) -> str | None:
        """RTN-R4: items never returnable for change of mind."""
        variant = item.variant
        if item.is_final_sale:
            return "final sale"
        if variant is not None and variant.is_collectible:
            return "collectible / library wine"
        if item.size_ml >= 3000:
            return "large format (3 L or more)"
        if item.vintage_year and self.now.year - item.vintage_year > OLDER_VINTAGE_YEARS:
            return "older vintage sold as-is"
        if listing is not None:
            if listing.listing_status in ("pre_arrival", "special_order"):
                return listing.listing_status.replace("_", "-")
            if listing.allocation_limit is not None:
                return "allocated item"
        return None

    def _is_collectible(self, item: OrderItem) -> bool:
        older = bool(item.vintage_year and self.now.year - item.vintage_year > OLDER_VINTAGE_YEARS)
        return older or bool(item.variant is not None and item.variant.is_collectible)

    def _window_end(self, facts: OrderFacts, rule: ClaimRule) -> datetime | None:
        if facts.delivered_at is None or rule.window is None:
            return None
        return facts.delivered_at + rule.window

    def _gates(self, facts: OrderFacts, mode: str) -> tuple[str, list[PolicyReason], list[str]] | None:
        """Order-level blockers that apply before any reason-specific rule."""
        order = facts.order
        if mode == "refund" and facts.chargeback_open:
            return (
                "requires_review",
                [_r("CHARGEBACK_OPEN", "A card dispute (chargeback) is open on this order, so no refund can be "
                    "issued here; our finance team resolves it through the dispute.", "RF-R5")],
                ["Escalate to finance (P2, reason chargeback_open). Do not issue a refund."],
            )
        if order.status == "cancelled":
            return (
                "ineligible",
                [_r("ORDER_CANCELLED", "This order was cancelled; its refund was handled with the cancellation.",
                    "OC-R1")],
                ["Check existing refunds on the order."],
            )
        if facts.delivered_units == 0:
            if order.status in NOT_DELIVERED_CANCELLABLE or order.status == "picking":
                return (
                    "cancel_instead",
                    [_r("NOT_YET_FULFILLED", "This order hasn't been delivered or picked up yet, so it can be "
                        "cancelled instead of refunded.", "A-21")],
                    ["Check cancellation eligibility for this order."],
                )
            return (
                "ineligible",
                [_r("NOT_YET_DELIVERED", "This order is on its way and hasn't been delivered yet. Refund options "
                    "open once it arrives; if delivery fails, failed-delivery rules apply.", "A-17")],
                ["Share tracking; if the delivery fails, explain redelivery or refund minus fees (A-17/A-18)."],
            )
        if mode == "refund" and facts.remaining_refundable_cents <= 0:
            if facts.active_refunds_cents > 0:
                return ("ineligible", [_r("FULLY_REFUNDED", "This order has already been fully refunded, or the "
                                          "rest of it is already in a refund awaiting approval.")],
                        ["Check existing refunds on the order."])
            return ("ineligible", [_r("NOTHING_CAPTURED", "No payment has been collected on this order yet.")], [])
        return None

    def _unit_capacity(self, facts: OrderFacts, mode: str) -> dict[int, int]:
        """Units still claimable per line_number. A unit already refunded or
        already on an open return can't be claimed again (max, not sum: a
        return's own refund covers the same units)."""
        return {
            lf.item.line_number: max(lf.delivered - max(lf.refunded_qty, lf.returned), 0)
            for lf in facts.lines.values()
        }

    def _quote(
        self,
        facts: OrderFacts,
        selection: dict[int, int],
        reason_code: str,
        method: str,
    ) -> RefundQuote:
        by_line = facts.by_line_number()
        quote = RefundQuote()
        for line_number, qty in sorted(selection.items()):
            lf = by_line[line_number]
            amount = min(lf.item.unit_net_cents(qty), lf.remaining_line_cents)
            tax = min(prorate(lf.item.tax_cents, qty, lf.item.quantity), amount)
            if amount > 0:
                quote.lines.append(QuoteLine(lf.item, qty, amount, tax))
        all_units = {lf.item.line_number: lf.delivered for lf in facts.lines.values()}
        whole_order = (
            reason_code in CLAIM_REASONS
            and facts.active_refunds_cents == 0
            and all(selection.get(n, 0) >= q for n, q in all_units.items())
            and all(lf.delivered == lf.item.quantity - lf.item.quantity_cancelled for lf in facts.lines.values())
        )
        if whole_order:  # refunds-and-store-credit.md §2: fee refunded if the whole order was affected
            quote.shipping_cents = facts.order.shipping_fee_cents + facts.fee_tax_cents
        if reason_code == "change_of_mind" and method == "original_payment":
            quote.restocking_fee_cents = pct_of(quote.items_cents + quote.tax_cents, RESTOCKING_FEE_BPS)
        overflow = quote.total_cents - facts.remaining_refundable_cents
        if overflow > 0:  # never exceed what is left on the order
            quote.shipping_cents = max(quote.shipping_cents - overflow, 0)
        return quote

    def _reason_options(self, facts: OrderFacts) -> list[ReasonOption]:
        options = []
        for code, rule in RULES.items():
            end = self._window_end(facts, rule)
            if code == "late_delivery":
                options.append(ReasonOption(reason_code=code, eligible=False, window_ends_at=None,
                                            note="Not refundable; goodwill store credit up to $15 may apply (A-61)."))
                continue
            if code == "change_of_mind" and facts.state_code == "NY":
                options.append(ReasonOption(reason_code=code, eligible=False, window_ends_at=None,
                                            note="NY Store: change-of-mind returns are not accepted (A-35)."))
                continue
            open_ = end is not None and self.now <= end
            note = f"Report within {_human(rule.window)} of delivery ({rule.policy_ref})"
            if rule.evidence_required:
                note += "; photos required"
            options.append(ReasonOption(reason_code=code, eligible=open_, window_ends_at=end, note=note))
        return options

    # ------------------------------------------------------------------ public
    def evaluate_claim(
        self,
        facts: OrderFacts,
        listings: dict[int, ProductListing],
        *,
        mode: str,  # "refund" | "return"
        reason_code: str | None,
        selection: dict[int, int] | None = None,
        method: str = "original_payment",
        recent_claims: int = 0,
        evidence_on_file: bool = False,
        is_staff: bool = False,
    ) -> ClaimEvaluation:
        order = facts.order
        refs: list[str] = []
        reasons: list[PolicyReason] = []
        next_steps: list[str] = []
        approval: list[str] = []
        options = self._reason_options(facts) if facts.delivered_units else []

        def result(decision, eligible, *, items=(), max_cents=0, window=None, quote=None, fee_bps=0):
            needs_human = bool(approval)
            return ClaimEvaluation(
                EligibilityResult(
                    order_id=order.order_number,
                    eligible=eligible,
                    decision="requires_review" if needs_human and decision == "eligible" else decision,
                    reason_code=reason_code,
                    reasons=reasons,
                    window_ends_at=window,
                    max_refundable_amount=max_cents,
                    restocking_fee_bps=fee_bps,
                    eligible_items=list(items),
                    agent_can_issue=eligible and not needs_human and mode == "refund",
                    requires_human_approval=needs_human,
                    approval_reasons=approval,
                    reason_options=options,
                    next_steps=next_steps,
                    policy_refs=sorted(set(refs + [r.policy_ref for r in reasons if r.policy_ref])),
                ),
                quote,
            )

        gate = self._gates(facts, mode)
        if gate:
            decision, gate_reasons, steps = gate
            reasons.extend(gate_reasons)
            next_steps.extend(steps)
            if decision == "requires_review":
                approval.append("chargeback_open")
            return result(decision, False)

        capacity = self._unit_capacity(facts, mode)
        by_line = facts.by_line_number()

        if reason_code is None:
            open_options = [o for o in options if o.eligible]
            max_cents = min(
                sum(by_line[n].item.unit_net_cents(q) for n, q in capacity.items() if q),
                facts.remaining_refundable_cents,
            )
            items = [
                EligibleItem(line_number=n, sku=by_line[n].item.sku, product_name=by_line[n].item.product_name,
                             refundable_quantity=q, refundable_amount=by_line[n].item.unit_net_cents(q))
                for n, q in capacity.items() if q
            ]
            if open_options:
                reasons.append(_r("REASON_NEEDED", "Eligibility depends on what went wrong. Open options: "
                                  + ", ".join(o.reason_code for o in open_options) + "."))
                next_steps.append("Ask the customer what was wrong with the order, then re-check with that reason.")
                return result("eligible", True, items=items, max_cents=max_cents)
            reasons.append(_r("ALL_WINDOWS_CLOSED", "Every refund window for this order has closed.", "RTN-R1"))
            next_steps.append("If the customer has a credible reason for the delay, offer a P2 "
                              "policy_exception_request (no promise of approval).")
            return result("ineligible", False, items=[], max_cents=0)

        rule = RULES[reason_code]
        refs.append(rule.policy_ref)
        window_end = self._window_end(facts, rule)

        if reason_code == "late_delivery":
            reasons.append(_r("LATE_DELIVERY_GOODWILL", "A late delivery isn't refundable, but a goodwill store "
                              "credit of up to $15 can be offered once per 90 days.", "A-61"))
            next_steps.append("Offer goodwill store credit via a support ticket (P3, category delivery_issue).")
            return result("ineligible", False)

        if reason_code == "change_of_mind" and facts.state_code == "NY":
            reasons.append(_r("NY_NO_CHANGE_OF_MIND", "Orders from our New York store can't be returned for a "
                              "change of mind; only damaged, faulty or incorrect items are covered.", "A-35"))
            next_steps.append("Offer help if anything was damaged, faulty or wrong.")
            return result("ineligible", False)

        if window_end is not None and self.now > window_end:
            reasons.append(_r("OUTSIDE_WINDOW", f"Claims for {rule.label} must be reported within "
                              f"{_human(rule.window)} of delivery; that window closed on "
                              f"{window_end:%B %d, %Y}.", rule.policy_ref))
            next_steps.append("If there is a credible reason (e.g., hospital stay), offer a P2 "
                              "policy_exception_request; never promise approval.")
            return result("ineligible", False, window=window_end)

        # Per-line eligibility
        excluded: dict[int, str] = {}
        if reason_code == "change_of_mind":
            for n, lf in by_line.items():
                why = self._excluded_for_change_of_mind(lf.item, listings.get(lf.item.variant_id))
                if why:
                    excluded[n] = why
            for n, why in excluded.items():
                reasons.append(_r("ITEM_EXCLUDED", f"Line {n} ({by_line[n].item.product_name}) can't be returned "
                                  f"for a change of mind: {why}.", "RTN-R4"))
        allowed = {n: q for n, q in capacity.items() if q > 0 and n not in excluded}

        if selection is not None:
            bad = [n for n, q in selection.items() if n not in allowed or q > allowed[n]]
            if bad:
                reasons.append(_r("INVALID_SELECTION", "Some selected lines or quantities aren't eligible: lines "
                                  + ", ".join(map(str, sorted(bad))) + "."))
                return result("ineligible", False, window=window_end)
            chosen = selection
        else:
            chosen = allowed
        if not chosen:
            reasons.append(_r("NOTHING_ELIGIBLE", "No units on this order are left to "
                              + ("refund." if mode == "refund" else "return.")))
            return result("ineligible", False, window=window_end)

        quote = self._quote(facts, chosen, reason_code, method)
        items = [
            EligibleItem(line_number=ql.item.line_number, sku=ql.item.sku, product_name=ql.item.product_name,
                         refundable_quantity=ql.quantity, refundable_amount=ql.amount_cents)
            for ql in quote.lines
        ]
        reasons.append(_r("WITHIN_WINDOW", f"Reported within the {_human(rule.window)} window for {rule.label}"
                          + (f" (ends {window_end:%B %d, %Y})." if window_end else "."), rule.policy_ref))
        fee_bps = 0
        if reason_code == "change_of_mind":
            refs += ["A-34", "RTN-R2"]
            fee_bps = RESTOCKING_FEE_BPS if method == "original_payment" else 0
            reasons.append(_r("CHANGE_OF_MIND_TERMS", "Bottles must be unopened and resaleable. Choose full value as "
                              "store credit, or a refund to the original card minus a 15% restocking fee.", "A-34"))
            next_steps.append("Offer store credit (full value) or card refund minus 15%; arrange drop-off or pickup.")
        else:
            refs.append("RTN-R1")

        # Authority / human approval (A-60, A-62, A-33)
        if mode == "refund" and not is_staff and quote.total_cents > self.limit:
            approval.append("refund_over_limit")
            reasons.append(_r("OVER_AGENT_LIMIT", f"Refunds over {cents_to_str(self.limit)} need a team member's "
                              "approval.", "A-60"))
        if rule.evidence_required and not evidence_on_file:
            if mode == "refund":
                approval.append("evidence_required")
            next_steps.append("Create a return/claim and send a secure photo upload link (RTN-R6) before refunding.")
            refs.append("RTN-R6")
        if reason_code in CLAIM_REASONS and recent_claims >= 1:
            approval.append("claim_review")
            reasons.append(_r("SECOND_CLAIM_60_DAYS", "This would be a second claim within 60 days, which our team "
                              "reviews.", "A-62"))
        if reason_code in CLAIM_REASONS and any(self._is_collectible(ql.item) for ql in quote.lines):
            approval.append("collectible_dispute")
            reasons.append(_r("COLLECTIBLE_REVIEW", "Older or collectible vintages are sold as-is; claims are "
                              "reviewed by our team.", "A-33"))
        if approval:
            next_steps.append("Explain that a team member must approve; create the refund request so it is queued "
                              "(P2), and never promise the outcome.")
        elif mode == "refund":
            next_steps.append("Summarize amount and method, ask for explicit confirmation, then request the refund.")
        refs.append("RF-R3")
        return result("eligible", True, items=items, max_cents=quote.total_cents, window=window_end,
                      quote=quote, fee_bps=fee_bps)

    def cancellation(self, facts: OrderFacts, listings: dict[int, ProductListing]) -> CancellationEligibility:
        order = facts.order
        refund_preview = sum(p.refundable_cents for p in order.payments)
        void_preview = sum(p.open_authorization_cents for p in order.payments)
        reasons: list[PolicyReason] = []
        refs = ["A-21", "OC-R1"]

        def out(decision: str, eligible: bool) -> CancellationEligibility:
            return CancellationEligibility(
                order_id=order.order_number, eligible=eligible, decision=decision, status=order.status,
                reasons=reasons, refund_preview=refund_preview if eligible else None,
                void_preview=void_preview if eligible else None,
                policy_refs=sorted(set(refs + [r.policy_ref for r in reasons if r.policy_ref])),
            )

        pre_arrival = any(
            (pl := listings.get(i.variant_id)) is not None and pl.listing_status == "pre_arrival" for i in order.items
        )
        if order.status in ("cancelled",):
            reasons.append(_r("ALREADY_CANCELLED", "This order is already cancelled."))
            return out("ineligible", False)
        if order.status in ("completed", "delivered", "picked_up", "returned_to_store", "returned_to_sender"):
            reasons.append(_r("ALREADY_FULFILLED", "This order has already been fulfilled; return and refund "
                              "policies apply instead.", "RTN-R1"))
            return out("ineligible", False)
        in_motion = any(
            sh.status not in (*STAGED_SHIPMENT_STATUSES, "cancelled")
            for sh in order.shipments
        )
        if order.status in DISPATCHED_STATUSES or in_motion:
            reasons.append(_r("ALREADY_DISPATCHED", "This order is already with the driver or carrier, so it can't be "
                              "cancelled. If no one can receive it, failed-delivery rules apply (one free "
                              "redelivery, or a refund minus the delivery fee).", "OC-R3"))
            return out("ineligible", False)
        if order.status == "on_hold" and order.hold_reason == "fraud_review":
            reasons.append(_r("UNDER_REVIEW", "This order is under review by our team and can't be changed here.",
                              "OC-R6"))
            return out("ineligible", False)
        if pre_arrival:
            refs.append("A-25")
            deadline = order.placed_at + timedelta(days=14)
            if self.now > deadline:
                reasons.append(_r("PRE_ARRIVAL_LOCKED", "Pre-arrival orders can be cancelled within 14 days of "
                                  f"ordering (ended {deadline:%B %d, %Y}). After that they're cancellable only if "
                                  "arrival slips more than 90 days past the estimate.", "A-25"))
                return out("ineligible", False)
        if order.status in REQUEST_ONLY_STATUSES:
            reasons.append(_r("PICKING_IN_PROGRESS", "The store has started packing this order. A cancellation can "
                              "be requested but isn't guaranteed.", "OC-R2"))
            return out("request_only", False)
        if order.status in FREE_CANCEL_STATUSES or order.status == "on_hold":
            reasons.append(_r("FREE_CANCELLATION", "The order hasn't started packing, so it can be cancelled free "
                              "of charge with a full refund of anything already charged.", "A-21"))
            return out("eligible", True)
        reasons.append(_r("NOT_CANCELLABLE", f"Orders in status '{order.status}' can't be cancelled here."))
        return out("ineligible", False)


def _human(window: timedelta | None) -> str:
    if window is None:
        return "n/a"
    if window < timedelta(days=3):
        return f"{int(window.total_seconds() // 3600)} hours"
    return f"{window.days} days"
