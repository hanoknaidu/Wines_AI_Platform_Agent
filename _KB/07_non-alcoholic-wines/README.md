---
id: KB-NAW-000
title: Non-Alcoholic Wines: Folder Index
category: non-alcoholic
subcategory: index
doc_type: index
intents: [recommend.non_alcoholic, product.details, compliance.health_claim_request]
tools: [search_products, get_product_details, check_inventory, get_fulfillment_options]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: wine-team
status: active
depends_on_assumptions: [A-04, A-06]
related: [KB-SYS-003, KB-LCW-003]
---

# Non-Alcoholic Wines: Folder Index

## Scope

Dealcoholized and alcohol-free wines (still, sparkling, rosé, red, white): definitions, how they're made, taste expectations, brands, how we sell them (age and state rules), and sensitive conversations (pregnancy, recovery, religion, driving).

## Files

| File | Answers |
|---|---|
| [non-alcoholic-wine-guide.md](non-alcoholic-wine-guide.md) | Definitions (< 0.5% vs 0.0%), production methods, taste, calories, shelf life, brands, how to recommend |
| [sale-policy-and-age-rules.md](sale-policy-and-age-rules.md) | 21+ rule, **NJ Store only** (NY restrictions), returns/discount treatment, sensitive situations |
| [non-alcoholic-recommendations-and-faq.md](non-alcoholic-recommendations-and-faq.md) | Recommendations by occasion and top customer questions |

## The two rules to remember

1. **21+ only**, even though the product is under 0.5% ABV (A-04).
2. **NJ Store only.** NY wine/liquor stores are, as of the last review, not permitted to sell non-alcoholic versions of alcoholic beverages; bills to change this were pending. NY addresses cannot receive NA wine (A-06). Always confirm with `check_inventory(...).sellable_in_jurisdiction`; compliance will update this rule if NY law changes (assumptions register Q-1).
