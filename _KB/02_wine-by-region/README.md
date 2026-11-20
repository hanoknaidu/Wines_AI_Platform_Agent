---
id: KB-REG-000
title: Wine by Region: Folder Index
category: region
subcategory: index
doc_type: index
intents: [recommend.by_region, education.wine_question, product.details]
tools: [search_products, get_product_details]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: wine-team
status: active
depends_on_assumptions: [A-44]
related: [KB-REG-001]
---

# Wine by Region: Folder Index

## Scope

How the catalog organizes wines by place, how to read appellation labels, and regional guides for recommending and educating. Region is a **secondary navigation** on the storefront ("Shop by Region"): country → region → sub-region → appellation. Customers who ask by region are often enthusiasts or gift buyers looking for a recognizable name.

## Files

| File | Covers |
|---|---|
| [region-taxonomy-and-label-terms.md](region-taxonomy-and-label-terms.md) | Catalog `region_path` hierarchy, appellation systems (AVA, AOC, DOCG, DOCa…), quality tiers, Old vs New World |
| [france.md](france.md) | Bordeaux, Burgundy, Rhône, Loire, Alsace, Provence, Languedoc-Roussillon, Beaujolais (Champagne → folder 04) |
| [italy.md](italy.md) | Piedmont, Tuscany, Veneto, Southern Italy & islands, Alto Adige/Friuli (Prosecco → folder 04) |
| [spain-and-portugal.md](spain-and-portugal.md) | Rioja, Ribera, Priorat, Rías Baixas, Rueda, Cava; Douro, Vinho Verde, Alentejo, Port, Madeira |
| [usa-california.md](usa-california.md) | Napa, Sonoma, Central Coast, Paso Robles, Lodi, Santa Barbara |
| [usa-pacific-northwest-new-york-and-new-jersey.md](usa-pacific-northwest-new-york-and-new-jersey.md) | Oregon, Washington, Finger Lakes, Long Island, Hudson Valley, New Jersey wine regions |
| [southern-hemisphere.md](southern-hemisphere.md) | Argentina, Chile, Australia, New Zealand, South Africa |
| [germany-austria-and-emerging-regions.md](germany-austria-and-emerging-regions.md) | Germany, Austria, Greece, Hungary, Portugal's neighbors, Lebanon, Israel, England, Canada |

## Rules for region answers

1. **Education is fine without tools; availability is not.** "Rioja is in northern Spain…" needs no tool; "We have three Riojas…" requires `search_products(filters.region=…)`.
2. Use `region_path` filters at the right level: country (`Italy`), region (`Italy>Tuscany`), appellation (`Italy>Tuscany>Chianti Classico`).
3. If a customer names a famous wine region we don't stock, say so and offer similar styles from regions we do stock.
4. Price bands are indicative (A-44); quote live prices only from `get_price`.
