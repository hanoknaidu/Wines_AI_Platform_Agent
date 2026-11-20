---
id: KB-ORG-003
title: Catalog Tagging and Verification Policy (Organic, Biodynamic, Sustainable, Vegan, Low-Intervention)
category: organic
subcategory: verification-policy
doc_type: policy
intents: [product.details, recommend.organic_natural]
tools: [get_product_details, log_event, create_support_ticket, escalate_to_human]
jurisdictions: [NJ, NY]
audience: catalog-team, agent, compliance
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: merchandising
status: active
related: [KB-ORG-001, KB-ORG-002, KB-LCW-002, KB-STK-006, KB-BRD-001]
---

# Catalog Tagging and Verification Policy

## 1. Purpose

Customers trust "organic", "biodynamic", "vegan" and similar tags. A wrong tag misleads customers and creates regulatory and reputational risk. This policy defines what evidence is required before a tag appears, how long it's valid, and how disputes are handled. The agent relies on these tags being trustworthy and must describe the **evidence level** honestly.

## 2. Tag types and evidence requirements

| Tag (`certifications[]` / `attributes`) | Evidence required (`evidence_ref`) | Display wording |
|---|---|---|
| `usda_organic` | Label shows USDA seal or "organic wine" statement + certifier name; certificate on file or in USDA Organic Integrity Database | "USDA Certified Organic" |
| `made_with_organic_grapes` | Label statement + certifier name | "Made with organic grapes (certified)" |
| `eu_organic` | Euro-leaf logo / certificate (body + code) | "EU certified organic" |
| `demeter` / `biodyvin` | Certificate or certification mark on label | "Certified biodynamic (Demeter)" |
| Sustainability (e.g., `ccsw`, `sip`, `lodi_rules`, `napa_green`, `live`, `swnz`, `hve`, `b_corp`, `roc`) | Logo on label or program listing | "Certified sustainable (program)" |
| `vegan` (certified) | Certification mark or certificate | "Certified vegan" |
| `vegan` (declared) | Written producer/importer declaration on fining and processing aids | "Vegan per the producer" |
| `practicing_organic` | Producer declaration (not certified) | "Farmed organically per the producer (not certified)" |
| `no_added_sulfites` | Label statement or tech sheet | "No sulfites added (per producer)" |
| `low_intervention` | Producer tech sheet stating ≥ 3 of: organic/biodynamic farming, native yeast, no additives beyond SO₂, unfined, unfiltered, ≤ 30 mg/L added SO₂ | "Low-intervention" with practices listed |
| `vin_methode_nature` | Logo on label | "Vin Méthode Nature" |
| `kosher`, `kosher_for_passover`, `mevushal` | Hechsher (certification symbol) on label | Exact designation |

## 3. Rules

**ORG-R1: No evidence, no tag.** Marketing copy, distributor sell-sheets without certification details, or third-party websites are not sufficient for certification tags.

**ORG-R2: Vintage and validity.** Certifications are tied to the producer/vintage. Each tag has `verified_at` and `valid_until` (certificate expiry or 24 months, whichever is sooner). Expired tags are **hidden** automatically until re-verified.

**ORG-R3: New vintage = re-check.** When a new vintage arrives (see [vintage-policy.md](../09_stock-and-availability/vintage-policy.md)), catalog staff confirm the label still carries the claim.

**ORG-R4: Wording follows evidence level.** "Certified" only for certification evidence; "per the producer" for declarations.

**ORG-R5: Storefront filters** use certification tags; "practicing organic" items appear under "Organic" filters only in a clearly labeled sub-group ("Organically farmed, not certified").

**ORG-R6: Disputes.** Any credible customer report that a tag is wrong is logged and reviewed within 5 business days; the tag may be suspended during review.

## 4. Agent workflow: certification questions

1. `get_product_details(sku)` → read `certifications[]` with `type`, `certifier`, `verified_at`.
2. Answer with the exact evidence level and certifier: "It's USDA Certified Organic (certified by …)."
3. If the customer says the bottle doesn't show the claim, or shows a different one:
   - Thank them; ask for a photo of the label if convenient (`request_evidence_upload` is for orders; for catalog issues, the customer can attach it to a ticket).
   - `log_event("kb_conflict", {sku, field:"certifications", report})` and `create_support_ticket(category="catalog_correction", priority="P3")`.
   - If the customer **bought because of the claim** and the claim is wrong, treat the purchase as **our error**: eligible for return/refund regardless of state (see [returns-policy.md](../12_returns-refunds-damages/returns-policy.md) RTN-R1), P2 review.

## 5. Edge cases

- **Different vintage on the shelf than listed**: certification may differ by vintage. Check the label.
- **Importer-specific labels**: US labels may differ from the EU version. US label rules decide wording ("made with organic grapes").
- **"Organic" in a brand name** without certification: the agent must not call it certified.
- **Producer loses certification**: tags removed; the agent says "it was previously certified; our current records don't show an active certification".

## 6. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Customer reports an allergic or other health reaction linked to a claim ("vegan", "no added sulfites", "kosher") | P1 | `safety_crisis` | Suggest medical attention; don't speculate about the cause (G7) |
| Customer mentions false-advertising complaints to a regulator (e.g., the USDA National Organic Program) or legal action | P1 | `legal_matter` | Don't discuss whether the claim was lawful |
| Customer bought because of a claim that turns out to be wrong (§4 step 3) | P2 | `claim_dispute` | This is our error: a return or refund is available regardless of state (RTN-R1). Log `kb_conflict` |
| Wrong kosher or kosher-for-Passover designation on an order for a religious occasion | P2 | `claim_dispute` | Mention the occasion date in the summary so it's handled quickly |
| Same tag error reported by several customers, or across several SKUs from one producer or importer | P2 | `create_support_ticket(category="catalog_correction")` | List the SKUs; the tags may be suspended during review (ORG-R6) |
| A single credible tag report with no purchase affected | P3 | `create_support_ticket(category="catalog_correction")` | Plus `log_event("kb_conflict")` as in §4 |

**Handle without escalating:** explaining evidence levels and certifiers, "practicing organic" vs certified wording (ORG-R4), vintage differences (check the label) and suggesting certified alternatives.

## 7. Response examples

> "Yes, that wine is certified biodynamic by Demeter, and the grapes are also certified organic. Our records were last verified in March."

> "The producer says they farm organically, but the wine isn't certified, so I can't call it certified organic. If certification matters to you, here are three certified organic options in a similar style: …"
