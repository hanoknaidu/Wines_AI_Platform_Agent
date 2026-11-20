---
id: KB-PRC-005
title: Taxes, Fees and How Order Totals Are Calculated
category: pricing
subcategory: taxes-fees
doc_type: reference
intents: [delivery.fees_and_minimums, price.inquiry, price.discrepancy, order.place_help]
tools: [calculate_order_totals, get_fulfillment_options, get_order]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: finance
status: active
depends_on_assumptions: [A-10, A-11, A-12, A-15, A-16, A-19, A-27, A-34, A-50, A-51, A-53, A-56]
related: [KB-PRC-001, KB-ORD-004, KB-ORD-007, KB-DSC-001]
---

# Taxes, Fees and Order Totals

## 1. Order of calculation (what `calculate_order_totals` does)

```
1. Line subtotal          = Σ (unit price × quantity)          [price per fulfilling store]
2. Item-level promotions  − sale prices already in unit price; promo-code item discounts
3. Mixed-case discount    − 10% / 15% on eligible lines (A-50), if not blocked by promo stacking rules (A-51)
4. Product subtotal       = after discounts, before tax and fees  → used for delivery minimum/free-delivery thresholds (A-11, A-12, A-15)
5. Rewards redemption     − applied as a discount on eligible products (A-53)
6. Fees                   + delivery fee (A-10) or shipping fee (A-15); pickup is free (A-16)
7. Sales tax              + per state/locality rules on taxable amounts
8. Gift card              − applied as payment (not a discount; not taxed) (A-56)
9. Order total
```

The agent always quotes the **tool's** totals. This document explains them.

## 2. Sales tax (reference only; the tool calculates)

| State | Basis | Typical rate (as of review) | Notes |
|---|---|---|---|
| **New Jersey** | Statewide sales tax on alcoholic beverages | 6.625% | Some zones (e.g., Urban Enterprise Zones) have special rates for certain sellers; rate is determined by the tool |
| **New York** | State 4% + local (county/city) rates; NYC also includes the Metropolitan Commuter Transportation District surcharge | Varies by locality; e.g., NYC 8.875% | Rate depends on the **delivery address** (or store location for pickup) |

- **Excise taxes** (federal and state) on wine are paid upstream and are **built into the shelf price**; they are not shown separately.
- **Delivery and shipping charges** may be taxable depending on state rules; the tool applies this.
- **Tax-exempt purchases:** we sell at retail to consumers. Tax-exempt requests (e.g., organizations) route to the business/events team (P3); the agent cannot remove tax.
- **Agent rule:** never quote a tax rate as definitive for an address; say "tax is calculated at checkout based on your delivery address" and use the tool for exact numbers.

## 3. Fees

| Fee | Amount | Waived when | Source |
|---|---|---|---|
| Local delivery, Zone 1 (0–5 mi) | $5.99 | Product subtotal ≥ $99 | A-10, A-12 |
| Local delivery, Zone 2 (5–15 mi) | $9.99 | Product subtotal ≥ $99 | A-10, A-12 |
| Local delivery minimum | $40 product subtotal | — | A-11 |
| In-state ground shipping | $14.99 (1–6 bottles), $19.99 (7–12), +$5 per additional 6 | Product subtotal ≥ $199 | A-15 |
| Insulated/expedited shipping during weather holds | Quoted by tool; optional | — | A-19 |
| Pickup | Free | — | A-16 |
| Restocking fee (NJ change-of-mind returns) | 15% of item price | Store credit option at full value; never on defective/damaged/our error | A-34 |
| Bottle deposit | None on wine in NJ or NY | — | NY's bottle bill covers beer, soda, water and certain wine coolers/wine products, not regular wine |

**Free-delivery nudges:** `calculate_order_totals.free_delivery_gap` shows how much more qualifies. Mention it only when the gap is ≤ $25 (persona rules).

## 4. Common questions

**"Why did my total change at checkout?"** The address determined the fulfilling store, tax rate, and delivery zone/fee; or a promotion/discount rule changed the subtotal; or an item repriced in the cart (PRC-R5).

**"Do discounts reduce the free-delivery threshold?"** Yes, the threshold uses the product subtotal **after** discounts. Example: $105 of wine with 10% case discount = $94.50, which is below the $99 free-delivery threshold.

**"Is tip included?"** Tip (if the delivery flow offers it) is optional, goes to the driver, and is shown separately. Tipping is offered for local delivery only (A-27).

**"Why is there tax on the delivery fee?"** Some states treat delivery charges on taxable goods as taxable. The tool follows the rules for your address.

**"Do gift cards get taxed?"** Buying a gift card isn't taxed; tax applies to the products when the card is used.

## 5. Sample response

> "Here's your breakdown: wine subtotal $112.00, mixed-case discount −$11.20, product subtotal $100.80, so delivery is free. NJ sales tax $6.68. Total: $107.48."
