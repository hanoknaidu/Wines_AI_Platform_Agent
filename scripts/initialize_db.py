#!/usr/bin/env python3
"""Create, seed and verify the Wines AI Platform Agent e-commerce database.

Builds database/ecommerce.db from database/schema.sql and database/seed_data.sql,
then verifies it:
  * PRAGMA integrity_check and foreign_key_check
  * every foreign key has a supporting index
  * business invariants (order totals, discount allocations, payment and refund
    caps, inventory ledger vs balances, reservations, A-01 state rule, ...)

The build is written to a temporary file and moved into place only if every
step and check passes, so a failed run never leaves a half-built database.

Usage:
  python3 scripts/initialize_db.py                 # build (refuses to overwrite)
  python3 scripts/initialize_db.py --force         # rebuild an existing database
  python3 scripts/initialize_db.py --force --demo  # rebuild and run sample queries
  python3 scripts/initialize_db.py --verify-only   # check an existing database
  python3 scripts/initialize_db.py --demo-only     # run sample queries on existing db
  python3 scripts/initialize_db.py --schema-only --db /tmp/empty.db

Exit codes: 0 = success, 1 = SQL error or failed checks, 2 = bad input/environment.
Standard library only; requires SQLite >= 3.38 (STRICT tables, JSON1, UPDATE FROM).
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / "database"
SCHEMA = DB_DIR / "schema.sql"
SEED = DB_DIR / "seed_data.sql"
SAMPLES = DB_DIR / "sample_queries.sql"
DEFAULT_DB = DB_DIR / "ecommerce.db"
MIN_SQLITE = (3, 38, 0)

# Each invariant is a query that must return zero rows.
INVARIANTS: list[tuple[str, str]] = [
    ("order header totals equal the sum of their lines", """
        SELECT o.order_id FROM orders o
        JOIN (SELECT order_id, SUM(line_subtotal_cents) s, SUM(discount_cents) d, SUM(tax_cents) t
              FROM order_items GROUP BY order_id) a ON a.order_id = o.order_id
        WHERE o.items_subtotal_cents <> a.s OR o.discount_total_cents <> a.d OR o.tax_total_cents < a.t"""),
    ("every order has at least one line", """
        SELECT order_id FROM orders WHERE order_id NOT IN (SELECT order_id FROM order_items)"""),
    ("order discounts equal the sum of their line allocations", """
        SELECT d.order_discount_id FROM order_discounts d
        LEFT JOIN order_discount_allocations a ON a.order_discount_id = d.order_discount_id
        GROUP BY d.order_discount_id HAVING d.amount_cents <> COALESCE(SUM(a.amount_cents), 0)"""),
    ("line discounts equal their allocations", """
        SELECT i.order_item_id FROM order_items i
        LEFT JOIN order_discount_allocations a ON a.order_item_id = i.order_item_id
        GROUP BY i.order_item_id HAVING i.discount_cents <> COALESCE(SUM(a.amount_cents), 0)"""),
    ("tenders on an order add up to the order total", """
        SELECT o.order_id FROM orders o JOIN payments p ON p.order_id = o.order_id
        WHERE p.status NOT IN ('failed')
        GROUP BY o.order_id HAVING SUM(p.amount_cents) <> o.grand_total_cents"""),
    ("captured + voided never exceeds authorized; refunded never exceeds captured", """
        SELECT payment_id FROM v_payment_balances
        WHERE captured_cents + voided_cents > authorized_cents OR refunded_cents > captured_cents"""),
    ("succeeded card refunds are backed by processor refund transactions", """
        SELECT f.refund_id FROM refunds f
        LEFT JOIN payment_transactions t ON t.refund_id = f.refund_id AND t.status = 'succeeded'
        WHERE f.method = 'original_payment' AND f.status = 'succeeded'
        GROUP BY f.refund_id HAVING COALESCE(SUM(t.amount_cents), 0) <> f.amount_cents"""),
    ("succeeded store-credit refunds are backed by a credit entry", """
        SELECT f.refund_id FROM refunds f
        LEFT JOIN store_credit_transactions s ON s.refund_id = f.refund_id
        WHERE f.method = 'store_credit' AND f.status = 'succeeded'
        GROUP BY f.refund_id HAVING COALESCE(SUM(s.amount_cents), 0) <> f.amount_cents"""),
    ("refund line amounts equal refund amount minus shipping and tip", """
        SELECT f.refund_id FROM refunds f JOIN refund_items ri ON ri.refund_id = f.refund_id
        GROUP BY f.refund_id
        HAVING SUM(ri.amount_cents) <> f.amount_cents - f.shipping_amount_cents - f.tip_amount_cents"""),
    ("inventory ledger reconciles to on-hand balances", """
        SELECT il.warehouse_id, il.variant_id FROM inventory_levels il
        WHERE il.qty_on_hand <> COALESCE((SELECT SUM(m.quantity_delta) FROM inventory_movements m
              WHERE m.warehouse_id = il.warehouse_id AND m.variant_id = il.variant_id), 0)"""),
    ("every inventory movement has a balance row", """
        SELECT DISTINCT m.warehouse_id, m.variant_id FROM inventory_movements m
        LEFT JOIN inventory_levels il ON il.warehouse_id = m.warehouse_id AND il.variant_id = m.variant_id
        WHERE il.variant_id IS NULL"""),
    ("reserved quantity equals active reservations", """
        SELECT il.warehouse_id, il.variant_id FROM inventory_levels il
        WHERE il.qty_reserved <> COALESCE((SELECT SUM(r.quantity) FROM inventory_reservations r
              WHERE r.warehouse_id = il.warehouse_id AND r.variant_id = il.variant_id AND r.status = 'active'), 0)"""),
    ("shipped quantity never exceeds ordered minus cancelled", """
        SELECT order_item_id FROM v_order_item_fulfillment WHERE qty_shipped > qty_ordered - qty_cancelled"""),
    ("returned quantity never exceeds shipped quantity", """
        SELECT order_item_id FROM v_order_item_fulfillment WHERE qty_returned > qty_shipped"""),
    ("shipping address is in the fulfilling store's state (A-01)", """
        SELECT o.order_id FROM orders o JOIN stores s ON s.store_id = o.store_id
        JOIN order_addresses a ON a.order_id = o.order_id AND a.address_role = 'shipping'
        WHERE a.state_code <> s.state_code"""),
    ("non-pickup orders have a shipping address; pickup orders do not", """
        SELECT o.order_id FROM orders o
        LEFT JOIN order_addresses a ON a.order_id = o.order_id AND a.address_role = 'shipping'
        WHERE (o.fulfillment_type = 'pickup') = (a.order_id IS NOT NULL)"""),
    ("order status matches the latest status-history entry", """
        SELECT o.order_id FROM orders o
        WHERE o.status <> (SELECT h.to_status FROM order_status_history h WHERE h.order_id = o.order_id
                           ORDER BY h.changed_at DESC, h.history_id DESC LIMIT 1)"""),
    ("store credit, gift card and loyalty balances are non-negative", """
        SELECT 'store_credit', customer_id FROM store_credit_transactions GROUP BY customer_id HAVING SUM(amount_cents) < 0
        UNION ALL SELECT 'gift_card', gift_card_id FROM gift_card_transactions GROUP BY gift_card_id HAVING SUM(amount_cents) < 0
        UNION ALL SELECT 'loyalty', customer_id FROM loyalty_point_transactions GROUP BY customer_id HAVING SUM(points) < 0"""),
    ("orders are placed only by customers who were 21+ at placement (A-04)", """
        SELECT o.order_id FROM orders o JOIN customers c ON c.customer_id = o.customer_id
        WHERE c.date_of_birth > date(o.placed_at, '-21 years')"""),
    ("released (shipped/picked-up) orders belong to age-verified customers (A-05)", """
        SELECT DISTINCT s.order_id FROM shipments s JOIN orders o ON o.order_id = s.order_id
        JOIN v_customer_age_verification v ON v.customer_id = o.customer_id
        WHERE s.shipped_at IS NOT NULL AND v.age_verification_status <> 'verified'"""),
    ("non-alcoholic wine is never sold by the NY Store (A-06)", """
        SELECT i.order_item_id FROM order_items i JOIN orders o ON o.order_id = i.order_id
        JOIN stores s ON s.store_id = o.store_id JOIN product_variants v ON v.variant_id = i.variant_id
        JOIN products p ON p.product_id = v.product_id
        WHERE s.state_code = 'NY' AND p.product_type = 'non_alcoholic_wine'"""),
]


def log(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg)


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")          # per-connection in SQLite
    return conn


def run_script(conn: sqlite3.Connection, path: Path) -> None:
    try:
        conn.executescript(path.read_text(encoding="utf-8"))
    except sqlite3.Error as exc:
        raise RuntimeError(f"{path.name}: {exc}") from exc


def unindexed_foreign_keys(conn: sqlite3.Connection) -> list[str]:
    """FK column lists that are not the leading columns of some index or the PK."""
    problems = []
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    for table in tables:
        fks: dict[int, list[str]] = {}
        for row in conn.execute(f'PRAGMA foreign_key_list("{table}")'):
            fks.setdefault(row[0], []).append(row[3])
        if not fks:
            continue
        prefixes = []
        pk = [r[1] for r in sorted(conn.execute(f'PRAGMA table_info("{table}")'), key=lambda r: r[5]) if r[5] > 0]
        if pk:
            prefixes.append(pk)
        for idx in conn.execute(f'PRAGMA index_list("{table}")'):
            if idx[4]:                                     # skip partial indexes
                continue
            cols = [r[2] for r in conn.execute(f'PRAGMA index_info("{idx[1]}")')]
            prefixes.append(cols)
        for cols in fks.values():
            if not any(p[:len(cols)] == cols for p in prefixes):
                problems.append(f"{table}({', '.join(cols)})")
    return problems


def verify(conn: sqlite3.Connection, quiet: bool) -> int:
    failures = 0
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    ok = integrity == "ok"
    failures += not ok
    log(f"  [{'PASS' if ok else 'FAIL'}] integrity_check: {integrity}", quiet and ok)

    fk_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
    failures += bool(fk_rows)
    log(f"  [{'PASS' if not fk_rows else 'FAIL'}] foreign_key_check: {len(fk_rows)} violation(s)", quiet and not fk_rows)
    for row in fk_rows[:10]:
        log(f"         {row}")

    missing = unindexed_foreign_keys(conn)
    failures += bool(missing)
    log(f"  [{'PASS' if not missing else 'FAIL'}] every foreign key is indexed"
        + (f": missing {', '.join(missing)}" if missing else ""), quiet and not missing)

    for name, sql in INVARIANTS:
        rows = conn.execute(sql).fetchall()
        failures += bool(rows)
        log(f"  [{'PASS' if not rows else 'FAIL'}] {name}" + (f" -> {rows[:5]}" if rows else ""), quiet and not rows)
    return failures


def print_counts(conn: sqlite3.Connection) -> None:
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    counts = [(t, conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]) for t in tables]
    width = max(len(t) for t, _ in counts)
    print(f"\nRow counts ({len(tables)} tables, {sum(c for _, c in counts)} rows):")
    for i in range(0, len(counts), 2):
        pair = counts[i:i + 2]
        print("   " + "    ".join(f"{t:<{width}} {c:>5}" for t, c in pair))


def parse_samples(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^-- @query\s+", text, flags=re.MULTILINE)[1:]
    queries = []
    for part in parts:
        title, _, body = part.partition("\n")
        queries.append((title.strip(), body.strip().rstrip(";")))
    return queries


def print_table(cursor: sqlite3.Cursor, max_width: int = 42) -> None:
    headers = [d[0] for d in cursor.description]
    rows = [["" if v is None else str(v) for v in r] for r in cursor.fetchall()]
    clip = lambda s: s if len(s) <= max_width else s[: max_width - 1] + "~"
    rows = [[clip(v) for v in r] for r in rows]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    print("  " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for r in rows:
        print("  " + " | ".join(v.ljust(w) for v, w in zip(r, widths)))
    print(f"  ({len(rows)} row{'s' if len(rows) != 1 else ''})")


def run_demo(conn: sqlite3.Connection) -> int:
    failures = 0
    for title, sql in parse_samples(SAMPLES):
        print(f"\n== {title}")
        try:
            print_table(conn.execute(sql))
        except sqlite3.Error as exc:
            failures += 1
            print(f"  ERROR: {exc}")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description="Create, seed and verify the e-commerce SQLite database.")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"database path (default: {DEFAULT_DB.relative_to(ROOT)})")
    ap.add_argument("--force", action="store_true", help="overwrite an existing database file")
    ap.add_argument("--schema-only", action="store_true", help="create the schema without seed data")
    ap.add_argument("--verify-only", action="store_true", help="only verify an existing database")
    ap.add_argument("--demo", action="store_true", help="run database/sample_queries.sql after building")
    ap.add_argument("--demo-only", action="store_true", help="only run the sample queries on an existing database")
    ap.add_argument("--quiet", action="store_true", help="print only failures and the summary")
    args = ap.parse_args()

    if sqlite3.sqlite_version_info < MIN_SQLITE:
        print(f"SQLite {sqlite3.sqlite_version} is too old; need {'.'.join(map(str, MIN_SQLITE))}+", file=sys.stderr)
        return 2
    db_path = args.db.resolve()

    if args.verify_only or args.demo_only:
        if not db_path.exists():
            print(f"{db_path} does not exist; build it first", file=sys.stderr)
            return 2
        conn = connect(db_path)
        try:
            if args.demo_only:
                return 1 if run_demo(conn) else 0
            log(f"Verifying {db_path}")
            failures = verify(conn, args.quiet)
            print(f"\n{'OK' if not failures else f'FAILED: {failures} check(s)'}")
            return 1 if failures else 0
        finally:
            conn.close()

    for f in (SCHEMA, SEED, SAMPLES):
        if not f.exists():
            print(f"missing {f}", file=sys.stderr)
            return 2
    if db_path.exists() and not args.force:
        print(f"{db_path} already exists. Re-run with --force to rebuild it.", file=sys.stderr)
        return 2

    db_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".ecommerce-build-", suffix=".db", dir=db_path.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    conn = connect(tmp)
    try:
        log(f"SQLite {sqlite3.sqlite_version}: building {db_path.name}", args.quiet)
        run_script(conn, SCHEMA)
        log(f"  applied {SCHEMA.name}", args.quiet)
        if not args.schema_only:
            run_script(conn, SEED)
            log(f"  applied {SEED.name}", args.quiet)
        log("Verifying", args.quiet)
        failures = verify(conn, args.quiet)
        demo_failures = run_demo(conn) if args.demo and not args.schema_only else 0
        if failures or demo_failures:
            print(f"\nFAILED: {failures} check(s), {demo_failures} sample query error(s); {db_path.name} not written",
                  file=sys.stderr)
            return 1
        if not args.quiet:
            print_counts(conn)
        conn.execute("PRAGMA optimize")
        conn.commit()
        conn.close()
        conn = None
        os.chmod(tmp, 0o644)                  # mkstemp creates 0600
        os.replace(tmp, db_path)
        print(f"\nOK: {db_path}")
        return 0
    except RuntimeError as exc:
        print(f"\nERROR {exc}", file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()
        if tmp.exists():
            tmp.unlink()


if __name__ == "__main__":
    sys.exit(main())
