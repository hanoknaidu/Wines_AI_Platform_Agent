---
id: KB-TST-006
title: Rosé Wines (Dry, Fuller and Off-Dry/Blush)
category: taste
subcategory: rose
doc_type: guide
intents: [recommend.by_taste, recommend.by_occasion, education.wine_question]
tools: [search_products, get_product_details]
jurisdictions: [NJ, NY]
audience: agent
priority: medium
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: wine-team
status: active
depends_on_assumptions: [A-22, A-44, A-50]
related: [KB-TST-001, KB-SPK-001, KB-REG-002, KB-STK-002]
---

# Rosé Wines

## 1. What they are

Rosé is made from red grapes with **brief skin contact** (hours, not weeks), giving pink color and light red-fruit flavors. Most quality rosé is **dry**. Sweet "blush" styles (e.g., White Zinfandel) are a separate category. Color depth doesn't reliably indicate sweetness or quality.

**Catalog:** `style_tag=rose-dry` or `rose-off-dry`. Sparkling rosé is in folder 04.

## 2. Styles

| Style | Examples | Taste | Notes |
|---|---|---|---|
| **Pale, dry Provence-style** | Côtes de Provence, Bandol (fuller), Coteaux d'Aix | Strawberry, citrus, white peach, herbs; crisp | Very popular. Many famous brands (see [european-brands.md](../03_wine-by-brand/european-brands.md)). |
| **Other French dry** | Tavel (deeper, fuller, "the rosé for red drinkers"), Sancerre rosé (Pinot Noir), Rhône/Languedoc | Cherry, raspberry, more body | Tavel is only rosé by appellation rules. |
| **Spanish Rosado / Italian Rosato** | Navarra (Garnacha), Rioja Rosado, Cerasuolo d'Abruzzo, Chiaretto | Watermelon, cherry, sometimes deeper | Good value. |
| **US dry rosé** | California, Oregon (Pinot Noir), Long Island, Finger Lakes | Bright red fruit | Long Island makes notable dry rosé (local option for NY customers). |
| **Off-dry / blush** | White Zinfandel, Pink Moscato, some sweet rosé blends | Sweet strawberry, candy | `rose-off-dry`. Crowd-pleaser for sweet-wine fans. |

## 3. Vintage freshness

Most rosé is best **young**: within 1–2 years of vintage. Customers often ask for "this year's rosé".

- The newest vintage of Northern Hemisphere rosé typically arrives in spring (March–May). Southern Hemisphere earlier.
- For rosé under $25, adjacent-vintage substitution is automatic (A-22); the agent should mention which vintage is in stock if the customer cares.
- Premium/age-worthy rosé (Bandol, top Provence cuvées, Tavel) can age 3–5+ years.

## 4. Indicative price bands

- **Everyday:** Many Provence, Spanish, Italian and US rosés; boxed rosé.
- **Step-up:** Top-name Provence brands, Sancerre rosé, Tavel.
- **Premium:** Bandol, prestige Provence cuvées.
- **Luxury:** Ultra-premium Provence cuvées, large formats (magnums are popular for summer parties).

## 5. How to recommend

- **"Dry rosé like Whispering Angel"**: `style_tag=rose-dry`, region Provence; `get_similar_products` from the reference SKU.
- **"Sweet pink wine"**: `style_tag=rose-off-dry`; also consider Brachetto d'Acqui (sweet, red, sparkling) or Pink Moscato.
- **"Rosé for red wine drinkers"**: Tavel, Bandol, Cerasuolo, deeper Spanish rosado.
- **Party / summer**: magnums (1.5 L count as 2 bottles toward the case discount, A-50).

## 6. Food pairing

Salads, Mediterranean mezze, grilled fish and shrimp, salmon, charcuterie, goat cheese, pizza, sushi, picnic fare, light Asian dishes. Serve chilled: 45–50°F.

## 7. Edge cases

- **"Is rosé a mix of red and white wine?"** Generally no. Most rosé is made by brief skin contact. Blending red and white is permitted for rosé Champagne and some other wines, but not for most EU still rosé.
- **"Pale = better?"** No. Paleness is a style choice, not a quality signal.
- **Off-season stock**: rosé assortment is smaller in winter. Check `check_inventory`; offer back-in-stock alerts for seasonal favorites.

## 8. Sample dialogue

> **Customer:** Do you have a rosé that's not sweet for a beach day?
> **Agent:** Yes! Dry, pale rosé is perfect for that. Here are two crisp Provence-style rosés and a Spanish rosado that's great value: … All three are dry: think strawberry and citrus, no sugar. Want them in a screw-cap or a magnum for the group?
