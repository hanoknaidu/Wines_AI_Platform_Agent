"""Order cancellation (A-21, A-25, OC-R1..R3): void open authorizations,
refund captured money, release stock reservations, append status history,
audit. One transaction."""
from __future__ import annotations

from app.core.errors import BusinessRuleError
from app.models import PaymentTransaction, Refund, RefundItem
from app.repositories.order_repo import OrderRepository
from app.schemas.order import CancellationEligibility, CancelOrderRequest, CancelOrderResult
from app.services.context import ServiceContext
from app.services.order_facts import compute_facts
from app.services.payment_gateway import PaymentGateway
from app.services.policy import STAGED_SHIPMENT_STATUSES, PolicyEngine, RefundQuote
from app.services.refund_service import RefundService, expected_posting


class CancellationService:
    def __init__(self, ctx: ServiceContext, gateway: PaymentGateway) -> None:
        self.ctx = ctx
        self.gateway = gateway
        self.orders = OrderRepository(ctx.session)
        self.engine = PolicyEngine(ctx.now, ctx.settings.agent_refund_limit_cents)

    async def eligibility(self, order_number: str) -> CancellationEligibility:
        order = await self.ctx.owned_order(order_number)
        listings = await self.orders.listings_for(order.store_id, [i.variant_id for i in order.items])
        return self.engine.cancellation(compute_facts(order), listings)

    async def cancel(
        self, order_number: str, req: CancelOrderRequest, idempotency_key: str
    ) -> tuple[int, CancelOrderResult]:
        ctx = self.ctx
        if not req.confirmed_by_customer:
            raise BusinessRuleError("The customer must explicitly confirm the cancellation first",
                                    code="CONFIRMATION_REQUIRED")
        order = await ctx.owned_order(order_number, for_update=True)
        facts = compute_facts(order)
        listings = await self.orders.listings_for(order.store_id, [i.variant_id for i in order.items])
        decision = self.engine.cancellation(facts, listings)
        if not decision.eligible:
            ctx.audit("order.cancel", "order", order.order_number, customer_id=order.customer_id, outcome="denied",
                      reason=",".join(r.code for r in decision.reasons), idempotency_key=idempotency_key)
            await ctx.session.commit()
            raise BusinessRuleError(
                decision.reasons[0].message if decision.reasons else "This order can't be cancelled",
                code="ORDER_NOT_CANCELLABLE",
                details={"decision": decision.decision, "reasons": [r.model_dump() for r in decision.reasons]},
            )

        now = ctx.now
        before = {"status": order.status, "payment_status": order.payment_status}

        # 1. Void every open authorization (nothing captured on those tenders yet).
        voided = 0
        for payment in order.payments:
            open_auth = payment.open_authorization_cents
            if open_auth <= 0:
                continue
            auth = next((t for t in payment.transactions
                         if t.transaction_type == "authorization" and t.status == "succeeded"), None)
            key = f"{order.order_number}:{payment.payment_id}:void"
            ref = None
            if payment.tender_type in ("card", "apple_pay", "google_pay"):
                ref = (await self.gateway.void(payment.processor_payment_ref or "", open_auth, key)).reference
            txn = PaymentTransaction(
                payment_id=payment.payment_id, order_id=order.order_id, transaction_type="void", status="succeeded",
                amount_cents=open_auth, parent_transaction_id=auth.transaction_id if auth else None,
                processor_reference=ref, idempotency_key=key, created_at=now, processed_at=now,
            )
            ctx.session.add(txn)
            payment.transactions.append(txn)
            payment.status = "voided" if payment.captured_cents == 0 else payment.status
            payment.updated_at = now
            voided += open_auth

        # 2. Refund anything already captured (prepaid pickup, pre-arrivals).
        refund_cents = sum(p.refundable_cents for p in order.payments)
        refund = None
        if refund_cents > 0:
            full = refund_cents == order.grand_total_cents
            fee_tax = facts.fee_tax_cents
            refund = Refund(
                order_id=order.order_id, reason_code="order_cancelled", method="original_payment",
                status="processing",
                items_amount_cents=(order.items_subtotal_cents - order.discount_total_cents) if full else refund_cents,
                tax_amount_cents=(order.tax_total_cents - fee_tax) if full else 0,
                shipping_amount_cents=(order.shipping_fee_cents + fee_tax) if full else 0,
                tip_amount_cents=order.tip_cents if full else 0,
                restocking_fee_cents=0, amount_cents=refund_cents, requires_human_approval=False,
                initiated_by_type=ctx.principal.actor_type, initiated_by_ref=ctx.actor_ref,
                idempotency_key=f"cancel:{order.order_number}:{idempotency_key}", created_at=now,
            )
            await self.orders.add_with_public_number(refund, "refund_number", "RF", 400000, "refund_id")
            if full:
                for item in order.items:
                    ctx.session.add(RefundItem(refund_id=refund.refund_id, order_id=order.order_id,
                                               order_item_id=item.order_item_id, quantity=item.quantity,
                                               amount_cents=item.line_total_cents))
            await RefundService(ctx, self.gateway)._execute_money_movement(order, refund, RefundQuote())

        # 3. Cancel staged (not yet handed off) shipments, cancel every unit not
        #    already handed off, and release stock reservations.
        staged = {sh.shipment_id for sh in order.shipments if sh.status in STAGED_SHIPMENT_STATUSES}
        for sh in order.shipments:
            if sh.shipment_id in staged:
                sh.status, sh.updated_at = "cancelled", now
        for lf in facts.lines.values():
            kept = sum(si.quantity for sh in order.shipments if sh.shipment_id not in staged
                       and sh.status != "cancelled" for si in sh.items if si.order_item_id == lf.item.order_item_id)
            lf.item.quantity_cancelled = lf.item.quantity - kept
        for res in await self.orders.active_reservations(order.order_id):
            res.status, res.closed_at = "released", now
            level = await self.orders.inventory_level(res.warehouse_id, res.variant_id)
            if level is not None:
                level.qty_reserved = max(level.qty_reserved - res.quantity, 0)
                level.updated_at = now

        # 4. Status, history, payment summary, audit.
        await self.orders.add_status_history(order, "cancelled", ctx.principal.actor_type, ctx.actor_ref,
                                             "Cancelled at customer request", now)
        order.status = "cancelled"
        order.hold_reason = None
        order.cancelled_at = now
        order.cancel_reason = req.reason_code
        order.payment_status = "refunded" if refund else "voided"
        order.updated_at = now
        ctx.audit("order.cancel", "order", order.order_number, customer_id=order.customer_id, outcome="success",
                  reason=req.reason_code, before=before,
                  after={"status": "cancelled", "voided_cents": voided, "refund_cents": refund_cents,
                         "refund": refund.refund_number if refund else None},
                  idempotency_key=idempotency_key)
        await ctx.session.flush()
        return 200, CancelOrderResult(
            order_id=order.order_number, cancelled=True, status="cancelled", voided_amount=voided,
            refund_amount=refund_cents, refund_id=refund.refund_number if refund else None,
            refund_method="original_payment" if refund else None,
            expected_posting=expected_posting("original_payment", "succeeded") if refund else
            "The pending authorization is released by your bank, usually within a few days.",
        )
