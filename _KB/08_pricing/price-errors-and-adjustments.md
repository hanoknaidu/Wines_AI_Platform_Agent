---
id: KB-PRC-003
title: Pricing Errors, Price Drops and Charge Disputes
category: pricing
subcategory: errors-adjustments
doc_type: policy
intents: [price.discrepancy, order.cancel, refund.status]
tools: [get_order, get_price, calculate_order_totals, cancel_order, issue_refund, issue_store_credit, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: pricing
status: active
depends_on_assumptions: [A-21, A-36, A-40, A-41, A-42, A-45, A-60, A-61, A-62, A-70]
related: [KB-PRC-001, KB-PRC-004, KB-ORD-003, KB-RTN-005, KB-SYS-006]
---

# Pricing Errors, Price Drops and Charge Disputes

## 1. Scenarios covered

1. **Price dropped after I bought** (sale started, price changed).
2. **Pricing error**: a price displayed in clear error (by us).
3. **Charged differently than shown**: card charge ≠ order confirmation.
4. **Shelf vs online mismatch** (in-store pickup customers).
5. **Promotion should have applied but didn't** (see also [discount-troubleshooting.md](../10_discounts-and-promotions/discount-troubleshooting.md)).

## 2. Policy rules

**PRC-E1: Post-purchase price drops (A-42).** No retroactive adjustment **after fulfillment** (delivered, picked up or shipped). **Before fulfillment**, the customer may cancel the affected items (A-21) and re-order at the new price if stock allows. The agent can do this for them with confirmation.

**PRC-E2: Clear pricing errors (A-41).** If a price was displayed in clear error (e.g., more than 50% below the regular price with no active promotion, or wrong decimal), the Store may cancel the **unfulfilled** items with notice and a full refund. **Fulfilled** orders are honored. The agent never accuses the customer of bad faith.

**PRC-E3: Our error in the customer's favor is honored once fulfilled.** We don't claw back money after fulfillment for our pricing mistakes.

**PRC-E4: Charge ≠ confirmation.** The customer pays the confirmation total, except for disclosed adjustments: removed/substituted items, weather-hold shipping upgrades the customer approved, or tip if offered. Any unexplained difference is refunded once verified (agent within A-60 limits; above → human).

**PRC-E5: Authorization holds.** Card statements may show a **temporary authorization** larger than the final total (e.g., before substitutions or for age-restricted orders). It drops off per bank timelines (typically 3–7 business days). Not an overcharge.

**PRC-E6: Promotion missed at checkout.** If an eligible, active published promotion failed to apply due to a system error, we refund the difference (within A-60; it counts as an error correction, not a goodwill credit). If the customer forgot to enter a code, see [promo-codes-and-coupons.md](../10_discounts-and-promotions/promo-codes-and-coupons.md) (DSC-P7).

## 3. Decision table

| Situation | Fulfilled? | Action |
|---|---|---|
| Sale started after purchase | No | Offer cancel and re-order (PRC-E1) |
| Sale started after purchase | Yes | Explain politely; no adjustment; mention current promotions for future orders |
| Our clear pricing error, customer ordered | No | Store may cancel the item with notice; agent explains, offers to re-order at the correct price, no fee |
| Our clear pricing error | Yes | Honor (PRC-E3) |
| Charge higher than confirmation, no disclosed reason | Either | Verify with `get_order` + `calculate_order_totals`; refund the difference (≤ $150 agent; > $150 human) |
| Card shows a pending amount higher than total | Either | Explain authorization holds (PRC-E5) |
| Shelf tag lower than online price at pickup store | Pickup | Online = shelf (A-45); a wrong shelf tag is a store error → refund the difference at pickup or after, via ticket P3 |
| Eligible promotion didn't apply (system error) | Either | Refund difference (PRC-E6) |

## 4. Workflow: "I was overcharged"

1. Verify identity if account data is needed (A-70) and get the order number.
2. `get_order(order_id)` → compare confirmation lines, discounts, fees, tax.
3. Ask what amount they see and where (pending vs posted).
4. If it's a pending authorization → PRC-E5 explanation.
5. If a real discrepancy → state the difference and cause (if known) → **confirm** → `issue_refund(order_id, amount, method="original_payment", reason_code="pricing_correction")`.
6. If the amount is over $150, unclear, or involves multiple orders → `escalate_to_human(reason_code="pricing_dispute", priority="P2")`.
7. Give the refund timeline (A-36: card refunds post in 5–10 business days).

## 5. Edge cases

- **Customer bought multiple units during an error price:** same rule. Unfulfilled items may be cancelled; fulfilled are honored.
- **Price changed between cart and checkout:** cart prices aren't locked (PRC-R5). The checkout price is final.
- **Tax differences** between a quote and the charge (address changed): totals follow the final delivery address. Explain and show the breakdown.
- **Chargeback threats:** stay calm, resolve if eligible, and escalate P2 if the customer has already filed a chargeback (finance handles it; the agent doesn't issue a duplicate refund).

## 6. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Customer mentions a lawsuit, attorney or regulator complaint about pricing | P1 | `legal_matter` | Don't discuss fault |
| Customer has already filed a chargeback | P2 | `chargeback_open` | Issue **no** refund; finance handles it (RF-R5). Include the chargeback date if known |
| Verified difference over $150 (A-60), cause unclear, or several orders involved | P2 | `pricing_dispute` | Include the confirmation total, the captured amount and the line comparison |
| Customer disputes a cancellation for a clear pricing error (PRC-E2) | P2 | `pricing_dispute` | Explain the rule without suggesting bad faith; include the displayed and regular prices |
| A published promotion fails for many customers, or a promoted SKU returns `blocked_by_price_floor` | P2 | `promo_config_error` | Include the promotion and affected SKUs |
| `issue_refund` fails after one retry | P2 | `tool_failure` | Don't tell the customer the refund is done |
| Shelf tag lower than the online price at the pickup store (A-45) | P3 | `create_support_ticket(category="store_pricing")` | Include the store, SKU and both prices |

**Handle without escalating:** authorization-hold explanations (PRC-E5), price drops after fulfillment (explain kindly), cancel-and-re-order before fulfillment (PRC-E1), and verified differences up to $150.

## 7. Response examples

> "I see the Barolo went on sale the day after you ordered. Since your order hasn't been picked yet, I can cancel those two bottles and re-add them at the sale price, so you'd save $12. Want me to do that?"

> "Thanks for flagging this. Your confirmation total was $86.40, but you were charged $92.15 because the delivery fee was applied even though your order qualified for free delivery. I've refunded $5.75 to your card. It usually appears in 5–10 business days."

> "The larger amount you see is a temporary authorization from your bank, not the final charge. Your final charge is $64.18, and the hold should drop off within a few business days."
