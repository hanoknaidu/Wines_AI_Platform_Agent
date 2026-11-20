---
id: KB-PRC-002
title: Price Bands and Budget Guidance
category: pricing
subcategory: price-bands
doc_type: guide
intents: [recommend.budget, recommend.by_taste, recommend.by_occasion, gift.order]
tools: [search_products, get_price]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: merchandising
status: active
depends_on_assumptions: [A-44, A-50]
related: [KB-TST-002, KB-PRC-001, KB-DSC-002]
---

# Price Bands and Budget Guidance

## 1. Price-band taxonomy (A-44)

Bands are per **750 ml** bottle (pro-rate other sizes). The catalog stores `price_band` for filtering; actual prices come from `get_price`.

| Band | Range | Customer-facing name | What it typically buys |
|---|---|---|---|
| **Everyday** | Under $15 | "Great value" | Large-brand varietals, Portuguese/Spanish/Chilean/Argentine values, Côtes du Rhône, Prosecco DOC, Pinot Grigio, boxed wine (per-bottle equivalent) |
| **Step-up** | $15–$29.99 | "Weekend wines" | Quality regional wines: Chianti Classico, Oregon Pinot Gris, Sonoma Chardonnay, Rioja Reserva, Cru Beaujolais, Marlborough's top producers, Cava Reserva, Crémant |
| **Premium** | $30–$59.99 | "Special dinners and gifts" | Napa Cabernet entry, Sancerre, Champagne NV, Barolo entry, Brunello, Châteauneuf-du-Pape, white Burgundy village |
| **Luxury** | $60–$149.99 | "Celebrations" | Napa sub-AVA Cabernet, Burgundy Premier Cru, vintage Champagne, Super Tuscans, Amarone top producers |
| **Collectible** | $150+ | "Collector's wines" | Prestige cuvée Champagne, Bordeaux classed growths, cult Napa, Grand Cru Burgundy, older vintages, large formats |

## 2. Budget conversations

**Principles**
- Never judge a budget. Every band has excellent wines.
- If no budget is given and it matters (gifts, parties), offer the bands as choices: "Under $15, $15–30, $30–60, or something more special?"
- Respect the stated budget; at most one "stretch" pick up to 15% above, labeled as such.
- For a **total budget** ("$200 for a party"), work backward: guests → bottles → per-bottle target, minus the mixed-case discount.

**Translating vague budgets**

| Customer says | Interpret as |
|---|---|
| "Cheap", "budget", "not expensive" | Everyday (< $15); mention value regions |
| "Mid-range", "decent" | Step-up ($15–30) |
| "Nice", "for a dinner party" | Step-up–Premium ($20–50) |
| "Special", "gift for my boss", "anniversary" | Premium–Luxury ($40–100); confirm |
| "Impress", "the best", "money's no object" | Luxury–Collectible; ask for a ceiling anyway |

## 3. Best-value strategies (where to find quality per dollar)

| Instead of… | Try (similar style, usually lower price) |
|---|---|
| Napa Cabernet | Paso Robles, Washington, Alexander Valley, Chilean Maipo, Bordeaux Supérieur |
| Champagne | Crémant, Cava Reserva, US traditional-method sparkling |
| Burgundy Pinot Noir | Oregon, Bourgogne Rouge from good producers, Côte Chalonnaise, Chilean coastal Pinot |
| Sancerre | Touraine Sauvignon Blanc, Bordeaux Blanc |
| Barolo | Langhe Nebbiolo |
| Brunello | Rosso di Montalcino |
| Châteauneuf-du-Pape | Côtes du Rhône Villages, Vacqueyras, Spanish Garnacha |
| Amarone | Valpolicella Ripasso |
| Rioja Gran Reserva | Rioja Reserva |
| Meursault | Mâcon, Pouilly-Fuissé, Sonoma Coast Chardonnay |

Also: **boxed wine** (3 L ≈ 4 bottles; freshness for weeks after opening) for parties and everyday drinking; **magnums** for gatherings.

## 4. Party budget method

1. Estimate bottles (see [sparkling-occasions-gifting-and-handling.md](../04_sparkling-champagne-prosecco/sparkling-occasions-gifting-and-handling.md); dinner ~1 bottle per 2 adults).
2. Divide the budget by bottles → per-bottle target.
3. Apply the mixed-case discount: 6–11 bottles −10%, 12+ −15% (eligible items; A-50). This raises the effective per-bottle target.
4. Leave room for tax and delivery: `calculate_order_totals` confirms.
5. Suggest a mix: one crowd-pleasing red, one white, one sparkling.

**Example:** "$250 for 20 guests, dinner party" → ~10 bottles → $25/bottle before discount; with 10% case discount, list prices up to ~$27 fit, minus tax → target $22–25 per bottle.

## 5. Sample dialogues

> **Customer:** What's a good wine under $10?
> **Agent:** There are some real gems under $10, especially from Portugal, Spain, Chile and the south of France. Red or white? For red, a Spanish Garnacha or Côtes du Rhône; for white, a Vinho Verde or Pinot Grigio. Here's what's in stock: …

> **Customer:** I have $150 to spend on wine for a party of 15.
> **Agent:** Great budget for that size! Plan about 8 bottles if it's a dinner party. With 8 bottles you get 10% off, so you can spend about $18 per bottle and still leave room for tax. A suggested mix: 3 reds, 3 whites, 2 Prosecco for a welcome toast. Want me to pick specific bottles?
