---
id: KB-DSC-006
title: Discount Troubleshooting (Codes, Case Discount, Rewards)
category: discounts
subcategory: troubleshooting
doc_type: workflow
intents: [discount.promo_code_issue, discount.case_discount, loyalty.redeem, price.discrepancy]
tools: [validate_promo_code, apply_promo_code, calculate_order_totals, get_cart, get_order, get_loyalty_account, redeem_reward, issue_refund, log_event, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: marketing-and-pricing
status: active
depends_on_assumptions: [A-50, A-51, A-52, A-53, A-54, A-60]
related: [KB-DSC-001, KB-DSC-002, KB-DSC-003, KB-DSC-004, KB-PRC-003]
---

# Discount Troubleshooting

## 1. Promo-code error reasons (`validate_promo_code.reason_code`)

| Reason code | What it means | What to tell the customer | Fix |
|---|---|---|---|
| `expired` | Past end date/time | "That code ended on [date]." | Offer current promotions, Rewards |
| `not_started` | Before start date | "It starts on [date]." | — |
| `min_not_met` | Product subtotal (after other discounts) below the minimum | "It needs $[X] in eligible items; you're $[gap] away." | Suggest adding an item only if helpful |
| `excluded_items` | Cart items excluded (sale, pre-arrival, gift cards…) | "It doesn't apply to [items]." | Show which lines qualify |
| `not_stackable` | Conflicts with the mixed-case discount or another code | "It can't combine with your case discount; I've kept whichever saves you more ($X)." | Show both savings |
| `already_used` | Per-customer limit reached | "That code has already been used on your account." | — |
| `first_order_only` | Customer has a previous fulfilled order (A-52) | "It's for first orders only." | Rewards, current promotions |
| `location_mismatch` | Code valid only at the other store | "That code is for our [NJ/NY] store only." | Show local promotions |
| `account_required` | Must be signed in | "Please sign in to use it." | — |
| `blocked_by_price_floor` | Would breach the legal price floor (A-54) | "That discount can't be applied to these items because of state pricing rules." | Don't try alternative stacking; `log_event` if it's a published promotion |
| `invalid` | Doesn't exist/typo | "I can't find that code. Could you double-check the spelling?" | Common typos: O vs 0, extra spaces |
| `usage_limit_reached` | Total redemptions capped | "That code has reached its limit." | — |

## 2. Mixed-case discount not applied

Checklist (use `get_cart`/`calculate_order_totals`):
1. Are there **6+ eligible bottle-equivalents**? (Boxed/canned wines and pre-arrivals don't count; 375 ml counts 0.5.)
2. Are some items on **sale**? They count toward the total but don't get the extra % (expected).
3. Is a **promo code** applied that isn't stackable? The system picked the better saving.
4. Did a line hit a **price floor**? The cart shows a note.
5. Still wrong → `log_event("tool_error", {cart_id})` → escalate P2 `pricing_dispute` if on a placed order.

## 3. Rewards not applying

| Symptom | Likely cause | Fix |
|---|---|---|
| Reward not visible | Expired, or points still under 250, or the order earning them isn't fulfilled yet | Check `get_loyalty_account` |
| Reward applied to fewer dollars | Ineligible items (gift cards), price floor on a sale item | Explain |
| Reward "disappeared" after a return | Reinstated with original expiry (RW-R3) | Check the account |

## 4. Post-purchase fixes

| Situation | Action |
|---|---|
| Valid code forgotten; order not picked | Cancel and re-place with code, or apply if supported (DSC-P7) |
| Valid code forgotten; order fulfilled | One-time courtesy refund within 7 days, ≤ A-60 limits (DSC-P7) |
| Eligible discount failed due to system error | Refund difference (PRC-E6); `log_event` |
| Customer wants a discount applied that they weren't eligible for | Kindly explain why; no exception |

## 5. Escalation

| Trigger | Priority |
|---|---|
| Published promotion fails for many customers / `blocked_by_price_floor` on a promoted SKU | P2 `promo_config_error` |
| Discount dispute on an order > $150 | P2 `pricing_dispute` |
| Suspected code abuse (multiple accounts) | P2 `fraud_signal` |

## 6. Response examples

> "I checked your cart: the code needs $75 of eligible wine, and two items in your cart are pre-arrivals, which are excluded, so the eligible total is $68. Adding one more regular bottle, or swapping a pre-arrival into a separate order, would make it work."

> "Your case discount is applied, but only on 8 of your 10 bottles, because the 2 Proseccos are already on sale. They still count toward the 10 bottles, so you're getting the full 10% on the rest."
