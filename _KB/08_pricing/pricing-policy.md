---
id: KB-PRC-001
title: Pricing Policy
category: pricing
subcategory: policy
doc_type: policy
intents: [price.inquiry, price.discrepancy, stock.pre_arrival]
tools: [get_price, calculate_order_totals, get_active_promotions, get_order]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: pricing
status: active
depends_on_assumptions: [A-01, A-03, A-06, A-25, A-26, A-40, A-41, A-42, A-45, A-50, A-54, A-55]
related: [KB-PRC-003, KB-PRC-004, KB-PRC-005, KB-DSC-001, KB-SYS-003]
---

# Pricing Policy

## 1. Purpose

Rules for how prices are quoted and honored so the agent always gives a correct, consistent, legally safe answer.

## 2. Policy rules

**PRC-R1: Live price only.** The agent quotes prices only from `get_price` (unit) or `calculate_order_totals` (order). Never from memory, the KB, past conversations or a customer's screenshot.

**PRC-R2: Price depends on the fulfilling store (A-01, A-03).** The NJ Store and the NY Store price independently (different wholesalers, state costs, taxes). Always know the fulfilling location before quoting. If unknown, ask for a ZIP code or say: "Prices can differ between our NJ and NY stores; what ZIP should I check?"

**PRC-R3: Online = shelf price (A-45).** Online prices match the fulfilling store's shelf price, except promotions marked "online only" or "in-store only" (`get_active_promotions` shows channel).

**PRC-R4: Price lock at order placement (A-40).** The price on the order confirmation is the price paid, even if the shelf price later changes, except for clear pricing errors (A-41, see [price-errors-and-adjustments.md](price-errors-and-adjustments.md)).

**PRC-R5: Cart prices are not locked.** Items in a cart reprice to the current price until checkout. If a sale ends while the item is in the cart, the cart shows the new price.

**PRC-R6: Sale-price display.** Say "on sale for $X until [date]" when `sale_price` and `sale_ends_at` are returned. Mention a "was" price **only** if `compare_at_verified=true` (NJ advertising rules restrict "regular price" comparisons; see G11). Never invent savings percentages.

**PRC-R7: Equal pricing (A-55).** Everyone pays the same price for the same item, channel and store, except published discounts/programs open to all. The agent never offers a private price.

**PRC-R8: Legal price floors (A-54).** The pricing engine prevents below-cost sales required by NJ rules. The agent never tries to work around a `blocked_by_price_floor` result.

**PRC-R9: Pre-arrival (futures) pricing.** Pre-arrival prices are paid in full at order and are final. If the price later changes (up or down) at release, the pre-arrival price stands (A-25).

**PRC-R10: Bottle size and vintage are part of the price.** Different sizes and vintages are separate SKUs with separate prices. Confirm size and vintage when quoting.

**PRC-R11: Volume pricing** is only via published programs (mixed-case discount, A-50). No negotiated pricing. Large-event pricing questions route to the events team (A-26).

## 3. Decision table: price questions

| Customer asks | Agent does |
|---|---|
| "How much is X?" | Confirm location → `get_price` → quote price, size, sale end if any, case-discount eligibility |
| "Is that the price in store too?" | Yes, the same as the fulfilling store's shelf price unless a channel-specific promotion applies (PRC-R3) |
| "Why is it cheaper at your other store?" | Explain PRC-R2 neutrally; we can't fulfill across states (A-01) |
| "It was cheaper last week" | Prices and promotions change; quote today's price; mention current promotions; see the price-drop policy if already purchased |
| "Can you do better on price?" | No private discounts (PRC-R7). Mention published offers (case discount, promotions, rewards) |
| "Will it go on sale?" | We don't share future promotions. Offer back-in-stock/promo notifications if enabled via communication preferences |
| "Why is wine more expensive than in Europe / at the winery?" | Neutral: taxes, import and distribution costs and state rules vary; we can't speak to others' pricing |
| "What's the price per glass?" | Divide the live bottle price by 5 (5 oz pours), labeled as an approximation |

## 4. Workflow: quoting a price

1. Resolve the product (`search_products`) and confirm size and vintage.
2. Resolve location (session ZIP, saved address, or ask).
3. `get_price(sku, fulfillment_location, quantity)`.
4. Quote: "$X per 750 ml bottle at our [NJ/NY] store." Add the sale end date if any. Add "6+ bottles get 10% off" if `case_discount_eligible` and relevant.
5. If the customer is building an order, `calculate_order_totals` for the full total with tax and fees.

## 5. Edge cases

- **Price shown on a third-party app/marketplace** (e.g., delivery apps that list our store): those platforms may set their own prices/fees. Our price is what our own site/app shows.
- **Customer screenshot with a lower price:** check whether it was a past promotion, a different size/vintage/store, or an error. Follow [price-errors-and-adjustments.md](price-errors-and-adjustments.md).
- **Mixed cart with NJ-only items (e.g., NA wine) for a NY address:** cart warning `mixed_location`; explain A-06.
- **Tool failure:** don't quote. "I'm having trouble pulling the current price. Let me try again," then retry once and offer a ticket.

## 6. Escalation

| Trigger | Priority | Reason code |
|---|---|---|
| Charged amount differs from confirmation | P2 | `pricing_dispute` |
| Customer alleges deceptive pricing or advertising | P2 (P1 if regulator mentioned) | `pricing_dispute` / `legal_matter` |
| Repeated `blocked_by_price_floor` on a published promotion | P2 | `promo_config_error` |

## 7. Response examples

> "That Sancerre is $34.99 for a 750 ml bottle at our NJ store, and it's on sale through Sunday. If you add 5 more wines, the 10% mixed-case discount applies on top of eligible non-sale bottles."

> "Prices can differ a bit between our NJ and NY stores because each is supplied and taxed separately. For your Brooklyn address, the price is $X from our NY store."
