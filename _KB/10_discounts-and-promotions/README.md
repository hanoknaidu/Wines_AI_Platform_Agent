---
id: KB-DSC-000
title: Discounts and Promotions: Folder Index
category: discounts
subcategory: index
doc_type: index
intents: [discount.current_offers, discount.case_discount, discount.promo_code_issue, loyalty.balance, loyalty.missing_points, loyalty.redeem]
tools: [get_active_promotions, validate_promo_code, apply_promo_code, calculate_order_totals, get_loyalty_account, redeem_reward, adjust_loyalty_points]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: marketing-and-pricing
status: active
depends_on_assumptions: [A-51]
related: [KB-PRC-000, KB-SYS-003]
---

# Discounts and Promotions: Folder Index

## Scope

Every way a customer can pay less: mixed-case discounts, promo codes and coupons, the Rewards loyalty program, seasonal sales and events, and how to fix a discount that didn't work. All discounts operate inside legal limits (NJ below-cost rule; equal availability). The pricing engine enforces them, and the agent explains them.

## Files

| File | Answers |
|---|---|
| [discount-policy-overview.md](discount-policy-overview.md) | Types of discounts, stacking matrix, exclusions, legal guardrails |
| [mixed-case-and-volume-discounts.md](mixed-case-and-volume-discounts.md) | 10%/15% mixed-case rules, counting bottles, eligible items, examples |
| [promo-codes-and-coupons.md](promo-codes-and-coupons.md) | Code types, first-order offer, referral, validity, one-code rule, missed codes |
| [rewards-loyalty-program.md](rewards-loyalty-program.md) | Earning, redeeming, tiers, expiry, returns, missing points, privacy |
| [seasonal-sales-and-events.md](seasonal-sales-and-events.md) | Recurring sale calendar, featured promotions, in-store tastings, communication |
| [discount-troubleshooting.md](discount-troubleshooting.md) | Code errors by reason code, missing discounts, post-purchase fixes |

## Golden rules

1. Only offer discounts returned by tools. Never invent a code or a "special price".
2. Explain **why** a discount didn't apply, in plain words, using the tool's `reason_code`.
3. One promo code per order; codes don't combine with the mixed-case discount unless marked stackable (A-51).
