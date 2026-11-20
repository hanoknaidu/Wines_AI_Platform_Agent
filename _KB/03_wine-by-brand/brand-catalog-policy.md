---
id: KB-BRD-001
title: Brand Catalog Policy (Sourcing, Listing, Exclusives, Provenance, Requests)
category: brand
subcategory: policy
doc_type: policy
intents: [recommend.by_brand, product.details, stock.product_request, stock.availability]
tools: [search_products, get_product_details, get_similar_products, submit_product_request, subscribe_back_in_stock, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent, merchandising
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: merchandising
status: active
depends_on_assumptions: [A-01, A-03, A-23, A-33, A-55]
related: [KB-BRD-000, KB-STK-005, KB-STK-006, KB-SYS-003]
---

# Brand Catalog Policy

## 1. Purpose

Rules for how brands appear in our catalog and how the agent talks about them, including availability differences between stores, exclusives, label changes, provenance of collectible wines, and customer brand requests.

## 2. Policy rules

**BRD-R1: Licensed sourcing only.** Every product is bought through the licensed three-tier system (state-licensed wholesalers/distributors) for the fulfilling store. We do not sell gray-market or parallel-imported alcohol, or bottles from private individuals, except where a properly licensed channel exists and compliance approves.

**BRD-R2: Availability differs by store (A-01, A-03).** A brand may be distributed in NJ but not NY, or vice versa, because distributor rights are state-specific. The agent must never say "we carry X" without checking the customer's fulfilling location.

**BRD-R3: Brand neutrality.** The agent describes brands factually and positively or neutrally. It never disparages a brand, a producer or a competitor. It never claims a brand is "better" than another; it explains style differences.

**BRD-R4: No paid-placement claims.** If a brand is featured in a promotion, it's described as "featured" or "on sale", never as "the best" because of a supplier deal.

**BRD-R5: Factual brand claims come from the catalog record or KB profile.** Awards, scores, organic/vegan status, calorie claims and ownership are stated only if present in `get_product_details` (claims) or a reviewed KB profile (background). Ownership changes often; say "according to our records" or avoid it unless asked.

**BRD-R6: Exclusive and private-label wines.** The Store may sell exclusive or direct-import wines flagged `exclusive=true` (modeled on retailer "direct" programs). The agent may highlight them as "only at our stores" when relevant, describe them by style, and must not imply they are a famous brand.

**BRD-R7: Label redesigns and renames.** When a producer changes a label or name, the catalog keeps the same product family with `formerly_known_as`. The agent can confirm "same wine, new label" only if the catalog says so.

**BRD-R8: Discontinued brands.** A discontinued product shows `stock_status=discontinued`. The agent says so plainly, removes it from recommendations, and offers similar wines. No back-in-stock alerts for discontinued items.

**BRD-R9: Collectible provenance.** For wines tagged `collectible` or `older_vintage` (A-33), the product record states provenance (e.g., "acquired from distributor at release" or "acquired from licensed collection"). The agent shares only what the record states, never speculates about authenticity, and escalates authenticity concerns (§6).

**BRD-R10: Producer promotions and rebates.** Some producers run their own consumer promotions (e.g., mail-in rebates) where state law allows. These are run by the producer, not the Store. The agent can mention them only if `get_active_promotions` returns them, and must direct questions about rebate fulfillment to the producer.

## 3. Decision table: brand questions

| Situation | Agent response |
|---|---|
| Brand carried, in stock | Name the specific wine(s), size, live price, offer to add to cart |
| Brand carried at the other store only | "That's available at our [NY/NJ] store, but we can only deliver alcohol within the same state as the store. For your [NJ/NY] address, here are close matches…" (A-01) |
| Brand carried, out of stock | Back-in-stock alert + similar wines |
| Brand discontinued | Say so; similar wines |
| Brand not carried | Say so; describe the style from the KB profile; similar wines; offer `submit_product_request` |
| Brand sold only by the winery (mailing list, cellar door) | Explain it's sold directly by the producer; suggest similar wines; no workaround |
| Brand only legal via winery direct shipping to their state (out-of-state customer) | Out of service area (G4) |
| Customer asks "which is better, A or B?" | Explain the style difference; recommend based on the customer's taste, not a quality ranking |
| Customer asks who owns a brand | Answer only if in a reviewed profile, with "as of our latest information"; otherwise say we don't have that detail |

## 4. Workflow: brand request

1. Confirm the exact product (producer, wine name, vintage if important, size, quantity).
2. `search_products` to make sure we don't already carry it (or a different size or vintage).
3. If not carried: `submit_product_request(customer_id, product_description, quantity, fulfillment_location, contact_ok=true)`.
4. Tell the customer the expected response time (`expected_response_by`) and that sourcing depends on distributor availability in their state. **Do not promise we will get it.**
5. Offer similar in-stock options in the meantime.

## 5. Edge cases

- **Same brand, different wines.** Brands like Kendall-Jackson or Robert Mondavi have many tiers. Ask which wine or tier ("the Vintner's Reserve Chardonnay?").
- **Same name, different producers.** e.g., "Stag's Leap" (Stag's Leap Wine Cellars vs Stags' Leap Winery are different wineries). Confirm via product data.
- **Celebrity brands.** Describe the wine (style, region), not the celebrity. Avoid gossip or ownership speculation.
- **Brand's own website shows a different price.** Producer-direct pricing is a different sales channel. Our live price comes from `get_price`. See [price-matching-policy.md](../08_pricing/price-matching-policy.md) (producer-direct pricing isn't eligible).
- **"Is this the same wine as in Europe?"** Some brands make region-specific blends for different markets. Answer only from product data.

## 6. Escalation

| Trigger | Priority | Reason code |
|---|---|---|
| Customer suspects counterfeit or tampered bottle | P2 (P1 if health concern) | `authenticity_concern` |
| Supplier, brand rep or distributor contacts the agent (sales pitch, listing request) | P3 | `vendor_inquiry`. Route to merchandising; don't negotiate |
| Request to buy an entire brand allocation or for resale | P2 | `bulk_order` / `compliance.resale` |

## 7. Response examples

> "We don't carry Silver Oak at the moment. It's a polished, American-oak-aged Cabernet, so you might enjoy these two in a similar style: … I can also put in a request for our buyers. We usually reply within a few days."

> "That label looks new, but it's the same wine. The producer redesigned it this year, and our record links the two."
