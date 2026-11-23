"""API-level tests for Category 1 read endpoints: auth, ownership, filtering,
pagination, response filtering, error envelope, rate limiting."""
from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models import AuditLog

API = "/api/v1"


class TestAuthAndOwnership:
    async def test_missing_token_is_401_with_error_envelope(self, client):
        r = await client.get(f"{API}/customers/C-100001")
        assert r.status_code == 401
        body = r.json()["error"]
        assert body["code"] == "UNAUTHENTICATED" and body["retryable"] is False and body["request_id"]
        assert r.headers["x-request-id"] == body["request_id"]

    async def test_invalid_token_is_401(self, client):
        r = await client.get(f"{API}/customers/C-100001", headers={"Authorization": "Bearer nope"})
        assert r.status_code == 401 and r.json()["error"]["code"] == "INVALID_TOKEN"

    async def test_other_customers_data_is_404_not_403(self, client, auth):
        h = auth("C-100001")
        for path in ("/customers/C-100002", "/customers/C-100002/orders", "/orders/WA-100102",
                     "/orders/WA-100102/payment", "/orders/WA-100102/refund-eligibility"):
            r = await client.get(API + path, headers=h)
            assert r.status_code == 404, path

    async def test_agent_token_is_bound_to_its_customer(self, client, auth):
        assert (await client.get(f"{API}/orders/WA-100114", headers=auth(agent="C-100005"))).status_code == 200
        assert (await client.get(f"{API}/orders/WA-100101", headers=auth(agent="C-100005"))).status_code == 404

    async def test_staff_can_read_any_customer(self, client, auth):
        r = await client.get(f"{API}/customers/C-100008", headers=auth(staff="S-1001"))
        assert r.status_code == 200 and r.json()["status"] == "locked"

    async def test_validation_error_never_echoes_input(self, client, auth):
        r = await client.get(f"{API}/orders/not-an-order<script>", headers=auth("C-100001"))
        assert r.status_code == 422
        err = r.json()["error"]
        assert err["code"] == "VALIDATION_ERROR" and "<script>" not in r.text

    async def test_request_id_is_propagated(self, client, auth):
        r = await client.get(f"{API}/customers/C-100001", headers={**auth("C-100001"), "X-Request-ID": "req-abc-123"})
        assert r.headers["x-request-id"] == "req-abc-123"

    @pytest.mark.settings(rate_limit_tool_per_minute=3)
    async def test_rate_limit(self, client, auth):
        h = auth("C-100001")
        codes = [(await client.get(f"{API}/customers/C-100001", headers=h)).status_code for _ in range(4)]
        assert codes[:3] == [200, 200, 200] and codes[3] == 429


class TestCustomers:
    async def test_profile_masks_contact_data_and_hides_internal_reason(self, client, auth):
        r = await client.get(f"{API}/customers/C-100008", headers=auth("C-100008"))
        body = r.json()
        assert body["email_masked"] == "w***@example.net" and body["phone_masked"] == "***-***-0118"
        assert "email" not in body and "status_reason" not in body and "date_of_birth" not in body
        assert "takeover" not in r.text  # internal status_reason never leaks

    async def test_addresses_masked_for_agent_and_flag_restricted(self, client, auth):
        cust = (await client.get(f"{API}/customers/C-100003/addresses", headers=auth("C-100003"))).json()
        agent = (await client.get(f"{API}/customers/C-100003/addresses", headers=auth(agent="C-100003"))).json()
        assert cust[0]["line1"] == "61 Cedarbrook Lane" and agent[0]["line1"] == "** C*** Lane"
        po_box = next(a for a in cust if a["address_type"] == "po_box")
        assert po_box["restricted_destination"] is True

    async def test_account_summary(self, client, auth):
        body = (await client.get(f"{API}/customers/C-100006/account", headers=auth("C-100006"))).json()
        assert body["loyalty"]["enrolled"] is True
        assert body["store_credit_balance"] == "107.29"  # corked-wine refund as store credit (seed)
        assert all(set(pm) >= {"card_brand", "card_last4"} and "processor_token" not in pm
                   for pm in body["payment_methods"])


class TestOrders:
    async def test_list_orders_filter_sort_paginate(self, client, auth):
        h = auth("C-100001")
        page = (await client.get(f"{API}/customers/C-100001/orders?page_size=1", headers=h)).json()
        assert page["total"] == 2 and page["has_more"] is True and page["items"][0]["order_id"] == "WA-100111"
        asc = (await client.get(f"{API}/customers/C-100001/orders?sort=placed_at", headers=h)).json()
        assert [o["order_id"] for o in asc["items"]] == ["WA-100101", "WA-100111"]
        filt = (await client.get(f"{API}/customers/C-100001/orders?status=completed&fulfillment_type=pickup",
                                 headers=h)).json()
        assert filt["total"] == 0

    async def test_order_detail_lines_and_quantities(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100103", headers=auth("C-100003"))).json()
        assert body["status"] == "partially_fulfilled" and len(body["shipments"]) == 2
        shipped = sum(line["quantity_shipped"] for line in body["lines"])
        delivered = sum(line["quantity_delivered"] for line in body["lines"])
        assert shipped == 12 and delivered == 9  # 9 delivered, 3 in transit (seed scenario)
        assert body["totals"]["grand_total"] == "304.53"

    async def test_status_tracking_history(self, client, auth):
        h = auth("C-100004")
        status = (await client.get(f"{API}/orders/WA-100120/status", headers=h)).json()
        assert status["status"] == "out_for_delivery" and status["status_description"]
        tracking = (await client.get(f"{API}/orders/WA-100120/tracking", headers=h)).json()
        assert tracking["shipments"] and "raw_payload" not in str(tracking)
        history = (await client.get(f"{API}/orders/WA-100120/history", headers=h)).json()
        assert history[0]["to_status"] == "placed"
        assert all("actor_ref" not in h for h in history)  # staff codes stay internal

    async def test_fraud_hold_is_reported_as_category_only(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100108/status", headers=auth("C-100008"))).json()
        assert body["hold_reason_category"] == "account_review" and "fraud" not in str(body)

    async def test_payment_read_is_audited_and_filtered(self, client, auth, container):
        body = (await client.get(f"{API}/orders/WA-100106/payment", headers=auth("C-100006"))).json()
        assert {t["tender_type"] for t in body["tenders"]} == {"gift_card", "card"}
        assert "tok_" not in str(body) and "pi_demo" not in str(body)
        async with container.session_factory() as db:
            n = (await db.execute(select(func.count()).where(AuditLog.action == "payment.read"))).scalar_one()
        assert n == 1

    async def test_chargeback_flag(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100118/payment", headers=auth("C-100010"))).json()
        assert body["chargeback_open"] is True

    async def test_invoice(self, client, auth):
        body = (await client.get(f"{API}/orders/WA-100101/invoice", headers=auth("C-100001"))).json()
        assert body["invoice_number"] == "INV-WA-100101" and body["grand_total"] == "141.27"
        assert body["seller_of_record"]["license_type"].startswith("NJ")


class TestCatalogStoresShipping:
    async def test_search_with_wine_filters_and_location(self, client, auth):
        h = auth("C-100001")
        body = (await client.get(f"{API}/products?color=red&location=NJ&page_size=50", headers=h)).json()
        assert body["total"] > 0
        assert all(p["color"] == "red" and p["price"] for p in body["items"])
        assert all("qty_on_hand" not in str(p) for p in body["items"])

    async def test_price_filter_requires_location(self, client, auth):
        r = await client.get(f"{API}/products?price_max=20", headers=auth("C-100001"))
        assert r.status_code == 422 and r.json()["error"]["code"] == "LOCATION_REQUIRED"
        ok = (await client.get(f"{API}/products?price_max=20&location=NJ&sort=price", headers=auth("C-100001"))).json()
        prices = [float(p["price"]["unit_price"]) for p in ok["items"]]
        assert prices == sorted(prices) and all(p <= 20 for p in prices)

    async def test_non_alcoholic_not_sellable_in_ny(self, client, auth):
        body = (await client.get(f"{API}/products?is_non_alcoholic=true", headers=auth("C-100001"))).json()
        sku = body["items"][0]["sku"]
        ny = (await client.get(f"{API}/products/{sku}/availability?location=NY", headers=auth("C-100001"))).json()
        assert ny["sellable_in_jurisdiction"] is False  # A-06

    async def test_product_detail_wine_information(self, client, auth):
        page = (await client.get(f"{API}/products?q=malbec", headers=auth("C-100001"))).json()
        detail = (await client.get(f"{API}/products/{page['items'][0]['sku']}", headers=auth("C-100001"))).json()
        assert detail["taste"]["body"] and detail["grapes"] and detail["region_path"]
        assert {p["location"] for p in detail["prices"]} <= {"NJ", "NY"}

    async def test_delivery_estimate_in_and_out_of_state(self, client, auth):
        h = auth("C-100001")
        nj = (await client.get(f"{API}/shipping/estimate?postal_code=07030&bottles=3&subtotal=60", headers=h)).json()
        types = {o["type"]: o for o in nj["options"]}
        assert nj["fulfilling_store"] == "NJ-HOB" and types["local_delivery"]["fee"] == "5.99"
        assert types["local_delivery"]["free_delivery_gap"] == "39.00"
        ca = (await client.get(f"{API}/shipping/estimate?postal_code=90210", headers=h)).json()
        assert ca["serviceable"] is False  # A-02

    async def test_store_info(self, client, auth):
        body = (await client.get(f"{API}/stores/NY-CHE", headers=auth("C-100001"))).json()
        assert len(body["hours"]) == 7
        assert any(e["is_closed"] for e in body["upcoming_exceptions"])  # Thanksgiving


class TestSupportTickets:
    async def test_create_and_read_ticket(self, client, auth):
        h = {**auth("C-100001"), "Idempotency-Key": "ticket-key-001"}
        payload = {"category": "delivery_issue", "priority": "P3", "subject": "Driver was late",
                   "summary": "Delivery arrived 2 hours after the window.", "order_id": "WA-100101"}
        r = await client.post(f"{API}/support/tickets", json=payload, headers=h)
        assert r.status_code == 201
        ticket = r.json()
        assert ticket["ticket_number"].startswith("TKT-") and ticket["order_id"] == "WA-100101"
        assert ticket["sla_due_at"] == "2026-11-20T18:00:00Z"  # P3 = 1 business day (A-63)
        got = await client.get(f"{API}/support/tickets/{ticket['ticket_number']}", headers=auth("C-100001"))
        assert got.status_code == 200
        other = await client.get(f"{API}/support/tickets/{ticket['ticket_number']}", headers=auth("C-100002"))
        assert other.status_code == 404

    async def test_internal_notes_are_never_returned(self, client, auth):
        # TKT-500005 has an internal fraud-review note in the seed.
        r = await client.get(f"{API}/support/tickets/TKT-500005", headers=auth("C-100008"))
        assert r.status_code == 200
        assert "unfamiliar IP" not in r.text and "new-device session" not in r.text

    async def test_p1_requires_reason_code(self, client, auth):
        payload = {"category": "fraud", "priority": "P1", "subject": "x" * 5, "summary": "Something urgent here"}
        r = await client.post(f"{API}/support/tickets", json=payload,
                              headers={**auth("C-100001"), "Idempotency-Key": "ticket-key-002"})
        assert r.status_code == 422

    async def test_ticket_cannot_reference_another_customers_order(self, client, auth):
        payload = {"category": "general", "subject": "Hello", "summary": "About someone else's order",
                   "order_id": "WA-100102"}
        r = await client.post(f"{API}/support/tickets", json=payload,
                              headers={**auth("C-100001"), "Idempotency-Key": "ticket-key-003"})
        assert r.status_code == 404
