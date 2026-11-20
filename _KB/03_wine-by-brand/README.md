---
id: KB-BRD-000
title: Wine by Brand: Folder Index
category: brand
subcategory: index
doc_type: index
intents: [recommend.by_brand, recommend.similar, product.details, stock.product_request]
tools: [search_products, get_product_details, get_similar_products, submit_product_request]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: wine-team
status: active
related: [KB-BRD-001, KB-BRD-006]
---

# Wine by Brand: Folder Index

## Scope

Brand profiles help the agent (1) recognize what a customer means by a brand ("I like Josh"), (2) infer the **style** behind it so it can recommend similar wines, and (3) answer brand questions accurately. Brand profiles are **reference knowledge only**. Whether we carry a brand, and its price, comes from `search_products` / `get_price` for the customer's fulfilling location.

## Files

| File | Covers |
|---|---|
| [brand-catalog-policy.md](brand-catalog-policy.md) | How brands are sourced and listed, exclusives/private label, label changes, discontinued brands, counterfeit/provenance, brand requests, neutrality rules |
| [champagne-and-sparkling-houses.md](champagne-and-sparkling-houses.md) | Major Champagne houses, Prosecco, Cava and US sparkling brands |
| [us-brands.md](us-brands.md) | Widely requested California, Washington and Oregon brands |
| [european-brands.md](european-brands.md) | French, Italian, Spanish, Portuguese and German brands and estates |
| [southern-hemisphere-brands.md](southern-hemisphere-brands.md) | New Zealand, Australia, Argentina, Chile, South Africa |
| [brand-profile-template.md](brand-profile-template.md) | Template for adding a new brand profile |

Low-calorie and better-for-you brands are in [05_low-calorie-and-better-for-you/](../05_low-calorie-and-better-for-you/README.md); non-alcoholic brands in [07_non-alcoholic-wines/](../07_non-alcoholic-wines/README.md).

## Workflow: "Do you have [brand]?"

1. `search_products(query="<brand>", fulfillment_location)`.
2. Found → `check_inventory` + `get_price` → answer with the specific wine(s), sizes and price.
3. Found but out of stock → back-in-stock alert + `get_similar_products`.
4. Not carried → say so honestly, use the brand profile here to describe the style, offer 2–3 similar wines we do carry, and offer a product request.

## Workflow: "Something like [brand]"

1. Find the reference SKU (or the brand profile if we don't carry it).
2. `get_similar_products(sku or taste_profile, constraints{price_band})`.
3. Explain the shared style in plain words, and what's different ("a bit less oaky", "more savory").
