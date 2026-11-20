---
id: KB-REG-001
title: Region Taxonomy, Appellation Systems and Label Terms
category: region
subcategory: taxonomy
doc_type: reference
intents: [recommend.by_region, education.wine_question, product.details]
tools: [search_products, get_product_details]
jurisdictions: [NJ, NY]
audience: agent, catalog-team
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 365
owner: wine-team
status: active
related: [KB-REG-000, KB-SYS-008, KB-STK-006]
---

# Region Taxonomy, Appellation Systems and Label Terms

## 1. Catalog hierarchy (`region_path`)

Every wine has a `region_path` with up to four levels, separated by `>`:

```
Country > Region > Sub-region > Appellation
France > Burgundy > Côte de Beaune > Meursault
USA > California > Napa Valley > Oakville
Italy > Piedmont > Langhe > Barolo
New Zealand > Marlborough
```

**Catalog rules (for staff; the agent relies on them)**
- Use the **most specific legally labeled appellation** on the bottle as the leaf level.
- Use accented official names (Rhône, Côte, Ribera del Duero) plus searchable aliases (`aliases: ["Rhone"]`).
- Multi-region blends (e.g., "California", "Vin de France", "South Eastern Australia") stop at the level stated on the label.
- **Old World / New World** is a derived tag (`world=old|new`), used for style queries ("old-world style").

**Search tips**
- Broad: `filters.country="Italy"`.
- Region: `filters.region_path_prefix="France>Rhône"`.
- Exact appellation: `filters.appellation="Sancerre"`.
- Synonyms: "Cali" → California; "Bordeaux blend" is a style, not a region (use grapes).

## 2. Appellation systems by country

| Country | System | Tiers (low → high) | What it controls |
|---|---|---|---|
| **USA** | AVA (American Viticultural Area), TTB | State/County → AVA → nested AVA (e.g., Napa Valley > Oakville) | **Geography only** (≥ 85% grapes from the AVA). Doesn't control grapes or yields. |
| **France** | AOC/AOP (INAO) | Vin de France → IGP (Pays d'Oc) → AOC regional → village → Premier Cru → Grand Cru (meaning varies by region) | Area, grapes, yields, methods, aging |
| **Italy** | DOC/DOCG | Vino → IGT/IGP → DOC → DOCG | Area, grapes, aging; DOCG adds stricter rules and a government neck seal |
| **Spain** | DO system | Vino → VdlT/IGP → DO → DOCa/DOQ (Rioja, Priorat) → Vino de Pago | Plus aging tiers: Joven, Crianza, Reserva, Gran Reserva |
| **Portugal** | DOC | Vinho → Regional (IGP) → DOC | |
| **Germany** | Prädikat & VDP | Deutscher Wein → Landwein → Qualitätswein → Prädikatswein (Kabinett, Spätlese, Auslese, BA, Eiswein, TBA). VDP estates: Gutswein → Ortswein → Erste Lage → Grosse Lage (dry = Grosses Gewächs, "GG") | Prädikat = **ripeness at harvest**, not sweetness |
| **Austria** | DAC | Regional DAC (e.g., Kamptal DAC), Wachau's Steinfeder/Federspiel/Smaragd | |
| **Australia / NZ / South Africa / Chile / Argentina** | Geographical Indications (GI), WO (South Africa), DO (Chile) | Mainly geographic | |

## 3. Label terms customers ask about

| Term | Meaning | Legal? |
|---|---|---|
| **Grand Cru** | Burgundy: top vineyard (e.g., Montrachet). Bordeaux Saint-Émilion: a classification that is revised. Alsace & Champagne: top villages/sites | Yes, region-specific |
| **Premier Cru / 1er Cru** | Burgundy: second-tier vineyard; Bordeaux 1855 "Premier Grand Cru Classé" = First Growth | Yes |
| **Classé / Classed Growth (Cru Classé)** | Bordeaux 1855 classification (Médoc + Haut-Brion; Sauternes) or Graves/Saint-Émilion classifications | Yes |
| **Riserva (Italy)** | Longer minimum aging, rules per DOC/DOCG | Yes |
| **Reserva / Gran Reserva (Spain)** | Minimum aging (e.g., Rioja red Reserva ≥ 3 years incl. ≥ 1 in oak; Gran Reserva ≥ 5 incl. ≥ 2 in oak) | Yes |
| **Reserve (US)** | Producer's choice | **No** |
| **Classico (Italy)** | The historic core zone of a DOC (Chianti Classico, Soave Classico) | Yes |
| **Superiore (Italy)** | Usually higher minimum alcohol/aging | Yes |
| **Estate Bottled (US)** | Grown, made and bottled by the winery in the stated AVA | Yes |
| **Old Vines / Vieilles Vignes** | Older vines | No |
| **Meritage** | US Bordeaux-style blend from a licensed member | Trademark program |
| **Côtes / Coteaux** | "Slopes / hillsides" | Part of appellation names |
| **Mis en bouteille au château/domaine** | Estate bottled | Yes |
| **Sur lie** | Aged on lees | Regulated in Muscadet |

## 4. Old World vs New World (style shorthand)

| Old World tendencies | New World tendencies |
|---|---|
| Labeled by **place** (Sancerre, Chianti) | Labeled by **grape** (Sauvignon Blanc, Cabernet) |
| Cooler climate: higher acidity, lower alcohol, more savory/earthy | Warmer, sunnier: riper fruit, fuller body, higher alcohol |
| More restrained oak | Oak more prominent (changing) |

**Always add:** "These are generalizations; many producers break the pattern." Use `fruit_profile` and other product data for the specific wine.

## 5. Translating "I want a wine like X but from Y"

| Customer wants | Suggest |
|---|---|
| Napa Cab style, from Europe | Bordeaux Left Bank, Bolgheri (Super Tuscan), Ribera del Duero |
| Burgundy Pinot style, at lower price | Oregon Willamette, Bourgogne Rouge, Côte Chalonnaise, NZ Central Otago, Sonoma Coast |
| Sancerre style, cheaper | Touraine Sauvignon, Bordeaux Blanc, Chilean coastal Sauvignon Blanc |
| Champagne style, cheaper | Crémant, Cava, US traditional-method sparkling, English sparkling (premium) |
| Barolo style, cheaper | Langhe Nebbiolo, Roero, Gattinara/Ghemme |
| Châteauneuf style, cheaper | Côtes du Rhône Villages, Vacqueyras, Gigondas, Spanish Garnacha |
| Malbec, but more savory | Cahors |

## 6. Edge cases

- **"Is Champagne a region or a style?"** Both. A region whose sparkling wine is legally "Champagne". US "champagne" labels exist only under a grandfather clause for pre-2006 brand names. See [champagne.md](../04_sparkling-champagne-prosecco/champagne.md).
- **"Chianti vs Chianti Classico"**: different DOCGs; Classico is the historic heartland (black rooster seal).
- **Vin de France / IGP wines** can be excellent; label tier ≠ taste quality.
- **Same name, different place**: "Côte de Beaune" (Burgundy) vs "Côtes du Rhône". Always confirm the region in product data.
