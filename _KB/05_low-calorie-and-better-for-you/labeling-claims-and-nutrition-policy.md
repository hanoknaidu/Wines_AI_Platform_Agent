---
id: KB-LCW-002
title: Labeling Claims and Nutrition Data Policy (What the Agent May Say)
category: low-calorie
subcategory: claims-policy
doc_type: policy
intents: [recommend.low_calorie, product.details, compliance.health_claim_request]
tools: [get_product_details, log_event, create_support_ticket]
jurisdictions: [NJ, NY, US]
audience: agent, catalog-team, compliance
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: compliance
status: active
related: [KB-SYS-003, KB-LCW-001, KB-LCW-003, KB-ORG-003, KB-STK-006]
---

# Labeling Claims and Nutrition Data Policy

## 1. Purpose

Defines (a) the federal rules behind nutrition and "better-for-you" claims on wine labels, (b) how nutrition data enters our catalog, and (c) **exactly what the agent may say**. This document enforces guardrail G7.

> Regulatory summary for business use, not legal advice. Status of pending rules must be re-checked each review cycle (assumptions register Q-5).

## 2. Regulatory background (US)

| Topic | Rule (summary) |
|---|---|
| **Who regulates labels** | Wine ≥ 7% ABV: TTB (Alcohol and Tobacco Tax and Trade Bureau). Wine < 7% ABV and most non-alcoholic wine: FDA food labeling. |
| **Nutrition info is voluntary (today)** | Producers may add a **Serving Facts** statement (TTB Ruling 2013-2) or a **statement of average analysis**: calories, carbohydrates, protein, fat per serving (wine serving = 5 fl oz), optionally alcohol content. |
| **"Low carb" claims** | Allowed only if ≤ **7 g carbohydrates per serving** and the label also carries a statement of average analysis or Serving Facts (TTB Ruling 2004-1, as modified by 2013-2). |
| **Other nutrient/comparative claims** (e.g., "lower calorie", "x calories") | Must be truthful and supported by a statement of average analysis or Serving Facts; tolerance rules per TTB Ruling 2020-1. |
| **Sugar claims** ("zero sugar", "no sugar") | TTB has issued FAQs on sugar claims; claims must be truthful and not misleading. Treat them as label claims only. |
| **Health claims** | TTB prohibits health-related statements that are false or misleading; specific health claims require strong qualification and are rarely approved. The agent never makes them. |
| **Mandatory allergen-type disclosures** | "Contains sulfites" (≥ 10 ppm), FD&C Yellow No. 5, cochineal/carmine when used. Major food allergens are not yet mandatory. |
| **Pending: "Alcohol Facts" rule** | TTB Notice No. 237 (Jan 17, 2025) **proposes** mandatory per-serving alcohol, calorie, carbohydrate, fat and protein disclosure; comment period was extended (Apr 7, 2025). Proposed compliance: 5 years after a final rule. **Not final as of this review.** Notice No. 238 proposes allergen labeling. |

**Agent wording on the pending rule:** "There's a proposal from the federal regulator to require nutrition facts on alcohol labels, but it isn't in effect yet, so today it's up to each producer."

## 3. How nutrition data enters the catalog

| Source (`nutrition.source`) | Accepted? | Display |
|---|---|---|
| `label_serving_facts`: from the bottle's Serving Facts or average-analysis statement | Yes | "Per label: 90 calories per 5 oz" |
| `producer_tech_sheet`: producer's official technical sheet with lab analysis | Yes | "Per the producer: …" |
| `lab_analysis_store`: commissioned lab analysis | Yes, if dated | "Per lab analysis (date)" |
| `estimated_from_abv`: computed estimate | **Not stored as a product fact**; the agent may compute a general range in conversation, labeled "estimate" | — |
| Blogs, third-party sites, marketing copy | **No** | — |

Catalog rules:
- Nutrition is **vintage-specific** when the source is a lab analysis. A new vintage requires re-verification (`verified_at`).
- `low_carb`, `low_calorie`, `zero_sugar` tags are only applied when the **label** carries the claim (see [new-product-onboarding-and-catalog-standards.md](../09_stock-and-availability/new-product-onboarding-and-catalog-standards.md)).

## 4. What the agent MAY say

- Label/producer numbers, with attribution: "According to the label, it has 85 calories and 2 g carbs per 5 oz."
- Factual style explanations: "Lower-alcohol wines are generally lower in calories."
- General, clearly labeled estimates: "As a rough estimate, a typical dry white at 12% alcohol is around 100–110 calories per 5 oz."
- Brand-name claims **as the brand's claim**: "The producer markets it as a lower-calorie wine."
- The fact that nutrition labeling is voluntary today.

## 5. What the agent MUST NOT say

| Don't say | Why | Say instead |
|---|---|---|
| "This wine is healthy / good for you / heart-healthy" | Health claim | "It's a lighter-style wine; here's what the label shows." |
| "This won't give you a hangover / headache" | Health claim, unsupported | "I can't promise how any wine will affect you. Some people prefer lower-alcohol or lower-sulfite wines; here are some options." |
| "Keto-approved", "diabetic-friendly", "safe for…" | Medical/diet claim | "It has X g carbs per 5 oz per the label. For dietary plans, check with your doctor." |
| "Guilt-free", "skinny" (as our description) | Implied health/weight claim | "Lower calorie per the label." |
| Exact numbers for products without nutrition data | Fabrication | "The producer doesn't list nutrition info for this wine." |
| "Zero sugar" when the label doesn't say so | Unsupported claim | "It's a dry wine, typically under 4 g/L of sugar, but the label doesn't list an exact figure." |

## 6. Workflow: nutrition question about a specific product

1. `get_product_details(sku)` → check `nutrition{calories, carbs_g, sugar_g, serving_ml, source}`.
2. If present → answer with attribution and serving size.
3. If absent → say it isn't listed; optionally give a **labeled estimate** from ABV and sweetness; offer alternatives that do have data.
4. If the customer reports that our data differs from the bottle → thank them, `log_event("kb_conflict", {sku, field:"nutrition"})`, `create_support_ticket(category="catalog_correction", priority="P3")`.

## 7. Escalation

| Trigger | Priority | Reason |
|---|---|---|
| Customer reports an adverse reaction or allergic reaction | P1 | `safety_crisis` / product safety. Advise medical attention first |
| Customer disputes a label claim as false/misleading | P2 | `claim_dispute` → compliance |
| Regulator, media or legal inquiry about claims | P1 | `legal_matter` |

## 8. Sample responses

> "This one lists 95 calories and 3 g of carbs per 5 oz on its Serving Facts label. If you'd like an even lighter option, here are two that list 80–85 calories."

> "That wine doesn't list nutrition information. Since it's a dry white at 12.5% alcohol, a rough general estimate would be around 100–110 calories per 5 oz, but I can't confirm it for this bottle. Want options that show calories on the label?"
