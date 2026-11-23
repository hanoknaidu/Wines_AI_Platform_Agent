"""Refund and return use cases. Read paths are side-effect free; write paths
re-run the policy engine server-side, compute amounts themselves (the client
never sends an amount), enforce authority limits and write audit rows in the
same transaction."""
from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta

from app.core.errors import BusinessRuleError, NotFoundError
from app.core.money import cents_to_str
from app.models import (
    GiftCardTransaction,
    Order,
    PaymentTransaction,
    Refund,
    RefundItem,
    ReturnItem,
    ReturnRequest,
    StoreCreditTransaction,
)
from app.repositories.misc_repo import ReturnRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.refund import (
    EligibilityResult,
    EvidenceUploadLink,
    RefundLineOut,
    RefundOut,
    RefundRequest,
    RefundResult,
    ReturnCreated,
    ReturnItemOut,
    ReturnOut,
    ReturnRequestIn,
)
from app.schemas.support import TicketCreate
from app.services.context import ServiceContext
from app.services.order_facts import OrderFacts, compute_facts
from app.services.payment_gateway import PaymentGateway
from app.services.policy import RULES, SECOND_CLAIM_WINDOW, ClaimEvaluation, PolicyEngine, RefundQuote
from app.services.support_service import SupportService

CUSTOMER_FACING_REASON = {
    "damaged_in_transit": "Item damaged in transit",
    "broken_on_arrival": "Bottle broken on arrival",
    "corked_or_flawed": "Corked or flawed wine",
    "leaking": "Leaking bottle",
    "wrong_item": "Wrong item delivered",
    "missing_item": "Item missing from the order",
    "change_of_mind": "Return of unopened items",
    "late_delivery": "Late delivery",
    "order_cancelled": "Order cancelled",
    "item_out_of_stock": "Item out of stock",
    "price_adjustment": "Price adjustment",
    "price_match": "Approved price match",
    "failed_delivery": "Delivery could not be completed (fee not refunded)",
    "duplicate_charge": "Duplicate charge",
}
TICKET_CATEGORY_BY_REASON = {
    "damaged_in_transit": "damaged_item", "broken_on_arrival": "damaged_item", "leaking": "damaged_item",
    "corked_or_flawed": "flawed_wine", "wrong_item": "wrong_or_missing_item", "missing_item": "wrong_or_missing_item",
    "change_of_mind": "return_request", "late_delivery": "delivery_issue",
}
DEFAULT_CONDITION = {
    "damaged_in_transit": "broken", "broken_on_arrival": "broken", "corked_or_flawed": "defective",
    "leaking": "defective", "wrong_item": "unopened", "missing_item": "not_received", "change_of_mind": "unopened",
    "late_delivery": "unopened",
}


def expected_posting(method: str, status: str) -> str | None:
    if status == "pending_approval":
        return "After approval: card refunds post in 5-10 business days; store credit is instant (A-36)."
    if method == "store_credit":
        return "Store credit is available immediately and never expires (A-36)."
    return "Card refunds are initiated within 1 business day and post in 5-10 business days (A-36)."


def refund_out(refund: Refund, order: Order) -> RefundOut:
    items = {i.order_item_id: i for i in order.items}
    return RefundOut(
        refund_id=refund.refund_number,
        order_id=order.order_number,
        rma_number=refund.return_request.rma_number if refund.return_request else None,
        reason_code=refund.reason_code,
        method=refund.method,
        status=refund.status,
        customer_facing_reason=CUSTOMER_FACING_REASON.get(refund.reason_code, refund.reason_code),
        items_amount=refund.items_amount_cents,
        tax_amount=refund.tax_amount_cents,
        shipping_amount=refund.shipping_amount_cents,
        tip_amount=refund.tip_amount_cents,
        restocking_fee=refund.restocking_fee_cents,
        amount=refund.amount_cents,
        requires_human_approval=refund.requires_human_approval,
        created_at=refund.created_at,
        completed_at=refund.completed_at,
        expected_posting=expected_posting(refund.method, refund.status),
        lines=[
            RefundLineOut(line_number=items[fi.order_item_id].line_number, sku=items[fi.order_item_id].sku,
                          quantity=fi.quantity, amount=fi.amount_cents)
            for fi in refund.items if fi.order_item_id in items
        ],
    )


def return_out(rma: ReturnRequest, order: Order) -> ReturnOut:
    items = {i.order_item_id: i for i in order.items}
    reasons = {ri.reason_code for ri in rma.items}
    return ReturnOut(
        rma_number=rma.rma_number,
        order_id=order.order_number,
        status=rma.status,
        eligibility=rma.eligibility,
        ineligible_reason=rma.ineligible_reason,
        remedy=rma.remedy,
        return_method=rma.return_method,
        evidence_count=len(rma.evidence),
        evidence_required=any(RULES[r].evidence_required for r in reasons if r in RULES) and not rma.evidence
        and rma.status in ("requested", "needs_review"),
        requested_at=rma.requested_at,
        decided_at=rma.decided_at,
        closed_at=rma.closed_at,
        items=[
            ReturnItemOut(
                line_number=items[ri.order_item_id].line_number, sku=items[ri.order_item_id].sku,
                product_name=items[ri.order_item_id].product_name, quantity=ri.quantity,
                reason_code=ri.reason_code, item_condition=ri.item_condition, disposition=ri.disposition,
                restocking_fee_bps=ri.restocking_fee_bps,
            )
            for ri in rma.items if ri.order_item_id in items
        ],
        refund_ids=[f.refund_number for f in order.refunds if f.return_id == rma.return_id],
    )


class _ClaimsBase:
    def __init__(self, ctx: ServiceContext) -> None:
        self.ctx = ctx
        self.orders = OrderRepository(ctx.session)
        self.engine = PolicyEngine(ctx.now, ctx.settings.agent_refund_limit_cents)

    async def _context(self, order: Order) -> tuple[OrderFacts, dict, int]:
        facts = compute_facts(order)
        listings = await self.orders.listings_for(order.store_id, [i.variant_id for i in order.items])
        recent = await self.orders.count_recent_claims(
            order.customer_id, self.ctx.now - SECOND_CLAIM_WINDOW, exclude_order_id=order.order_id
        )
        return facts, listings, recent

    @staticmethod
    def _evidence_on_file(order: Order, reason_code: str | None, rma: ReturnRequest | None = None) -> bool:
        candidates = [rma] if rma else [r for r in order.returns if r.is_active]
        return any(
            r.evidence and (reason_code is None or any(ri.reason_code == reason_code for ri in r.items))
            for r in candidates
        )


class RefundService(_ClaimsBase):
    def __init__(self, ctx: ServiceContext, gateway: PaymentGateway) -> None:
        super().__init__(ctx)
        self.gateway = gateway

    async def eligibility(self, order_number: str, reason_code: str | None) -> EligibilityResult:
        order = await self.ctx.owned_order(order_number)
        facts, listings, recent = await self._context(order)
        return self.engine.evaluate_claim(
            facts, listings, mode="refund", reason_code=reason_code, recent_claims=recent,
            evidence_on_file=self._evidence_on_file(order, reason_code), is_staff=self.ctx.principal.is_staff,
        ).result

    async def list_refunds(self, order_number: str) -> list[RefundOut]:
        order = await self.ctx.owned_order(order_number)
        return [refund_out(f, order) for f in order.refunds]

    async def request_refund(
        self, order_number: str, req: RefundRequest, idempotency_key: str
    ) -> tuple[int, RefundResult]:
        ctx = self.ctx
        if not req.confirmed_by_customer:
            raise BusinessRuleError("The customer must explicitly confirm the refund first",
                                    code="CONFIRMATION_REQUIRED")
        order = await ctx.owned_order(order_number, for_update=True)
        rma = None
        selection = {i.line_number: i.quantity for i in req.items} if req.items else None
        if req.rma_number:
            rma = next((r for r in order.returns if r.rma_number == req.rma_number and r.is_active), None)
            if rma is None:
                raise NotFoundError("Return not found on this order", code="RETURN_NOT_FOUND")
            if any(ri.reason_code != req.reason_code for ri in rma.items):
                raise BusinessRuleError("reason_code does not match the return request", code="REASON_MISMATCH")
            if selection is None:
                by_id = {i.order_item_id: i.line_number for i in order.items}
                selection = {by_id[ri.order_item_id]: ri.quantity for ri in rma.items}

        facts, listings, recent = await self._context(order)
        evaluation: ClaimEvaluation = self.engine.evaluate_claim(
            facts, listings, mode="refund", reason_code=req.reason_code, selection=selection, method=req.method,
            recent_claims=recent, evidence_on_file=self._evidence_on_file(order, req.reason_code, rma),
            is_staff=ctx.principal.is_staff,
        )
        result = evaluation.result
        if not result.eligible or evaluation.quote is None:
            ctx.audit("refund.request", "order", order.order_number, customer_id=order.customer_id,
                      outcome="denied", reason=",".join(r.code for r in result.reasons),
                      idempotency_key=idempotency_key)
            await ctx.session.commit()
            code = "CHARGEBACK_OPEN" if "chargeback_open" in result.approval_reasons else "REFUND_NOT_ELIGIBLE"
            raise BusinessRuleError(
                result.reasons[0].message if result.reasons else "This order isn't eligible for a refund",
                code=code,
                details={"reasons": [r.model_dump() for r in result.reasons], "decision": result.decision,
                         "next_steps": result.next_steps},
            )

        quote = evaluation.quote
        needs_human = result.requires_human_approval
        now = ctx.now
        refund = Refund(
            order_id=order.order_id,
            return_id=rma.return_id if rma else None,
            reason_code=req.reason_code,
            method=req.method,
            status="pending_approval" if needs_human else "processing",
            items_amount_cents=quote.items_cents,
            tax_amount_cents=quote.tax_cents,
            shipping_amount_cents=quote.shipping_cents,
            tip_amount_cents=0,
            restocking_fee_cents=quote.restocking_fee_cents,
            amount_cents=quote.total_cents,
            requires_human_approval=needs_human,
            initiated_by_type=ctx.principal.actor_type,
            initiated_by_ref=ctx.actor_ref,
            idempotency_key=f"api:{ctx.principal.rate_limit_key}:{idempotency_key}",
            note=req.customer_note,
            created_at=now,
        )
        await self.orders.add_with_public_number(refund, "refund_number", "RF", 400000, "refund_id")
        for ql in quote.lines:
            ctx.session.add(RefundItem(refund_id=refund.refund_id, order_id=order.order_id,
                                       order_item_id=ql.item.order_item_id, quantity=ql.quantity,
                                       amount_cents=ql.amount_cents))
        await ctx.session.flush()

        ticket_number = None
        if needs_human:
            reason = "refund_over_limit" if "refund_over_limit" in result.approval_reasons else "claim_review"
            ticket = await SupportService(ctx).create_ticket(
                TicketCreate(
                    customer_id=order.customer.customer_number,
                    order_id=order.order_number,
                    rma_number=rma.rma_number if rma else None,
                    category=TICKET_CATEGORY_BY_REASON.get(req.reason_code, "refund_status"),
                    priority="P2",
                    reason_code=reason,
                    subject=f"Refund approval needed: {refund.refund_number} on {order.order_number}",
                    summary=(f"Refund {refund.refund_number} for {CUSTOMER_FACING_REASON[req.reason_code].lower()} "
                             f"awaits approval. Amount ${cents_to_str(quote.total_cents)} via {req.method}. "
                             f"Approval reasons: {', '.join(result.approval_reasons)}."),
                ),
                commit=False,
            )
            ticket_number = ticket.ticket_number
        else:
            await self._execute_money_movement(order, refund, quote)

        await ctx.session.flush()
        order = await self.orders.refresh_full(order)
        self._update_order_payment_status(order)
        ctx.audit(
            "refund.request", "refund", refund.refund_number, customer_id=order.customer_id,
            outcome="requires_approval" if needs_human else "success",
            reason=",".join(result.approval_reasons) or req.reason_code,
            after={"order": order.order_number, "amount_cents": refund.amount_cents, "method": refund.method,
                   "status": refund.status},
            idempotency_key=idempotency_key,
        )
        await ctx.session.flush()
        order = await self.orders.refresh_full(order)
        refund = next(f for f in order.refunds if f.refund_id == refund.refund_id)
        status = refund.status if refund.status in ("succeeded", "processing", "pending_approval") else "processing"
        message = (
            "A team member must approve this refund; it has been queued for review."
            if needs_human else "Refund issued."
        )
        return (202 if needs_human else 201), RefundResult(
            refund=refund_out(refund, order), status=status, requires_human_approval=needs_human,
            approval_reasons=result.approval_reasons, ticket_number=ticket_number, message=message,
        )

    async def _execute_money_movement(self, order: Order, refund: Refund, quote: RefundQuote) -> None:
        ctx = self.ctx
        now = ctx.now
        issuer = "ai_agent" if ctx.principal.role == "agent" else ("staff" if ctx.principal.is_staff else "system")
        if refund.method == "store_credit":
            ctx.session.add(StoreCreditTransaction(
                customer_id=order.customer_id, entry_type="issue_refund", amount_cents=refund.amount_cents,
                order_id=order.order_id, refund_id=refund.refund_id,
                reason=f"Refund {refund.refund_number} ({refund.reason_code})",
                issued_by_type=issuer, issued_by_ref=ctx.actor_ref, created_at=now,
            ))
        else:
            remaining = refund.amount_cents
            for payment in order.payments:  # ordered by refund_priority: card refunded last
                take = min(remaining, payment.refundable_cents)
                if take <= 0:
                    continue
                capture = next((t for t in reversed(payment.transactions)
                                if t.transaction_type == "capture" and t.status == "succeeded"), None)
                if capture is None:
                    continue
                key = f"{refund.refund_number}:{payment.payment_id}:refund"
                if payment.tender_type in ("card", "apple_pay", "google_pay"):
                    gw = await self.gateway.refund(payment.processor_payment_ref or "", take, key)
                    status, reference, failure = gw.status, gw.reference, gw.failure_code
                else:
                    status, reference, failure = "succeeded", None, None
                    if payment.tender_type == "gift_card" and payment.gift_card_id:
                        ctx.session.add(GiftCardTransaction(gift_card_id=payment.gift_card_id, entry_type="refund",
                                                            amount_cents=take, payment_id=payment.payment_id,
                                                            refund_id=refund.refund_id, created_at=now))
                    elif payment.tender_type == "store_credit":
                        ctx.session.add(StoreCreditTransaction(
                            customer_id=order.customer_id, entry_type="issue_refund", amount_cents=take,
                            order_id=order.order_id, refund_id=refund.refund_id, payment_id=payment.payment_id,
                            reason=f"Refund {refund.refund_number} to store-credit tender",
                            issued_by_type=issuer, issued_by_ref=ctx.actor_ref, created_at=now,
                        ))
                txn = PaymentTransaction(
                    payment_id=payment.payment_id, order_id=order.order_id, transaction_type="refund",
                    status=status, amount_cents=take, parent_transaction_id=capture.transaction_id,
                    refund_id=refund.refund_id, processor_reference=reference, failure_code=failure,
                    failure_message=None, idempotency_key=key, created_at=now,
                    processed_at=now if status != "pending" else None,
                )
                ctx.session.add(txn)
                payment.transactions.append(txn)
                if status == "failed":
                    raise BusinessRuleError("The payment processor declined the refund", code="REFUND_FAILED")
                payment.status = "refunded" if payment.refundable_cents == 0 else "partially_refunded"
                payment.updated_at = now
                remaining -= take
                if remaining == 0:
                    break
            if remaining > 0:
                raise BusinessRuleError("Refund exceeds the amount captured on this order",
                                        code="REFUND_EXCEEDS_CAPTURED")
        refund.status = "succeeded"
        refund.completed_at = now
        refund.approved_at = now

    def _update_order_payment_status(self, order: Order) -> None:
        succeeded = sum(f.amount_cents for f in order.refunds if f.status == "succeeded")
        if succeeded <= 0:
            return
        order.payment_status = "refunded" if succeeded >= order.grand_total_cents else "partially_refunded"
        order.updated_at = self.ctx.now


class ReturnService(_ClaimsBase):
    async def eligibility(self, order_number: str, reason_code: str | None) -> EligibilityResult:
        order = await self.ctx.owned_order(order_number)
        facts, listings, recent = await self._context(order)
        return self.engine.evaluate_claim(
            facts, listings, mode="return", reason_code=reason_code, recent_claims=recent,
            evidence_on_file=self._evidence_on_file(order, reason_code),
        ).result

    async def list_returns(self, order_number: str) -> list[ReturnOut]:
        order = await self.ctx.owned_order(order_number)
        return [return_out(r, order) for r in order.returns]

    async def get_return(self, rma_number: str) -> ReturnOut:
        rma = await ReturnRepository(self.ctx.session).get_by_rma(rma_number)
        if rma is None:
            raise NotFoundError("Return not found", code="RETURN_NOT_FOUND")
        order = await self.orders.get_full_by_id(rma.order_id)
        if order is None or not self.ctx.principal.can_access_customer(order.customer.customer_number):
            raise NotFoundError("Return not found", code="RETURN_NOT_FOUND")
        rma = next(r for r in order.returns if r.return_id == rma.return_id)
        return return_out(rma, order)

    async def create_return(
        self, order_number: str, req: ReturnRequestIn, idempotency_key: str
    ) -> tuple[int, ReturnCreated]:
        ctx = self.ctx
        if not req.confirmed_by_customer:
            raise BusinessRuleError("The customer must explicitly confirm the return first",
                                    code="CONFIRMATION_REQUIRED")
        if req.reason_code == "change_of_mind" and req.item_condition not in (None, "unopened"):
            raise BusinessRuleError("Change-of-mind returns must be unopened (A-34)", code="RETURN_NOT_ELIGIBLE")
        if req.reason_code == "late_delivery":
            raise BusinessRuleError("Late deliveries are handled with goodwill credit, not returns (A-61)",
                                    code="RETURN_NOT_ELIGIBLE")
        order = await ctx.owned_order(order_number, for_update=True)
        facts, listings, recent = await self._context(order)
        selection = {i.line_number: i.quantity for i in req.items}
        evaluation = self.engine.evaluate_claim(
            facts, listings, mode="return", reason_code=req.reason_code, selection=selection,
            method="store_credit" if req.remedy == "store_credit" else "original_payment", recent_claims=recent,
        )
        result = evaluation.result
        if not result.eligible:
            ctx.audit("return.create", "order", order.order_number, customer_id=order.customer_id,
                      outcome="denied", reason=",".join(r.code for r in result.reasons),
                      idempotency_key=idempotency_key)
            await ctx.session.commit()
            raise BusinessRuleError(
                result.reasons[0].message if result.reasons else "These items aren't eligible for a return",
                code="RETURN_NOT_ELIGIBLE",
                details={"reasons": [r.model_dump() for r in result.reasons], "next_steps": result.next_steps},
            )
        rule = RULES[req.reason_code]
        needs_review = rule.evidence_required or bool(result.approval_reasons)
        now = ctx.now
        if req.return_method:
            method = req.return_method
        elif req.reason_code == "change_of_mind":
            method = "in_store_dropoff"
        elif req.reason_code == "wrong_item":
            method = "courier_pickup"
        else:
            method = "not_required"
        rma = ReturnRequest(
            order_id=order.order_id, customer_id=order.customer_id,
            status="requested" if needs_review else "approved",
            eligibility="needs_review" if needs_review else "auto_approved",
            remedy=req.remedy, return_method=method,
            initiated_via="chat_agent" if ctx.principal.role == "agent" else "web",
            customer_notes=req.customer_notes,
            decided_by_type=None if needs_review else ("ai_agent" if ctx.principal.role == "agent" else "system"),
            requested_at=now, decided_at=None if needs_review else now,
        )
        await self.orders.add_with_public_number(rma, "rma_number", "RMA", 300000, "return_id")
        by_line = {i.line_number: i for i in order.items}
        fee_bps = 1500 if req.reason_code == "change_of_mind" and req.remedy == "refund_original_payment" else 0
        for line_number, qty in selection.items():
            ctx.session.add(ReturnItem(
                return_id=rma.return_id, order_id=order.order_id, order_item_id=by_line[line_number].order_item_id,
                quantity=qty, reason_code=req.reason_code,
                item_condition=req.item_condition or DEFAULT_CONDITION[req.reason_code],
                disposition="pending", restocking_fee_bps=fee_bps,
            ))
        ctx.audit("return.create", "return", rma.rma_number, customer_id=order.customer_id,
                  outcome="success", reason=req.reason_code,
                  after={"order": order.order_number, "eligibility": rma.eligibility, "lines": selection},
                  idempotency_key=idempotency_key)
        await ctx.session.flush()
        order = await self.orders.refresh_full(order)
        rma = next(r for r in order.returns if r.return_id == rma.return_id)
        steps = []
        if rule.evidence_required:
            steps.append("Send the customer a secure photo upload link (request_evidence_upload); photos of the "
                         "bottle, label and packaging. Never ask for photos of people or IDs.")
        if result.approval_reasons:
            steps.append("A team member reviews this claim (P2, 4 business hours).")
        if method == "in_store_dropoff":
            steps.append(f"Bring the unopened bottles to the {order.store.name} with RMA {rma.rma_number}.")
        elif method == "courier_pickup":
            steps.append("We'll schedule a free return pickup for the wrong item.")
        if not needs_review:
            steps.append("The claim is approved: the refund or replacement can be issued after confirmation.")
        quote = evaluation.quote
        return 201, ReturnCreated(
            rma=return_out(rma, order),
            eligibility=rma.eligibility,
            evidence_required=rule.evidence_required,
            next_steps=steps,
            estimated_refund=quote.total_cents if quote else None,
        )

    async def evidence_upload_link(self, rma_number: str) -> EvidenceUploadLink:
        rma = await ReturnRepository(self.ctx.session).get_by_rma(rma_number)
        order = await self.orders.get_full_by_id(rma.order_id) if rma else None
        if rma is None or order is None or not self.ctx.principal.can_access_customer(order.customer.customer_number):
            raise NotFoundError("Return not found", code="RETURN_NOT_FOUND")
        if not rma.is_active or rma.status in ("completed",):
            raise BusinessRuleError("This return is closed", code="RETURN_CLOSED")
        expires = self.ctx.now + timedelta(hours=24)
        secret = self.ctx.settings.jwt_secret.get_secret_value().encode()
        sig = hmac.new(secret, f"{rma_number}|{int(expires.timestamp())}".encode(), hashlib.sha256).hexdigest()[:32]
        self.ctx.audit("return.evidence_link", "return", rma_number, customer_id=rma.customer_id)
        await self.ctx.session.commit()
        return EvidenceUploadLink(
            rma_number=rma_number,
            upload_link=f"{self.ctx.settings.evidence_upload_base_url}/{rma_number}?exp={int(expires.timestamp())}&sig={sig}",
            expires_at=expires,
            instructions="Upload clear photos of the bottle, label, fill level/cork and packaging. "
                         "Please don't include people or ID documents.",
        )


__all__ = ["RefundService", "ReturnService", "refund_out", "return_out"]
