---
id: KB-SPK-002
title: Champagne: Appellation, Styles, Labels and Buying Guide
category: sparkling
subcategory: champagne
doc_type: guide
intents: [recommend.sparkling, recommend.by_occasion, education.wine_question, stock.vintage_question]
tools: [search_products, get_product_details, check_inventory, get_price]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 365
owner: wine-team
status: active
depends_on_assumptions: [A-06, A-23, A-33, A-34, A-44, A-50]
related: [KB-SPK-001, KB-SPK-004, KB-SPK-005, KB-BRD-002, KB-STK-002]
---

# Champagne

## 1. What Champagne is

Champagne is sparkling wine from the **Champagne appellation (AOC) in northeastern France**, made by the traditional method. Only wine from this region may be labeled "Champagne" in the EU and most of the world. The main sub-areas are the **Montagne de Reims** (Pinot Noir), **Vallée de la Marne** (Pinot Meunier), **Côte des Blancs** (Chardonnay), **Côte de Sézanne** and the **Côte des Bar / Aube** (Pinot Noir).

**Grapes:** Chardonnay (finesse, citrus), Pinot Noir (body, red fruit), Pinot Meunier (fruitiness, roundness). Arbane, Petit Meslier, Pinot Blanc and Pinot Gris are permitted but rare.

**Minimum aging on lees:** 15 months for non-vintage (NV), 3 years for vintage. Many houses age much longer.

## 2. Champagne styles

| Style | What it means | Taste |
|---|---|---|
| **Non-Vintage (NV) Brut** | Blend of several years for a consistent house style; ~most Champagne sold | Varies by house: fresh to rich |
| **Vintage (Millésime)** | From a single declared year | More intensity and aging character; **vintage-specific** (A-23) |
| **Blanc de Blancs** | 100% white grapes (usually Chardonnay) | Lean, citrus, elegant, creamy with age |
| **Blanc de Noirs** | White wine from black grapes (Pinot Noir, Meunier) | Fuller, red-fruit hints |
| **Rosé** | Blending red wine (assemblage, unique to Champagne) or skin maceration (saignée) | Red berries; often pricier |
| **Prestige cuvée (Tête de cuvée)** | A house's top wine | Most complex; Luxury–Collectible |
| **Multi-vintage / numbered editions** | Some houses number blends instead of NV | |
| **Zero dosage / Brut Nature, Extra Brut** | Little or no added sugar | Very dry, mineral |
| **Demi-Sec, Doux** | Sweeter | Dessert pairing |

Sweetness levels and grams per liter are in [sparkling-sweetness-scale.md](sparkling-sweetness-scale.md).

## 3. Houses vs growers: label codes

The small code on the label (e.g., "NM-123-456") shows the producer type:

| Code | Meaning | Customer explanation |
|---|---|---|
| **NM** (Négociant-Manipulant) | House that buys grapes (and may own vineyards) | Most famous brands |
| **RM** (Récoltant-Manipulant) | Grower making wine from its own grapes | "Grower Champagne": small family producers; terroir-focused |
| **CM** (Coopérative de Manipulation) | Cooperative | Often good value |
| **RC** (Récoltant-Coopérateur) | Grower selling wine made by a cooperative under its own label | |
| **SR** (Société de Récoltants) | Group of growers | |
| **ND** (Négociant-Distributeur) | Buys finished wine and labels it | |
| **MA** (Marque d'Acheteur) | Buyer's own brand (e.g., retailer private label) | Store-label Champagne |

## 4. Village classification

Champagne villages were historically rated on the *Échelle des Crus*: **17 Grand Cru villages** (e.g., Aÿ, Bouzy, Cramant, Avize, Le Mesnil-sur-Oger, Ambonnay, Verzenay) and **42 Premier Cru villages**. "Grand Cru" on a label means all grapes came from those villages.

## 5. Bottle sizes

| Name | Size | Standard bottles | Case-discount count (A-50) |
|---|---|---|---|
| Split / Piccolo | 187.5 ml | ¼ | 0.25 |
| Half (Demi) | 375 ml | ½ | 0.5 |
| Standard | 750 ml | 1 | 1 |
| Magnum | 1.5 L | 2 | 2 |
| Jeroboam | 3 L | 4 | 4 (formats ≥ 3 L are excluded from NJ change-of-mind returns, A-34) |
| Rehoboam | 4.5 L | 6 | 6 |
| Methuselah | 6 L | 8 | 8 |
| Salmanazar | 9 L | 12 | 12 |
| Balthazar | 12 L | 16 | 16 |
| Nebuchadnezzar | 15 L | 20 | 20 |

Magnums are often considered to age best (a lower ratio of oxygen to wine). Formats above 1.5 L are usually special-order (see [special-orders-and-product-requests.md](../09_stock-and-availability/special-orders-and-product-requests.md)). Not every bottling exists in every size.

## 6. Indicative price bands (A-44)

- **Step-up–Premium ($30–60):** NV Brut from cooperatives, smaller houses, many growers, some major houses on promotion.
- **Premium ($40–80):** major-house NV Brut, Blanc de Blancs, many rosés.
- **Luxury ($80–150):** vintage Champagne, top grower cuvées, rosé from top houses, magnums of NV.
- **Collectible ($150+):** prestige cuvées (e.g., Dom Pérignon, Cristal, Krug Grande Cuvée, La Grande Dame, Comtes de Champagne, Belle Époque), older vintages.

Champagne is rarely under $30 at retail. If the customer's budget is lower, recommend Crémant, Cava or US traditional method, and explain why.

## 7. How to recommend

1. Ask (if unknown): budget; occasion (toast, gift, dinner); preferred style (fresh and light, or rich and toasty); sweetness (almost always Brut).
2. Filter: `search_products(filters={sparkling:true, appellation:"Champagne", sweetness_label:"Brut", price_max})`.
3. Style mapping:
   - **Fresh and elegant:** Blanc de Blancs, Chardonnay-led houses.
   - **Rich and toasty:** Pinot Noir-led houses, longer aging, vintage.
   - **Terroir / enthusiast:** grower (RM) Champagne, Extra Brut.
   - **Celebration / recognizable gift:** well-known Grandes Marques NV or prestige cuvées, gift boxes.
4. Mention gift boxes or magnums if relevant, and check `check_inventory` for the delivery date.

## 8. Edge cases

- **"Is this vintage?"** Check `vintage` and `vintage_specific`. NV doesn't have a vintage; some show a disgorgement date or base-year on the back label.
- **Older Champagne**: develops nutty, honeyed flavors and gentler bubbles. Older bottles fall under A-33 (sold as-is for natural aging).
- **"California Champagne"**: see the grandfather note in [sparkling-styles-and-production-methods.md](sparkling-styles-and-production-methods.md).
- **Price comparisons with duty-free/European prices**: US prices include import, distribution and state-specific costs. Don't speculate on pricing reasons beyond that.
- **Gift for a non-drinker**: suggest non-alcoholic sparkling (folder 07), NJ Store only (A-06).

## 9. Sample dialogue

> **Customer:** I need a nice Champagne for my parents' 40th anniversary, around $100.
> **Agent:** Congratulations to them! At about $100 you can choose a vintage Champagne from a major house, or a top grower Champagne. Do they prefer something fresh and elegant, or rich and toasty? Here are two in stock that ship in a gift box: …
