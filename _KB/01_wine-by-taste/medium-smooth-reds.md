---
id: KB-TST-008
title: Smooth & Medium-Bodied Red Wines
category: taste
subcategory: medium-red
doc_type: guide
intents: [recommend.by_taste, recommend.by_food, education.wine_question]
tools: [search_products, get_product_details, get_similar_products]
jurisdictions: [NJ, NY]
audience: agent
priority: medium
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: wine-team
status: active
depends_on_assumptions: [A-44]
related: [KB-TST-001, KB-TST-007, KB-TST-009, KB-REG-003, KB-REG-004]
---

# Smooth & Medium-Bodied Red Wines

## 1. What they are

Medium reds sit in the middle: **dry, medium-bodied, with moderate (often smooth) tannins and fresh acidity**. This is the most versatile food category and where most "everyday red" requests land. Customers say "smooth red", "easy-drinking", "something for pasta", "a red everyone will like".

**Catalog:** `style_tag=medium-red` · `body=medium`, `tannin in (smooth, moderate)`, `acidity=fresh`.

## 2. Key wines

| Wine | Taste in plain words | Notes |
|---|---|---|
| **Merlot** | Plum, black cherry, chocolate, soft | Washington, California, Chile, Bordeaux Right Bank (Saint-Émilion, Pomerol). |
| **Chianti / Chianti Classico (Sangiovese)** | Sour cherry, tomato leaf, herbs, high acid | Classico Riserva and Gran Selezione are higher tiers. A pasta classic. |
| **Montepulciano d'Abruzzo** | Plum, soft tannins, rustic | Value superstar. Not the same as Vino Nobile di Montepulciano (Sangiovese, Tuscany). |
| **Barbera (d'Asti, d'Alba)** | Juicy cherry, very fresh acid, low tannin | Piedmont. Smooth and food-friendly. |
| **Dolcetto** | Blackberry, almond, soft | Piedmont everyday red. |
| **Rioja Crianza / Reserva (Tempranillo)** | Cherry, vanilla, leather, dill (American oak) | Aging tiers: Joven → Crianza → Reserva → Gran Reserva. |
| **Côtes du Rhône (Grenache-Syrah blends)** | Raspberry, pepper, herbs (garrigue) | Excellent value; Villages and named villages (Rasteau, Cairanne) step up. |
| **Garnacha (Spain)** | Ripe strawberry, spice, soft | Calatayud, Campo de Borja, Priorat (fuller). |
| **Carménère** | Red pepper, plum, spice | Chile. |
| **Valpolicella / Ripasso** | Cherry, almond; Ripasso is richer | Veneto. Amarone (full) is in [bold-full-bodied-reds.md](bold-full-bodied-reds.md). |
| **Cabernet Franc (Loire: Chinon, Bourgueil)** | Red currant, pencil, bell pepper | Also Finger Lakes. |
| **Red blends (California "smooth red")** | Ripe dark fruit, vanilla, sometimes noticeable residual sugar | Many popular brands. Check `sweetness`; several are fruit-sweet. |
| **Bordeaux (Médoc, Bordeaux Supérieur)** | Cassis, cedar, earthy | Entry Bordeaux is medium; classed growths are bold. |

## 3. Indicative price bands

- **Everyday:** Montepulciano d'Abruzzo, Côtes du Rhône, Chilean Merlot/Carménère, Spanish Garnacha, California red blends.
- **Step-up:** Chianti Classico, Barbera d'Asti/Alba, Rioja Reserva, Washington Merlot, Rhône Villages.
- **Premium:** Chianti Classico Gran Selezione, Rioja Gran Reserva, Saint-Émilion Grand Cru, top Napa Merlot.
- **Luxury:** Pomerol (and top Right Bank), single-vineyard Rioja icons.

## 4. How to recommend

- **"Smooth red"**: Merlot, Garnacha, Barbera, Côtes du Rhône, red blends (`tannin=smooth`).
- **"Red for pasta / pizza / red sauce"**: Chianti, Montepulciano, Barbera. Acidity matches tomato.
- **"Red that everyone will like" / party**: Côtes du Rhône, Merlot, red blend, Montepulciano; mention the mixed-case discount.
- **"Like Apothic / 19 Crimes / Josh"**: `get_similar_products` from the reference; note that some are fruit-sweet, so check `sweetness`.
- **Bordeaux on a budget**: Bordeaux Supérieur, Côtes de Bordeaux, Saint-Émilion satellites.

## 5. Food pairing

Pasta with red sauce, pizza, lasagna, burgers, meatloaf, roast pork, sausages, mushroom risotto, Manchego, aged cheddar, tapas, BBQ chicken, weeknight dinners. Serve at 60–65°F (16–18°C). "Room temperature" in a warm apartment is too warm; 15 minutes in the fridge helps.

## 6. Edge cases

- **"Sweet red"**: confirm whether they mean fruit-forward (dry) or actually sweet. Truly sweet reds are `style_tag=sweet-red` (e.g., Lambrusco amabile, Brachetto d'Acqui, some branded sweet red blends).
- **Chianti in a straw basket (fiasco)**: nostalgic; the quality range is wide. Recommend by producer data, not the bottle.
- **Rioja labels**: "Crianza / Reserva / Gran Reserva" are legal aging tiers. Generic "Reserve" on US labels has no legal meaning.

## 7. Sample dialogue

> **Customer:** Need a crowd-pleasing red for a dinner party of 10, around $15 a bottle.
> **Agent:** For a group, smooth and food-friendly is the way to go. Three great options near you: a Côtes du Rhône (raspberry and pepper), a Montepulciano d'Abruzzo (soft plum), and a Washington Merlot (plush and smooth). For 10 people, 4–5 bottles is usually plenty with dinner. Buy 6 and you'd also get 10% off with the mixed-case discount.
