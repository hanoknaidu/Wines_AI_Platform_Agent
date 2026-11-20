---
id: KB-DSC-002
title: Mixed-Case and Volume Discounts
category: discounts
subcategory: mixed-case
doc_type: policy
intents: [discount.case_discount, stock.bulk_quantity, order.place_help]
tools: [calculate_order_totals, get_cart, add_to_cart, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: pricing
status: active
depends_on_assumptions: [A-12, A-26, A-50, A-51, A-54, A-60]
related: [KB-DSC-001, KB-STK-007, KB-PRC-005, KB-STK-003]
---

# Mixed-Case and Volume Discounts

## 1. The offer (A-50)

| Eligible wines in the cart | Discount on eligible lines |
|---|---|
| 6–11 bottle-equivalents | **10% off** |
| 12+ bottle-equivalents | **15% off** |

- **Mix and match** any eligible wines: reds, whites, sparkling, rosé, NA wine (NJ Store), different producers.
- Applies automatically in the cart; no code needed.

## 2. Counting bottles (750 ml equivalents)

| Size | Counts as |
|---|---|
| 187 ml | 0.25 |
| 375 ml (half) | 0.5 |
| 500 ml | 0.67 |
| 750 ml | 1 |
| 1 L | 1.33 |
| 1.5 L (magnum) | 2 |
| 3 L+ large-format **bottles** | 4 per 3 L |
| 3 L **boxed** wine, cans | Not eligible (don't count) |

**Sale-priced items count toward the 6/12 threshold** but don't receive the extra % (stacking rule).

## 3. Eligibility

| Eligible | Not eligible (don't count, no discount) |
|---|---|
| Regular-priced still, sparkling, fortified, dessert and NA wines in glass bottles | Boxed/bag-in-box and canned wine |
| | Pre-arrival/futures, allocated, special-order and collectible items |
| | Gift cards, accessories, gift wrapping |
| | Price-matched items |
| | Spirits and beer (separate rules, out of scope) |

## 4. Interaction with other offers

- **Promo codes:** not combined unless `stackable=true` (A-51); the system applies the better one.
- **Rewards:** combine.
- **Free delivery threshold:** uses the product subtotal **after** the case discount (so a discount can drop an order below $99; see the example in [taxes-fees-and-order-totals.md](../08_pricing/taxes-fees-and-order-totals.md)).
- **Price floors:** if 15% would breach a SKU's floor, that line gets the maximum allowed and the cart notes it (A-54).

## 5. Partial fulfillment and returns

- If an item is removed during picking (out of stock) and the count drops below 6 or 12, **we keep the original discount tier** (see [out-of-stock-and-substitutions.md](../09_stock-and-availability/out-of-stock-and-substitutions.md) §4).
- If the customer **returns** bottles (NJ change-of-mind) and the remaining count drops below the tier, the refund is reduced by the discount no longer earned. The return is calculated by the tool; the agent explains it.

## 6. Agent behavior

- Mention the discount **once**, at a helpful moment: when the cart has 4–5 bottles ("one more bottle gets 10% off") or 10–11 bottles ("one more for 15%").
- Don't pressure. If the customer wants 5 bottles, that's fine.
- Use `calculate_order_totals` to show the real savings.

## 7. Examples

| Cart | Result |
|---|---|
| 5 × 750 ml regular price | No discount; "Add one more to save 10%." |
| 4 × 750 ml + 2 × 375 ml | 5 bottle-equivalents; no discount |
| 6 × 750 ml, 2 of them on sale | 6 count; 10% off the 4 regular-priced lines only |
| 11 × 750 ml + 1 magnum | 13 equivalents; 15% off eligible lines |
| 6 × 750 ml + code WELCOME10 ($10 off $75) | Not stackable: the system applies the larger saving |
| 2 boxed wines + 5 × 750 ml | Boxes don't count; 5 → no discount |

## 8. Escalation

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| The cart shows the wrong tier or no case discount, after you've recounted 750 ml equivalents and exclusions (§2–§3) | P2 | `promo_config_error` | Include cart ID, each line's size and eligibility, and the expected vs shown tier |
| A placed order was charged without the case discount it qualified for | P2 | `pricing_dispute` | Under PRC-E6 the agent refunds a system-error difference within A-60. Escalate only if it's over $150 or unclear ([price-errors-and-adjustments.md](../08_pricing/price-errors-and-adjustments.md)) |
| The discount tier was removed after an out-of-stock removal, contrary to §5 | P2 | `pricing_dispute` | Include the original and final bottle counts |
| Customer disputes a reduced refund after a return dropped the tier (§5) | P2 | `pricing_dispute` | Share the tool's calculation; don't recalculate by hand |
| More than 60 bottles or $2,500 (A-26) | P2 | `bulk_order` | Follow [purchase-limits-and-bulk-orders.md](../09_stock-and-availability/purchase-limits-and-bulk-orders.md) §3 |
| Buying cases for resale (a shop, bar or online reselling) | P2 | `business_sales` | Don't process the order (PL-R4) |

**Handle without escalating:** bottle-count questions, sale items that count but don't get the extra percentage, lines held back by a price floor (A-54), and code-vs-case comparisons (the system applies the better saving).

## 9. Response examples

> "Nice picks! You have 5 bottles in your cart. If you add one more wine, you'll get 10% off the eligible bottles, about $11 off this order. Want a suggestion for the sixth?"

> "The two Champagnes are already on sale, so they count toward your 12 bottles but don't get the extra 15%. The other 10 bottles do. Your total savings come to $38.40."
