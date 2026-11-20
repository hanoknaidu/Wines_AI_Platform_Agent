---
id: KB-ORD-003
title: Order Changes and Cancellations
category: orders
subcategory: changes-cancellations
doc_type: policy
intents: [order.modify, order.cancel]
tools: [get_order, get_order_status, modify_order, reschedule_delivery, cancel_order, calculate_order_totals, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: fulfillment-operations
status: active
depends_on_assumptions: [A-01, A-17, A-18, A-21, A-25, A-28, A-36, A-41, A-70]
related: [KB-ORD-002, KB-STK-004, KB-PRC-003, KB-RTN-005]
---

# Order Changes and Cancellations

## 1. What can change, and when

| Change | `placed` / `confirmed` | `picking` | `ready_for_pickup` | `out_for_delivery` / `in_transit` |
|---|---|---|---|---|
| Add items | ✅ (same store; stock permitting) | ⚠️ Request; may become a separate order | ❌ Place a new order | ❌ |
| Remove items / change quantity | ✅ | ⚠️ Request (A-21) | ⚠️ Decline items at pickup → refund | ❌ (refuse at door = failed delivery for those items) |
| Change delivery window | ✅ `reschedule_delivery` | ✅ if slots allow | n/a | ❌ (contact driver via tracking) |
| Switch delivery ↔ pickup | ✅ (same store) | ⚠️ Request | ✅ pickup → delivery (fees apply) | ❌ |
| Change address (same state, same store) | ✅ (identity verified; restricted-destination check) | ⚠️ Request | n/a | ❌ (fraud safeguard) |
| Change address to the **other state** | ❌ Cancel and re-order from the other store (A-01) | ❌ | ❌ | ❌ |
| Change payment method | ✅ via secure checkout link | ❌ | ❌ | ❌ |
| Add/edit gift message | ✅ | ⚠️ | ❌ | ❌ |
| Cancel whole order | ✅ free (A-21) | ⚠️ Request; free if successful | ✅ Cancel → refund (no fee) | ❌ → refusal/failed delivery rules (A-17/A-18) |

✅ = agent can do it with confirmation · ⚠️ = possible but not guaranteed; submit and confirm the outcome · ❌ = not possible

## 2. Policy rules

**OC-R1: Free cancellation before `picking` (A-21).** Full refund to the original payment method, including fees.

**OC-R2: During `picking`,** a cancellation request is sent to the store. If the order hasn't been handed off, it's cancelled at no fee. The agent says "I've requested it" until the tool confirms.

**OC-R3: After dispatch,** the order can't be cancelled. If the customer refuses the delivery or isn't available, failed-delivery rules apply (A-17/A-18): refund minus delivery/shipping fees.

**OC-R4: Pre-arrivals and special orders** follow their own cancellation rules (A-25, A-28).

**OC-R5: Address changes** require an authenticated session or OTP (A-70), and the new address must pass `get_fulfillment_options` (zone, restricted destinations). Address changes after dispatch are refused to prevent fraud.

**OC-R6: Store-initiated cancellations** (fraud screening, failed ID verification, compliance, pricing error A-41, out of stock): the customer is notified with the reason category and fully refunded. The agent explains in general terms and doesn't reveal fraud-screening logic.

## 3. Workflow: cancel

1. Verify the customer (A-70) and get the order.
2. `get_order_status` → apply §1.
3. State the outcome before acting: "Cancelling now gives you a full refund of $X to your Visa ending 4421."
4. On explicit yes → `cancel_order(order_id, reason_code)`.
5. Report the result and refund timeline (A-36). If `not_allowed_reason` comes back, explain and offer alternatives (refuse at door, return rules).

## 4. Workflow: modify

1. `get_order` → current lines and status.
2. Propose the change and new total (`calculate_order_totals` preview via `modify_order` dry-run if available).
3. Confirm → `modify_order` / `reschedule_delivery`.
4. Confirm the new total and window.

## 5. Edge cases

| Case | Handling |
|---|---|
| Customer wants to add a bottle after picking started | Offer a separate small order. If it doesn't meet the delivery minimum, suggest pickup, or ask the store to combine (no guarantee) |
| Removing items drops below the free-delivery threshold before picking | Customer-initiated changes do recalculate fees (unlike out-of-stock removals) |
| Change from NJ address to NY address | Cancel and re-order from the NY Store; prices/stock may differ |
| Accidental duplicate order | Cancel the duplicate (free if before picking); if both shipped, standard return rules + P2 review for courtesy |
| Cancel because the customer can't be present for the window | Offer `reschedule_delivery` or pickup first |

## 6. Escalation

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Request to change the address after dispatch, especially to an unrelated address | P1 | `fraud_signal` | Refuse the change (OC-R5); stay neutral |
| An order was dispatched or charged despite a confirmed cancellation | P2 | `fulfillment_delay` | Include the cancellation time and confirmation; the team contacts the store or driver |
| Cancellation requested during `picking` (OC-R2) still unconfirmed after 2 hours | P2 | `fulfillment_delay` | Tell the customer it's requested, not done |
| Customer disputes a store-initiated cancellation for fraud screening or compliance (OC-R6) | P2 | `order_review` | Explain in general terms only; never reveal screening logic |
| Customer disputes a cancellation for a pricing error (A-41) | P2 | `pricing_dispute` | Follow [price-errors-and-adjustments.md](../08_pricing/price-errors-and-adjustments.md) |
| Store-initiated cancellation after ID verification failed | P2 | `id_verification_failure` | The agent can't reinstate the order |
| Accidental duplicate where both orders have already shipped | P2 | `policy_exception_request` | Standard return rules apply unless the team approves a courtesy (§5) |
| `cancel_order` or `modify_order` errors after one retry | P2 | `tool_failure` | Don't say it's done; tell the customer a team member will confirm |

**Handle without escalating:** free cancellations before `picking`, changes the tools allow, window changes, NJ↔NY moves (cancel and re-order), and explaining why an order can't be cancelled after dispatch. Pre-arrivals and special orders escalate per their own documents (OC-R4).

## 7. Response examples

> "Your order hasn't started packing yet, so I can cancel it with a full $87.40 refund to your card. It'll show in 5–10 business days. Shall I go ahead?"

> "Your order is already with the driver, so it can't be cancelled now. If no one can receive it, the driver will bring it back to the store, and you can either schedule one free redelivery or get a refund minus the delivery fee."
