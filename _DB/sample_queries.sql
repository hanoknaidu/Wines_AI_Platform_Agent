-- =============================================================================
-- Sample customer-support queries
-- Each block starts with "-- @query <id>: <title>" so scripts/initialize_db.py
-- --demo can run and print them. Literals stand in for API parameters
-- (in phase 2 these become bound parameters, never string concatenation).
-- Tool names refer to _KB/00_system/tool-reference.md.
-- =============================================================================

-- @query Q01: get_customer_profile - verified customer summary with masked contact data
SELECT c.customer_number,
       c.first_name || ' ' || c.last_name                                         AS name,
       substr(c.email, 1, 1) || '***@' || substr(c.email, instr(c.email, '@') + 1) AS email_masked,
       '***-***-' || substr(c.phone_e164, -4)                                     AS phone_masked,
       c.status, av.age_verification_status, b.loyalty_tier, b.loyalty_points,
       printf('$%.2f', b.store_credit_cents / 100.0)                              AS store_credit,
       (SELECT COUNT(*) FROM customer_addresses a WHERE a.customer_id = c.customer_id AND a.deleted_at IS NULL) AS saved_addresses
FROM customers c
JOIN v_customer_age_verification av ON av.customer_id = c.customer_id
JOIN v_customer_balances b ON b.customer_id = c.customer_id
WHERE lower(c.email) = lower('Olivia.Martinez@example.com');

-- @query Q02: list_orders - a customer's orders, newest first
SELECT o.order_number, o.placed_at, s.store_code, o.fulfillment_type, o.status, o.payment_status,
       printf('$%.2f', o.grand_total_cents / 100.0) AS total,
       (SELECT SUM(quantity) FROM order_items i WHERE i.order_id = o.order_id) AS bottles
FROM orders o JOIN stores s ON s.store_id = o.store_id
WHERE o.customer_id = (SELECT customer_id FROM customers WHERE customer_number = 'C-100001')
ORDER BY o.placed_at DESC;

-- @query Q03: get_order_status - "Where is my order?" for a partially shipped order
SELECT o.order_number, o.status AS order_status, sh.shipment_number, sh.carrier, sh.tracking_number,
       sh.status AS shipment_status, sh.estimated_delivery_at,
       (SELECT group_concat(si.quantity || ' x ' || i.product_name, '; ')
          FROM shipment_items si JOIN order_items i ON i.order_item_id = si.order_item_id
         WHERE si.shipment_id = sh.shipment_id) AS contents,
       (SELECT e.description || ' @ ' || e.location_city || ', ' || e.location_state
          FROM shipment_tracking_events e WHERE e.shipment_id = sh.shipment_id
         ORDER BY e.occurred_at DESC LIMIT 1) AS latest_event
FROM orders o JOIN shipments sh ON sh.order_id = o.order_id
WHERE o.order_number = 'WA-100103'
ORDER BY sh.shipment_id;

-- @query Q04: track_shipment - full tracking timeline incl. failed attempts
SELECT e.occurred_at, e.event_code, e.description, e.location_city, e.source
FROM shipment_tracking_events e JOIN shipments sh ON sh.shipment_id = e.shipment_id
WHERE sh.order_id = (SELECT order_id FROM orders WHERE order_number = 'WA-100107')
ORDER BY e.occurred_at;

-- @query Q05: get_order - per-line lifecycle (ordered / cancelled / shipped / returned / refunded)
SELECT f.line_number, f.product_name, f.vintage_year, f.qty_ordered, f.qty_cancelled, f.qty_shipped,
       f.qty_delivered, f.qty_returned, f.qty_refunded, printf('$%.2f', f.amount_refunded_cents / 100.0) AS refunded
FROM v_order_item_fulfillment f
WHERE f.order_id IN (SELECT order_id FROM orders WHERE order_number IN ('WA-100103','WA-100111','WA-100114'))
ORDER BY f.order_id, f.line_number;

-- @query Q06: order timeline - status history for a failed-delivery order
SELECT h.changed_at, h.from_status, h.to_status, h.actor_type, h.actor_ref, h.note
FROM order_status_history h
WHERE h.order_id = (SELECT order_id FROM orders WHERE order_number = 'WA-100110')
ORDER BY h.changed_at;

-- @query Q07: create_return_request pre-check - returnable units and claim windows (A-30..A-35)
--          (reference "now" fixed to 2026-11-19 so results are stable)
SELECT o.order_number, s.state_code, i.line_number, i.product_name,
       f.qty_delivered - f.qty_returned                                   AS returnable_units,
       date(sh.delivered_at)                                               AS delivered_on,
       CAST(julianday('2026-11-19') - julianday(sh.delivered_at) AS INTEGER) AS days_since_delivery,
       CASE WHEN julianday('2026-11-19') - julianday(sh.delivered_at) <= 2  THEN 'open' ELSE 'closed' END AS damage_window_48h,
       CASE WHEN julianday('2026-11-19') - julianday(sh.delivered_at) <= 30 THEN 'open' ELSE 'closed' END AS defect_window_30d,
       CASE WHEN s.state_code = 'NY' THEN 'not offered (A-35)'
            WHEN i.is_final_sale = 1 THEN 'final sale'
            WHEN julianday('2026-11-19') - julianday(sh.delivered_at) <= 14 THEN 'open (15% restocking to card, A-34)'
            ELSE 'closed' END                                              AS change_of_mind
FROM orders o
JOIN stores s ON s.store_id = o.store_id
JOIN order_items i ON i.order_id = o.order_id
JOIN v_order_item_fulfillment f ON f.order_item_id = i.order_item_id
JOIN shipment_items si ON si.order_item_id = i.order_item_id
JOIN shipments sh ON sh.shipment_id = si.shipment_id AND sh.status IN ('delivered','picked_up')
WHERE o.order_number IN ('WA-100114','WA-100116','WA-100104');

-- @query Q08: get_return_status / "Where is my refund?"
SELECT r.rma_number, r.status AS return_status, r.eligibility, f.refund_number, f.status AS refund_status, f.method,
       printf('$%.2f', f.amount_cents / 100.0) AS amount, f.requires_human_approval, f.completed_at,
       t.processor_reference AS processor_refund_ref
FROM refunds f
LEFT JOIN returns r ON r.return_id = f.return_id
LEFT JOIN payment_transactions t ON t.refund_id = f.refund_id
WHERE f.order_id IN (SELECT order_id FROM orders WHERE customer_id IN
                     (SELECT customer_id FROM customers WHERE customer_number IN ('C-100003','C-100010')))
ORDER BY f.created_at;

-- @query Q09: issue_refund guard - what is still refundable per tender (split payment)
SELECT o.order_number, pb.tender_type, pb.status,
       printf('$%.2f', pb.authorized_cents / 100.0) AS authorized,
       printf('$%.2f', pb.captured_cents / 100.0)   AS captured,
       printf('$%.2f', pb.voided_cents / 100.0)     AS voided,
       printf('$%.2f', pb.refunded_cents / 100.0)   AS refunded,
       printf('$%.2f', (pb.captured_cents - pb.refunded_cents) / 100.0) AS refundable,
       CASE WHEN pb.chargeback_cents > 0 OR EXISTS (SELECT 1 FROM payment_transactions t WHERE t.payment_id = pb.payment_id
                 AND t.transaction_type = 'chargeback' AND t.status = 'pending')
            THEN 'chargeback open: do not refund (RF-R5)' ELSE 'ok' END AS refund_guard
FROM v_payment_balances pb JOIN orders o ON o.order_id = pb.order_id
WHERE o.order_number IN ('WA-100106','WA-100114','WA-100118','WA-100120')
ORDER BY o.order_number, pb.payment_id;

-- @query Q10: check_inventory - stock_status and qty bucket per store (never exact counts)
SELECT v.sku, c.product_name, st.store_code, a.stock_status, a.qty_bucket, a.sellable_in_jurisdiction,
       a.allocation_limit, a.next_arrival_estimate
FROM v_inventory_availability a
JOIN product_variants v ON v.variant_id = a.variant_id
JOIN v_product_catalog c ON c.variant_id = a.variant_id
JOIN stores st ON st.store_id = a.store_id
WHERE v.sku IN ('WN-VDC-BRU-2019-750','NA-CLZ-SPR-NV-750','WN-ADV-MAL-2023-750','WN-STL-CDP-2025-1500','WN-ARD-MIL-2015-750')
ORDER BY v.sku, st.store_code;

-- @query Q11: get_price - live price incl. sale, compare-at and case-discount eligibility
SELECT v.sku, st.store_code,
       printf('$%.2f', p.regular_price_cents / 100.0) AS regular,
       CASE WHEN p.sale_price_cents IS NOT NULL THEN printf('$%.2f', p.sale_price_cents / 100.0) END AS sale,
       p.sale_ends_at, p.compare_at_verified, v.case_discount_eligible
FROM v_current_prices p
JOIN product_variants v ON v.variant_id = p.variant_id
JOIN stores st ON st.store_id = p.store_id
WHERE v.sku IN ('WN-ARD-BRT-NV-750','WN-BMR-RIO-2019-750','WN-HCC-NCS-2022-750')
ORDER BY v.sku, st.store_code;

-- @query Q12: search_products - "a crisp, dry white under $35" for an NJ address, orderable now
SELECT c.sku, c.product_name, c.vintage_year, c.region_path, c.grapes,
       printf('$%.2f', p.effective_price_cents / 100.0) AS price, a.stock_status, c.certifications
FROM v_product_catalog c
JOIN v_current_prices p ON p.variant_id = c.variant_id AND p.store_id = 1
JOIN v_inventory_availability a ON a.variant_id = c.variant_id AND a.store_id = 1
WHERE c.wine_color = 'white' AND c.sweetness = 'dry' AND c.acidity = 'crisp' AND c.size_ml = 750
  AND p.effective_price_cents <= 3500
  AND a.stock_status IN ('in_stock','low_stock','allocated')
ORDER BY p.effective_price_cents;

-- @query Q13: certified organic / biodynamic wines with evidence (ORG-R1: no evidence, no tag)
SELECT c.sku, c.product_name, vc.certification_type, vc.evidence_level, vc.certifier, vc.verified_at, vc.status
FROM variant_certifications vc JOIN v_product_catalog c ON c.variant_id = vc.variant_id
WHERE vc.certification_type IN ('usda_organic','eu_organic','demeter','biodyvin','practicing_organic')
ORDER BY vc.status, c.product_name;

-- @query Q14: get_active_promotions for the NJ Store (reference time 2026-11-19)
SELECT pr.code, pr.name, pr.promo_type,
       CASE WHEN pr.percent_off_bps IS NOT NULL THEN printf('%.0f%%', pr.percent_off_bps / 100.0)
            WHEN pr.amount_off_cents IS NOT NULL THEN printf('$%.2f', pr.amount_off_cents / 100.0)
            WHEN pr.promo_type = 'mixed_case' THEN 'tiered'
            WHEN pr.promo_type = 'free_delivery' THEN 'free delivery' END AS value,
       printf('$%.2f', pr.min_subtotal_cents / 100.0) AS minimum, pr.is_stackable, pr.ends_at,
       (SELECT group_concat(t.min_bottle_equivalents || '+ = ' || (t.percent_off_bps / 100) || '%', ', ')
          FROM promotion_tiers t WHERE t.promotion_id = pr.promotion_id) AS tiers
FROM promotions pr
WHERE pr.status = 'active' AND (pr.store_id IS NULL OR pr.store_id = 1)
  AND pr.starts_at <= '2026-11-19T12:00:00Z' AND (pr.ends_at IS NULL OR pr.ends_at > '2026-11-19T12:00:00Z');

-- @query Q15: cart check - mixed-case bottle equivalents and allocation warnings (A-26, A-50)
SELECT ca.cart_token, v.sku, ci.quantity, v.case_discount_eligible,
       ci.quantity * v.bottle_equiv_milli / 1000.0 AS bottle_equivalents,
       l.allocation_limit,
       CASE WHEN l.allocation_limit IS NOT NULL AND ci.quantity > l.allocation_limit THEN 'allocation_limit'
            WHEN ci.quantity > l.max_per_order THEN 'max_per_order' END AS warning
FROM carts ca
JOIN cart_items ci ON ci.cart_id = ca.cart_id
JOIN product_variants v ON v.variant_id = ci.variant_id
JOIN product_listings l ON l.store_id = ca.store_id AND l.variant_id = ci.variant_id
WHERE ca.status = 'active'
ORDER BY ca.cart_token, v.sku;

-- @query Q16: agent authority checks for a customer (A-60 claims in 60 days, A-61 goodwill in 90 days)
SELECT c.customer_number,
       (SELECT COALESCE(SUM(ri.quantity), 0) FROM return_items ri JOIN returns r ON r.return_id = ri.return_id
         WHERE r.customer_id = c.customer_id AND ri.reason_code = 'corked_or_flawed'
           AND r.requested_at >= datetime('2026-11-19', '-60 days'))            AS defective_bottles_60d,
       (SELECT COUNT(*) FROM store_credit_transactions s WHERE s.customer_id = c.customer_id
           AND s.entry_type = 'issue_goodwill' AND s.created_at >= datetime('2026-11-19', '-90 days')) AS goodwill_credits_90d,
       CASE WHEN (SELECT COUNT(*) FROM store_credit_transactions s WHERE s.customer_id = c.customer_id
                   AND s.entry_type = 'issue_goodwill' AND s.created_at >= datetime('2026-11-19', '-90 days')) = 0
            THEN 'may issue up to $15' ELSE 'escalate to human' END        AS goodwill_decision
FROM customers c WHERE c.customer_number IN ('C-100001','C-100004','C-100006');

-- @query Q17: human queue - open escalations by priority and SLA
SELECT t.ticket_number, t.priority, t.reason_code, t.category, t.status, t.assigned_team,
       su.full_name AS assignee, t.sla_due_at, o.order_number
FROM support_tickets t
LEFT JOIN staff_users su ON su.staff_id = t.assigned_staff_id
LEFT JOIN orders o ON o.order_id = t.order_id
WHERE t.status NOT IN ('resolved','closed')
ORDER BY t.priority, t.sla_due_at;

-- @query Q18: ticket thread as the customer sees it (internal notes excluded)
SELECT m.created_at, m.author_type, m.body
FROM ticket_messages m JOIN support_tickets t ON t.ticket_id = m.ticket_id
WHERE t.ticket_number = 'TKT-500002' AND m.visibility = 'public'
ORDER BY m.created_at;

-- @query Q19: price history for a SKU (A-40 price lock: orders keep their snapshot)
SELECT st.store_code, p.price_type, printf('$%.2f', p.amount_cents / 100.0) AS price, p.starts_at, p.ends_at, p.change_reason,
       (SELECT COUNT(*) FROM order_items i WHERE i.price_id = p.price_id) AS order_lines_using_this_price
FROM product_prices p JOIN stores st ON st.store_id = p.store_id
JOIN product_variants v ON v.variant_id = p.variant_id
WHERE v.sku IN ('WN-HCC-NCS-2022-750','WN-ARD-BRT-NV-750')
ORDER BY v.sku, st.store_code, p.starts_at;

-- @query Q20: audit trail - every agent action and denial for one customer
SELECT a.occurred_at, a.actor_type, a.actor_ref, a.action, a.entity_type, a.entity_id, a.outcome, a.reason
FROM audit_logs a
WHERE a.customer_id = (SELECT customer_id FROM customers WHERE customer_number = 'C-100008')
ORDER BY a.occurred_at;
