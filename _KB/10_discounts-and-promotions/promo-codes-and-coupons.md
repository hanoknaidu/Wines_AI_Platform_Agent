---
id: KB-DSC-003
title: Promo Codes, Coupons, First-Order and Referral Offers
category: discounts
subcategory: promo-codes
doc_type: policy
intents: [discount.promo_code_issue, discount.current_offers, account.create]
tools: [validate_promo_code, apply_promo_code, get_active_promotions, calculate_order_totals, get_order, issue_refund, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: marketing
status: active
depends_on_assumptions: [A-03, A-21, A-51, A-52, A-54, A-55, A-60]
related: [KB-DSC-001, KB-DSC-006, KB-PRC-003]
---

# Promo Codes, Coupons, First-Order and Referral Offers

## 1. Code types

| Type | Example | Typical terms |
|---|---|---|
| **Public promotion** | `HOLIDAY15` | Published on site/email/social; time-limited; may target a category |
| **First-order offer** | Sign-up code | $10 off a first order of $75+ product subtotal (A-52) |
| **Free-delivery code** | `SHIPFREE75` | Waives delivery/shipping fee above a minimum |
| **Referral** | Unique code per member | Referred friend: first-order offer; referrer: Rewards points after the friend's first order is fulfilled (both 21+) |
| **Service-recovery code** | One-time code issued by support | Tied to one account; alternative to goodwill credit |
| **Partner/event code** | Tasting event attendees | Terms per event |

## 2. Rules

**DSC-P1: One code per order (A-51).** Codes don't combine with each other, and don't combine with the mixed-case discount unless `stackable=true`. When both qualify, the engine applies the better saving.

**DSC-P2: Validity.** Each code has start/end dates (store local time), a minimum (product subtotal after other discounts), eligible categories/SKUs, a location (NJ, NY or both; A-03), and usage limits (per customer, total).

**DSC-P3: First-order offer (A-52).** One per person, household, address and payment method. A "first order" means the first **fulfilled** order on any account matching those identifiers. A cancelled first order doesn't use up the offer.

**DSC-P4: Exclusions.** Gift cards, taxes and fees (unless a delivery code), pre-arrivals, allocated/collectible, special orders, price-matched items, and any item the code terms exclude. Codes can't bring any item below its legal price floor (A-54).

**DSC-P5: No cash value.** Codes aren't redeemable for cash or transferable (except referral codes meant to be shared with eligible 21+ friends).

**DSC-P6: Returns.** If items bought with a code are returned, the refund reflects the discount allocated to those items. If a return drops the order below the code's minimum, the code's value is deducted from the refund.

**DSC-P7: Forgot to apply a code.** If the order **hasn't been picked**, the agent can cancel and re-place the order with the code (A-21), or, if the system supports it, apply the code to the open order. If **already fulfilled**, as a one-time courtesy within **7 days**, the agent may refund the code's value when the code was valid at the time of order and conditions were met (within A-60 limits; one courtesy per customer per 12 months).

**DSC-P8: Agent never creates or reveals codes.** The agent only shares codes returned by `get_active_promotions` that are marked `public=true`, and service-recovery codes issued through tools.

**DSC-P9: Equal availability (A-55).** Codes posted publicly are available to all eligible customers. Influencer/partner codes are allowed if publicly usable by anyone with the code and not restricted to particular customer groups beyond age.

## 3. Workflow: apply a code

1. Ask for the code (or find an applicable public code via `get_active_promotions` if the customer asks "is there a code?").
2. `validate_promo_code(code, cart_id)` → if `valid`, explain the saving, then `apply_promo_code`.
3. If invalid, translate `reason_code` (see [discount-troubleshooting.md](discount-troubleshooting.md)) and suggest the best alternative (e.g., the mixed-case discount might save more).
4. Show totals via `calculate_order_totals`.

## 4. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| A published code fails though the cart meets its terms, after [discount-troubleshooting.md](discount-troubleshooting.md) | P2 | `promo_config_error` | Include the code, cart ID and the `validate_promo_code` `reason_code` |
| A code that isn't public and isn't tied to this customer is circulating (DSC-P8) | P2 | `promo_config_error` | Don't apply it; don't comment on where it came from |
| Forgot-to-apply courtesy (DSC-P7) worth more than $150 (A-60) | P2 | `refund_over_limit` | Confirm the code was valid at order time and the terms were met |
| Forgot-to-apply after 7 days, or a second courtesy within 12 months, with a credible reason | P2 | `policy_exception_request` | Include the earlier courtesy date; don't promise the refund |
| First-order offer rejected because the household, address or payment method already used it (DSC-P3), and the customer disputes it | P2 | `policy_exception_request` | Never reveal which identifier matched |
| Referral points missing after the friend's first order was fulfilled | P3 | `create_support_ticket(category="loyalty")` | Include both order numbers if the customer has them |

**Handle without escalating:** applying valid codes, expired or below-minimum codes (explain and suggest the better alternative), one-code-per-order questions, and DSC-P7 courtesies within its limits.

## 5. Response examples

> "Your code WELCOME10 works. That's $10 off your $82 order. One note: your 6 bottles also qualify for the 10% mixed-case discount ($8.20), and they don't combine, so the system is applying the $10 code since it saves you more."

> "That code ended on Sunday, so it won't apply now. You do have a $10 Rewards reward available. Want me to use that instead?"
