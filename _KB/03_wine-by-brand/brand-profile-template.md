---
id: KB-BRD-006
title: Brand Profile Template (for adding new brands)
category: brand
subcategory: template
doc_type: template
intents: []
tools: []
jurisdictions: [NJ, NY]
audience: kb-maintainers, merchandising
priority: low
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 365
owner: merchandising
status: active
related: [KB-BRD-001, KB-SYS-010, KB-STK-006]
---

# Brand Profile Template

> Maintainer-facing. Copy the block below into a new file (`03_wine-by-brand/<brand-slug>.md`) when a brand needs **more** detail than a row in a grouped brand table: typically top-20 sellers, exclusives, or brands with frequent customer questions. Otherwise add a row to the relevant grouped file.

## When to create a dedicated profile

| Create a dedicated file when… | Otherwise |
|---|---|
| The brand is a top-20 seller or a frequent `recommend.by_brand` intent | Add a row to the grouped table |
| The brand is a Store exclusive (`exclusive=true`) | — |
| The brand has many tiers that confuse customers (e.g., value vs estate lines) | — |
| There are recurring brand-specific questions (label change, recall, availability by state) | — |

## Sourcing rules for profile content

- Producer website, technical sheets, importer/distributor sheets, reputable trade publications.
- **Never** copy marketing superlatives as fact ("the best Chardonnay in the world").
- Mark anything time-sensitive (ownership, winemaker, certifications) with "as of <date>".
- Certifications (organic, biodynamic, vegan, kosher) belong in the **product record** with evidence. The profile can mention them only generally.

---

## TEMPLATE (copy from here)

```markdown
---
id: KB-BRD-<NNN>
title: <Brand Name>: Brand Profile
category: brand
subcategory: brand-profile
doc_type: reference
intents: [recommend.by_brand, recommend.similar, product.details]
tools: [search_products, get_product_details, get_similar_products]
jurisdictions: [NJ, NY]          # narrow if only distributed in one state
audience: agent
priority: medium
version: 1.0.0
last_reviewed: <YYYY-MM-DD>
review_cycle_days: 180
owner: merchandising
status: draft
related: [KB-BRD-001]
---

# <Brand Name>: Brand Profile

## 1. Snapshot
- **Producer / origin:** <winery, region, country>
- **Founded:** <year, if verified>
- **Distributed at:** NJ Store <yes/no> · NY Store <yes/no>   (verify with search_products)
- **Exclusive to the Store:** <yes/no>

## 2. Product lines / tiers
| Line | Wines | Style in plain words | Indicative band |
|---|---|---|---|
| <Value line> | <...> | <...> | Everyday |
| <Estate / Reserve> | <...> | <...> | Premium |

## 3. Signature style
<2–4 sentences: taste axes (sweetness, body, acidity, tannin, oak, fruit), what fans like>

## 4. Who it's for / when to recommend
- <occasion, food, customer profile>

## 5. Similar-style alternatives
| If the customer likes… | Suggest |
|---|---|
| <wine> | <2–3 alternatives across price points> |

## 6. Frequently asked questions
- **Q:** <e.g., Is it sweet?> **A:** <answer, referencing product data>
- **Q:** <Did the label change?> **A:** <...>

## 7. Known issues / notes for agents
- <vintage variation, recalls, availability limits, allocation>

## 8. Sources
- <URL / document, accessed date>
```
