---
id: KB-RTN-004
title: Wrong or Missing Items (Including "Delivered but Not Received")
category: returns
subcategory: wrong-missing
doc_type: workflow
intents: [claim.wrong_or_missing, order.status]
tools: [get_order, get_order_status, track_shipment, create_return_request, request_evidence_upload, issue_refund, add_to_cart, reschedule_delivery, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: customer-support
status: active
depends_on_assumptions: [A-22, A-23, A-24, A-31, A-36, A-60, A-62]
related: [KB-RTN-001, KB-STK-002, KB-STK-003, KB-ORD-007, KB-SYS-006]
---

# Wrong or Missing Items

## 1. Policy (A-31)

Report within **7 days** of delivery/pickup. We fix our mistakes at no cost in both states: no fees, no restocking, free pickup of wrong items.

## 2. First, rule out expected differences

Before treating something as wrong or missing, check `get_order`:

| What the customer sees | Check | Expected? |
|---|---|---|
| Different vintage | Line `vintage_substituted` under $25 (A-22) | Expected (on the receipt). If $25+ without consent → policy violation (VIN-R2) → RTN-R1 |
| Different wine | Line `substituted` per "Substitute similar" preference (A-24) | Expected, but returnable unopened within 7 days with a full refund |
| Item missing | Line `removed_out_of_stock` and refunded | Expected; confirm the refund |
| Multiple boxes | Shipment split into several parcels | Check `track_shipment` for the other parcel |
| Label looks different | New label design (`formerly_known_as`) | Same wine |

## 3. Wrong item workflow

1. Identify the wrong item (what was ordered vs received); ask for a photo of the received label (`request_evidence_upload`).
2. Ask the customer **not to open** the wrong item.
3. Remedy options:
   - **Exchange:** deliver the correct item (if in stock) with the next window, at no charge, and collect the wrong item at the same time.
   - **Refund** the ordered item and collect the wrong one.
4. `create_return_request(reason_code="wrong_item", ...)`.
5. **The wrong item must be returned** (collected by the driver or dropped at the store). We don't tell customers to keep wrong alcohol items, to avoid giving away alcohol (a pricing-rule concern).
6. If the wrong item is more valuable and the customer would like to **buy it instead**, they can keep it by paying the difference at its live price (`modify_order`), only if they want to.

## 4. Missing item workflow

1. `get_order` + delivery/packing data: was it packed? Split shipment? Removed for stock?
2. If genuinely missing → remedy: **redeliver** (next window, no fee) or **refund**.
3. `create_return_request(reason_code="missing_item")` → `auto_approved` if within A-60.

## 5. "Delivered but not received" (whole order)

1. `get_order_status` / `track_shipment`: delivery time, **signature name**, driver photo/notes.
2. Ask the customer to check with household members, the building concierge or neighbors, and whether the signer's name is familiar.
3. If still missing → **P2 investigation** (`escalate_to_human(reason_code="delivered_not_received")`). Alcohol requires an adult signature, so a signed-for package not received is a potential fraud/compliance issue.
4. Don't promise a refund before the investigation. Typical resolution within 2 business days.
5. If the signature belongs to an unknown person, or the customer suspects a handoff to a minor → **P1** `handoff_compliance_incident`.

## 6. Edge cases

| Case | Handling |
|---|---|
| Wrong item already opened (customer didn't notice) | Still our error: refund/replace the ordered item; collect the opened bottle if practical; no charge |
| Reported after 7 days | Human review (P2) |
| Gift order wrong item | Coordinate with the purchaser (GF-R6); deliver the correct item to the recipient |
| Repeated wrong/missing claims on one account | RTN-R9 review |

## 7. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Signature by someone the customer doesn't know, or a suspected handoff to a minor (§5) | P1 | `handoff_compliance_incident` | Include tracking, signer name and delivery time |
| Whole order "delivered" but not received after household and building checks | P2 | `delivered_not_received` | Don't promise a refund before the investigation (§5) |
| Reported after 7 days (A-31) | P2 | `claim_review` | Include delivery date and what's wrong or missing |
| Remedy over $150 (A-60) | P2 | `refund_over_limit` | Create the return request first |
| A $25+ vintage change without consent (VIN-R2) | P2 | `policy_violation` | Offer a full refund or return regardless of state |
| Repeated wrong or missing claims on one account (RTN-R9) | P2 | `claim_review` | Process the current claim normally; don't mention the history |
| The same packing error across several orders (e.g., one SKU always picked wrong) | P3 | `create_support_ticket(category="fulfillment_quality")` | Include the SKUs and order numbers |

**Handle without escalating:** expected differences (§2), wrong-item exchanges and refunds within A-60, redelivery of missing items, and customers who want to keep a more valuable wrong item by paying the difference.

## 8. Response examples

> "I'm sorry, you ordered the 2022 Sancerre and received a Pouilly-Fumé. That's our mistake. Please keep it unopened. I can bring the Sancerre tomorrow between 11 and 1 and collect the Pouilly-Fumé at the same time, at no cost. Or I can refund the Sancerre and collect the other bottle. Which do you prefer?"

> "Your tracking shows the package was signed for by 'M. RIVERA' at 2:41 pm. Is that someone in your household or building? If not, I'll open an investigation right away. Our team will update you within 2 business days."
