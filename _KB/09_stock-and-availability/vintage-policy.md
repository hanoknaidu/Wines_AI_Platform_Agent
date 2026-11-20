---
id: KB-STK-002
title: Vintage Policy (Display, Changes and Substitution)
category: stock
subcategory: vintage
doc_type: policy
intents: [stock.vintage_question, order.substitution_response, product.details]
tools: [get_product_details, check_inventory, get_order, respond_to_substitution, cancel_order]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: inventory-operations
status: active
depends_on_assumptions: [A-22, A-23, A-24, A-33]
related: [KB-STK-003, KB-STK-006, KB-ORG-003, KB-LCW-002]
---

# Vintage Policy

## 1. Why vintages change

Most wines are released yearly. When a store sells through one vintage and receives the next, the listing may change mid-season, and stock of the two vintages can briefly overlap. Retail practice across major online wine sellers is to substitute adjacent vintages of the same wine for everyday bottles, but **never** for vintage-sensitive wines without consent.

## 2. Listing types

| Listing type | Flag | Meaning |
|---|---|---|
| **Vintage-specific** | `vintage_specific=true` | You get exactly the vintage shown. Used for vintage Champagne, scored/collectible wines, older vintages, all wines $25+ (A-23) |
| **Current vintage** | `vintage_specific=false` | The listing shows the vintage currently in stock, but an adjacent vintage may be supplied (A-22). The product page says "Vintage may vary" |
| **Non-vintage (NV)** | `vintage=null` | Blend of years (most Champagne, many sparkling and fortified wines). No vintage applies |

## 3. Substitution rules

**VIN-R1: Automatic substitution (A-22).** If the item is **under $25** and **not vintage-specific**, staff may supply an adjacent vintage (± 2 years) of the **same producer, same wine, same bottle size**. The receipt notes "Vintage substituted: 2022 → 2023". No action needed from the customer.

**VIN-R2: Consent required (A-23).** If the item is **$25 or more**, or `vintage_specific=true`, we **never substitute without consent**. The customer receives a notification (email/SMS/app) and has **24 hours** to approve or decline. No response = the item is removed and refunded; the rest of the order proceeds.

**VIN-R3: Never a different wine without consent.** A different producer or wine is not a vintage substitution. It follows the customer's substitution preference (A-24; see [out-of-stock-and-substitutions.md](out-of-stock-and-substitutions.md)).

**VIN-R4: Price.** A substituted vintage is supplied at the **lower** of the two prices. If the new vintage costs more, the customer pays the original price for VIN-R1 substitutions; for VIN-R2, the customer is shown both prices before approving.

**VIN-R5: Claims data.** Certifications, scores and nutrition data are **vintage-specific**. When a vintage changes, the catalog re-verifies them (ORG-R3). The agent never carries a score from one vintage to another.

**VIN-R6: Customer doesn't want a substitute.** A customer who received a VIN-R1 substitution and is unhappy may return it unopened under the store's rules, or, as a policy exception, within **7 days** for full refund/credit with **no restocking fee** (substitution is treated as our action).

## 4. Workflow: customer approves/declines a vintage change

1. `get_order(order_id)` → find the line with `substitution_pending`.
2. Explain: original vintage, proposed vintage, price, any notable difference (e.g., "the 2022 has a 93-point score from [source]; the 2023 hasn't been rated yet", only if in data).
3. Ask for a decision → `respond_to_substitution(order_id, line_id, decision)` after explicit confirmation.
4. Confirm the updated order total.

## 5. Common questions

**"What vintage will I get?"** For vintage-specific listings: the one shown. Otherwise: "The listing shows 2023 currently in stock. If it changes before we pick your order, you may receive an adjacent vintage of the same wine; it'll be noted on your receipt."

**"Is the new vintage as good?"** Be honest and neutral: vintage quality varies by region and year; for everyday wines, producers aim for a consistent style. Share critics' data only from `accolades`.

**"I want the older vintage specifically."** Check `check_inventory` for that vintage SKU (vintages can be separate SKUs). If unavailable, offer a back-in-stock alert or a product request (older vintages are hard to source).

**"Why is my bottle a different vintage from the photo?"** Photos may show a past vintage. The vintage line on the listing and the receipt are authoritative.

## 6. Edge cases

- **Rosé and crisp whites:** the newer vintage is usually preferred; substitution in that direction is welcome.
- **Older vintages / library wines** (A-33) are always vintage-specific and sold as-is for natural aging variation.
- **Vintage Port, vintage Champagne:** declared vintages only; never substitute NV for vintage or vice versa.
- **Gift orders:** for vintage-specific items in gift orders, the **purchaser** (not the recipient) receives the consent request.

## 7. Escalation

| Trigger | Priority |
|---|---|
| Substitution made in violation of VIN-R2 (no consent, $25+) | P2 `policy_violation`. Offer a full refund/return regardless of state, and log |
| Dispute about vintage on a collectible purchase | P2 `collectible_dispute` |

## 8. Response examples

> "Heads-up on your order: the 2021 Napa Cabernet you chose just sold out, but we have the 2022 of the same wine at the same price ($64.99). Would you like the 2022, or should I remove it and refund that item?"

> "That Pinot Grigio listing is 'vintage may vary'. It's currently the 2024, and if the 2025 arrives before we pick your order, you'd get the newer one. For everyday whites like this, newer is usually fresher."
