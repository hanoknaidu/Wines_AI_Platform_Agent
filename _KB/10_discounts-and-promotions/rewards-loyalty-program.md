---
id: KB-DSC-004
title: Rewards Loyalty Program
category: discounts
subcategory: loyalty
doc_type: policy
intents: [loyalty.balance, loyalty.missing_points, loyalty.redeem, account.create, account.privacy_request]
tools: [get_loyalty_account, redeem_reward, adjust_loyalty_points, get_order, verify_customer_identity, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: marketing
status: active
depends_on_assumptions: [A-02, A-03, A-04, A-53, A-54, A-55, A-70, A-72]
related: [KB-DSC-001, KB-ACC-006, KB-ACC-004]
---

# Rewards Loyalty Program

> Compliance note: loyalty programs for alcohol retailers are generally acceptable when **free to join and open to all customers** on equal terms (as reflected in regulator guidance in other states). NJ-specific confirmation is listed as open question Q-3 in the assumptions register.

## 1. Program summary (A-53)

| Element | Rule |
|---|---|
| **Who** | Any account holder 21+; free; automatic enrollment option at sign-up; can opt out anytime |
| **Earn** | **1 point per $1** of eligible spend (product subtotal after discounts, before tax/fees/tips) |
| **Not earned on** | Taxes, delivery/shipping fees, tips, and purchases of gift cards. (Paying *with* a gift card or store credit still earns points on the products.) |
| **Rewards** | **250 points = $10 reward**, issued automatically in $10 increments |
| **Reward expiry** | **90 days** after issue |
| **Points expiry** | After **12 months with no qualifying purchase** |
| **Insider tier** | **$750** eligible spend in a rolling 12 months → 1.25 points per $1 + early access to selected releases (access only; same prices) |
| **Where** | Online and in store (scan the member barcode at either NJ or NY store); one combined balance |
| **When points post** | When the order is **fulfilled** (delivered/picked up/shipped) |

## 2. Rules

**RW-R1: Redemption.** Rewards apply to eligible products at checkout via `redeem_reward`. Multiple rewards can be used on one order. Rewards don't apply to gift cards, taxes or fees; any unused portion of a reward is forfeited unless the remaining value is ≥ $1 (then it stays on the account until expiry).

**RW-R2: Combining.** Rewards combine with sale prices, the mixed-case discount and promo codes (stacking matrix).

**RW-R3: Returns and cancellations.** Returned/cancelled items reverse the points earned. A reward used on a returned order is reinstated with its original expiry (if expired, reissued with 30 days' validity).

**RW-R4: Missing points.** Purchases without the member account (e.g., in store without scanning) can be added within **30 days** with the receipt/order number via `adjust_loyalty_points`. Older than 30 days → human review.

**RW-R5: Price floors.** Rewards are treated as a discount in the price-floor check (A-54). Rarely, a reward can't be fully applied to a heavily discounted item; the system applies it to other items.

**RW-R6: No transfer, no cash.** Points and rewards are non-transferable, have no cash value, and are forfeited on account deletion (privacy request) or account closure for fraud.

**RW-R7: Equal terms (A-55).** Tier benefits are published. No secret tiers or individual deals.

**RW-R8: Program changes.** The Store may change or end the program with **30 days' notice**; earned rewards are honored until their expiry.

**RW-R9: Privacy.** Program data (purchase history used for points and personalized offers) is covered in the privacy notice. Members can opt out of personalized offers without leaving the program (A-72).

## 3. Workflows

**Balance question**
1. Verify identity if not authenticated (A-70).
2. `get_loyalty_account(customer_id)` → points, tier, rewards and expiry dates.
3. Answer with the next milestone: "You have 210 points; 40 more earns a $10 reward."

**Missing points**
1. `get_order(order_id)` → check it's fulfilled and linked to the account.
2. If not yet fulfilled → explain that points post on fulfillment.
3. If fulfilled and not linked, within 30 days → confirm → `adjust_loyalty_points(customer_id, order_id, points, reason="missing_points")`.
4. If over 30 days, or the tool returns `requires_human_approval` → ticket P3.

**Redeem**
1. `get_loyalty_account` → available rewards.
2. Confirm which reward(s) → `redeem_reward(customer_id, reward_id, cart_id)` → show the new total.

## 4. Edge cases

| Case | Handling |
|---|---|
| Customer has two accounts | Points can be merged once, after identity verification of both; P3 ticket |
| Reward expired yesterday | Policy is 90 days; courtesy reissue once per 12 months (7-day validity) if it expired within the last 7 days |
| Under-21 account discovered | Account suspended; P1 (G1) |
| Customer moving out of state | Points stay; purchases must still be delivered within NJ/NY (A-02) |
| Customer asks to delete their account | Warn that points and rewards are forfeited (RW-R6), then proceed per the privacy process |

## 5. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| An account belongs to someone under 21 | P1 | `underage_risk` | Stop all sale and redemption activity (G1); the team suspends the account |
| Points or rewards redeemed by someone the customer doesn't know | P1 | `account_takeover` | Contain per [account-takeover-and-fraud.md](../13_account-management/account-takeover-and-fraud.md) §2 |
| Points balance dropped sharply, and returns, expiry or a merge don't explain it | P2 | `claim_review` | Include the before and after balances and dates from `get_loyalty_account` |
| Missing points older than 30 days, or `adjust_loyalty_points` returns `requires_human_approval` (RW-R4) | P3 | `create_support_ticket(category="loyalty")` | Include order or receipt number, store, date and amount |
| Merging two accounts (after verifying both) | P3 | `create_support_ticket(category="loyalty")` | Include both customer IDs; don't move points yourself |
| Reward reissue outside the courtesy rule (expired more than 7 days ago, or a second reissue within 12 months) | P3 | `create_support_ticket(category="loyalty")` | Don't promise the reissue |

**Handle without escalating:** balance questions, redemptions, missing points within 30 days, the one courtesy reissue, and questions about program changes (RW-R8). Requests for a special tier or extra points are declined (RW-R7).

## 6. Response examples

> "You have 480 points and one $10 reward that expires on December 14. Want me to apply the reward to this order? After this purchase you'll be about 20 points from your next one."

> "I see your in-store purchase from last week wasn't linked to your account. I've added the 64 points. They're in your balance now."
