---
id: KB-TST-007
title: Light & Fruity Red Wines
category: taste
subcategory: light-red
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
related: [KB-TST-001, KB-TST-008, KB-REG-002, KB-REG-006]
---

# Light & Fruity Red Wines

## 1. What they are

Light reds are **dry, light-bodied, with soft tannins and fresh acidity**: bright cherry, raspberry, cranberry, sometimes earthy or floral. Customers say "light red", "not heavy", "smooth", "a red I can drink in summer", "red for fish", "red that's not bitter".

**Catalog:** `style_tag=light-red` · `body=light`, `tannin=smooth`, `acidity=fresh`, `sweetness=dry`.

## 2. Key wines

| Wine | Taste in plain words | Notes |
|---|---|---|
| **Pinot Noir (Burgundy)** | Red cherry, raspberry, mushroom, forest floor, silky | Bourgogne Rouge (entry) → village (e.g., Gevrey-Chambertin) → Premier/Grand Cru (luxury). |
| **Pinot Noir (Oregon, Willamette Valley)** | Cherry, cranberry, earth; balanced | Fine middle ground between Burgundy and California. |
| **Pinot Noir (California: Sonoma Coast, Russian River, Santa Rita Hills, Central Coast)** | Riper cherry, cola, spice; can be medium-bodied | Some popular brands are fuller and sweeter-fruited. Check `body`. |
| **Pinot Noir (New Zealand: Central Otago, Marlborough)** | Bright cherry, herbs | Good value premium. |
| **Beaujolais (Gamay)** | Juicy strawberry, raspberry, banana-candy (Nouveau), floral | Beaujolais Nouveau (released 3rd Thursday of November), Beaujolais-Villages, and the 10 Crus (e.g., Morgon, Fleurie, Moulin-à-Vent) with more depth. |
| **Frappato / Cerasuolo di Vittoria** | Strawberry, pomegranate, floral | Sicily. |
| **Schiava, Pinot Nero (Alto Adige)** | Light, almond, red fruit | Niche Italian. |
| **Lambrusco (dry, "secco")** | Fizzy, dark berry, slightly bitter | Sparkling red, often served chilled. Sweet (amabile/dolce) versions too: check `sweetness`. |
| **Zweigelt, Blaufränkisch (lighter styles)** | Cherry, pepper | Austria. |
| **Light Grenache / Garnacha, Cinsault, Mencía** | Raspberry, herbs | Mencía (Bierzo, Spain) can be medium. |
| **Finger Lakes Cabernet Franc / Pinot Noir** | Red fruit, herbs, high acid | Local NY option. |

## 3. Indicative price bands

- **Everyday:** Beaujolais-Villages, California/Chilean Pinot Noir, Lambrusco, Frappato.
- **Step-up:** Oregon Pinot Noir, Cru Beaujolais, Bourgogne Rouge, NZ Pinot Noir.
- **Premium:** Willamette single-vineyard, Burgundy village wines, Sonoma Coast top producers.
- **Luxury/Collectible:** Burgundy Premier/Grand Cru.

Pinot Noir is expensive to grow well. A "good Pinot under $15" is harder to find than a good Cabernet at the same price. Set expectations kindly.

## 4. How to recommend

- **"Light red"**: `style_tag=light-red`.
- **"Smooth red, not bitter"**: light reds, or [medium-smooth-reds.md](medium-smooth-reds.md) with `tannin=smooth`.
- **"Red with fish / salmon / tuna"**: Pinot Noir, Gamay. Low tannin avoids a metallic clash with oily fish.
- **"Chillable red for summer"**: Beaujolais, Frappato, Lambrusco, light Grenache. Serve 55–60°F (15 minutes in the fridge).
- **Thanksgiving**: Pinot Noir and Cru Beaujolais are classic turkey reds.

## 5. Food pairing

Salmon, tuna, roast chicken, turkey, duck, mushroom dishes, pork, charcuterie, pizza, Gruyère and Brie, vegetarian grain bowls. Serve slightly cool: 55–60°F (13–15°C).

## 6. Edge cases

- **Beaujolais Nouveau** is seasonal (November release, best drunk by spring). After winter, stock clears; suggest Beaujolais-Villages instead.
- **Pinot Noir color**: naturally pale; customers sometimes think it's "watered down". Explain it's normal.
- **Some mass-market "Pinot Noir" blends** are fuller and fruit-sweet. Trust `get_product_details.taste`, not the grape name.

## 7. Sample dialogue

> **Customer:** I usually drink white but want to try a red that's not heavy.
> **Agent:** A light red is the perfect bridge. Try a Beaujolais-Villages (juicy strawberry, almost no grip) or an Oregon Pinot Noir (cherry and a little earthiness). Both are lovely slightly chilled. Here's what's available near you: …
