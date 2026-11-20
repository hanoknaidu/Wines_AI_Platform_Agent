---
id: KB-ROOT-000
title: Wines AI Platform Agent: Knowledge Base (README)
category: system
subcategory: root-index
doc_type: index
intents: ["*"]
tools: [search_kb]
jurisdictions: [NJ, NY]
audience: agent, kb-maintainers, ai-platform
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: ai-platform
status: active
related: [KB-SYS-001, KB-SYS-002, KB-SYS-003, KB-SYS-004, KB-SYS-005, KB-SYS-010]
---

# Wines AI Platform Agent: Knowledge Base (`_KB`)

## 1. What this is

The knowledge base for an **agentic AI wine assistant** serving an online wine and spirits retailer with licensed stores in **New Jersey and New York**. The agent:

1. understands the customer's request and classifies its **intent** ([00_system/intent-taxonomy.md](00_system/intent-taxonomy.md));
2. retrieves **policy and product knowledge** from this KB (RAG);
3. gets **live facts** (price, stock, orders, accounts, promotions) and takes **actions** only through backend tools/APIs ([00_system/tool-reference.md](00_system/tool-reference.md)), never by reading the database directly;
4. stays inside **compliance guardrails** ([00_system/compliance-guardrails.md](00_system/compliance-guardrails.md)) and **escalates** to humans when needed ([00_system/escalation-matrix.md](00_system/escalation-matrix.md)).

**The KB never contains live data.** It holds rules, procedures, definitions and wine knowledge. Prices, inventory and order state always come from tools.

## 2. Folder structure

```
_KB/
├── README.md                              ← you are here (root index)
├── 00_system/                             ← cross-cutting rules: assumptions, guardrails, tools, intents, escalation, tone
├── 01_wine-by-taste/                      ← taste framework, interview flow, 8 style categories, food pairing
├── 02_wine-by-region/                     ← appellation systems + France, Italy, Iberia, California, PNW/NY/NJ, Southern Hemisphere, others
├── 03_wine-by-brand/                      ← brand catalog policy, brand references by origin, brand template
├── 04_sparkling-champagne-prosecco/       ← methods, Champagne, Prosecco, sweetness scale, occasions & handling
├── 05_low-calorie-and-better-for-you/     ← calorie guide, labeling-claims policy, dietary questions
├── 06_organic-biodynamic-natural/         ← certifications, sulfites & additives, tag verification, FAQ
├── 07_non-alcoholic-wines/                ← NA guide, sale policy & age rules, recommendations & FAQ
├── 08_pricing/                            ← pricing policy, price bands, errors, price matching, taxes & fees
├── 09_stock-and-availability/             ← status definitions, vintages, substitutions, pre-arrivals, special orders, onboarding, limits
├── 10_discounts-and-promotions/           ← stacking rules, mixed case, promo codes, Rewards, seasonal, troubleshooting
├── 11_orders-delivery-pickup/             ← payment, status lifecycle, changes, delivery, pickup, ID at handoff, shipping, failed delivery, gifts
├── 12_returns-refunds-damages/            ← master returns policy, damage, corked/flawed, wrong/missing, refunds
├── 13_account-management/                 ← sign-up & age verification, login, profile, history, communications, privacy, fraud
└── 14_general-faqs/                       ← store info, responsible drinking, storage & serving, gift cards, events, top FAQ, out-of-scope
```

Every folder has a `README.md` index that maps intents → documents → tools.

## 3. Read these first

| Priority | Document | Why |
|---|---|---|
| 1 | [Business Profile and Assumptions Register](00_system/business-profile-and-assumptions.md) | Every business-specific number (fees, windows, thresholds, limits) is an assumption with an ID (`A-xx`). Change values here first |
| 2 | [Compliance Guardrails](00_system/compliance-guardrails.md) | Absolute rules (21+, intoxication, NJ/NY only, health claims, privacy) |
| 3 | [Agent Operating Principles](00_system/agent-operating-principles.md) | Source-of-truth hierarchy, confirmation rules, things never to do |
| 4 | [Tool and API Reference](00_system/tool-reference.md) | Contract for the Backend APIs/Tools component (phase 2) |
| 5 | [Intent Taxonomy](00_system/intent-taxonomy.md) | Intent IDs, routing to folders and tools |
| 6 | [Escalation Matrix](00_system/escalation-matrix.md) | P1–P3 triggers, handoff template |

## 4. Document conventions

- **YAML frontmatter on every file**: `id`, `title`, `category`, `subcategory`, `doc_type`, `intents`, `tools`, `jurisdictions`, `audience`, `priority`, `version`, `last_reviewed`, `review_cycle_days`, `owner`, `status`, `depends_on_assumptions`, `related`. Full spec: [kb-authoring-and-maintenance-standards.md](00_system/kb-authoring-and-maintenance-standards.md).
- **Policy/workflow documents** follow a fixed shape: purpose → numbered rules (e.g., `RTN-R1`) → decision tables → step-by-step workflow with tool calls → edge cases → escalation → customer-friendly response examples.
- **Product-knowledge documents** follow: what it is → key wines → taste profile → indicative price bands → how to search/recommend → misconceptions/edge cases → sample dialogue.
- **Assumptions** are referenced inline as `(A-xx)` and listed in `depends_on_assumptions`, so a value change can be traced with `grep -r "A-xx" _KB/`.
- **Open compliance questions** (Q-1 … Q-6) are listed in the assumptions register and must be resolved before launch.

## 5. RAG integration guide

**Ingestion**
1. Parse frontmatter; store all fields as chunk metadata.
2. Chunk on `##` headings (sections are written to stand alone; ~150–600 words). Keep tables intact within a chunk. Prepend the document `title` and section heading to each chunk's text.
3. Embed chunk text; index metadata for filtering.

**Retrieval**
- Filter by `category` and `intents` from the classifier's routing ([intent-taxonomy.md](00_system/intent-taxonomy.md) §2), and by `jurisdictions` containing the customer's fulfilling state (`NJ` or `NY`).
- Exclude `audience` values that don't include `agent` (e.g., research references, authoring standards, templates) from customer-facing retrieval.
- Boost `priority: critical` documents on ties; resolve conflicts by priority, then `last_reviewed` ([agent-operating-principles.md](00_system/agent-operating-principles.md) §3.1).
- **Always-on context** (system prompt or pinned retrieval): compliance guardrails, operating principles, persona/tone, and a compact summary of the assumptions register.

**Generation**
- Live data from tools overrides KB numbers. Never quote prices, stock or fees from the KB.
- Cite rule IDs internally (for logs/evals), not to customers.

**Evaluation** (see the authoring standards, §8)
- Golden sets per folder; adversarial cases in [out-of-scope-and-sensitive-requests.md](14_general-faqs/out-of-scope-and-sensitive-requests.md) §3.
- Track retrieval hit rate, policy accuracy, escalation precision/recall and tool-call correctness.

## 6. Maintenance

- Owners and review cycles are in each file's frontmatter; compliance-critical documents review every 60 days.
- Changes: update the assumptions register → dependent documents → bump `version` and `last_reviewed`.
- `kb_conflict` / `kb_gap` events logged by the agent are triaged weekly.
- Research sources and synthesis decisions: [research-references.md](00_system/research-references.md).

## 7. Document index

### `00_system/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-SYS-001 | [Business Profile and Assumptions Register](00_system/business-profile-and-assumptions.md) | reference | critical |
| KB-SYS-002 | [Agent Operating Principles and Source-of-Truth Hierarchy](00_system/agent-operating-principles.md) | policy | critical |
| KB-SYS-003 | [Compliance Guardrails (Alcohol Sales, Age, Responsible Service)](00_system/compliance-guardrails.md) | policy | critical |
| KB-SYS-004 | [Tool and API Reference (Agent ↔ Backend Contract)](00_system/tool-reference.md) | reference | critical |
| KB-SYS-005 | [Intent Taxonomy and Routing Map](00_system/intent-taxonomy.md) | reference | critical |
| KB-SYS-006 | [Escalation Matrix and Human Handoff Procedure](00_system/escalation-matrix.md) | workflow | critical |
| KB-SYS-007 | [Agent Persona, Voice and Tone](00_system/agent-persona-and-tone.md) | guide | high |
| KB-SYS-008 | [Wine and Store Glossary (Plain-Language Definitions)](00_system/glossary.md) | reference | medium |
| KB-SYS-009 | [Research References and Policy Synthesis Notes](00_system/research-references.md) | reference | medium |
| KB-SYS-010 | [KB Authoring, Metadata and Maintenance Standards](00_system/kb-authoring-and-maintenance-standards.md) | reference | high |

### `01_wine-by-taste/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-TST-000 | [Wine by Taste: Folder Index](01_wine-by-taste/README.md) | index | high |
| KB-TST-001 | [Taste Profile Framework and Customer-Language Mapping](01_wine-by-taste/taste-profile-framework.md) | reference | high |
| KB-TST-002 | [Taste Discovery Conversation Flow (Interview, Clarify, Refine)](01_wine-by-taste/taste-discovery-conversation-flow.md) | workflow | high |
| KB-TST-003 | [Light & Crisp White Wines](01_wine-by-taste/light-crisp-whites.md) | guide | medium |
| KB-TST-004 | [Aromatic & Off-Dry White Wines](01_wine-by-taste/aromatic-and-off-dry-whites.md) | guide | medium |
| KB-TST-005 | [Rich & Full-Bodied White Wines](01_wine-by-taste/rich-full-bodied-whites.md) | guide | medium |
| KB-TST-006 | [Rosé Wines (Dry, Fuller and Off-Dry/Blush)](01_wine-by-taste/rose-wines.md) | guide | medium |
| KB-TST-007 | [Light & Fruity Red Wines](01_wine-by-taste/light-fruity-reds.md) | guide | medium |
| KB-TST-008 | [Smooth & Medium-Bodied Red Wines](01_wine-by-taste/medium-smooth-reds.md) | guide | medium |
| KB-TST-009 | [Bold & Full-Bodied Red Wines](01_wine-by-taste/bold-full-bodied-reds.md) | guide | medium |
| KB-TST-010 | [Sweet, Dessert and Fortified Wines](01_wine-by-taste/sweet-dessert-and-fortified-wines.md) | guide | medium |
| KB-TST-011 | [Food and Wine Pairing Guide](01_wine-by-taste/food-pairing-guide.md) | guide | medium |

### `02_wine-by-region/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-REG-000 | [Wine by Region: Folder Index](02_wine-by-region/README.md) | index | high |
| KB-REG-001 | [Region Taxonomy, Appellation Systems and Label Terms](02_wine-by-region/region-taxonomy-and-label-terms.md) | reference | high |
| KB-REG-002 | [France: Regional Wine Guide](02_wine-by-region/france.md) | guide | medium |
| KB-REG-003 | [Italy: Regional Wine Guide](02_wine-by-region/italy.md) | guide | medium |
| KB-REG-004 | [Spain and Portugal: Regional Wine Guide](02_wine-by-region/spain-and-portugal.md) | guide | medium |
| KB-REG-005 | [USA, California: Regional Wine Guide](02_wine-by-region/usa-california.md) | guide | medium |
| KB-REG-006 | [USA, Oregon, Washington, New York and New Jersey: Regional Guide](02_wine-by-region/usa-pacific-northwest-new-york-and-new-jersey.md) | guide | medium |
| KB-REG-007 | [Southern Hemisphere: Argentina, Chile, Australia, New Zealand, South Africa](02_wine-by-region/southern-hemisphere.md) | guide | medium |
| KB-REG-008 | [Germany, Austria and Other Regions (Greece, Hungary, Eastern Med, England, Canada)](02_wine-by-region/germany-austria-and-emerging-regions.md) | guide | low |

### `03_wine-by-brand/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-BRD-000 | [Wine by Brand: Folder Index](03_wine-by-brand/README.md) | index | high |
| KB-BRD-001 | [Brand Catalog Policy (Sourcing, Listing, Exclusives, Provenance, Requests)](03_wine-by-brand/brand-catalog-policy.md) | policy | high |
| KB-BRD-002 | [Champagne Houses and Sparkling Wine Brands](03_wine-by-brand/champagne-and-sparkling-houses.md) | reference | medium |
| KB-BRD-003 | [US Wine Brands (California, Washington, Oregon)](03_wine-by-brand/us-brands.md) | reference | medium |
| KB-BRD-004 | [European Wine Brands and Estates (France, Italy, Spain, Portugal, Germany)](03_wine-by-brand/european-brands.md) | reference | medium |
| KB-BRD-005 | [Southern Hemisphere Wine Brands (NZ, Australia, Argentina, Chile, South Africa)](03_wine-by-brand/southern-hemisphere-brands.md) | reference | medium |
| KB-BRD-006 | [Brand Profile Template (for adding new brands)](03_wine-by-brand/brand-profile-template.md) | template | low |

### `04_sparkling-champagne-prosecco/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-SPK-000 | [Sparkling, Champagne and Prosecco: Folder Index](04_sparkling-champagne-prosecco/README.md) | index | high |
| KB-SPK-001 | [Sparkling Wine Styles and Production Methods](04_sparkling-champagne-prosecco/sparkling-styles-and-production-methods.md) | guide | medium |
| KB-SPK-002 | [Champagne: Appellation, Styles, Labels and Buying Guide](04_sparkling-champagne-prosecco/champagne.md) | guide | high |
| KB-SPK-003 | [Prosecco: DOC, DOCG, Styles and Buying Guide](04_sparkling-champagne-prosecco/prosecco.md) | guide | high |
| KB-SPK-004 | [Sparkling Wine Sweetness Scale (Brut Nature to Doux)](04_sparkling-champagne-prosecco/sparkling-sweetness-scale.md) | reference | high |
| KB-SPK-005 | [Sparkling Wine for Occasions, Party Quantities, Gifting and Safe Handling](04_sparkling-champagne-prosecco/sparkling-occasions-gifting-and-handling.md) | guide | medium |

### `05_low-calorie-and-better-for-you/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-LCW-000 | [Low-Calorie and Better-for-You Wines: Folder Index](05_low-calorie-and-better-for-you/README.md) | index | high |
| KB-LCW-001 | [Low-Calorie Wine Guide](05_low-calorie-and-better-for-you/low-calorie-wine-guide.md) | guide | high |
| KB-LCW-002 | [Labeling Claims and Nutrition Data Policy (What the Agent May Say)](05_low-calorie-and-better-for-you/labeling-claims-and-nutrition-policy.md) | policy | critical |
| KB-LCW-003 | [Dietary Questions: Sugar, Carbs, Keto, Gluten, Vegan, Sulfites, Histamines, Pregnancy](05_low-calorie-and-better-for-you/dietary-questions-sugar-keto-gluten-vegan.md) | faq | high |

### `06_organic-biodynamic-natural/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-ORG-000 | [Organic, Biodynamic, Sustainable and Natural Wines: Folder Index](06_organic-biodynamic-natural/README.md) | index | high |
| KB-ORG-001 | [Organic, Biodynamic, Sustainable, Natural and Vegan: Definitions and Certifications](06_organic-biodynamic-natural/certifications-and-definitions.md) | reference | high |
| KB-ORG-002 | [Sulfites, Additives and Ingredient Labeling](06_organic-biodynamic-natural/sulfites-and-additives.md) | reference | high |
| KB-ORG-003 | [Catalog Tagging and Verification Policy (Organic, Biodynamic, Sustainable, Vegan, Low-Intervention)](06_organic-biodynamic-natural/catalog-tagging-and-verification-policy.md) | policy | high |
| KB-ORG-004 | [Organic and Natural Wine: Customer FAQ](06_organic-biodynamic-natural/organic-natural-customer-faq.md) | faq | medium |

### `07_non-alcoholic-wines/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-NAW-000 | [Non-Alcoholic Wines: Folder Index](07_non-alcoholic-wines/README.md) | index | high |
| KB-NAW-001 | [Non-Alcoholic Wine Guide (Definitions, Production, Taste, Brands)](07_non-alcoholic-wines/non-alcoholic-wine-guide.md) | guide | high |
| KB-NAW-002 | [Non-Alcoholic Wine Sale Policy, Age Rules and Sensitive Situations](07_non-alcoholic-wines/sale-policy-and-age-rules.md) | policy | critical |
| KB-NAW-003 | [Non-Alcoholic Wine Recommendations by Occasion and FAQ](07_non-alcoholic-wines/non-alcoholic-recommendations-and-faq.md) | faq | medium |

### `08_pricing/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-PRC-000 | [Pricing: Folder Index](08_pricing/README.md) | index | high |
| KB-PRC-001 | [Pricing Policy](08_pricing/pricing-policy.md) | policy | critical |
| KB-PRC-002 | [Price Bands and Budget Guidance](08_pricing/price-bands-and-budget-guidance.md) | guide | high |
| KB-PRC-003 | [Pricing Errors, Price Drops and Charge Disputes](08_pricing/price-errors-and-adjustments.md) | policy | high |
| KB-PRC-004 | [Price Matching Policy](08_pricing/price-matching-policy.md) | policy | high |
| KB-PRC-005 | [Taxes, Fees and How Order Totals Are Calculated](08_pricing/taxes-fees-and-order-totals.md) | reference | high |

### `09_stock-and-availability/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-STK-000 | [Stock and Availability: Folder Index](09_stock-and-availability/README.md) | index | high |
| KB-STK-001 | [Inventory Status Definitions and Agent Responses](09_stock-and-availability/inventory-status-definitions.md) | reference | critical |
| KB-STK-002 | [Vintage Policy (Display, Changes and Substitution)](09_stock-and-availability/vintage-policy.md) | policy | high |
| KB-STK-003 | [Out-of-Stock Handling, Substitutions and Partial Fulfillment](09_stock-and-availability/out-of-stock-and-substitutions.md) | workflow | high |
| KB-STK-004 | [Pre-Arrivals, Futures (En Primeur) and Allocations](09_stock-and-availability/pre-arrivals-futures-and-allocations.md) | policy | high |
| KB-STK-005 | [Special Orders and Product Requests ("Can you get X for me?")](09_stock-and-availability/special-orders-and-product-requests.md) | workflow | high |
| KB-STK-006 | [New Product Onboarding and Catalog Data Standards](09_stock-and-availability/new-product-onboarding-and-catalog-standards.md) | workflow | high |
| KB-STK-007 | [Purchase Limits, Bulk Orders and Resale Prevention](09_stock-and-availability/purchase-limits-and-bulk-orders.md) | policy | high |

### `10_discounts-and-promotions/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-DSC-000 | [Discounts and Promotions: Folder Index](10_discounts-and-promotions/README.md) | index | high |
| KB-DSC-001 | [Discount Policy Overview and Stacking Rules](10_discounts-and-promotions/discount-policy-overview.md) | policy | critical |
| KB-DSC-002 | [Mixed-Case and Volume Discounts](10_discounts-and-promotions/mixed-case-and-volume-discounts.md) | policy | high |
| KB-DSC-003 | [Promo Codes, Coupons, First-Order and Referral Offers](10_discounts-and-promotions/promo-codes-and-coupons.md) | policy | high |
| KB-DSC-004 | [Rewards Loyalty Program](10_discounts-and-promotions/rewards-loyalty-program.md) | policy | high |
| KB-DSC-005 | [Seasonal Sales, Featured Promotions and In-Store Events](10_discounts-and-promotions/seasonal-sales-and-events.md) | guide | medium |
| KB-DSC-006 | [Discount Troubleshooting (Codes, Case Discount, Rewards)](10_discounts-and-promotions/discount-troubleshooting.md) | workflow | high |

### `11_orders-delivery-pickup/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-ORD-000 | [Orders, Delivery and Pickup: Folder Index](11_orders-delivery-pickup/README.md) | index | high |
| KB-ORD-001 | [Order Placement and Payment](11_orders-delivery-pickup/order-placement-and-payment.md) | policy | high |
| KB-ORD-002 | [Order Status Lifecycle](11_orders-delivery-pickup/order-status-lifecycle.md) | reference | critical |
| KB-ORD-003 | [Order Changes and Cancellations](11_orders-delivery-pickup/order-changes-and-cancellations.md) | policy | high |
| KB-ORD-004 | [Local Delivery Policy](11_orders-delivery-pickup/local-delivery-policy.md) | policy | high |
| KB-ORD-005 | [In-Store and Curbside Pickup Policy](11_orders-delivery-pickup/pickup-policy.md) | policy | high |
| KB-ORD-006 | [Age Verification at Handoff (Accepted IDs and Refusals)](11_orders-delivery-pickup/age-verification-at-handoff.md) | policy | critical |
| KB-ORD-007 | [In-State Shipping Policy (NJ and NY Only)](11_orders-delivery-pickup/in-state-shipping-policy.md) | policy | high |
| KB-ORD-008 | [Failed Delivery, Redelivery and Returned-to-Store Orders](11_orders-delivery-pickup/failed-delivery-and-redelivery.md) | workflow | high |
| KB-ORD-009 | [Gift Orders (Sending Wine to Someone Else)](11_orders-delivery-pickup/gift-orders.md) | policy | high |

### `12_returns-refunds-damages/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-RTN-000 | [Returns, Refunds and Damages: Folder Index](12_returns-refunds-damages/README.md) | index | critical |
| KB-RTN-001 | [Returns Policy (Master Policy and Decision Tree)](12_returns-refunds-damages/returns-policy.md) | policy | critical |
| KB-RTN-002 | [Damaged or Broken Items on Delivery](12_returns-refunds-damages/damaged-or-broken-items.md) | workflow | critical |
| KB-RTN-003 | [Corked or Flawed Wine (Fault Identification and Claims)](12_returns-refunds-damages/corked-or-flawed-wine.md) | workflow | critical |
| KB-RTN-004 | [Wrong or Missing Items (Including "Delivered but Not Received")](12_returns-refunds-damages/wrong-or-missing-items.md) | workflow | high |
| KB-RTN-005 | [Refunds and Store Credit](12_returns-refunds-damages/refunds-and-store-credit.md) | policy | high |

### `13_account-management/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-ACC-000 | [Account Management: Folder Index](13_account-management/README.md) | index | high |
| KB-ACC-001 | [Account Creation and Age Verification](13_account-management/account-creation-and-age-verification.md) | policy | critical |
| KB-ACC-002 | [Login, Password and Account Security](13_account-management/login-password-and-security.md) | workflow | high |
| KB-ACC-003 | [Profile, Saved Addresses and Payment Methods](13_account-management/profile-addresses-and-payment-methods.md) | workflow | high |
| KB-ACC-004 | [Order History, Reorders, Favorites and Taste Profile](13_account-management/order-history-reorders-and-taste-profile.md) | workflow | medium |
| KB-ACC-005 | [Communication Preferences (Email, SMS, Push)](13_account-management/communication-preferences.md) | policy | medium |
| KB-ACC-006 | [Privacy Rights, Data Requests and Account Deletion](13_account-management/privacy-rights-and-account-deletion.md) | policy | critical |
| KB-ACC-007 | [Account Takeover, Unauthorized Orders and Fraud](13_account-management/account-takeover-and-fraud.md) | workflow | critical |

### `14_general-faqs/`

| ID | Document | Type | Priority |
|---|---|---|---|
| KB-FAQ-000 | [General FAQs: Folder Index](14_general-faqs/README.md) | index | medium |
| KB-FAQ-001 | [Store Information, Hours and Contact Channels](14_general-faqs/store-information-and-contact.md) | reference | medium |
| KB-FAQ-002 | [Responsible Drinking and Safety](14_general-faqs/responsible-drinking-and-safety.md) | policy | critical |
| KB-FAQ-003 | [Wine Storage, Serving and Care](14_general-faqs/wine-storage-serving-and-care.md) | guide | medium |
| KB-FAQ-004 | [Gift Cards](14_general-faqs/gift-cards.md) | policy | medium |
| KB-FAQ-005 | [Events, Tastings and Corporate Orders](14_general-faqs/events-tastings-and-corporate-orders.md) | workflow | medium |
| KB-FAQ-006 | [General FAQ (Top Customer Questions)](14_general-faqs/general-faq.md) | faq | high |
| KB-FAQ-007 | [Out-of-Scope, Sensitive and Adversarial Requests](14_general-faqs/out-of-scope-and-sensitive-requests.md) | policy | critical |
