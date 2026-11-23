"""Refund / return / cancellation business rules, idempotency and audit.
Clock frozen at 2026-11-19T18:00Z (seed reference date)."""
from __future__ import annotations

from sqlalchemy import func, select

from app.models import AuditLog, IdempotencyRecord, PaymentTransaction, Refund, SupportTicket

API = "/api/v1"


def idem(headers: dict, key: str) -> dict:
    return {**headers, "Idempotency-Key": key}


class TestRefundEligibility:
    async def test_no_reason_lists_open_windows_and_asks(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100114/refund-eligibility", headers=auth("C-100005"))).json()
        assert body["eligible"] is True and body["reason_code"] is None
        options = {o["reason_code"]: o["eligible"] for o in body["reason_options"]}
        # Delivered 2026-11-14 21:10: 48 h damage window closed, 7/14/30-day windows open
        assert options["broken_on_arrival"] is False
        assert options["wrong_item"] and options["corked_or_flawed"] and options["change_of_mind"]
        assert options["late_delivery"] is False
        # delivered units only: the unit cancelled before shipping was never captured,
        # and the $3.00 driver tip is not refundable once delivered (refunds doc §2)
        assert body["max_refundable_amount"] == "83.18"

    async def test_outside_damage_window(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100114/refund-eligibility?reason_code=broken_on_arrival",
                                 headers=auth("C-100005"))).json()
        assert body["eligible"] is False and body["reasons"][0]["code"] == "OUTSIDE_WINDOW"
        assert "A-30" in body["policy_refs"]

    async def test_defect_claim_needs_evidence_before_refund(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100114/refund-eligibility?reason_code=corked_or_flawed",
                                 headers=auth("C-100005"))).json()
        assert body["eligible"] is True and body["decision"] == "requires_review"
        assert body["approval_reasons"] == ["evidence_required"] and body["agent_can_issue"] is False

    async def test_wrong_item_within_authority(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100114/refund-eligibility?reason_code=wrong_item",
                                 headers=auth(agent="C-100005"))).json()
        assert body["decision"] == "eligible" and body["agent_can_issue"] is True

    async def test_ny_change_of_mind_not_accepted(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100104/refund-eligibility?reason_code=change_of_mind",
                                 headers=auth("C-100004"))).json()
        assert body["eligible"] is False and body["reasons"][0]["code"] == "NY_NO_CHANGE_OF_MIND"

    async def test_open_chargeback_blocks_refunds(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100118/refund-eligibility?reason_code=corked_or_flawed",
                                 headers=auth("C-100010"))).json()
        assert body["eligible"] is False and body["requires_human_approval"] is True
        assert body["approval_reasons"] == ["chargeback_open"] and "RF-R5" in body["policy_refs"]

    async def test_not_delivered_points_to_cancellation(self, client, auth):
        pending = (await client.get(f"{API}/orders/WA-100109/refund-eligibility",
                                    headers=auth("C-100009"))).json()
        assert pending["decision"] == "cancel_instead"
        en_route = (await client.get(f"{API}/orders/WA-100120/refund-eligibility",
                                     headers=auth("C-100004"))).json()
        assert en_route["decision"] == "ineligible" and en_route["reasons"][0]["code"] == "NOT_YET_DELIVERED"

    async def test_eligibility_is_read_only(self, client, auth, container):
        await client.get(f"{API}/orders/WA-100114/refund-eligibility?reason_code=wrong_item", headers=auth("C-100005"))
        async with container.session_factory() as db:
            assert (await db.execute(select(func.count()).select_from(Refund))).scalar_one() == 7  # seed count


class TestRequestRefund:
    BODY = {"reason_code": "wrong_item", "items": [{"line_number": 1, "quantity": 1}], "confirmed_by_customer": True}

    async def test_agent_refund_within_limit_succeeds_and_is_audited(self, client, auth, container):
        r = await client.post(f"{API}/orders/WA-100114/refunds", json=self.BODY,
                              headers=idem(auth(agent="C-100005"), "refund-key-0001"))
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["status"] == "succeeded" and body["requires_human_approval"] is False
        refund = body["refund"]
        # 1 of 2 units of a $46.92 line (22.00 + 2.92 tax -> per unit 23.46)
        assert refund["amount"] == "23.46" and refund["items_amount"] == "22.00" and refund["tax_amount"] == "1.46"
        async with container.session_factory() as db:
            row = (await db.execute(select(Refund).where(Refund.refund_number == refund["refund_id"]))).scalar_one()
            assert row.initiated_by_type == "ai_agent"
            txns = (await db.execute(select(PaymentTransaction).where(
                PaymentTransaction.refund_id == row.refund_id))).scalars().all()
            assert sum(t.amount_cents for t in txns) == 2346 and all(t.status == "succeeded" for t in txns)
            audit = (await db.execute(select(AuditLog).where(AuditLog.action == "refund.request"))).scalars().all()
            assert audit[-1].outcome == "success" and audit[-1].actor_type == "ai_agent"
        order = (await client.get(f"{API}/orders/WA-100114", headers=auth("C-100005"))).json()
        assert order["payment_status"] == "partially_refunded"

    async def test_idempotent_replay_and_key_reuse(self, client, auth, container):
        h = idem(auth("C-100005"), "refund-key-0002")
        first = await client.post(f"{API}/orders/WA-100114/refunds", json=self.BODY, headers=h)
        again = await client.post(f"{API}/orders/WA-100114/refunds", json=self.BODY, headers=h)
        assert first.status_code == again.status_code == 201
        assert again.headers["idempotent-replayed"] == "true" and again.json() == first.json()
        changed = {**self.BODY, "items": [{"line_number": 1, "quantity": 2}]}
        reuse = await client.post(f"{API}/orders/WA-100114/refunds", json=changed, headers=h)
        assert reuse.status_code == 422 and reuse.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
        async with container.session_factory() as db:
            n = (await db.execute(select(func.count()).select_from(Refund))).scalar_one()
            assert n == 8  # exactly one new refund
            assert (await db.execute(select(func.count()).select_from(IdempotencyRecord))).scalar_one() == 1

    async def test_requires_idempotency_key_and_confirmation(self, client, auth):
        no_key = await client.post(f"{API}/orders/WA-100114/refunds", json=self.BODY, headers=auth("C-100005"))
        assert no_key.status_code == 400 and no_key.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"
        unconfirmed = await client.post(f"{API}/orders/WA-100114/refunds",
                                        json={**self.BODY, "confirmed_by_customer": False},
                                        headers=idem(auth("C-100005"), "refund-key-0003"))
        assert unconfirmed.status_code == 422 and unconfirmed.json()["error"]["code"] == "CONFIRMATION_REQUIRED"

    async def test_cannot_refund_more_units_than_delivered(self, client, auth):
        body = {**self.BODY, "items": [{"line_number": 1, "quantity": 5}]}
        r = await client.post(f"{API}/orders/WA-100114/refunds", json=body,
                              headers=idem(auth("C-100005"), "refund-key-0004"))
        assert r.status_code == 422 and r.json()["error"]["code"] == "REFUND_NOT_ELIGIBLE"

    async def test_chargeback_blocks_refund_request(self, client, auth):
        body = {"reason_code": "corked_or_flawed", "confirmed_by_customer": True}
        r = await client.post(f"{API}/orders/WA-100118/refunds", json=body,
                              headers=idem(auth("C-100010"), "refund-key-0005"))
        assert r.status_code == 422 and r.json()["error"]["code"] == "CHARGEBACK_OPEN"

    async def test_over_agent_limit_goes_to_human_approval(self, client, auth, container):
        # WA-100103: 9 delivered bottles, corked claim worth > $150; C-100003 also has a recent claim.
        body = {"reason_code": "corked_or_flawed", "confirmed_by_customer": True}
        r = await client.post(f"{API}/orders/WA-100103/refunds", json=body,
                              headers=idem(auth(agent="C-100003"), "refund-key-0006"))
        assert r.status_code == 202, r.text
        out = r.json()
        assert out["status"] == "pending_approval" and out["requires_human_approval"] is True
        assert {"refund_over_limit", "evidence_required", "claim_review"} <= set(out["approval_reasons"])
        assert out["ticket_number"].startswith("TKT-")
        async with container.session_factory() as db:
            ticket = (await db.execute(select(SupportTicket).where(
                SupportTicket.ticket_number == out["ticket_number"]))).scalar_one()
            assert (ticket.priority, ticket.reason_code) == ("P2", "refund_over_limit")
            txns = (await db.execute(select(func.count()).select_from(PaymentTransaction).where(
                PaymentTransaction.transaction_type == "refund"))).scalar_one()
            assert txns == 5  # no money moved

    async def test_staff_can_refund_over_limit_without_approval_queue(self, client, auth):
        body = {"reason_code": "wrong_item", "confirmed_by_customer": True}
        r = await client.post(f"{API}/orders/WA-100114/refunds", json=body,
                              headers=idem(auth(staff="S-1003"), "refund-key-0007"))
        assert r.status_code == 201 and r.json()["refund"]["amount"] == "83.18"

    async def test_store_credit_refund(self, client, auth):
        body = {**self.BODY, "method": "store_credit"}
        r = await client.post(f"{API}/orders/WA-100114/refunds", json=body,
                              headers=idem(auth("C-100005"), "refund-key-0008"))
        assert r.status_code == 201
        account = (await client.get(f"{API}/customers/C-100005/account", headers=auth("C-100005"))).json()
        assert account["store_credit_balance"] == "23.46"


class TestReturns:
    async def test_nj_change_of_mind_return_auto_approved(self, client, auth):
        items = (await client.get(f"{API}/orders/WA-100114/items", headers=auth("C-100005"))).json()
        line = items[1]
        body = {"reason_code": "change_of_mind",
                "items": [{"line_number": line["line_number"], "quantity": line["quantity_delivered"]}],
                "remedy": "store_credit", "confirmed_by_customer": True}
        r = await client.post(f"{API}/orders/WA-100114/returns", json=body,
                              headers=idem(auth("C-100005"), "return-key-0001"))
        assert r.status_code == 201, r.text
        out = r.json()
        assert out["eligibility"] == "auto_approved" and out["rma"]["return_method"] == "in_store_dropoff"
        assert out["rma"]["items"][0]["restocking_fee_bps"] == 0  # store credit = full value (A-34)
        got = (await client.get(f"{API}/returns/{out['rma']['rma_number']}", headers=auth("C-100005"))).json()
        assert got["status"] == "approved"
        # every delivered unit of that line is now on a return: it can't be claimed again
        again = await client.post(f"{API}/orders/WA-100114/returns", json=body,
                                  headers=idem(auth("C-100005"), "return-key-0002"))
        assert again.status_code == 422 and again.json()["error"]["code"] == "RETURN_NOT_ELIGIBLE"

    async def test_defect_claim_needs_review_and_evidence_link(self, client, auth):
        body = {"reason_code": "corked_or_flawed", "items": [{"line_number": 1, "quantity": 1}],
                "confirmed_by_customer": True}
        r = await client.post(f"{API}/orders/WA-100114/returns", json=body,
                              headers=idem(auth("C-100005"), "return-key-0003"))
        out = r.json()
        assert out["eligibility"] == "needs_review" and out["evidence_required"] is True
        link = await client.post(f"{API}/returns/{out['rma']['rma_number']}/evidence-upload-link",
                                 headers=auth("C-100005"))
        assert link.status_code == 200 and "sig=" in link.json()["upload_link"]

    async def test_ny_change_of_mind_rejected(self, client, auth):
        body = {"reason_code": "change_of_mind", "items": [{"line_number": 1, "quantity": 1}],
                "confirmed_by_customer": True}
        r = await client.post(f"{API}/orders/WA-100104/returns", json=body,
                              headers=idem(auth("C-100004"), "return-key-0004"))
        assert r.status_code == 422 and r.json()["error"]["code"] == "RETURN_NOT_ELIGIBLE"

    async def test_rejected_claim_visible_with_reason(self, client, auth):
        returns = (await client.get(f"{API}/orders/WA-100118/returns", headers=auth("C-100010"))).json()
        rejected = [r for r in returns if r["status"] == "rejected"]
        assert rejected and rejected[0]["ineligible_reason"]


class TestCancellation:
    async def test_cancel_before_picking_voids_authorization(self, client, auth, container):
        elig = (await client.get(f"{API}/orders/WA-100109/cancellation-eligibility", headers=auth("C-100009"))).json()
        assert elig["eligible"] is True and elig["void_preview"] == "87.43"
        h = idem(auth("C-100009"), "cancel-key-0001")
        r = await client.post(f"{API}/orders/WA-100109/cancellation", json={"confirmed_by_customer": True}, headers=h)
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["cancelled"] is True and out["voided_amount"] == "87.43" and out["refund_amount"] == "0.00"
        status = (await client.get(f"{API}/orders/WA-100109/status", headers=auth("C-100009"))).json()
        assert (status["status"], status["payment_status"]) == ("cancelled", "voided")
        history = (await client.get(f"{API}/orders/WA-100109/history", headers=auth("C-100009"))).json()
        assert history[-1]["to_status"] == "cancelled"
        replay = await client.post(f"{API}/orders/WA-100109/cancellation", json={"confirmed_by_customer": True},
                                   headers=h)
        assert replay.headers["idempotent-replayed"] == "true"
        async with container.session_factory() as db:
            voids = (await db.execute(select(func.count()).select_from(PaymentTransaction).where(
                PaymentTransaction.transaction_type == "void"))).scalar_one()
            assert voids == 3  # 2 in seed + 1 new (not 2: replay did not act twice)

    async def test_prepaid_pickup_cancellation_refunds_captured_money(self, client, auth):
        r = await client.post(f"{API}/orders/WA-100105/cancellation", json={"confirmed_by_customer": True},
                              headers=idem(auth("C-100005"), "cancel-key-0002"))
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["refund_amount"] == "104.50" and out["refund_id"].startswith("RF-")

    async def test_dispatched_order_cannot_be_cancelled(self, client, auth):
        r = await client.post(f"{API}/orders/WA-100120/cancellation", json={"confirmed_by_customer": True},
                              headers=idem(auth("C-100004"), "cancel-key-0003"))
        assert r.status_code == 422 and r.json()["error"]["code"] == "ORDER_NOT_CANCELLABLE"

    async def test_pre_arrival_past_14_days_is_locked(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100115/cancellation-eligibility", headers=auth("C-100006"))).json()
        assert body["eligible"] is False and body["reasons"][0]["code"] == "PRE_ARRIVAL_LOCKED"
