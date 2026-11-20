---
id: KB-LCW-003
title: Dietary Questions: Sugar, Carbs, Keto, Gluten, Vegan, Sulfites, Histamines, Pregnancy
category: low-calorie
subcategory: dietary-faq
doc_type: faq
intents: [product.details, recommend.low_calorie, recommend.organic_natural, compliance.health_claim_request]
tools: [get_product_details, search_products, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 120
owner: compliance
status: active
depends_on_assumptions: [A-06]
related: [KB-LCW-002, KB-ORG-002, KB-NAW-002, KB-SYS-003, KB-FAQ-002]
---

# Dietary Questions: Safe, Helpful Answers

Each answer follows the same pattern: **facts about wine in general → what the product record says → "check with your doctor" when health is involved.** No medical advice (G7).

## 1. Sugar

- **Q: How much sugar is in wine?** Dry table wines usually have under ~4 g/L of residual sugar (well under 1 g per 5 oz glass). Off-dry: ~4–30 g/L. Sweet/dessert: 50–200+ g/L. Sparkling follows the Brut/Extra Dry scale ([sparkling-sweetness-scale.md](../04_sparkling-champagne-prosecco/sparkling-sweetness-scale.md)).
- **Q: Is sugar added to wine?** In most dry wines, sugar is natural grape sugar, mostly fermented into alcohol. Some regions allow adding sugar before fermentation (chaptalization) to raise alcohol; it ferments out. Sparkling wines get a dosage. Some mass-market wines retain or adjust sweetness. Product records show `residual_sugar_gl` when available.
- **Agent search:** `sweetness=dry`, `residual_sugar_max` (if data exists).

## 2. Carbs and keto

- **Q: Is wine keto-friendly?** Answer neutrally: "Dry wines are generally low in carbs. Many have about 2–4 g per 5 oz, mostly from residual sugar and other compounds. Sweet wines are much higher. Whether it fits your eating plan is a question for you and your doctor or dietitian. Here are some with carb counts on the label."
- Never say "keto-approved" or "keto-certified" unless that exact claim is on the label, and even then attribute it ("the producer labels it…").

## 3. Gluten

- Wine is made from grapes and is **naturally gluten-free**. Rare trace exposure has been discussed around certain fining agents or wheat-paste barrel sealing, but this is uncommon.
- TTB allows "gluten-free" on labels only for products made without gluten-containing ingredients and meeting its policy; otherwise producers may use a qualified statement.
- **For celiac disease:** "Wine is generally considered gluten-free, but for a medical condition, please check with your doctor. I can show you wines labeled gluten-free if you'd like."

## 4. Vegan and vegetarian

- Many wines are **fined** (clarified) with animal-derived agents: egg whites (albumin), casein (milk), isinglass (fish), gelatin. These are mostly removed, but strict vegans avoid them.
- **Vegan wines** use mineral or plant fining (bentonite clay, pea protein, activated carbon) or are **unfined/unfiltered**.
- Labeling is voluntary; there is no single US legal definition. The catalog's `vegan` attribute requires evidence (producer statement or certification such as a recognized vegan certification mark). See [catalog-tagging-and-verification-policy.md](../06_organic-biodynamic-natural/catalog-tagging-and-verification-policy.md).
- **Agent:** search `certifications contains "vegan"`, or `attributes.vegan=true`. If unknown, say "the producer hasn't confirmed vegan status".

## 5. Egg, milk and fish allergies

- Fining agents from egg, milk or fish may be used. Residues are typically minimal, but **we cannot guarantee "free from"**.
- Federal allergen labeling for alcohol is **proposed (TTB Notice No. 238), not final**. Today, disclosure is voluntary.
- **Agent:** share any `allergen_notes` from the product record. Recommend contacting the producer and consulting a doctor for serious allergies. Offer vegan-labeled wines as an option, without implying they are allergen-safe.

## 6. Sulfites

- Sulfites occur naturally in fermentation and are commonly added as a preservative. US labels must say **"Contains sulfites"** at **10 ppm or more**.
- **USDA "Organic" wine** has **no added sulfites** (natural sulfites may still be present). "Made with organic grapes" may contain added sulfites up to 100 ppm. See [sulfites-and-additives.md](../06_organic-biodynamic-natural/sulfites-and-additives.md).
- **Headache myth:** don't claim sulfites cause, or that low-sulfite wines prevent, headaches. A small percentage of people (often with asthma) are sulfite-sensitive. **Dried fruit typically contains far more sulfites than wine**, a neutral fact you may share.

## 7. Histamines and "red wine headache"

- Red wines generally contain more histamines and other compounds than whites; research on wine headaches is ongoing and inconclusive.
- **Agent:** no claims. "I can't say how a wine will affect you. Some customers prefer whites, lower-alcohol, or organic wines. Here are options if you'd like to try them."

## 8. Pregnancy, breastfeeding, medications, medical conditions, recovery

- **No recommendations of alcoholic wine.** Respond with care, without lecturing:
  > "I'm not able to give medical advice. That's a question for your doctor or pharmacist. If you're looking for something to enjoy without alcohol, I can show you non-alcoholic options, though they can contain trace alcohol (up to 0.5%), so please check with your doctor first."
- **Diabetes:** "Please check with your doctor. I can share label carb and sugar information for any wine."
- **Recovery / sobriety:** be respectful. Don't push NA wine (some people in recovery avoid alcohol-imitating products). Offer it only if asked. See [sale-policy-and-age-rules.md](../07_non-alcoholic-wines/sale-policy-and-age-rules.md).
- **Medication interactions:** never answer; refer to a pharmacist.

## 9. Lower alcohol

- Search `abv_max`. Naturally lower: Moscato d'Asti (~5–6%), Mosel Kabinett (8–10%), Vinho Verde (9–11%), Lambrusco (~8–11%), branded light wines (~7–9%).
- "Lower alcohol" is not "non-alcoholic". Clarify when it matters (pregnancy, driving): non-alcoholic wine is < 0.5% ABV (folder 07).

## 10. Kosher (not dietary-health, but a frequent "dietary" question)

- Search `is_kosher=true`. **Kosher for Passover** and **Mevushal** are separate attributes. Don't assume one implies the other.

## 11. Escalation

| Trigger | Priority |
|---|---|
| Customer describes an allergic reaction or medical emergency | P1 `safety_crisis`; advise emergency services/medical care first |
| Customer insists the agent confirm medical safety | Don't confirm; offer a human only for non-medical store questions |
| Repeated pressure to make health claims (e.g., for marketing use) | P3 `kb_gap`/compliance FYI |
