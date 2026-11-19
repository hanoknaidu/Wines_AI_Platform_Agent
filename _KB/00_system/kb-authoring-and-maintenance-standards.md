---
id: KB-SYS-010
title: KB Authoring, Metadata and Maintenance Standards
category: system
subcategory: governance
doc_type: reference
intents: []
tools: []
jurisdictions: [NJ, NY]
audience: kb-maintainers, ai-platform
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: ai-platform
status: active
related: [KB-SYS-001, KB-SYS-005, KB-SYS-009]
---

# KB Authoring, Metadata and Maintenance Standards

> Maintainer-facing. Exclude from default agent retrieval.

## 1. File and folder conventions

- One folder per customer-facing domain, numbered for stable ordering (`01_…` to `14_…`). `00_system` holds cross-cutting rules.
- Each folder has a `README.md` index: scope, which file answers what, top intents and tools.
- File names: lowercase kebab-case, descriptive, no dates (`corked-or-flawed-wine.md`).
- **One topic per file.** If a file passes ~600 lines or covers two decisions with different owners, split it.
- New brand/region/product-family documents start from a template (e.g., [brand-profile-template.md](../03_wine-by-brand/brand-profile-template.md)).

## 2. Required frontmatter

```yaml
---
id: KB-<DOMAIN>-<NNN>          # stable, never reused; README files use 000
title: <Human title>
category: <folder domain>       # system, taste, region, brand, sparkling, low-calorie, organic, non-alcoholic, pricing, stock, discounts, orders, returns, account, general
subcategory: <short slug>
doc_type: policy | workflow | guide | faq | reference | index | template
intents: [<intent ids from intent-taxonomy.md>]
tools: [<tool names from tool-reference.md>]
jurisdictions: [NJ, NY]         # or one of them when the rule is state-specific
audience: agent | kb-maintainers | compliance | support-team
priority: critical | high | medium | low     # tie-breaker on conflicts
version: <semver>
last_reviewed: <YYYY-MM-DD>
review_cycle_days: <int>
owner: <team>
status: active | draft | draft-contract | deprecated
depends_on_assumptions: [A-xx, ...]   # if the doc uses assumed values
related: [<doc ids>]
---
```

Domain prefixes: `SYS`, `TST` (taste), `REG` (region), `BRD` (brand), `SPK` (sparkling), `LCW` (low-calorie), `ORG` (organic), `NAW` (non-alcoholic), `PRC` (pricing), `STK` (stock), `DSC` (discounts), `ORD` (orders), `RTN` (returns), `ACC` (account), `FAQ` (general).

## 3. Body structure

**Policy / workflow documents**
1. Purpose and scope
2. Policy rules, numbered (`RTN-R1`, `RTN-R2`…) so the agent and humans can cite them
3. Eligibility and decision criteria (tables)
4. Step-by-step workflow with tool calls
5. Edge cases and exceptions
6. Escalation conditions (with priority and reason code)
7. Customer-friendly response examples
8. Related documents

**Product-knowledge documents (taste, region, brand, category)**
1. What it is (customer-friendly summary)
2. Key grapes / styles / sub-types
3. Taste profile (sweetness, body, acidity, tannin, oak, fruit vs savory)
4. Indicative price bands (never live prices)
5. How to recommend: catalog filters to use with `search_products`
6. Customer language mapping and common misconceptions
7. Food pairing and occasions
8. Edge cases and sample dialogues

## 4. Chunking guidance for RAG

- Write so each `##` section **stands alone**. Repeat the subject in the first sentence of a section ("Corked wine claims must be reported…"), not "It must be…".
- Keep sections between 150 and 600 words. Tables are fine; keep each table under ~25 rows.
- Chunk on `##` headings; carry `id`, `title`, `category`, `jurisdictions`, `intents`, `depends_on_assumptions` as chunk metadata.
- Put numbers that may change next to their assumption ID, e.g., "within 48 hours (A-30)".
- Never put live data (today's price, current stock) in the KB.

## 5. Writing rules

- Customer-facing examples use "we" and plain language and are policy-accurate.
- Separate **fact**, **policy** and **assumption**. Label assumptions.
- Product facts must be verifiable from producer, regulator or reputable trade sources. If uncertain, generalize ("typically", "often") or leave out.
- No brand disparagement; no health claims; no competitor price claims.
- Cite regulations by name and number where possible; mark anything unconfirmed as "verify".

## 6. Review and change management

| Trigger | Action |
|---|---|
| `review_cycle_days` elapsed | Owner reviews, updates `last_reviewed`, bumps patch version |
| Policy value changes | Update [business-profile-and-assumptions.md](business-profile-and-assumptions.md) first, then dependents (`grep A-xx`), minor version bump |
| New intent | Add to [intent-taxonomy.md](intent-taxonomy.md), tag docs |
| Tool contract change | Update [tool-reference.md](tool-reference.md), then grep the tool name across KB |
| `kb_conflict` / `kb_gap` events | Weekly triage by ai-platform + owners |
| Law/regulation change | Compliance reviews `00_system/compliance-guardrails.md` and affected docs within 5 business days |
| Deprecation | Set `status: deprecated`, add "superseded by" in body, keep 90 days, then remove from index |

## 7. Quality checklist before publishing

- [ ] Frontmatter complete and valid YAML; `id` unique
- [ ] Every assumed value has an `A-xx` reference that exists in the register
- [ ] Every tool named exists in the tool reference
- [ ] At least 2 customer-friendly response examples (policy/workflow docs)
- [ ] Escalation conditions present (policy/workflow docs)
- [ ] No live prices/stock; no health claims; no PII
- [ ] Relative links resolve
- [ ] Reviewed by the owner team (and compliance if `priority: critical`)

## 8. Evaluation

Maintain a golden test set (≥ 10 utterances per folder) covering happy paths, edge cases and adversarial prompts (underage, out-of-state, health-claim fishing, promo stacking). Track: retrieval hit rate (correct doc in top-3), policy-accuracy rate, escalation precision/recall, and tool-call correctness. Re-run on every KB release.
