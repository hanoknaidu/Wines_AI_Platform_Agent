---
id: KB-NAW-001
title: Non-Alcoholic Wine Guide (Definitions, Production, Taste, Brands)
category: non-alcoholic
subcategory: guide
doc_type: guide
intents: [recommend.non_alcoholic, education.wine_question, product.details]
tools: [search_products, get_product_details, check_inventory]
jurisdictions: [NJ, NY, US]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 120
owner: wine-team
status: active
depends_on_assumptions: [A-06, A-44]
related: [KB-NAW-002, KB-NAW-003, KB-LCW-002]
---

# Non-Alcoholic Wine Guide

## 1. Definitions (US)

| Term | Meaning | Regulator |
|---|---|---|
| **Dealcoholized wine / alcohol-removed wine** | Made as regular wine, then alcohol removed to **less than 0.5% ABV** | FDA (food labeling). Label must say "contains less than 0.5% alcohol by volume" |
| **Non-alcoholic** | May be used alongside "dealcoholized", for < 0.5% ABV | FDA |
| **Alcohol-free / 0.0%** | **No detectable alcohol** | FDA. Stricter than "non-alcoholic" |
| **Low-alcohol / "lighter" wine** | Reduced alcohol but above 0.5% (often 5–9%) | TTB if ≥ 7%; FDA if < 7%. **Not non-alcoholic** |
| **Wine alternatives** | Non-alcoholic drinks built from juices, teas, botanicals to mimic wine (not made from wine) | FDA |

**Agent clarity rule:** when a customer needs **no alcohol at all** (pregnancy, medication, religious reasons, recovery), point out the difference between "< 0.5%" and "0.0% / alcohol-free". Don't advise whether either is appropriate for them.

Because NA wine is labeled as a food, it typically carries a **Nutrition Facts** panel, so calorie and sugar data are more often available in `get_product_details.nutrition`.

## 2. How alcohol is removed

| Method | How | Effect |
|---|---|---|
| **Vacuum distillation** | Low-temperature distillation under vacuum | Gentle on aromas |
| **Spinning cone column** | Thin film of wine in a spinning column separates aromas, then alcohol; aromas are returned | Widely used for larger brands |
| **Reverse osmosis** | Filtration separates water/alcohol from flavor compounds | Preserves flavor well |
| **Fermentation-limited / blending** (alternatives) | Little fermentation, or no wine base | Fruit-forward, juice-like |

Removing alcohol also removes **body and warmth**, so producers may add grape juice/must, sugar, CO₂ (carbonation) or botanical flavor to rebuild texture. As a result, many NA wines taste **sweeter or lighter** than their alcoholic counterparts.

## 3. Taste expectations (be honest)

| Style | How well it works without alcohol | Tips |
|---|---|---|
| **Sparkling (white & rosé)** | **Best**: bubbles provide texture | Easiest recommendation; great for toasts |
| **Aromatic whites (Riesling, Sauvignon Blanc, Muscat)** | Good: aromatics carry flavor | Serve very cold |
| **Rosé** | Good | Serve cold |
| **Reds** | Hardest: alcohol carries body and tannin; can taste thin or sweet | Set expectations; slightly chilled often tastes better |

**Agent wording:** "Non-alcoholic wines have come a long way, especially sparkling ones. They're lighter-bodied than regular wine, and many are a little sweeter."

## 4. Calories, sugar and shelf life

- **Calories:** typically **much lower** than regular wine (no alcohol), often well under half, but **not zero**; sugar can be higher. Quote from Nutrition Facts only.
- **Unopened shelf life:** alcohol is a preservative, so NA wine is **less stable**. Many carry best-by dates; the catalog stores `best_by`. Recommend drinking within the best-by window.
- **Opened:** refrigerate with a stopper; best within **2–5 days** (sparkling with a sparkling stopper: 1–3 days).

## 5. Brands in the category (examples; check availability)

| Brand | Origin | Known for |
|---|---|---|
| **Fre** (Sutter Home family) | California | Wide range (Brut, rosé, Chardonnay, red blend, Cabernet); dealcoholized by spinning cone |
| **Ariel** (J. Lohr) | California | Long-running dealcoholized Chardonnay and Cabernet |
| **St. Regis** | France | Sparkling and still dealcoholized wines |
| **Leitz Eins Zwei Zero** | Germany (Rheingau) | Dealcoholized Riesling (still and sparkling), sparkling rosé, red |
| **Giesen 0%** | New Zealand | Dealcoholized Marlborough Sauvignon Blanc, rosé, Pinot Gris |
| **Noughty** (Thomson & Scott) | UK / Spain / South Africa sourcing | Organic, vegan, low-sugar sparkling and rosé |
| **Oddbird** | Sweden / France | Premium dealcoholized sparkling and still |
| **Freixenet 0.0%** | Spain | Alcohol-removed sparkling (and rosé) |
| **French Bloom** | France | Premium organic alcohol-free sparkling |
| **Torres Natureo** | Spain | Dealcoholized Muscat, rosé, red |
| **Surely** | California | Dealcoholized sparkling, rosé, reds |
| **Pierre Zéro** | France | Dealcoholized range |

Wine alternatives (not dealcoholized): **Proxies** (Acid League), **Jukes Cordials**, **TÖST** (sparkling tea-based). Describe these accurately as "wine alternatives".

## 6. How to recommend

```
search_products(filters={is_non_alcoholic:true, sparkling?, color?, abv_label:["<0.5%","0.0%"]}, fulfillment_location="NJ")
```

1. Confirm the delivery location is NJ (or NJ Store pickup) (A-06). See [sale-policy-and-age-rules.md](sale-policy-and-age-rules.md).
2. Ask the occasion (toast, dinner, everyday) and preferred style.
3. Lead with sparkling or aromatic whites unless the customer wants red.
4. For "absolutely no alcohol" needs, filter `abv_label="0.0%"` and say so.
5. Mention calorie data from the label if the customer cares.

## 7. Sample dialogue

> **Customer:** Something non-alcoholic for a baby shower toast, about 20 people.
> **Agent:** Congratulations! Non-alcoholic sparkling is perfect for a toast. For 20 guests with one toast each, 3 bottles is plenty; get 4 if people may want a second glass. Two great options from our NJ store: a dealcoholized Brut and a 0.0% alcohol-free sparkling rosé. Note that "dealcoholized" means less than 0.5% alcohol, while the 0.0% option has no detectable alcohol, if that matters for any guests.
