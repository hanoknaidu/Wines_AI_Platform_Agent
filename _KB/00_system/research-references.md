---
id: KB-SYS-009
title: Research References and Policy Synthesis Notes
category: system
subcategory: research
doc_type: reference
intents: []
tools: []
jurisdictions: [NJ, NY, US]
audience: kb-maintainers, compliance
priority: medium
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: operations-and-compliance
status: active
depends_on_assumptions: [A-01, A-02, A-05, A-06, A-07, A-10, A-11, A-13, A-15, A-18, A-20, A-22, A-23, A-32, A-33, A-34, A-35, A-50, A-53, A-54, A-55, A-72, A-81]
related: [KB-SYS-001]
---

# Research References and Policy Synthesis Notes

> **Not for customer-facing retrieval.** Exclude this document from the agent's default `search_kb` scope (`audience` excludes `agent`). It documents where policy ideas came from so maintainers and compliance can audit them.

## 1. Method

Research covered public policy pages, regulator materials and industry guidance (November 2026). The goal was to see the **range** of practice, not to copy one retailer. For each policy area we recorded what several companies do, then chose a value for the Store and logged it as an assumption in [business-profile-and-assumptions.md](business-profile-and-assumptions.md).

**Caveats**
- Several retailer pages (Wine Library store policy, Wine.com delivery-issues page, Total Wine rewards FAQ) blocked automated fetching (HTTP 403). Their details come from search-result excerpts and should be re-verified by a person before citing.
- Legal points are summaries for business design, **not legal advice**. Compliance/counsel must confirm items listed in §4 of the assumptions register.

## 2. Retailer practices observed

| Source | Practice observed | How we used it |
|---|---|---|
| **Costco** (return policy coverage, e.g., Tasting Table, Foodie) | Generous general returns, but alcohol excluded "where prohibited by law"; no single company-wide alcohol rule; often makes good on quality problems (spoiled wine). | Jurisdiction-specific return rules (A-34/A-35); quality issues always remedied (A-32). |
| **Amazon** (shipping policy; UK age-verification pages) | Age-restricted goods require age verification or a signature on delivery; recipient verifies age at delivery; alcohol returns generally not accepted (third-party summaries, unverified). | Multipoint age verification (A-05); handoff ID rules. |
| **City Hive** (retailer platform for many NY/NJ liquor stores) | Licensed retailer is seller of record; fulfilled from the store's own inventory; age checks at entry and checkout; checkout blocks illegal destinations; delivery zones by drive time/distance with per-zone fees; driver ID verification before release; FedEx Alcohol Shipping Agreement; pickup + delivery + shipping on all plans. | Operating model (§2 profile), zones/fees (A-10), destination blocking (A-20), driver ID checks. |
| **Shopify-based stores / alcohol app vendors** | Merchant responsible for licensing, age verification, shipping and records in every jurisdiction; checkbox age gates are insufficient; USPS cannot ship alcohol; UPS/FedEx require agreements and adult signature. | Rejected checkbox-only age gates; carrier adult signature (A-15). |
| **Wine Library** (Springfield, NJ) | Suspect bottle: re-cork and keep the wine in the bottle (no empties); notify within 30 days of purchase/delivery; receipt required; 25% restocking fee on returns; no returns on beer, cider, seltzer, mixers; title passes in NJ. | 30-day defect window and keep-contents rule (A-32); NJ change-of-mind returns with restocking fee (A-34, set at 15%). |
| **Astor Wines** (New York, NY) | Wine and sake sales final; defective opened bottle exchanged for equal or greater value; unopened spirits returnable within 30 days; shipped orders: call to discuss. | NY no change-of-mind returns (A-35); defect exchanges. |
| **Flatiron Wines** (New York, NY) | Corked wine ≤ 10 years old: refund or exchange within 60 days with proof of purchase; wine older than 10 years at buyer's risk except storage damage; unopened returns generally not accepted (storage unknown); cancellations within 30 days at discretion with 15% restocking fee. | Older-vintage exception (A-33); 15% restocking fee (A-34). |
| **Gary's Wine & Marketplace** (NJ) | 10% off 6+ (some materials say 15%) on its direct-import wines; local delivery $39.99 minimum, $5 fee in radius; same-day cutoffs 6 pm weekdays/Sat, 3 pm Sunday; paid membership for free shipping; 4% restocking fee on non-defective card refunds; no fee when the issue is the retailer's error. | Delivery minimum (A-11), cutoffs (A-13), mixed-case tiers (A-50), "no fees on our error" principle. |
| **Wine.com** (largest US online wine retailer) | Under $20: automatically substitutes comparable vintage of the same type, varietal and winery; never substitutes a different wine. | Vintage substitution thresholds (A-22, set at $25). |
| **KosherWine.com / BevMo / Skyview** | Under $15 substitute without notice; over $15 email and wait 24 h; "vintage may vary" on non-vintage-specific listings. | 24-hour consent window (A-23). |
| **Total Wine & More** | Pickup by third party allowed if sharing billing last name/address (state exceptions such as Wisconsin); state-specific return limits (Kansas 24 h, defective only); navigation by region, price, trend. | Pickup rules; state-aware returns; catalog navigation (region + price + style). |
| **Bottle King** (NJ) | In-store, curbside pickup, free local delivery; loyalty app with app-only savings. | Pickup options; loyalty program design (A-53) with equal-availability rule (A-55). |
| **Vinearts / CWS / NL Liquor** (style taxonomies) | Shop by style: "Crisp & Refreshing", "Rich & Creamy", "Bold & Structured", "Smooth"; style tag on every bottle. | Taste-based category design in `01_wine-by-taste/`. |
| **Drizly (closed 2024) / marketplaces** | Marketplace model where licensed stores fulfil; third-party apps settle payment. | Reinforced "store is seller of record" model. |

## 3. Regulatory and standards references

| Topic | Reference | Key point used |
|---|---|---|
| NJ below-cost sales | N.J.A.C. 13:2-24.8; NJ ABC Advisory Notice 2026-10 (sales below cost/coupons); 2019-11 special ruling on combination offerings; RIP rulemaking petition | Discounts/coupons cannot bring price below cost; combination offers too; sale-price comparisons with "regular price" restricted (ABC handbook). A-54, G11. |
| NJ delivery | NJ ABC 2020 advisories (transit insignia); 2022 Third-Party Delivery Permit (SR 2022-15) | Delivery by licensee vehicles with transit insignia or permitted third-party delivery; workers 21+. Q-6. |
| NY Sunday hours | ABC Law §105 as amended Oct 2023 (S.2854/A.7305) | Liquor/wine stores may open 10 am – 10 pm Sundays. A-07, A-81. |
| NY direct shipping | ABC Law §79-c; Wine Institute NY DTC summary; bills S1700/A556/S3331 (retailer shipping proposals) | DTC path exists for licensed wineries, not out-of-state retailers; SLA enforcement history (Empire Wine 2014). A-01, A-02. |
| NY quantity discounts | ABC Law §101-b (inducement rules; quantity discount carve-out, 2019 text) | Quantity/case discounts customary and allowed; verify current text. A-50. |
| NY grocery/NA restrictions | Bills on grocery wine sales (not passed); NY liquor stores not allowed to sell NA versions of alcoholic beverages; A6726 (dealcoholized wine at liquor stores) pending | A-06 (NA via NJ Store only). |
| NY retail-to-retail | SLA FAQ (Chapter 613 of Laws of 2025, effective Mar 5, 2026) | Business purchases handled by staff only (G9). |
| Loyalty programs (other states) | Indiana ATC Advisory 22-04; Texas TABC MPB-014 | Programs acceptable when free and open to all customers. A-53, A-55. |
| Organic wine | USDA AMS organic labeling; NOP wine guidance | "Organic" = no added sulfites; "Made with organic grapes" = sulfites ≤ 100 ppm, no USDA seal. |
| Low-carb claims | TTB Ruling 2004-1, 2013-2 (Serving Facts), 2020-1 (tolerances); TTB newsletter Mar 2021 | "Low carb" ≤ 7 g carbs/serving plus statement of average analysis or Serving Facts. |
| Alcohol Facts rule | TTB Notice No. 237 (Jan 17, 2025), comment period extended (Apr 7, 2025) | Proposed only; do not describe as final. Q-5. |
| Non-alcoholic wine | FDA CPG 7101.04 (dealcoholized wine labeling) | <0.5% ABV statement; "alcohol-free" only if no detectable alcohol; under 7% ABV wine is FDA-labeled. |
| Champagne dosage | EU sparkling sweetness categories (multiple sources) | Brut Nature 0–3 g/L … Doux 50+ g/L. |
| Prosecco | Consorzio rules summarized by Decanter, Wine Enthusiast, Italian Wine Central | DOC vs DOCG hierarchy; Glera ≥ 85%; Rive; Cartizze. |
| Privacy | NJ Data Privacy Act (eff. Jan 15, 2025); NJ Division of Consumer Affairs FAQ; proposed NJ regulations (loyalty notices, consent design) | Rights offered to all customers (A-72); loyalty privacy notice. |
| Carriers | UPS wine shipping guide; FedEx Alcohol Shipping Agreement; ShipCompliant/Sovos guidance | Adult signature 21+ with ID; carrier attempt limits vary (A-18). |

## 4. Synthesis decisions (why we chose what we chose)

1. **Jurisdiction-aware returns** (NJ limited returns; NY none) instead of one rule: it reflects real practice in each state and teaches the agent to check `fulfillment_location` before answering.
2. **$25 vintage-substitution threshold**, between Wine.com's $20 and the more premium-leaning NYC merchants, because the Store's assortment skews to step-up and premium price bands.
3. **15% restocking fee**: between Gary's 4% (card-fee offset) and Wine Library's 25%. Matches Flatiron's cancellation fee. Store credit at full value gives customers a no-fee option.
4. **Mixed-case 10%/15% tiers**: the most common pattern across NJ/NY independents. Kept simple to reduce price-floor conflicts.
5. **21+ for non-alcoholic wine**: legal minimum ages for NA products are inconsistent and poorly documented. One age rule is simpler and safer for an alcohol retailer.
6. **No interstate shipping**: the regulatory risk for retailers is high and uneven; NJ/NY in-state fulfillment covers the target market.
