---
id: KB-STK-007
title: Purchase Limits, Bulk Orders and Resale Prevention
category: stock
subcategory: limits-bulk
doc_type: policy
intents: [stock.bulk_quantity, events.corporate, compliance.resale, stock.availability]
tools: [check_inventory, add_to_cart, create_support_ticket, escalate_to_human, get_fulfillment_options]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: inventory-operations
status: active
depends_on_assumptions: [A-10, A-12, A-15, A-26, A-34, A-35, A-50, A-55]
related: [KB-STK-004, KB-SPK-005, KB-FAQ-005, KB-SYS-003]
---

# Purchase Limits, Bulk Orders and Resale Prevention

## 1. Policy rules

**PL-R1: Default per-SKU limit.** Maximum **36 bottles (3 cases) per SKU per order** (A-26) unless the listing shows a lower `allocation_limit`.

**PL-R2: Allocation limits** override the default and apply per customer per release, counting household, address and payment method together.

**PL-R3: Bulk/event threshold.** Orders over **$2,500** or **60 bottles** total are reviewed by the events/bulk team before release (A-26). Reasons: stock reservation across deliveries, delivery logistics (vehicle capacity, stairs/loading), fraud screening and compliance.

**PL-R4: Retail sale only.** We sell to consumers for personal use, gifts and private events. We don't sell for **resale** to unlicensed persons, and the agent doesn't process orders that suggest resale ("for my store", "to sell at my bar", "reselling online"). Licensed on-premises businesses must use the business channel (staff-handled; NY retail-to-retail limits apply).

**PL-R5: No circumvention.** Splitting orders across accounts, addresses or cards to exceed limits → excess orders cancelled and refunded.

**PL-R6: Equal access (A-55).** Limits are applied consistently, never waived as a favor.

## 2. Decision table

| Request | Action |
|---|---|
| ≤ 36 bottles of one SKU, total ≤ 60 bottles and ≤ $2,500 | Normal order; `check_inventory(quantity)` |
| > 36 of one SKU | Explain the limit; offer the max plus similar wines, or route to the events team for review |
| > 60 bottles or > $2,500 | Collect event details → `create_support_ticket(category="bulk_order", priority="P2")`; explain the review step (response within 4 business hours) |
| Allocated item over the limit | Decline above the limit; offer the waitlist and alternatives |
| Wedding/party in the future | Offer reservation via the events team; mention delivery logistics |
| Resale / business purchase | PL-R4; escalate to the business team (P2, `compliance.resale`) |

## 3. Bulk-order intake (information to collect)

- Event date and delivery date/time window; delivery address (venue?); on-site 21+ contact with ID.
- Wines and quantities (or budget and guest count for a recommendation).
- Whether chilling/ice or rentals are needed (we don't provide them unless a program exists; say so).
- Payment method (the bulk team may require full prepayment).
- Venue rules: some venues require the alcohol supplier's certificate of insurance or licensed caterers. Our team will advise.

## 4. Mixed-case and bulk pricing

- The mixed-case discount (10% for 6–11, 15% for 12+; A-50) applies to bulk orders on eligible items. There's no higher tier and no negotiated pricing (PRC-R11).
- Delivery: large orders above the free-delivery threshold deliver free locally (A-12); statewide shipping above $199 is free (A-15), but very large shipments may need freight scheduling.

## 5. Unsold-bottle returns for events

Customers often ask whether unopened bottles can be returned after an event:
- **NJ Store:** unopened, resaleable, within 14 days with the order number: refund minus the 15% restocking fee, or full store credit (A-34). **Exceptions:** special orders, allocated items, large formats ≥ 3 L, items stored in hot venues (labels/capsules showing heat damage).
- **NY Store:** no change-of-mind returns (A-35). Recommend ordering in stages or starting conservatively.
- Mention this **before** the order, so expectations are clear.

## 6. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Purchase for resale, or a business purchase (PL-R4) | P2 | `business_sales` | Don't add items or process the order; explain we sell at retail |
| More than 60 bottles or $2,500 in total (PL-R3) | P2 | `create_support_ticket(category="bulk_order")` | Collect the intake details in §3 so the team doesn't re-ask |
| Bulk ticket has no response after 4 business hours, and the event is within 7 days | P2 | `bulk_order` | Live handoff; include the ticket ID and event date |
| More than 36 bottles of one SKU for a real event | P2 | `bulk_order` | The events team decides; the agent can't raise the limit |
| Dispute over unopened event returns refused for heat damage or an exception (§5) | P2 | `claim_review` | Ask for photos of labels and capsules |

**Handle without escalating:** orders within limits, allocation limits (offer the waitlist and alternatives), and requests to waive a limit as a favor (decline per PL-R6). If a customer asks how to get around a limit with other accounts, addresses or cards, decline (PL-R5). Escalate P1 `fraud_signal` only if other G9 signals appear too.

## 7. Response examples

> "For 80 bottles, our events team reviews the order to reserve stock and plan the delivery. I've sent them your details (ticket #E-7731), and they'll reach you within 4 business hours. Your mixed-case discount of 15% applies to eligible wines."

> "That wine has a limited allocation of 2 bottles per customer. I can add 2 for you and suggest a similar wine for the rest of your order."
