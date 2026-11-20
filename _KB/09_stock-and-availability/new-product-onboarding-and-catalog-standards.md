---
id: KB-STK-006
title: New Product Onboarding and Catalog Data Standards
category: stock
subcategory: catalog-operations
doc_type: workflow
intents: [stock.product_request, product.details, stock.availability]
tools: [get_product_details, search_products, log_event, create_support_ticket, escalate_to_human]
jurisdictions: [NJ, NY]
audience: merchandising, catalog-team, agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: merchandising
status: active
depends_on_assumptions: [A-01, A-03, A-06, A-22, A-23, A-44, A-45]
related: [KB-TST-001, KB-REG-001, KB-ORG-003, KB-LCW-002, KB-BRD-001, KB-STK-002]
---

# New Product Onboarding and Catalog Data Standards

## 1. Purpose

Defines how a new wine moves from supplier pitch to sellable listing, and the **data standards** every listing must meet so search, filters and the AI agent work correctly. The agent uses this to answer "how do you choose wines?", "when will the new vintage be online?" and catalog-correction issues. Catalog staff use it as their operating procedure.

## 2. Onboarding stages

| Stage | Owner | What happens | Exit criteria |
|---|---|---|---|
| **1. Sourcing** | Buyer | Product comes from a distributor presentation, customer requests, or a category gap analysis | Product + in-state distributor identified |
| **2. Evaluation** | Buyer + tasting panel | Tasting (quality, style typicity), price-to-quality, fit with assortment, demand signals (requests, search terms with no results), margin | Approved for listing, by store (NJ, NY, or both) |
| **3. Compliance check** | Compliance | Product must be registered/approved for sale in the state (NY SLA brand label registration; NJ ABC brand registration), with a federal label approval (TTB COLA) for wines in interstate commerce; NA products checked for jurisdiction rules (A-06) | `sellable_in_jurisdiction` set per store |
| **4. Item creation** | Catalog team | SKU per producer × wine × vintage-policy × size × pack; UPC; POS item mapped per store | SKU live in POS and e-commerce (inactive) |
| **5. Data enrichment** | Catalog team | Attributes (§3), description, photography, taste profile, tags, evidence files | Passes data quality checklist (§5) |
| **6. Pricing** | Pricing team | Shelf price per store (A-03, A-45), floor checks | Price active |
| **7. Receiving** | Store operations | Physical receipt, inspection (damage, vintage, label match), shelf/stockroom placement; quantity synced to POS | `in_stock` |
| **8. Launch** | Merchandising | "New Arrival" badge for 30 days; optional feature or email; agent recommendations include it when it fits | Listed |
| **9. Lifecycle** | Merchandising | Vintage changes (§4), re-verification of claims, delisting/discontinuation | — |

## 3. Required catalog attributes

| Group | Attributes | Standard |
|---|---|---|
| Identity | producer, wine name/cuvée, brand, vintage (or NV), size_ml, pack (single, 3-pack, gift box, case), UPC | Producer and cuvée as on the label; accents preserved; `aliases` for search |
| Place | `region_path` (country > region > sub-region > appellation), `world` | Most specific legal appellation on the label (see [region-taxonomy-and-label-terms.md](../02_wine-by-region/region-taxonomy-and-label-terms.md)) |
| Composition | grapes with % if known, color, `sparkling`, method, `sweetness_label` (for sparkling) | From label or tech sheet |
| Taste | `sweetness`, `body`, `acidity`, `tannin`, `oak`, `fruit_profile`, `style_tag`, `alcohol_level` | Assigned per [taste-profile-framework.md](../01_wine-by-taste/taste-profile-framework.md); tasting-panel validated for top sellers |
| Analysis | ABV (label), `residual_sugar_gl` (if known), `nutrition{}` with `source` | Only from label/tech sheet/lab (LCW policy) |
| Claims | `certifications[]` with evidence, `attributes` (vegan, low_intervention, kosher…) | Evidence rules in [catalog-tagging-and-verification-policy.md](../06_organic-biodynamic-natural/catalog-tagging-and-verification-policy.md) |
| Accolades | source, score, **vintage** | Only published scores for that exact vintage |
| Commerce | `price_band`, `vintage_specific`, `final_sale`, `allocation_limit`, `case_discount_eligible`, `exclusive` | Vintage-specific if $25+ (A-23) or collectible |
| Content | Description (60–120 words), tasting notes, food pairing, serving temperature | Plain language first; no health claims; no superlatives as fact |
| Media | Front label image of the **current vintage** where possible | If the image shows a different vintage, add "label image may show a previous vintage" |

## 4. Vintage changes

1. Receiving detects a new vintage (label check).
2. If the listing is **not vintage-specific**: update `vintage`, keep the SKU, re-verify claims/nutrition/accolades (remove scores from the old vintage).
3. If **vintage-specific**: create a **new SKU** for the new vintage; the old SKU goes `out_of_stock`/`discontinued` when sold through.
4. Notify the agent ecosystem: product data updates propagate to `get_product_details` immediately; the KB doesn't change.

## 5. Data quality checklist (before go-live)

- [ ] Correct store assignment and `sellable_in_jurisdiction`
- [ ] All required attributes filled; taste axes complete
- [ ] Claims have evidence; no unverifiable claims in the description
- [ ] Vintage and image consistent (or disclaimer)
- [ ] ABV and size match the label
- [ ] Price set and floor-checked; band computed
- [ ] Search test: product appears for its name, producer, grape, region and style tag
- [ ] Agent test: `search_products` with its taste profile returns it in the top 20 for a matching query

## 6. Agent-facing guidance

- **"How do you pick your wines?"** "Our buyers taste and evaluate wines from licensed distributors in each state, looking at quality, value and what customers ask for. Customer requests really do influence what we stock."
- **"When will the new vintage be on the site?"** If `coming_soon` or `next_arrival_estimate` exists, share it as an estimate; otherwise say new vintages are added when they arrive at the store and pass our checks.
- **Catalog data looks wrong** (wrong vintage, ABV, region, photo, claim): thank the customer, `log_event("kb_conflict", {sku, field, report})`, and `create_support_ticket(category="catalog_correction", priority="P3")`. If the customer bought based on wrong data, treat it as our error for returns (RTN-R1).

## 7. Escalation

**Agent-side**

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Customer reports a health reaction and the listing's ABV, allergen or additive data seems wrong | P1 | `safety_crisis` | Suggest medical attention; record the SKU and what the label says |
| An order contains a product not sellable in the customer's state (e.g., NA wine on an NY order, A-06) | P2 | `compliance_order_review` | Don't cancel the order yourself; compliance decides |
| Customer bought based on wrong catalog data (vintage, size, ABV, claim) | P2 | `claim_review` | Treat it as our error for returns (RTN-R1); log `kb_conflict` |
| Size or pack error that affects the price charged (e.g., a 375 ml priced as 750 ml) | P2 | `pricing_dispute` | Follow [price-errors-and-adjustments.md](../08_pricing/price-errors-and-adjustments.md) |
| Routine catalog error (photo, region, typo, description) | P3 | `create_support_ticket(category="catalog_correction")` | Plus `log_event("kb_conflict")` as in §6 |
| A supplier, distributor or winery contacts the agent to pitch a product | P3 | `create_support_ticket(category="vendor_inquiry")` | Don't discuss terms, prices or listing decisions |

**Staff-side:** a listing that fails the compliance check (§2 stage 3), or carries a claim without evidence (§5), doesn't go live. Route it to compliance, or remove the claim. There is no override for launch dates or promotions.

**Handle without escalating:** "how do you pick your wines?", new-vintage timing questions (share estimates only) and back-in-stock alerts.

## 8. Response example

> "Thanks for catching that. The photo shows the 2021 label, but the wine we're selling is the 2022. I've flagged it so our catalog team can update the image. If the vintage matters for your purchase, the listing's vintage line is what you'll receive."
