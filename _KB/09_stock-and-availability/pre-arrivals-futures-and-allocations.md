---
id: KB-STK-004
title: Pre-Arrivals, Futures (En Primeur) and Allocations
category: stock
subcategory: pre-arrival-allocation
doc_type: policy
intents: [stock.pre_arrival, stock.availability, order.cancel, order.status]
tools: [check_inventory, get_order, get_order_status, cancel_order, subscribe_back_in_stock, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: fine-wine-team
status: active
depends_on_assumptions: [A-01, A-02, A-23, A-25, A-26, A-28, A-33, A-34, A-43, A-50, A-51, A-55]
related: [KB-STK-001, KB-STK-002, KB-STK-007, KB-REG-002, KB-PRC-001]
---

# Pre-Arrivals, Futures and Allocations

## 1. Definitions

| Term | What it means for the customer |
|---|---|
| **Futures / en primeur** | Buying wine (classically top Bordeaux) **while it's still aging at the château**, typically in the spring after the harvest. Bottles arrive roughly 2–3 years later. Price is set at the offer. |
| **Pre-arrival** | Wine that has been bottled and purchased from the producer/importer but **hasn't arrived** in our store yet (in transit, at port, or awaiting distributor release). Typically weeks to months. |
| **Allocation** | Limited quantities granted by the producer/distributor. We cap per-customer quantities and may use waitlists. |
| **Release / offer** | A time-limited offering (email, site) for allocated or pre-arrival wine. |

## 2. Policy rules

**PA-R1: Payment.** Pre-arrival and futures orders are **paid in full at purchase** (A-25).

**PA-R2: Price is final.** The purchase price stands regardless of later market price (PRC-R9). Pre-arrivals are excluded from price matching (A-43), the mixed-case discount (A-50) and promo codes (A-51) unless an offer explicitly says otherwise.

**PA-R3: Cancellation (A-25).** Cancellable for a full refund within **14 days** of purchase. After 14 days, **non-cancellable**, **unless** arrival is more than **90 days later than the latest published estimate**. Then the customer may cancel for a full refund.

**PA-R4: Estimates, not guarantees.** Arrival windows depend on producers, shipping, customs and distributors. The agent always calls them estimates.

**PA-R5: In-state only (A-01, A-02).** Pre-arrivals are sold by the store in the customer's state and delivered only within NJ/NY. A customer who moves out of state before arrival can pick up in store, have it delivered to an in-state address with a 21+ recipient, or (exception) request a refund (P2 review).

**PA-R6: On arrival (A-28).** The customer is notified; they schedule delivery or pickup within **30 days**; after that, we deliver via their default method with standard fees.

**PA-R7: Condition.** Pre-arrival wines are inspected on receipt. Damage found at receipt → we contact the customer with replacement (if available) or refund. After handoff, standard damage/defect policies apply. Futures wines are vintage-specific (A-23); older-vintage rules (A-33) don't apply to new-release futures.

**PA-R8: Allocations.** `allocation_limit` per customer per release (household/payment method/address counted together). Attempts to exceed it with multiple accounts → orders over the limit are cancelled and refunded. Allocations may be offered first to waitlisted customers, then generally. No "VIP-only" pricing; access rules must be published (A-55).

**PA-R9: No storage service.** The Store doesn't offer long-term cellaring. (If added, it gets its own KB document.)

**PA-R10: Returns.** Pre-arrivals, futures and allocated items are excluded from change-of-mind returns (A-34), but defects and damage are covered as usual.

## 3. Workflow: "Where's my pre-arrival?"

1. `get_order(order_id)` → line status `pre_arrival`, `estimated_arrival_window`.
2. If within the window: share the estimate and what happens on arrival (PA-R6).
3. If past the window: apologize, share the updated estimate if any, and check PA-R3 (90-day rule) → offer cancellation if eligible.
4. If no update data: `escalate_to_human(reason_code="pre_arrival_issue", priority="P2")` for a buyer update.

## 4. Workflow: allocation sold out

1. `check_inventory` → `waitlist`.
2. Offer `subscribe_back_in_stock(waitlist=true)`. Explain that waitlist offers are not guaranteed.
3. Suggest similar in-stock wines.

## 5. Edge cases

| Case | Handling |
|---|---|
| Customer wants to change the delivery address for a futures order | Allowed within the same state; through `modify_order` when arrival is scheduled |
| Customer passed away / estate inquiry | P2 human handling with care; refund or transfer per legal guidance |
| Producer declassifies a vintage or cancels a cuvée | Full refund; P2 notice |
| Customer asks about investment value or resale | We don't give investment advice and don't support resale (G9) |
| Multiple pre-arrivals in one order | Each line has its own window; ship together or separately per customer choice (separate shipments may each incur fees unless waived) |

## 6. Escalation

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Past the estimated window, and `get_order` has no updated estimate (§3) | P2 | `pre_arrival_issue` | Include the original estimate and order date |
| Producer declassifies the vintage or cancels the cuvée | P2 | `pre_arrival_issue` | Full refund; the team sends the notice |
| Allocation dispute: customer says they were skipped on the waitlist, or over-limit orders were cancelled (PA-R8) | P2 | `pre_arrival_issue` | Never explain how household, address or payment matching works |
| Request to cancel after 14 days that doesn't meet the 90-day rule, with a credible reason | P2 | `policy_exception_request` | Don't promise a refund (PA-R3) |
| Customer moved out of NJ/NY before arrival and asks for a refund (PA-R5) | P2 | `policy_exception_request` | First offer in-store pickup or an in-state address |
| Estate inquiry after a customer's death | P2 | `pre_arrival_issue` | Respond with care; share no order details until the team verifies authority |
| A business wants allocations for resale | P2 | `business_sales` | Don't process the order (G9) |

**Handle without escalating:** arrival estimates, the 14-day and 90-day cancellations, waitlists and in-state address changes. Investment or resale-value questions are declined, not escalated.

## 7. Response examples

> "Your 2024 Bordeaux futures are estimated to arrive in spring 2027. That's typical, since the wine is still aging at the château. As soon as they land, we'll notify you to schedule delivery or pickup within 30 days."

> "I'm sorry for the wait. Your pre-arrival Barolo was estimated for September, and it's now more than 90 days past that estimate, so you can cancel for a full refund if you'd like, or keep your order and we'll update you as soon as we hear from the importer. Which would you prefer?"
