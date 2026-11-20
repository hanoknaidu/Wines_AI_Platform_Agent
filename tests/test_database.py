#!/usr/bin/env python3
"""Integrity tests for database/schema.sql + database/seed_data.sql.

Each test runs inside a SAVEPOINT that is rolled back, so tests are independent.
They prove the database itself (not only a future API) rejects bad data.

Run:  python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import initialize_db  # noqa: E402  (reuses the same invariants as the build script)


class DatabaseTestCase(unittest.TestCase):
    conn: sqlite3.Connection

    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(":memory:", isolation_level=None)
        cls.conn.execute("PRAGMA foreign_keys = ON")
        cls.conn.executescript((ROOT / "database" / "schema.sql").read_text())
        cls.conn.executescript((ROOT / "database" / "seed_data.sql").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        self.conn.execute("SAVEPOINT t")

    def tearDown(self):
        self.conn.execute("ROLLBACK TO t")
        self.conn.execute("RELEASE t")

    def x(self, sql: str, params=()):
        return self.conn.execute(sql, params)

    def rejects(self, sql: str, params=(), match: str | None = None):
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            self.x(sql, params)
        if match:
            self.assertIn(match, str(ctx.exception))


class TestSeedIsValid(DatabaseTestCase):
    def test_build_checks_pass(self):
        self.assertEqual(initialize_db.verify(self.conn, quiet=True), 0)

    def test_every_table_has_rows(self):
        tables = [r[0] for r in self.x("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        empty = [t for t in tables if self.x(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] == 0]
        self.assertEqual(empty, [])

    def test_seed_covers_kb_stock_statuses(self):
        statuses = {r[0] for r in self.x("SELECT DISTINCT stock_status FROM v_inventory_availability")}
        for s in ("in_stock", "low_stock", "out_of_stock", "backorder", "pre_arrival", "allocated", "coming_soon",
                  "special_order", "discontinued", "in_store_only", "temporarily_unavailable", "not_sellable_in_jurisdiction"):
            self.assertIn(s, statuses)

    def test_seed_covers_real_world_scenarios(self):
        q = lambda sql: self.x(sql).fetchone()[0]
        self.assertGreaterEqual(q("SELECT MAX(c) FROM (SELECT COUNT(*) c FROM orders GROUP BY customer_id)"), 2)  # repeat customers
        self.assertGreaterEqual(q("SELECT MAX(c) FROM (SELECT COUNT(*) c FROM shipments GROUP BY order_id)"), 2)  # partial shipment
        self.assertGreaterEqual(q("SELECT MAX(c) FROM (SELECT COUNT(*) c FROM payments GROUP BY order_id)"), 2)   # split tender
        self.assertGreaterEqual(q("SELECT COUNT(*) FROM payment_transactions WHERE transaction_type='capture' AND payment_id=3"), 2)
        self.assertGreaterEqual(q("SELECT COUNT(*) FROM return_items ri JOIN order_items i USING(order_item_id) WHERE ri.quantity < i.quantity"), 1)
        self.assertGreaterEqual(q("SELECT COUNT(*) FROM refunds WHERE amount_cents < (SELECT grand_total_cents FROM orders o WHERE o.order_id = refunds.order_id)"), 1)


class TestMoneyAndTypes(DatabaseTestCase):
    def test_strict_rejects_decimal_string_money(self):
        self.rejects("UPDATE product_prices SET amount_cents = '12.99' WHERE price_id = 1001", match="INTEGER")

    def test_negative_price_rejected(self):
        self.rejects("UPDATE product_prices SET amount_cents = -1 WHERE price_id = 1001", match="CHECK")

    def test_order_total_must_add_up(self):
        self.rejects("UPDATE orders SET grand_total_cents = grand_total_cents + 1 WHERE order_id = 1", match="CHECK")

    def test_line_math_enforced(self):
        self.rejects("""INSERT INTO order_items (order_id, line_number, variant_id, sku, product_name, brand_name, size_ml,
                        unit_regular_price_cents, unit_price_cents, quantity, line_subtotal_cents, line_total_cents)
                        VALUES (1, 9, 4, 'x', 'x', 'x', 750, 3200, 3200, 2, 6000, 6000)""", match="CHECK")

    def test_overlapping_price_window_rejected(self):
        self.rejects("""INSERT INTO product_prices (store_id, variant_id, price_type, amount_cents, starts_at, change_reason)
                        VALUES (1, 4, 'regular', 3000, '2026-06-01T00:00:00Z', 'test')""", match="overlapping")


class TestOrderSnapshotsAndQuantities(DatabaseTestCase):
    def test_snapshot_price_is_immutable(self):
        self.rejects("UPDATE order_items SET unit_price_cents = 1 WHERE order_item_id = 1", match="immutable")

    def test_order_items_cannot_be_deleted(self):
        self.rejects("DELETE FROM order_items WHERE order_item_id = 1", match="cannot be deleted")

    def test_quantity_cancelled_is_mutable_before_shipping(self):
        self.x("UPDATE order_items SET quantity_cancelled = 1 WHERE order_item_id = 21")  # O-9 not picked yet

    def test_cannot_cancel_shipped_units(self):
        self.rejects("UPDATE order_items SET quantity_cancelled = 1 WHERE order_item_id = 1", match="assigned to a shipment")

    def test_over_shipment_rejected(self):
        self.rejects("INSERT INTO shipment_items VALUES (16, 19, 37, 5)", match="exceeds")

    def test_over_return_rejected(self):
        self.x("""INSERT INTO returns (return_id, rma_number, order_id, customer_id, eligibility, return_method, initiated_via, requested_at)
                  VALUES (99, 'RMA-T', 1, 1, 'needs_review', 'courier_pickup', 'web', '2026-11-19T00:00:00Z')""")
        self.rejects("INSERT INTO return_items (return_id, order_id, order_item_id, quantity, reason_code) VALUES (99, 1, 1, 3, 'leaking')",
                     match="exceeds shipped")

    def test_return_item_must_belong_to_return_order(self):
        self.rejects("INSERT INTO return_items (return_id, order_id, order_item_id, quantity, reason_code) VALUES (1, 1, 1, 1, 'leaking')",
                     match="FOREIGN KEY")


class TestPaymentsAndRefunds(DatabaseTestCase):
    def test_capture_cannot_exceed_authorization(self):
        self.rejects("""INSERT INTO payment_transactions (payment_id, order_id, transaction_type, status, amount_cents,
                        parent_transaction_id, idempotency_key, created_at, processed_at)
                        VALUES (8, 8, 'capture', 'succeeded', 99999999, 81, 't-cap', '2026-11-19T00:00:00Z', '2026-11-19T00:00:00Z')""",
                     match="exceeds the authorized")

    def test_refund_cannot_exceed_capture(self):
        self.rejects("""INSERT INTO refunds (refund_number, order_id, reason_code, method, status, items_amount_cents, amount_cents,
                        initiated_by_type, idempotency_key, created_at)
                        VALUES ('RF-T1', 1, 'leaking', 'original_payment', 'approved', 999999, 999999, 'staff', 't-rf', '2026-11-19T00:00:00Z')""",
                     match="exceed the order total")

    def test_processor_refund_capped_by_captured(self):
        self.rejects("""INSERT INTO payment_transactions (payment_id, order_id, transaction_type, status, amount_cents,
                        parent_transaction_id, refund_id, idempotency_key, created_at)
                        VALUES (2, 2, 'refund', 'pending', 9000, 22, 1, 't-ref', '2026-11-19T00:00:00Z')""",
                     match="captured amount")

    def test_ai_agent_refund_over_150_needs_approval(self):
        self.rejects("""INSERT INTO refunds (refund_number, order_id, reason_code, method, status, items_amount_cents, amount_cents,
                        initiated_by_type, idempotency_key, created_at)
                        VALUES ('RF-T2', 15, 'leaking', 'original_payment', 'approved', 15001, 15001, 'ai_agent', 't-ai', '2026-11-19T00:00:00Z')""",
                     match="CHECK")

    def test_ai_goodwill_capped_at_15(self):
        self.rejects("""INSERT INTO store_credit_transactions (customer_id, entry_type, amount_cents, reason, issued_by_type, created_at)
                        VALUES (1, 'issue_goodwill', 1501, 'test', 'ai_agent', '2026-11-19T00:00:00Z')""", match="CHECK")

    def test_store_credit_cannot_go_negative(self):
        self.rejects("""INSERT INTO store_credit_transactions (customer_id, entry_type, amount_cents, payment_id, reason, issued_by_type, created_at)
                        VALUES (2, 'redeem', -100, 2, 'test', 'system', '2026-11-19T00:00:00Z')""", match="insufficient")

    def test_card_must_belong_to_paying_customer(self):
        self.rejects("""INSERT INTO payments (order_id, customer_id, tender_type, payment_method_id, processor, amount_cents, created_at, updated_at)
                        VALUES (1, 1, 'card', 3, 'card_gateway', 100, '2026-11-19T00:00:00Z', '2026-11-19T00:00:00Z')""", match="FOREIGN KEY")

    def test_restocking_fee_only_on_change_of_mind(self):
        self.rejects("""INSERT INTO refunds (refund_number, order_id, reason_code, method, items_amount_cents, restocking_fee_cents, amount_cents,
                        initiated_by_type, idempotency_key, created_at)
                        VALUES ('RF-T3', 1, 'leaking', 'original_payment', 1000, 150, 850, 'staff', 't-rs', '2026-11-19T00:00:00Z')""", match="CHECK")


class TestComplianceRules(DatabaseTestCase):
    def test_under_21_account_rejected(self):
        self.rejects("""INSERT INTO customers (customer_number, first_name, last_name, email, date_of_birth, created_at, updated_at)
                        VALUES ('C-T1', 'Teen', 'User', 'teen@example.com', '2006-01-01', '2026-11-19T00:00:00Z', '2026-11-19T00:00:00Z')""", match="CHECK")

    def test_out_of_state_shipping_rejected(self):
        self.x("DELETE FROM order_addresses WHERE order_id = 1 AND address_role = 'shipping'")
        self.rejects("""INSERT INTO order_addresses (order_id, address_role, recipient_name, line1, city, state_code, postal_code)
                        VALUES (1, 'shipping', 'X', '1 Main St', 'Philadelphia', 'PA', '19103')""", match="state")  # A-01 trigger or NJ/NY CHECK

    def test_cross_state_fulfillment_rejected(self):
        self.x("DELETE FROM order_addresses WHERE order_id = 1 AND address_role = 'shipping'")
        self.rejects("""INSERT INTO order_addresses (order_id, address_role, recipient_name, line1, city, state_code, postal_code)
                        VALUES (1, 'shipping', 'X', '1 Main St', 'New York', 'NY', '10001')""", match="A-01")

    def test_po_box_shipping_rejected(self):
        self.x("DELETE FROM order_addresses WHERE order_id = 1 AND address_role = 'shipping'")
        self.rejects("""INSERT INTO order_addresses (order_id, address_role, recipient_name, line1, city, state_code, postal_code, address_type)
                        VALUES (1, 'shipping', 'X', 'PO Box 1', 'Hoboken', 'NJ', '07030', 'po_box')""", match="CHECK")

    def test_handoff_requires_id_check(self):
        self.rejects("UPDATE shipments SET status = 'delivered', delivered_at = '2026-11-19T22:00:00Z' WHERE shipment_id = 17", match="CHECK")

    def test_warehouse_must_belong_to_order_store(self):
        self.rejects("""INSERT INTO shipments (shipment_number, order_id, store_id, warehouse_id, method, carrier, created_at, updated_at)
                        VALUES ('SH-T', 1, 1, 3, 'local_delivery', 'store_driver', '2026-11-19T00:00:00Z', '2026-11-19T00:00:00Z')""",
                     match="FOREIGN KEY")

    def test_address_limit_of_10(self):
        for i in range(8):  # customer 1 already has 2
            self.x("""INSERT INTO customer_addresses (customer_id, recipient_name, line1, city, state_code, postal_code)
                      VALUES (1, 'O', ?, 'Hoboken', 'NJ', '07030')""", (f"{i} Test St",))
        self.rejects("""INSERT INTO customer_addresses (customer_id, recipient_name, line1, city, state_code, postal_code)
                        VALUES (1, 'O', '99 Test St', 'Hoboken', 'NJ', '07030')""", match="A-75")

    def test_one_promo_code_per_order(self):
        self.x("INSERT INTO order_discounts (order_id, discount_type, description, amount_cents) VALUES (2, 'promo_code', 'a', 0)")
        self.rejects("INSERT INTO order_discounts (order_id, discount_type, description, amount_cents) VALUES (2, 'promo_code', 'b', 0)", match="UNIQUE")


class TestAppendOnly(DatabaseTestCase):
    def test_audit_log_is_append_only(self):
        self.rejects("UPDATE audit_logs SET outcome = 'success' WHERE audit_id = 1", match="append-only")
        self.rejects("DELETE FROM audit_logs WHERE audit_id = 1", match="append-only")

    def test_ledgers_are_append_only(self):
        for table in ("inventory_movements", "order_status_history", "shipment_tracking_events", "ticket_messages",
                      "store_credit_transactions", "gift_card_transactions", "loyalty_point_transactions", "payment_transactions"):
            with self.subTest(table=table):
                self.rejects(f'DELETE FROM "{table}"', match="append-only")

    def test_settled_payment_transaction_is_frozen(self):
        self.rejects("UPDATE payment_transactions SET amount_cents = 1 WHERE transaction_id = 11", match="pending")

    def test_pending_transaction_can_settle(self):
        self.x("UPDATE payment_transactions SET status = 'succeeded', processed_at = '2026-11-19T00:00:00Z' WHERE transaction_id = 188")


if __name__ == "__main__":
    unittest.main()
