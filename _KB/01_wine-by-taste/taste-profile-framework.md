---
id: KB-TST-001
title: Taste Profile Framework and Customer-Language Mapping
category: taste
subcategory: framework
doc_type: reference
intents: [recommend.by_taste, refine.results, education.wine_question]
tools: [search_products, get_product_details]
jurisdictions: [NJ, NY]
audience: agent, catalog-team
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: wine-team
status: active
related: [KB-TST-002, KB-SYS-008, KB-STK-006]
---

# Taste Profile Framework and Customer-Language Mapping

## 1. Purpose

Every wine in the catalog carries a **taste profile** on six axes plus a **style tag**. This document defines the axes, the catalog values that `search_products` accepts, and how to translate what customers actually say into those values. Catalog staff use the same definitions when tagging new products ([new-product-onboarding-and-catalog-standards.md](../09_stock-and-availability/new-product-onboarding-and-catalog-standards.md)).

## 2. The six taste axes

| Axis | Catalog values | What it means for the customer | Primary driver |
|---|---|---|---|
| `sweetness` | `dry` · `off_dry` · `medium_sweet` · `sweet` | How sugary it tastes | Residual sugar (dry < ~4 g/L; off-dry ~4–30; medium-sweet ~30–60; sweet > 60, still wine), balanced by acidity |
| `body` | `light` · `medium` · `full` | How heavy it feels (skim vs whole milk) | Alcohol, extract, glycerol, sugar |
| `acidity` | `soft` · `fresh` · `crisp` | Mouthwatering zing | Grape, climate, harvest timing |
| `tannin` (reds, orange) | `smooth` · `moderate` · `grippy` | Drying, tea-like grip | Skins, seeds, stems, oak |
| `oak` | `none` · `subtle` · `pronounced` | Vanilla, toast, spice, butter | New vs neutral oak, time in barrel |
| `fruit_profile` | `fruit_forward` · `balanced` · `earthy_savory` | Fruit flavors vs herbs, earth, leather | Climate, grape, winemaking, age |

Additional tags used often: `alcohol_level` (`low` < 11.5%, `moderate` 11.5–13.5%, `high` > 13.5% ABV), `aromatic` (bool), `sparkling` (bool), `serve_chilled` (bool).

## 3. Style tags (storefront "shop by style")

| `style_tag` | Customer-facing name | Typical axis values |
|---|---|---|
| `light-crisp-white` | Light & Crisp Whites | dry, light, crisp, no oak |
| `aromatic-white` | Aromatic & Off-Dry Whites | dry to off-dry, light–medium, fresh–crisp, aromatic |
| `rich-white` | Rich & Creamy Whites | dry, medium–full, soft–fresh, subtle–pronounced oak |
| `rose-dry` | Dry Rosé | dry, light, fresh–crisp |
| `rose-off-dry` | Sweet & Blush Rosé | off-dry–medium sweet, light |
| `light-red` | Light & Fruity Reds | dry, light, fresh, smooth tannin |
| `medium-red` | Smooth & Medium Reds | dry, medium, fresh, smooth–moderate tannin |
| `bold-red` | Bold & Structured Reds | dry, full, moderate–grippy tannin, often oaked |
| `sweet-red` | Sweet Reds | off-dry–sweet, light–medium (e.g., Lambrusco amabile, Brachetto, sweet red blends) |
| `sparkling` | Sparkling (see folder 04) | varies |
| `dessert` | Dessert Wines | sweet |
| `fortified` | Fortified (Port, Sherry, Madeira) | dry to sweet, full, high alcohol |
| `orange` | Orange / Skin-Contact | dry, medium, moderate tannin, earthy |

## 4. Customer language → axis mapping

| Customer says | Most likely meaning | Filters to try | Confirm? |
|---|---|---|---|
| "Smooth", "easy drinking" | Low tannin, soft acidity, fruit-forward, no harshness | `tannin=smooth`, `acidity in (soft, fresh)`, `fruit_profile=fruit_forward` | Usually not |
| "Dry" | Not sweet **or** tannic/astringent **or** "sophisticated" | `sweetness=dry`; if they also dislike bitterness, `tannin != grippy` | **Yes, always clarify** |
| "Not too sweet" | Dry to off-dry | `sweetness in (dry, off_dry)` | No |
| "Sweet but not syrupy" | Off-dry to medium-sweet with good acidity | `sweetness in (off_dry, medium_sweet)`, `acidity in (fresh, crisp)` | No |
| "Crisp", "refreshing", "zesty" | High acidity, light, no oak | `acidity=crisp`, `body=light`, `oak=none` | No |
| "Buttery", "creamy" | Rich Chardonnay style | `style_tag=rich-white`, `oak in (subtle, pronounced)` | No |
| "Not oaky", "no butter" | Unoaked | `oak=none` | No |
| "Bold", "big", "strong" | Full body, possibly grippy, possibly high alcohol | `body=full`; ask if "strong" means alcohol | Sometimes |
| "Light" (red) | Light body, low tannin | `style_tag=light-red` | No |
| "Fruity" | Fruit-forward (not necessarily sweet) | `fruit_profile=fruit_forward` | If they also say sweet |
| "Jammy" | Very ripe fruit, often warm-climate, full | `fruit_profile=fruit_forward`, `body=full` (Zinfandel, Shiraz, some Malbec) | No |
| "Earthy", "funky", "old-world style" | Savory profile | `fruit_profile=earthy_savory` | No |
| "Bitter" (as complaint) | Usually high tannin, sometimes high alcohol or oak | avoid `tannin=grippy`, `oak=pronounced` | No |
| "Sour" (as complaint) | High acidity | avoid `acidity=crisp`; prefer `soft/fresh` | No |
| "Doesn't give me a headache" | Health-adjacent; no product guarantees | Don't filter; explain we can't promise effects (G7). Offer lower-alcohol options if they want lighter wine | **Careful** |
| "Like Josh / Meiomi / Kim Crawford" | Reference wine | `get_similar_products(reference sku)` | No |
| "Light alcohol" | Low ABV | `alcohol_level=low` / `abv_max` | No |

## 5. Grapes as shortcuts (default axis profile)

Use these defaults only when product data is missing. Individual wines vary by producer and region.

| Grape | Sweetness | Body | Acidity | Tannin | Oak | Fruit |
|---|---|---|---|---|---|---|
| Sauvignon Blanc | dry | light | crisp | – | none | fruit-forward (NZ) / balanced (Loire) |
| Pinot Grigio / Gris | dry | light (IT) / medium (OR, Alsace) | fresh | – | none | balanced |
| Riesling | dry → sweet (check label) | light | crisp | – | none | fruit-forward |
| Chardonnay (unoaked) | dry | medium | fresh–crisp | – | none | balanced |
| Chardonnay (oaked) | dry | full | soft–fresh | – | pronounced | fruit-forward |
| Pinot Noir | dry | light–medium | fresh | smooth | subtle | balanced |
| Gamay | dry | light | fresh | smooth | none | fruit-forward |
| Merlot | dry | medium | fresh | smooth–moderate | subtle | fruit-forward |
| Sangiovese | dry | medium | crisp | moderate | subtle | earthy-savory |
| Tempranillo | dry | medium–full | fresh | moderate | subtle–pronounced | balanced |
| Grenache | dry | medium | soft | smooth | none–subtle | fruit-forward |
| Malbec | dry | full | fresh | moderate | subtle | fruit-forward |
| Syrah / Shiraz | dry | full | fresh | moderate–grippy | subtle | savory (Rhône) / jammy (Australia) |
| Zinfandel | dry | full | soft | moderate | subtle | fruit-forward (jammy) |
| Cabernet Sauvignon | dry | full | fresh | grippy | pronounced | balanced |
| Nebbiolo | dry | medium (feel) / high structure | crisp | grippy | subtle | earthy-savory |

## 6. Building the query

1. Start with the **style tag** if clear; otherwise combine axes.
2. Add **hard constraints**: budget (`price_max`), color, location, certifications, non-alcoholic, size.
3. Add **soft preferences** (fruit profile, oak) as sort/weight hints, not hard filters, so you don't end up with zero results.
4. If results < 2, relax in this order: `fruit_profile` → `oak` → `acidity` → `body` → widen price ±15%. Never relax `sweetness` (people notice it most) or hard constraints without telling the customer.
5. Diversify: avoid recommending 3 wines from the same producer or grape unless asked.

## 7. Example

**Customer:** "I want a red that's smooth, not sweet, around $20, for pasta night."

**Mapping:** `color=red`, `sweetness=dry`, `tannin=smooth`, `acidity=fresh` (tomato sauce needs acidity), `price_max=22`, `price_min=15`.

**Likely results:** Chianti, Montepulciano d'Abruzzo, Barbera, Côtes du Rhône. Present 3, each with a one-line "why".
