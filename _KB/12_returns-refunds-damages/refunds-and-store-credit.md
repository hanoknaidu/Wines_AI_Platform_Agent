---
id: KB-RTN-005
title: Refunds and Store Credit
category: returns
subcategory: refunds
doc_type: policy
intents: [refund.status, return.change_of_mind, claim.damaged, claim.flawed_wine, claim.wrong_or_missing, order.cancel]
tools: [get_return_status, get_order, issue_refund, issue_store_credit, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: finance
status: active
depends_on_assumptions: [A-17, A-18, A-27, A-29, A-34, A-36, A-56, A-60, A-61, A-62]
related: [KB-RTN-001, KB-PRC-003, KB-ORD-003, KB-ORD-008]
---

# Refunds and Store Credit

## 1. Refund methods

| Method | When | Timing (A-36) |
|---|---|---|
| **Original payment method** (card, Apple Pay, Google Pay) | Default for cancellations, claims, approved returns | Initiated within 1 business day of approval; posts in **5–10 business days** depending on the bank |
| **Store credit** | Customer's choice; NJ change-of-mind returns at full value (A-34); goodwill (A-61) | **Instant**; usable online and in both stores; **doesn't expire** |
| **Gift card portion** | Part of the order paid by gift card | Returned to the **same gift card** (or new e-gift card if the original is unavailable) |
| **Split payment** | Gift card/credit + card | Refunded proportionally to each method, card last |

## 2. What's included in a refund

| Scenario | Products | Tax | Delivery/shipping fee |
|---|---|---|---|
| Store cancels / out-of-stock (whole order) | ✅ | ✅ | ✅ |
| Customer cancels before picking | ✅ | ✅ | ✅ |
| Damage, defect, wrong/missing item | ✅ (affected items) | ✅ | ✅ if the whole order was affected; otherwise n/a |
| Partial out-of-stock removal | ✅ (removed item, net of allocated discounts) | ✅ | Fee waiver preserved (no extra charge) |
| Failed delivery → refund (A-17/A-18) | ✅ | ✅ | ❌ (delivery/shipping fee deducted) |
| NJ change-of-mind to card | ✅ minus 15% restocking | ✅ (on the refunded amount) | ❌ |
| NJ change-of-mind to store credit | ✅ full value | ✅ | ❌ |
| Price correction / missed promo | Difference only | ✅ on the difference | — |

Tips (A-27) are refunded only if the delivery didn't happen.

## 3. Rules

**RF-R1: Never promise faster timing** than A-36. Banks control posting.

**RF-R2: Refund only to the original payer.** No refunds to a different card, bank account, cash or Venmo. If the original card is closed, the bank usually forwards the refund to the new card; otherwise store credit or a P2 finance review (check).

**RF-R3: Authority (A-60, A-62).** The agent issues refunds ≤ $150 per order on approved claims; over $150, no-evidence claims or second claims within 60 days → human.

**RF-R4: Goodwill credit (A-61)** is store credit up to $15, once per 90 days, for service failures; never cash.

**RF-R5: No double refunds.** If a chargeback is open, don't issue a refund; escalate to finance (P2).

**RF-R6: Store credit has no cash value** and can't be transferred or used to buy gift cards.

## 4. "Where's my refund?" workflow

1. `get_return_status(rma_id)` or `get_order` → refund status, amount, method, date issued.
2. If issued: share the amount, date and method; explain bank posting (5–10 business days); suggest checking pending transactions.
3. If more than 10 business days since issued and not received → P2 `refund_trace` (finance provides the acquirer reference number, ARN, that the bank can use to trace it).
4. If not yet issued (claim pending) → share the review status and SLA.

## 5. Escalation

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Refund issued more than 10 business days ago and not received | P2 | `refund_trace` | Include the refund date, amount and last 4 digits of the card; finance provides the ARN |
| Original card closed and the bank isn't forwarding the refund (RF-R2) | P2 | `refund_trace` | Never redirect to another card, bank account, cash or Venmo |
| A chargeback is open for the order (RF-R5) | P2 | `chargeback_open` | Issue nothing; tell the customer finance will resolve it through the dispute |
| Approved claim over $150, a claim without evidence, or a second claim within 60 days (RF-R3) | P2 | `refund_over_limit` / `claim_review` | Share the approved amount and what still needs approval |
| Store credit issued but not showing on the account | P2 | `tool_failure` | Include the credit amount and the time it was issued |

**Handle without escalating:** "where's my refund?" within 10 business days (explain bank posting, RF-R1), choosing between card refund and store credit, refunds up to $150 on approved claims, and requests to cash out store credit or refund to a different card. Decline those per RF-R2 and RF-R6. A customer threatening a chargeback who hasn't filed one should get the normal resolution path.

## 6. Response examples

> "Your refund of $52.18 was issued on November 12 to your Mastercard ending 9910. Banks usually take 5–10 business days to post it. If it's not there by November 26, let me know and I'll ask our finance team for a trace number your bank can use."

> "You can choose a refund to your card, which takes 5–10 business days, or store credit, which is instant, never expires, and works online and in both our stores. Which would you prefer?"
