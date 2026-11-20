---
id: KB-TST-004
title: Aromatic & Off-Dry White Wines
category: taste
subcategory: aromatic-white
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
related: [KB-TST-001, KB-TST-003, KB-TST-010, KB-REG-008]
---

# Aromatic & Off-Dry White Wines

## 1. What they are

Aromatic whites have **intensely perfumed** aromas: flowers, stone fruit, tropical fruit, honey, lychee. Many are **off-dry** (a touch of sweetness) and balanced by acidity. They are the go-to for customers who say "a little sweet but not dessert", "fruity white", "something for spicy food", or who like Moscato and want to explore.

**Catalog:** `style_tag=aromatic-white`, `aromatic=true`, sweetness spans `dry` → `medium_sweet`. **Always check `sweetness` per product.** In this category the grape does not tell you the sweetness.

## 2. Key wines

| Wine | Typical sweetness | Taste in plain words | Notes |
|---|---|---|---|
| **Riesling (Germany: Kabinett, Spätlese)** | Off-dry to medium-sweet | Lime, green apple, peach, honey; racy acidity keeps it fresh | German ripeness levels (Kabinett → Spätlese → Auslese) indicate grape ripeness at harvest, **not** guaranteed sweetness. "Trocken" = dry; "feinherb/halbtrocken" = off-dry. |
| **Riesling (US, Washington, Finger Lakes)** | Dry → sweet; many show an IRF sweetness scale on the back label | Apple, peach, citrus | The International Riesling Foundation scale (Dry / Medium Dry / Medium Sweet / Sweet) helps. |
| **Moscato / Moscato d'Asti** | Sweet, low alcohol (~5–7% for Moscato d'Asti) | Peach, orange blossom, grape; gently fizzy (d'Asti) | Huge US crowd-pleaser; Moscato d'Asti is lightly sparkling (frizzante). |
| **Gewürztraminer** | Dry to off-dry | Lychee, rose, ginger, spice; full and perfumed | Best with spicy Asian food, Alsace and Munster cheese. |
| **Torrontés** | Dry | Very floral (jasmine), peach; dry despite the perfume | Argentina. Surprises people expecting sweetness. |
| **Viognier** | Dry | Apricot, honeysuckle, rich texture | Also fits "rich whites". Condrieu (Rhône) is the classic. |
| **Chenin Blanc (Vouvray)** | Sec (dry) → Demi-Sec (off-dry) → Moelleux (sweet) | Quince, apple, honey, wool/lanolin | Label word decides sweetness. South African Chenin is usually dry. |
| **Pinot Gris (Alsace)** | Dry to off-dry | Pear, honey, smoky, fuller | Alsace labels may show a sweetness scale. |
| **Müller-Thurgau, Kerner, Grüner (aromatic styles)** | Mostly dry | Floral, light | Niche. |
| **Malvasia, Muscat Sec** | Dry versions exist | Grape-y, floral, dry | Clarify when a customer wants "Moscato but not sweet": dry Muscat from Alsace or Spain. |

## 3. Indicative price bands (A-44)

- **Everyday:** US Riesling, Moscato, Torrontés, many Washington/California aromatic whites.
- **Step-up:** German Kabinett/Spätlese from quality estates, Alsace Gewürztraminer and Pinot Gris, Vouvray, Finger Lakes Riesling.
- **Premium+:** German VDP Grosses Gewächs (dry), Alsace Grand Cru, Condrieu, mature Mosel Riesling.

## 4. How to recommend

- Ask sweetness first: "Just a hint of sweetness, or properly sweet like Moscato?"
- **Off-dry:** `sweetness=off_dry`, grapes Riesling, Chenin Blanc, Gewürztraminer, Pinot Gris.
- **Sweet and light:** `sweetness in (medium_sweet, sweet)`, Moscato / Moscato d'Asti, Spätlese/Auslese Riesling.
- **Aromatic but dry:** Torrontés, dry Muscat, Alsace Riesling, Trocken Riesling, Viognier.
- **Spicy food:** off-dry Riesling or Gewürztraminer (sweetness and lower alcohol tame chili heat).
- **Low alcohol:** Moscato d'Asti, Mosel Kabinett Riesling (often 8–10% ABV). Use `abv_max`.

## 5. Food pairing

Thai, Vietnamese, Indian, Sichuan, Korean dishes; pork with fruit; ham; spicy wings; fruit tarts (sweeter styles); soft cheeses; Asian takeout. Serve chilled: 45–50°F.

## 6. Edge cases and misconceptions

- **"I want sweet white"**: confirm the level. Moscato (sweet, light, fizzy) vs Riesling Spätlese (sweet-tart) vs dessert wine (see [sweet-dessert-and-fortified-wines.md](sweet-dessert-and-fortified-wines.md)).
- **Petrol aroma in aged Riesling** is a recognized varietal trait (TDN), not a fault, though some people dislike it. Mention it for older vintages only.
- **German label reading**: don't promise sweetness from Prädikat names alone. Use `get_product_details.sweetness` and residual sugar if present.
- **"Pink Moscato"** is a blush style, often grouped with rosé (`rose-off-dry`).

## 7. Sample dialogue

> **Customer:** I like Moscato but want something a bit less sweet.
> **Agent:** Great direction! Try an off-dry Riesling, still fruity and a little sweet, but with fresh acidity so it isn't sugary. A Vouvray (Chenin Blanc) is another option, with honey-apple notes. Here are two available near you: …
