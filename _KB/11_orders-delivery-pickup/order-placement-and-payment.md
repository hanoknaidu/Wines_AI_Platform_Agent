---
id: KB-ORD-001
title: Order Placement and Payment
category: orders
subcategory: placement-payment
doc_type: policy
intents: [order.place_help, account.payment_methods, account.age_verification]
tools: [get_cart, add_to_cart, calculate_order_totals, get_fulfillment_options, get_age_verification_status, start_age_verification, get_order_status, escalate_to_human, create_support_ticket, get_order, issue_refund]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: fulfillment-operations
status: active
depends_on_assumptions: [A-01, A-04, A-05, A-06, A-11, A-24, A-29, A-56, A-60, A-74]
related: [KB-ORD-002, KB-ACC-001, KB-PRC-005, KB-SYS-003]
---

# Order Placement and Payment

## 1. How ordering works

1. **Enter address or choose a pickup store.** This sets the **fulfilling store** (NJ or NY) and the catalog, prices and promotions shown (A-01).
2. **Add wines to the cart.** The agent can add items with `add_to_cart` after the customer agrees.
3. **Choose fulfillment:** delivery window, pickup, or shipping (`get_fulfillment_options`).
4. **Choose substitution preference** per item (default "Contact me"; A-24).
5. **Sign in / create an account** (21+ DOB required; A-04).
6. **Pay** in the secure checkout (A-74: never in chat).
7. **First order only:** complete **ID verification** in the secure flow (A-05). The order is held as `age_verification_pending` until verified.
8. **Confirmation** email/SMS with the order number.

## 2. Payment methods (A-29)

| Accepted | Not accepted |
|---|---|
| Visa, Mastercard, American Express, Discover (credit/debit) | Cash on delivery |
| Apple Pay, Google Pay | Buy-now-pay-later |
| Store gift cards, store credit (combinable with one card) | Checks (online), cryptocurrency |
| — | Payment via chat, email or phone to the agent |

- **Authorization vs capture:** the card is **authorized** when you order and **charged (captured)** when the order is fulfilled. If items are removed or substituted, the final charge is lower. Unused authorization drops off per the bank (typically 3–7 business days).
- **Cardholder name:** for age-verification and fraud reasons, the payment cardholder should be the account holder. Gift orders can be paid by the purchaser for any recipient.
- **Corporate invoicing:** only through the events/corporate team.

## 3. Payment problems

| Problem | What to tell the customer | Agent action |
|---|---|---|
| Card declined | "Your bank declined the payment. Common reasons: billing address mismatch, a fraud check by your bank, or insufficient funds. Try another card or contact your bank." | None in chat; the customer retries in checkout |
| Multiple declines | Same, and suggest contacting the bank | If signs of fraud (G9), P1 `fraud_signal` |
| Charged twice | Usually one is an authorization that drops off | Check `get_order`; if two captures, refund the duplicate (within A-60) or escalate P2 |
| Apple Pay not working | Try another browser/device or card | — |
| Gift card balance not enough | Use split payment (gift card + card) | — |
| "Can I pay at pickup / in store?" | Pickup orders are prepaid online (A-29) | — |

## 4. Minimums and limits

- Local delivery minimum: $40 product subtotal (A-11). Pickup and shipping have no minimum (shipping fees apply).
- Per-SKU and bulk limits: see [purchase-limits-and-bulk-orders.md](../09_stock-and-availability/purchase-limits-and-bulk-orders.md).

## 5. First-order ID verification (A-05)

- Why: alcohol sales require age verification; a date-of-birth checkbox isn't enough.
- How: a secure third-party flow (photo of a government ID, sometimes a selfie match). The agent sends the link via `start_age_verification` and checks status via `get_age_verification_status`.
- Status `failed` / `manual_review`: one retry link; then escalate P2 (`id_verification_failure`). The agent cannot override.
- ID images never pass through chat (A-74).

## 6. Edge cases

- **Mixed-location cart** (an NJ-only item with a NY address): checkout warns; the item must be removed (A-06).
- **Address entered after browsing** changes the store: prices and availability may change; tell the customer.
- **Placing an order by phone with the agent:** the agent can build the cart and send a checkout link; payment is completed by the customer.

## 7. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Multiple declines together with fraud signals (different cardholder names, many cards in quick succession; G9) | P1 | `fraud_signal` | Stop troubleshooting; say "I need a team member to help with this order" |
| Charged twice with two captures, and the duplicate is over $150 (A-60) | P2 | `refund_over_limit` | Confirm two captures with `get_order`. Within A-60, refund the duplicate yourself with `issue_refund` |
| Final charge differs from the total shown at checkout, not explained by removals or substitutions | P2 | `pricing_dispute` | Include the checkout total, the captured amount and the line items |
| ID verification `failed` or in `manual_review` after one retry link | P2 | `id_verification_failure` | The order stays on hold; the agent can't override |
| Verification shows `verified`, but the order is still `age_verification_pending` after 1 business day | P2 | `fulfillment_delay` | Include both statuses and the order number |
| Cart, totals or checkout-link tools error after one retry | P2 | `tool_failure` | Keep the cart contents in the summary so the customer doesn't rebuild it |
| Corporate invoicing or payment on terms | P2 | `create_support_ticket(category="event_order")` | See [events-tastings-and-corporate-orders.md](../14_general-faqs/events-tastings-and-corporate-orders.md) |

**Handle without escalating:** single declines (the customer retries or calls the bank), authorization vs capture questions, Apple Pay issues, split payments, and requests to pay in chat or by phone. Decline those and send the secure checkout link (A-74).

## 8. Response examples

> "To finish your first order, we need a quick ID check. It's a secure link that takes about a minute. I've just sent it to your email. Once it's verified, your order moves straight to packing."

> "Your card is authorized for $142.10 now, but you'll only be charged when your order goes out. If anything is removed, the final charge will be lower."
