---
id: KB-ORG-001
title: Organic, Biodynamic, Sustainable, Natural and Vegan: Definitions and Certifications
category: organic
subcategory: definitions
doc_type: reference
intents: [recommend.organic_natural, product.details, education.wine_question]
tools: [search_products, get_product_details]
jurisdictions: [US, NJ, NY]
audience: agent, catalog-team
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: compliance
status: active
related: [KB-ORG-002, KB-ORG-003, KB-ORG-004, KB-LCW-003]
---

# Definitions and Certifications

## 1. USDA organic wine labels (US market)

Under the USDA National Organic Program (NOP), with TTB approving the labels, wine sold in the US can carry one of these organic statements:

| Label wording | Requirements (summary) | USDA seal? | Customer explanation |
|---|---|---|---|
| **"Organic wine"** (or "100% organic") | Certified organic grapes **and** certified organic winemaking; **no added sulfites** (naturally occurring sulfites can still be present) | **Yes, allowed** | "Organic from vineyard to bottle, with no sulfites added." |
| **"Made with organic grapes"** | 100% certified organic grapes (no mixing with conventional grapes); winemaking may add **sulfur dioxide up to 100 ppm**; other ingredients per NOP rules; certifier must be identified | **No** | "Organic grapes, but the winemaker may add a small amount of sulfites as a preservative." |
| **"Ingredients: organic grapes"** or organic listed only in the ingredient statement | Some organic ingredients but doesn't meet the "made with" standard | No | "Contains some organic ingredients." |

**Why this matters:** Most European organic wines **add sulfites**, so in the US they are usually labeled "made with organic grapes", not "organic", even though they're certified organic in Europe.

## 2. EU organic ("Euro-leaf" logo)

- EU organic wine (since 2012 rules) requires organic grapes **and** organic winemaking rules, with **lower maximum sulfite levels** than conventional wine and a restricted additive list.
- Common on French, Italian, Spanish and German organic wines. The catalog records the certification body (e.g., Ecocert, AB France label, ICEA, CCPAE).

## 3. Biodynamic

- An agricultural philosophy that **includes organic practices** and adds holistic farm management: on-farm fertility, specific herbal/mineral preparations, biodiversity, and planting/harvest timing often aligned with a lunar/astronomical calendar.
- **Certification:** **Demeter** (international; "Biodynamic®" is a certification mark of Demeter USA in the US), **Biodyvin** (France).
- US label tiers (Demeter USA): **"Biodynamic wine"** (biodynamic grapes and winemaking with strict additive limits) and **"Made with Biodynamic grapes"** (biodynamic grapes; winemaking with more flexibility).
- **Customer explanation:** "Biodynamic goes beyond organic. The vineyard is farmed as a whole self-sustaining ecosystem, with natural preparations and calendar-based timing."
- No health or "tastes better" claims.

## 4. Sustainable certifications

Sustainability programs cover environmental, social and economic practices. They **may allow** some conventional inputs, so they are **not organic**.

| Program | Where |
|---|---|
| **Certified California Sustainable Winegrowing (CCSW)** | California |
| **SIP Certified** (Sustainability in Practice) | California, Michigan, others |
| **LODI RULES** | Lodi and beyond |
| **Napa Green** (vineyard and winery) | Napa |
| **Fish Friendly Farming** | California |
| **LIVE** (Low Input Viticulture & Enology) | Oregon, Washington, Idaho |
| **Salmon-Safe** | Pacific Northwest |
| **Sustainable Winegrowing New Zealand (SWNZ)** | New Zealand (most NZ wine is certified) |
| **Sustainable Wines of South Africa / IPW** | South Africa |
| **HVE** (Haute Valeur Environnementale), **Terra Vitis** | France |
| **Equalitas**, **SQNPI** | Italy |
| **Certified B Corporation** | Company-level social/environmental certification |
| **Regenerative Organic Certified (ROC)** | Organic + soil health + animal welfare + social fairness |

**Customer explanation:** "Sustainable certification means the winery is audited on environmental and social practices, like water use, biodiversity and worker welfare. It isn't the same as organic, but it's a meaningful commitment."

## 5. "Natural" wine and low intervention

- **No legal definition in the US.** The term generally means minimal intervention: organic/biodynamic farming, hand harvesting, native (wild) yeast fermentation, no or minimal additives, little or no added sulfites, often unfined and unfiltered.
- **France: "Vin Méthode Nature"** (a recognized labeling charter since 2020): certified organic grapes, hand-harvested, indigenous yeasts, no additives, no "brutal" techniques (e.g., reverse osmosis, flash pasteurization), and either **no added sulfites** or a small dose (≤ 30 mg/L) before bottling. Two logo versions reflect the sulfite choice.
- **Typical natural-wine characteristics:** can be cloudy, have sediment, show "funky" or cider-like notes, be more variable bottle to bottle, and be more sensitive to heat. Pét-nat and orange (skin-contact) wines are common styles.
- **Agent wording:** "Natural wine isn't a regulated term, but it usually means organic farming with as little added in the cellar as possible. Expect lively, sometimes cloudy or funky flavors that vary from bottle to bottle."
- **Catalog tag:** `low_intervention` (practices-based, producer-declared) rather than "natural". See [catalog-tagging-and-verification-policy.md](catalog-tagging-and-verification-policy.md).

## 6. Vegan

- Relates to **fining agents** (egg albumin, casein, isinglass, gelatin) and sometimes other animal-derived processing aids.
- No US legal definition; certifications include **Certified Vegan (Vegan Action)**, the **Vegan Society** trademark, **BeVeg**, and others; some producers self-declare.
- Catalog: `vegan=true` with evidence type `certification` or `producer_declaration`. The agent says which: "certified vegan" vs "the producer states it's vegan".

## 7. Other related terms

| Term | Meaning |
|---|---|
| **"Organically farmed" / "practicing organic"** | Producer says it farms organically but isn't certified (cost, transition). Say "per the producer, not certified". |
| **"Transitional"** | Converting to organic (typically a 3-year transition) |
| **"No sulfites added" (NSA)** | Can appear without organic certification; sulfites may still naturally exist |
| **"Low sulfite"** | No legal definition; describe from data if available |
| **"Clean wine"** | Marketing term, **no definition**; don't use it as our own claim |
| **"Unfined / unfiltered"** | Not clarified by fining or filtration; may be hazy; often vegan-friendly |
| **"Native / wild yeast"** | Spontaneous fermentation with ambient yeasts |
| **"Dry-farmed"** | No irrigation |

## 8. Search recipes

| Customer asks | Filters |
|---|---|
| "Organic wine" | `certifications` includes any of `usda_organic`, `made_with_organic_grapes`, `eu_organic` |
| "Strictly no added sulfites" | `certifications=usda_organic` **or** `attributes.no_added_sulfites=true` |
| "Biodynamic" | `certifications` includes `demeter`/`biodyvin` |
| "Sustainable" | `certifications` includes any sustainability program |
| "Natural wine" | `attributes.low_intervention=true` (optionally `no_added_sulfites`, `unfiltered`) |
| "Vegan" | `attributes.vegan=true` |
