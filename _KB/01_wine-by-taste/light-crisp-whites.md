---
id: KB-TST-003
title: Light & Crisp White Wines
category: taste
subcategory: light-crisp-white
doc_type: guide
intents: [recommend.by_taste, recommend.by_food, education.wine_question]
tools: [search_products, get_product_details]
jurisdictions: [NJ, NY]
audience: agent
priority: medium
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: wine-team
status: active
depends_on_assumptions: [A-44]
related: [KB-TST-001, KB-TST-004, KB-REG-002, KB-REG-003, KB-REG-004]
---

# Light & Crisp White Wines

## 1. What they are

Light & Crisp whites are **dry, light-bodied, high in acidity and unoaked**. Customers describe them as refreshing, zesty, clean, "like lemonade without the sugar", or "great on a hot day". They are the most-requested white category for warm weather, seafood, salads and aperitifs.

**Catalog:** `style_tag=light-crisp-white` · typical axes `sweetness=dry`, `body=light`, `acidity=crisp`, `oak=none`.

## 2. Key wines in this category

| Wine | Where from | Taste in plain words | Notes for the agent |
|---|---|---|---|
| **Sauvignon Blanc (New Zealand)** | Marlborough | Zingy grapefruit, passion fruit, fresh-cut grass | Very popular, very aromatic, recognizable. Good default. |
| **Sancerre / Pouilly-Fumé** | Loire Valley, France (Sauvignon Blanc) | Lemon, flint, chalky, more restrained than NZ | Premium step-up from NZ Sauvignon Blanc. |
| **Pinot Grigio (Italy)** | Veneto, Friuli, Alto Adige, Trentino | Light, neutral, lemon-pear, easy | Crowd-pleaser. Alto Adige/Friuli versions have more flavor. |
| **Albariño / Alvarinho** | Rías Baixas (Spain) / Vinho Verde (Portugal) | Peach, lime, saline, sea breeze | Excellent with shellfish. |
| **Vinho Verde** | Portugal | Very light, lemony, sometimes slightly spritzy, often lower alcohol (~9–11%) | Budget-friendly; good low-ABV pick. |
| **Muscadet (Sèvre-et-Maine sur lie)** | Loire, France (Melon de Bourgogne) | Lemon, saline, light bready note | Classic oyster wine; great value. |
| **Chablis** | Burgundy, France (unoaked Chardonnay, mostly) | Green apple, lemon, chalk | For "Chardonnay but not buttery" customers. Premier/Grand Cru can be richer. |
| **Picpoul de Pinet** | Languedoc, France | Lemon, salty, very crisp | Value seafood wine. |
| **Grüner Veltliner** | Austria | Green apple, white pepper, lentil/green notes | Food-versatile, good with vegetables. |
| **Assyrtiko** | Santorini, Greece | Lemon, intense minerality, high acid | Premium; seafood. |
| **Dry Riesling (Trocken)** | Germany, Austria, Alsace, Finger Lakes, Clare Valley | Lime, green apple, floral | Confirm dryness; many Rieslings are off-dry (see [aromatic-and-off-dry-whites.md](aromatic-and-off-dry-whites.md)). |
| **Verdejo** | Rueda, Spain | Citrus, fennel, slightly bitter almond finish | Value alternative to Sauvignon Blanc. |
| **Soave Classico** | Veneto, Italy (Garganega) | Almond, pear, gentle | Softer edge, still light. |

## 3. Indicative price bands (A-44)

| Band | What to expect |
|---|---|
| Everyday (< $15) | Italian Pinot Grigio, Vinho Verde, Spanish Verdejo, Picpoul, many NZ Sauvignon Blancs |
| Step-up ($15–30) | Top NZ Sauvignon Blanc, Albariño, Muscadet cru, Grüner Veltliner, Alto Adige Pinot Grigio, entry Chablis |
| Premium ($30–60) | Sancerre, Pouilly-Fumé, Chablis Premier Cru, Santorini Assyrtiko |
| Luxury ($60+) | Chablis Grand Cru, top Loire single-vineyard Sauvignon Blanc |

Always quote live prices from `get_price`.

## 4. How to recommend

- **Search:** `search_products(filters={style_tag:"light-crisp-white"}, price_max=…)`. For "Sauvignon Blanc" specifically, use `grape=["Sauvignon Blanc"]`.
- **Lower alcohol** request: add `abv_max=12`. Vinho Verde, Muscadet, some German Rieslings fit.
- **"Chardonnay, but not buttery"**: Chablis, Mâcon-Villages, other unoaked Chardonnay (`grape=Chardonnay`, `oak=none`).
- **"Pinot Grigio fan who wants to branch out"**: Albariño, Soave, Grüner Veltliner, Picpoul.
- **NZ Sauvignon Blanc fan who wants something different**: Sancerre (more restrained), Verdejo, Grüner.

## 5. Food pairing and occasions

- Oysters, clams, ceviche, sushi, grilled fish, goat cheese, salads, asparagus, green vegetables, lemony chicken, fish tacos.
- Aperitif, summer picnics, beach, brunch, light lunch.
- Serve well chilled: 45–50°F (7–10°C).

## 6. Common misconceptions and edge cases

- **"Pinot Grigio and Pinot Gris are different grapes."** Same grape; Italian-style Grigio is lighter and crisper, Alsace/Oregon-style Gris rounder and fuller.
- **"Riesling is always sweet."** No. Look for "Trocken" (German), "dry" on US labels, or the sweetness scale on the back label. Check product data before stating sweetness.
- **"Chablis is a cheap jug wine."** In the US, "Chablis" was historically used on generic jug wines. True Chablis is a French appellation of unoaked Chardonnay.
- **Acid sensitivity:** if a customer finds crisp whites "sour", move to softer whites (Soave, Pinot Gris from Alsace/Oregon, unoaked Chardonnay from warmer regions).
- **Vinho Verde fizz** is normal for many brands, not a fault.

## 7. Sample dialogue

> **Customer:** Something crisp and refreshing for a seafood boil, under $20.
> **Agent:** Perfect match for crisp whites. Three in stock near you:
> - **[Albariño, Rías Baixas, $X]**: peachy and salty-fresh, great with shellfish.
> - **[Muscadet Sèvre-et-Maine, $X]**: lemony and light, a classic with seafood.
> - **[Marlborough Sauvignon Blanc, $X]**: zesty grapefruit; a crowd-pleaser if guests like bold aromas.
> Buying 6 or more bottles for the party gets you 10% off with the mixed-case discount.
