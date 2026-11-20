---
id: KB-DSC-001
title: Discount Policy Overview and Stacking Rules
category: discounts
subcategory: policy
doc_type: policy
intents: [discount.current_offers, discount.case_discount, discount.promo_code_issue]
tools: [get_active_promotions, validate_promo_code, calculate_order_totals, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: marketing-and-pricing
status: active
depends_on_assumptions: [A-03, A-43, A-50, A-51, A-52, A-53, A-54, A-55, A-56, A-61]
related: [KB-DSC-002, KB-DSC-003, KB-DSC-004, KB-DSC-006, KB-PRC-001, KB-SYS-003]
---

# Discount Policy Overview and Stacking Rules

## 1. Discount types

| Type | Example | How applied | Source |
|---|---|---|---|
| **Sale price** | "Featured: $5 off this Rioja through Sunday" | Built into the unit price (`sale_price`) | `get_price`, `get_active_promotions` |
| **Mixed-case discount** | 10% off 6–11 eligible wines; 15% off 12+ | Automatic at cart | A-50 |
| **Promo code** | `WELCOME10`, seasonal codes, partner codes | Entered at checkout | A-51 |
| **First-order offer** | $10 off first order of $75+ | Code delivered at sign-up | A-52 |
| **Rewards** | $10 reward per 250 points | Redeemed at checkout | A-53 |
| **Gift card** | Prepaid balance | Payment method, **not** a discount | A-56 |
| **Goodwill credit** | Store credit for a service failure | Agent-issued within A-61 | A-61 |
| **Price match** | Human-approved match | Final unit price | A-43 |

## 2. Stacking matrix

| Combination | Allowed? |
|---|---|
| Sale price + mixed-case discount | **No** on the sale-priced line. Sale items **count toward** the 6-bottle total but don't get the extra % (A-50) |
| Mixed-case discount + promo code | **No**, unless the code is marked `stackable=true` (A-51). The system applies whichever is better for the customer if both qualify and aren't stackable |
| Promo code + promo code | **No**. One code per order |
| Rewards + mixed-case discount | **Yes** |
| Rewards + promo code | **Yes** |
| Rewards + sale prices | **Yes** |
| Gift card + anything | **Yes** (it's payment) |
| Price-matched item + any % discount | **No** (PM-R3) |
| Goodwill credit + anything | **Yes** (store credit is payment) |
| Any combination resulting in below-cost price | **Blocked** by the engine (A-54) |

## 3. Universal exclusions (unless a promotion explicitly includes them)

- Gift cards (never discountable).
- Pre-arrivals/futures, allocated, collectible and special-order items.
- Taxes; delivery/shipping fees (except free-delivery promotions).
- Items marked `final_sale` or "excluded from promotions" by the producer/distributor program.
- Boxed and canned wine for the mixed-case discount (A-50).

## 4. Legal and fairness guardrails

**DSC-G1: Equal availability (A-55).** Every discount is published and open to all eligible 21+ customers on the same terms. No private negotiations, no "manager's discount", no unadvertised codes from the agent.

**DSC-G2: Price floors (A-54).** NJ prohibits retail sales below cost (N.J.A.C. 13:2-24.8), including through coupon redemption and combination offers. The engine enforces cost floors per SKU; an over-discounted line returns `blocked_by_price_floor`.

**DSC-G3: No inducement framing.** The agent never uses discounts to pressure quantity ("buy 12 and drink more!"). Quantity discounts are presented as savings on what the customer already wants.

**DSC-G4: Truthful savings.** Savings amounts come from `calculate_order_totals`; "was/now" comparisons only with `compare_at_verified=true` (G11).

**DSC-G5: Store-specific promotions.** Promotions can differ between the NJ and NY Stores (A-03). Codes may be location-restricted (`location_mismatch`).

## 5. Agent workflow: "Any deals?"

1. Determine location and, if known, the items of interest.
2. `get_active_promotions(fulfillment_location, sku?)`.
3. Share up to 3 relevant offers in one short list, with end dates.
4. Always mention the **mixed-case discount** if the customer is buying several bottles, and **Rewards** if they're a member (or invite them to join, free).
5. Never imply that a better deal is coming.

## 6. Escalation

The agent never creates, negotiates or "honors" a discount that the tools don't return (DSC-G1). Anything outside the published offers goes to a person.

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Customer mentions a lawsuit, attorney or regulator complaint about a promotion or advertised price | P1 | `legal_matter` | Don't discuss whether the promotion was lawful |
| Customer says they were promised a discount that `get_active_promotions` doesn't show (by staff, an email or an ad) | P2 | `pricing_dispute` | Ask where they saw it; don't apply or promise it |
| Customer says a "was/now" comparison or advertised saving is misleading (G11) | P2 | `pricing_dispute` | Include the product, the advertised claim and where it appeared, so compliance can review it |
| An advertised promotion doesn't apply although the cart meets its terms, after [discount-troubleshooting.md](discount-troubleshooting.md) | P2 | `promo_config_error` | Include cart ID, promotion name and the tool's `reason_code` |
| A promotion seems to give far more than advertised (e.g., a code taking 50% off everything) | P2 | `promo_config_error` | Don't apply it further; don't promise the price will be honored |
| A bar, restaurant or other business asks for trade or wholesale pricing (G9) | P2 | `business_sales` | Explain we sell at retail; don't quote a business price |
| Price-match requests | P2 | `price_match` | Follow [price-matching-policy.md](../08_pricing/price-matching-policy.md) |

**Handle without escalating:** "any deals?" questions, stacking explanations, `blocked_by_price_floor` messages (explain that legal minimum pricing applies, without detail) and requests for a "VIP" or manager discount. Decline those politely (DSC-G1).

## 7. Response examples

> "Here's what's running at our NY store this week: 15% off all Spanish reds through Sunday, and free delivery on orders over $75 with code SHIPFREE75. And if you buy 6 or more wines, our mixed-case discount gives 10% off eligible bottles (the code and the case discount don't combine, but the system will apply whichever saves you more)."

> "I can't create a special discount, but here's how to save on this order: you have a $10 Rewards reward available, and adding one more bottle unlocks 10% off your case."
