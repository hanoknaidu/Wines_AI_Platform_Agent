---
id: KB-NAW-002
title: Non-Alcoholic Wine Sale Policy, Age Rules and Sensitive Situations
category: non-alcoholic
subcategory: policy
doc_type: policy
intents: [recommend.non_alcoholic, compliance.underage, compliance.health_claim_request, delivery.eligibility]
tools: [check_inventory, get_fulfillment_options, search_products, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent, compliance
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: compliance
status: active
depends_on_assumptions: [A-04, A-05, A-06, A-34, A-35, A-50]
related: [KB-SYS-003, KB-NAW-001, KB-LCW-003, KB-FAQ-002]
---

# Non-Alcoholic Wine Sale Policy, Age Rules and Sensitive Situations

## 1. Policy rules

**NAW-R1: 21+ only (A-04).** All customers buying or receiving non-alcoholic (NA) wine must be 21+ with the same age verification as alcohol (A-05).
*Why:* NA wine is sold by a licensed liquor retailer, mimics an alcoholic product, can contain trace alcohol, and state rules for selling NA products to under-21s are inconsistent. One rule prevents errors.

**NAW-R2: NJ Store only (A-06).** NA wine is sold for **NJ delivery, NJ shipping, or pickup at the NJ Store**. NY addresses cannot receive NA wine. New York wine and liquor stores are, as of this review, generally not permitted to sell non-alcoholic versions of alcoholic beverages; bills that would change this (e.g., A6726 on dealcoholized wine) were pending, not enacted.

**NAW-R3: Tool check required.** Before offering NA wine, the agent calls `check_inventory(sku, fulfillment_location)` and respects `sellable_in_jurisdiction`. If compliance changes the rule, the tool will reflect it before this document is updated.

**NAW-R4: Same commercial rules as wine (NJ Store).** NA 750 ml wines count toward the mixed-case discount (A-50); NJ returns rules apply (A-34); damaged/defective claims are handled the same way. Best-by-dated products past their date at delivery are treated as defective.

**NAW-R5: No health positioning.** NA wine is not described as healthy, safe for pregnancy, or suitable for any medical condition (G7).

## 2. Decision table

| Situation | Agent action |
|---|---|
| NJ customer, 21+ verified | Recommend normally |
| NY delivery address | "Our non-alcoholic wines are only available through our NJ store right now, because of New York rules on what wine stores can sell. If you're ever near our NJ store, you can pick up there." No other workaround. |
| NY customer asks to ship to a NJ address (friend/office) for their own use | Allowed only if a 21+ recipient receives it at that NJ address, like any NJ order. Don't suggest forwarding to NY. |
| Customer under 21 (or buying for someone under 21, e.g., teen's party) | Decline (G1): "We can only sell to adults 21 and over, including our non-alcoholic wines." |
| Parent asks whether NA wine is OK for their child | Don't advise. Explain our 21+ sales policy. |
| Pregnancy / breastfeeding | Care script (§3). |
| Recovery / sobriety | Respect script (§3). |
| Religious reasons (e.g., avoiding all alcohol) | Explain < 0.5% vs 0.0%; share certifications only if in product data (e.g., halal certification, if any); no religious rulings. |
| Driving | Don't advise on driving after any product. Can state the ABV fact. |
| Event planner wants NA for under-21 guests | We can't sell for consumption by under-21s. Suggest they source NA beverages for minors elsewhere. Adults' NA needs are fine. |

## 3. Sensitive-situation scripts

**Pregnancy**
> "Congratulations! I can't give medical advice, so please check with your doctor. If it helps, we have **alcohol-free (0.0%)** options as well as **dealcoholized** wines, which can contain trace alcohol up to 0.5%. Want me to show you the 0.0% ones?"

**Recovery / sobriety**
> "Thanks for sharing that. Some people in recovery enjoy non-alcoholic wine and others prefer to avoid anything that resembles alcohol, so you know best what's right for you. If you'd like, I can show you alcohol-free options; otherwise, I'm happy to help with anything else."
- Never push NA wine. Never upsell to alcoholic wine. If distress or risk is expressed, follow G8 (resources; P1 if immediate risk).

**Medication**
> "That's a question for your pharmacist or doctor. I can tell you the alcohol content of any product, but I can't advise whether it's safe with medication."

**Religious**
> "Dealcoholized wines can contain up to 0.5% alcohol; '0.0%' or 'alcohol-free' products have none detectable. Whether either fits your practice is a personal decision, but I'm happy to show you the 0.0% options."

## 4. Workflow

1. Detect `recommend.non_alcoholic` (or NA mention inside another intent).
2. Determine fulfilling location (`get_fulfillment_options` or session ZIP).
3. If NY → NAW-R2 response; offer NJ pickup information; stop NA recommendations.
4. If NJ → `search_products(is_non_alcoholic=true, fulfillment_location="NJ")` → `check_inventory` → recommend.
5. If the situation is sensitive (§3), use the script; don't add sales pressure.

## 5. Escalation

| Trigger | Priority | Reason |
|---|---|---|
| Report that NA wine was delivered to a minor | P1 | `handoff_compliance_incident` |
| NY order containing NA wine slipped through checkout | P2 | `compliance_order_review`. Do not cancel unilaterally; flag for compliance |
| Customer reports an alcohol-like effect or a label ABV discrepancy | P2 | `product_quality` → compliance |
| Customer in crisis | P1 | `safety_crisis` |

## 6. Response examples

> "Yes! Our NJ store has a good range of non-alcoholic wines. Just so you know, we sell them only to adults 21 and over, the same as our regular wines. What style would you like, bubbly, white, rosé or red?"

> "I'm sorry, our non-alcoholic wines aren't available for New York delivery at the moment because of state rules for wine stores. They're available for pickup at our NJ store if that's ever convenient."
