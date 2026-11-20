---
id: KB-TST-000
title: Wine by Taste: Folder Index
category: taste
subcategory: index
doc_type: index
intents: [recommend.by_taste, recommend.by_food, recommend.by_occasion, refine.results, education.wine_question]
tools: [search_products, get_product_details, get_similar_products]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: wine-team
status: active
depends_on_assumptions: [A-44]
related: [KB-TST-001, KB-TST-002]
---

# Wine by Taste: Folder Index

## Scope

How to understand what a customer likes in **their own words** and turn it into catalog filters and good recommendations. The taste categories mirror the **"shop by style"** navigation on the storefront, the most common primary browse pattern among wine retailers, with region, grape and price as secondary filters.

## Files

| File | Answers |
|---|---|
| [taste-profile-framework.md](taste-profile-framework.md) | The 6 taste axes, catalog filter values, how customer words map to axes |
| [taste-discovery-conversation-flow.md](taste-discovery-conversation-flow.md) | How to interview, handle vague or contradictory requests, refine results |
| [light-crisp-whites.md](light-crisp-whites.md) | Sauvignon Blanc, Pinot Grigio, Albariño, Muscadet, Vinho Verde, Chablis… |
| [aromatic-and-off-dry-whites.md](aromatic-and-off-dry-whites.md) | Riesling, Gewürztraminer, Moscato, Torrontés, Chenin Blanc, Viognier |
| [rich-full-bodied-whites.md](rich-full-bodied-whites.md) | Oaked Chardonnay, white Rhône, white Burgundy, aged whites |
| [rose-wines.md](rose-wines.md) | Provence-style dry rosé, fuller rosés, off-dry/blush |
| [light-fruity-reds.md](light-fruity-reds.md) | Pinot Noir, Gamay/Beaujolais, Frappato, light Grenache |
| [medium-smooth-reds.md](medium-smooth-reds.md) | Merlot, Chianti/Sangiovese, Rioja, Côtes du Rhône, Barbera, red blends |
| [bold-full-bodied-reds.md](bold-full-bodied-reds.md) | Cabernet Sauvignon, Malbec, Syrah/Shiraz, Zinfandel, Nebbiolo, Amarone |
| [sweet-dessert-and-fortified-wines.md](sweet-dessert-and-fortified-wines.md) | Sauternes, late harvest, ice wine, Port, Sherry, Madeira, sweet reds |
| [food-pairing-guide.md](food-pairing-guide.md) | Pairing rules and quick lookups by dish |

Sparkling wines are in [04_sparkling-champagne-prosecco/](../04_sparkling-champagne-prosecco/README.md).

## Top intents → first document

| Intent | Start with |
|---|---|
| "Something smooth / not too sweet / crisp" | taste-profile-framework → matching style file |
| "I don't know what I like" | taste-discovery-conversation-flow |
| "What goes with…" | food-pairing-guide |
| "Something lighter / bolder / less oaky" | taste-discovery-conversation-flow §6 (refine) |

## Rules that apply to every file here

1. Taste descriptions are **general style guidance**. Specific bottles must come from `search_products` for the customer's fulfilling location.
2. Price bands are **indicative** (A-44); quote live prices only from `get_price`.
3. Never claim a specific bottle has a taste attribute unless `get_product_details.taste` supports it.
