---
id: KB-SPK-004
title: Sparkling Wine Sweetness Scale (Brut Nature to Doux)
category: sparkling
subcategory: sweetness-scale
doc_type: reference
intents: [recommend.sparkling, education.wine_question, product.details]
tools: [get_product_details, search_products]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 365
owner: wine-team
status: active
related: [KB-SPK-002, KB-SPK-003, KB-SYS-008, KB-LCW-003]
---

# Sparkling Wine Sweetness Scale

## 1. The scale

Sparkling wine sweetness is labeled by **residual sugar in grams per liter (g/L)** under EU rules, also used widely elsewhere. Most of the sugar comes from the **dosage**, a small addition of wine and sugar after disgorgement in traditional-method wines.

| Label term | Residual sugar (g/L) | Taste in plain words | Catalog `sweetness` |
|---|---|---|---|
| **Brut Nature** (also Pas Dosé, Dosage Zéro, Zero Dosage, Non Dosé) | 0–3 (no added sugar) | Bone dry, very crisp, mineral | `dry` |
| **Extra Brut** | 0–6 | Very dry | `dry` |
| **Brut** | 0–12 (under 12) | Dry; the most common style | `dry` |
| **Extra Dry / Extra Sec / Extra Seco** | 12–17 | **Off-dry**: a touch of sweetness, softer, fruitier | `off_dry` |
| **Dry / Sec / Seco / Trocken** | 17–32 | **Noticeably sweet** despite the name | `medium_sweet` |
| **Demi-Sec / Semi-Seco / Halbtrocken** | 32–50 | Sweet; pairs with desserts | `sweet` |
| **Doux / Dulce / Mild** | 50+ | Very sweet | `sweet` |

Sources differ slightly at the edges (e.g., Sec 17–32 vs 17–35). Labels overlap: a wine with 3 g/L could legally be Brut Nature, Extra Brut or Brut.

**Grams to sugar for customers (approximate, general estimate):** 12 g/L is about 9 g of sugar per 750 ml bottle, or roughly 1.8 g per 5 oz glass. Use this only as a general illustration. Product-specific values must come from `get_product_details.nutrition` (G7).

## 2. The confusion to clear up

> "It's a bit backwards: **Extra Dry is actually sweeter than Brut**, and **'Dry' sparkling wine is fairly sweet**. The words date from a time when Champagne was much sweeter overall. If you want the driest, look for Brut, Extra Brut or Brut Nature."

## 3. Sweetness and perception

- High acidity makes a wine taste **less sweet** than its sugar level suggests. A Brut with 10 g/L can taste bone dry.
- Cold temperature hides sweetness; warm temperature shows it.
- Fruity aromas (Prosecco) can make a dry wine seem sweeter.

## 4. Which sweetness for which use

| Use | Best sweetness |
|---|---|
| Aperitif, oysters, sushi, salty snacks | Brut Nature, Extra Brut, Brut |
| Mimosas | Brut or Extra Dry (the juice adds sweetness) |
| Aperol Spritz | Brut (Extra Dry is fine but sweeter) |
| Spicy food | Extra Dry |
| Wedding cake, fruit desserts | Demi-Sec, Moscato d'Asti |
| Sweet-wine lovers | Extra Dry → Dry → Demi-Sec |
| Low-sugar / "keto" requests | Brut Nature, Extra Brut. Give label-based ranges only; no health claims (see [dietary-questions-sugar-keto-gluten-vegan.md](../05_low-calorie-and-better-for-you/dietary-questions-sugar-keto-gluten-vegan.md)) |

## 5. Agent workflow

1. If the customer mentions sweetness, map it to label terms with the table.
2. `search_products(filters={sparkling:true, sweetness_label:[...]})`.
3. Before saying "this has X g/L", check `get_product_details` for `residual_sugar_gl`. If missing, say "it's labeled Brut, which means under 12 g/L".

## 6. Sample dialogues

> **Customer:** Is Extra Dry Prosecco very dry?
> **Agent:** Surprisingly, no. Extra Dry is a little sweeter than Brut, with a soft, fruity touch. If you want it crisper and drier, go for a Brut. Both are great for mimosas.

> **Customer:** What's the least sweet Champagne?
> **Agent:** Look for "Brut Nature" (also called Zero Dosage or Pas Dosé). No sugar is added, so it's bone-dry and mineral. Extra Brut is next. Here are a few in stock: …
