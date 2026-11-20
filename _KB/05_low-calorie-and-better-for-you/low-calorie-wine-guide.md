---
id: KB-LCW-001
title: Low-Calorie Wine Guide
category: low-calorie
subcategory: guide
doc_type: guide
intents: [recommend.low_calorie, education.wine_question, product.details]
tools: [search_products, get_product_details, get_similar_products]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 120
owner: wine-team
status: active
depends_on_assumptions: [A-06, A-44]
related: [KB-LCW-002, KB-LCW-003, KB-SPK-004, KB-NAW-001, KB-SYS-003]
---

# Low-Calorie Wine Guide

## 1. Where calories in wine come from

Wine calories come almost entirely from **alcohol** (about 7 kcal per gram) and **residual sugar/carbohydrates** (about 4 kcal per gram). Wine has essentially no fat or protein.

**General estimate formula (for education only; not for a specific product):**

```
kcal per serving ≈ (serving_ml × ABV × 0.789 × 7) + (serving_ml × residual_sugar_g_per_L ÷ 1000 × 4)
```

| Example (5 oz / 148 ml) | ABV | Residual sugar | Approx. kcal |
|---|---|---|---|
| Light, dry white (Vinho Verde, Mosel Kabinett trocken) | 9–10% | 2–5 g/L | ~75–90 |
| Dry white or rosé | 12–12.5% | 2–4 g/L | ~100–110 |
| Brut sparkling | 12% | 6–10 g/L | ~100–105 |
| Dry red, medium | 13.5% | 2–3 g/L | ~112–118 |
| Bold red / Zinfandel | 15% | 3–5 g/L | ~125–130 |
| Moscato d'Asti | 5.5% | 100–130 g/L | ~105–120 |
| Dessert or fortified (3 oz / 89 ml) | 17–20% | 80–120 g/L | ~115–135 |
| Branded "lower-calorie" wines | often 7–9% | low | often ~70–90 (check label) |

**Key message for customers:** "In most wines, alcohol accounts for most of the calories, so lower-alcohol, dry wines are naturally lighter."

## 2. Naturally lighter styles (non-branded)

| Style | Why lighter | Taste |
|---|---|---|
| **Vinho Verde** | Often 9–11% ABV | Zesty, lightly spritzy |
| **German Riesling Kabinett (trocken/feinherb) and Mosel styles** | 8–11% ABV; note off-dry versions add sugar | Lime, apple |
| **Brut Nature / Extra Brut sparkling** | Little or no added sugar | Crisp, dry |
| **Muscadet, Picpoul, Txakoli, some Albariño** | Moderate ABV (~11–12.5%), dry | Crisp |
| **Light reds: Beaujolais, cool-climate Pinot Noir, Lambrusco secco** | Lower ABV than bold reds | Fruity, light |
| **Moscato d'Asti** | Very low alcohol (~5–6%) but high sugar: calories similar to dry wine | Sweet |

## 3. Branded better-for-you lines

Several producers market wines specifically as lower-calorie, lower-sugar or lower-alcohol, often around 7–9% ABV, with Serving Facts on the label. Brands in this space (assortment varies by store) include:

- **Kim Crawford Illuminate** (lower-alcohol, lower-calorie Sauvignon Blanc and rosé)
- **Kendall-Jackson** lower-calorie Chardonnay line
- **Cupcake LightHearted**
- **FitVine** (low residual sugar, label-disclosed nutrition)
- **Skinnygirl**
- **Bev**, and **Avaline** (brands positioned on transparency and low sugar)
- Many producers' "light" or "lower alcohol" sub-ranges

**Rules for the agent**
- Brands listed here are **category examples**, not a claim that we carry them. Use `search_products`.
- Quote calories, carbs and sugar **only** from `get_product_details.nutrition`. Brand marketing numbers can change between vintages.
- Brand names that include words like "skinny" are names, not our claims. Don't repeat the idea as a benefit ("this will help you lose weight").

## 4. How to search

```
search_products(filters={
  calories_max: 90,          # per 5 oz, only matches products with nutrition data
  abv_max: 11,               # alternative proxy when nutrition data is missing
  sweetness: ["dry"],
  color: <customer choice>,
}, sort: "calories_asc")
```

- **Two-pass approach:** (1) products with verified nutrition data (`calories_max`), then (2) naturally lighter styles using `abv_max` + `sweetness=dry`, presented as "lighter in alcohol, so typically lower in calories".
- **Diversity:** show at least one non-branded naturally-light option alongside branded lines.

## 5. Recommendation workflow

1. Clarify the goal in neutral words: "Are you looking for fewer calories, less sugar, less alcohol, or all three?"
2. Ask style (white/rosé/red/sparkling) and budget.
3. Search (§4). Present 2–4 options with **label-based** numbers where available.
4. If the customer seems to be managing a medical condition, add one sentence: "If this is for a health reason, your doctor is the best guide; I can share what's on the labels."
5. Offer non-alcoholic options if the goal is the fewest calories or no alcohol (NJ Store only, A-06).

## 6. Edge cases

- **"Which wine has zero calories?"** None. Even non-alcoholic wine has calories from sugar (often ~15–50 kcal per 5 oz, label-dependent).
- **"Is red or white lower in calories?"** It depends on alcohol and sugar, not color. Dry wines with lower ABV are lowest.
- **Serving size**: calories are per 5 oz (148 ml) on US Serving Facts. Many home pours are bigger.
- **Sweet = high calorie?** Not always. Low-alcohol sweet wines (Moscato d'Asti) can be similar to dry table wine.
- **Product lacks nutrition data**: say so; offer the ABV-based estimate as a general range, labeled as an estimate.

## 7. Sample dialogues

> **Customer:** What's your lowest calorie white wine?
> **Agent:** Here are the lowest-calorie whites we have with calories listed on the label: [Wine A], 80 calories per 5 oz (label), and [Wine B], 85 per 5 oz (label). If you'd like a classic wine instead of a "light" brand, a Vinho Verde is naturally lighter because it's lower in alcohol, usually around 9–10%.

> **Customer:** I'm on a diet, which wine won't make me gain weight?
> **Agent:** I can't give diet advice, but I can help you find wines that are lower in calories per glass. Lower-alcohol, dry wines tend to be lightest. Here are a few with calorie counts on the label: … If you're following a specific plan, your doctor or dietitian is the best guide.
