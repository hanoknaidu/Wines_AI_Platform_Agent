---
id: KB-ORG-002
title: Sulfites, Additives and Ingredient Labeling
category: organic
subcategory: sulfites-additives
doc_type: reference
intents: [product.details, recommend.organic_natural, education.wine_question, compliance.health_claim_request]
tools: [get_product_details, search_products]
jurisdictions: [US, NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: compliance
status: active
related: [KB-ORG-001, KB-LCW-003, KB-LCW-002, KB-SYS-003]
---

# Sulfites, Additives and Ingredient Labeling

## 1. Sulfites: the facts

- **What:** Sulfur dioxide (SO₂) and related compounds protect wine from oxidation and microbes. Yeasts produce small amounts naturally during fermentation, so **virtually all wine contains some sulfites**.
- **US label rule:** wines with **10 ppm (mg/L) or more** total sulfur dioxide must state **"Contains sulfites"**. The US legal maximum for wine is 350 ppm. Most wines are far below that.
- **Typical levels (general):** dry reds tend to be lower than dry whites and rosés; sweet wines tend to be highest (sugar needs more protection). Organic and natural wines are generally lower.
- **EU limits** (conventional): lower maximums than the US, with lower limits again for EU-organic wine.
- **Context fact the agent may share:** many foods, such as dried fruit, can contain far more sulfites than wine.

## 2. Sulfites and sensitivity

- A small share of people, more often people with asthma, are **sulfite-sensitive**; reactions can be serious. That's why the label warning exists.
- The idea that sulfites cause common "wine headaches" is **not established**. The agent does not say sulfites cause or prevent headaches.
- **Agent wording:**
  > "All wine contains some sulfites. If you're sensitive, look for wines labeled USDA Organic, which have no added sulfites, but they may still contain natural sulfites, so please follow your doctor's advice."

## 3. Common additives and processing aids (US)

US wine regulations (27 CFR Part 24) permit a defined list of materials. Most need not be listed on labels. Neutral descriptions:

| Material | Purpose | Notes |
|---|---|---|
| **Sulfur dioxide / potassium metabisulfite** | Preservative, antioxidant | Labeled "contains sulfites" ≥ 10 ppm |
| **Cultured yeast** | Reliable fermentation | Natural-wine producers use native yeast |
| **Yeast nutrients (DAP)** | Healthy fermentation | |
| **Tartaric / citric acid** | Adjust acidity (common in warm climates) | |
| **Sugar (chaptalization)** | Raise potential alcohol; ferments out | Not permitted in some places (e.g., California); permitted in cooler regions within limits |
| **Grape concentrate** | Sweetness/color adjustment | Includes concentrated color products |
| **Oak chips, staves, oak extract** | Oak flavor without barrels | Common in value wines |
| **Tannin** | Structure, color stability | |
| **Fining agents**: bentonite, egg albumin, casein, isinglass, gelatin, PVPP, pea protein, activated carbon | Clarity and stability | Animal-derived agents → not vegan |
| **Enzymes** | Extraction, clarification | |
| **Gum arabic, CMC, mannoproteins** | Stability, mouthfeel | |
| **Potassium sorbate** | Stops re-fermentation in sweet wines | |
| **Copper sulfate** | Removes sulfur off-odors | Trace limits |
| **Cochineal/carmine, FD&C Yellow No. 5** | Color (rare in wine) | **Must be declared** if used |

**Agent rule:** Don't describe additives as harmful or "chemicals" pejoratively, and don't say a wine is "additive-free" unless the product record says so with evidence.

## 4. Ingredient and nutrition labeling: US vs EU

| | US (today) | EU |
|---|---|---|
| Ingredient list | **Not required** (voluntary). TTB proposals pending | **Required** for wine produced from **Dec 8, 2023** (may be via QR code e-label) |
| Energy value / nutrition | Voluntary (Serving Facts) | Energy value on label; full nutrition may be on e-label |
| Allergens | Sulfites mandatory; others voluntary (TTB Notice 238 proposed) | Allergens such as sulfites, egg, milk must be shown |

**Practical tip for customers:** some imported European wines carry a **QR code** that links to ingredients and nutrition information (from the EU e-label requirement), even when the US back label doesn't list them.

## 5. Search recipes

| Customer wants | Search |
|---|---|
| No added sulfites | `certifications=usda_organic` or `attributes.no_added_sulfites=true` |
| Lower sulfites (no strict requirement) | Organic, biodynamic, `low_intervention`; prefer dry reds; avoid sweet wines |
| Vegan | `attributes.vegan=true` |
| "Clean" wine | Clarify the goal (organic? no additives? low sugar?), then use the matching filter. Never adopt "clean" as our claim |
| Ingredient list | `get_product_details.ingredients` if present; otherwise say it isn't provided, and mention EU QR e-labels where relevant |

## 6. Sample dialogues

> **Customer:** Which wines have no sulfites?
> **Agent:** No wine is completely sulfite-free, because yeast makes a little naturally. But wines labeled **USDA Organic** have **no added sulfites**, and some producers make "no sulfites added" wines too. Here are a few: … If you have a sulfite sensitivity, please follow your doctor's advice.

> **Customer:** Does this wine have additives?
> **Agent:** US labels aren't required to list ingredients, and this producer doesn't publish a list. What I can tell you from our records: it's made with organic grapes and native yeast. If you're looking for the most minimal-intervention style, here are a few wines the producers describe as unfined, unfiltered and with no added sulfites: …
