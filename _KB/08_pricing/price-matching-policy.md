---
id: KB-PRC-004
title: Price Matching Policy
category: pricing
subcategory: price-match
doc_type: policy
intents: [price.match_request, price.discrepancy]
tools: [get_price, search_products, submit_price_match_request, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent, pricing-team
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: pricing
status: active
depends_on_assumptions: [A-26, A-43, A-54, A-55, A-62]
related: [KB-PRC-001, KB-PRC-003, KB-SYS-003]
---

# Price Matching Policy

## 1. Purpose

Customers sometimes find the same wine cheaper elsewhere. A limited, human-approved price match keeps us competitive while respecting state rules: NJ prohibits retail sales below cost (N.J.A.C. 13:2-24.8), and both states require consistent, non-discriminatory pricing practices.

## 2. Eligibility (A-43)

A price match **may be approved** when **all** of these are true:

| Requirement | Detail |
|---|---|
| **Identical item** | Same producer, same wine/cuvée, same vintage, same bottle size, same pack (not gift box vs plain) |
| **Licensed retailer, same state** | A licensed brick-and-mortar or online retailer in the **same state as the fulfilling store** (NJ for NJ Store orders, NY for NY Store orders) |
| **Currently available** | In stock at that price, publicly visible (URL, ad or flyer), not requiring login/membership |
| **Timing** | Before purchase, or within **7 days after purchase** |
| **Quantity** | Up to **12 bottles** per SKU; **one match per SKU per customer per 30 days** |
| **Price floor** | The matched price cannot fall below our legal minimum price; the system enforces this |

## 3. Exclusions

- Marketplaces and auction sites; private sellers.
- **Membership-warehouse prices** (e.g., club stores), loyalty-member-only or app-only prices, subscription/club pricing.
- Bundles, "buy X get Y", gift-with-purchase, mail-in rebates, coupons.
- Clearance, closeout, "while supplies last" or limited-quantity doorbusters.
- Out-of-state retailers (including winery direct prices).
- Pricing errors by the competitor.
- Pre-arrival/futures, allocated, collectible or older-vintage items.
- Items already on sale with us (we'll match only one or the other: whichever is lower for the customer).
- Third-party delivery app prices (they include their own markups).

## 4. Rules

**PM-R1: The agent cannot approve.** The agent collects the information and submits the request (`submit_price_match_request`). Pricing staff approve or decline (A-62).

**PM-R2: No promises.** Say "I'll submit a price-match request," never "I'll match it."

**PM-R3: Matched price replaces discounts.** An approved match is the final unit price; the mixed-case discount and promo codes don't stack on matched items (to protect legal price floors).

**PM-R4: Equal availability (A-55).** The match program is open to every eligible customer on the same terms. It's a published policy, not a negotiation.

## 5. Workflow

1. **Collect:** product (confirm exact SKU, vintage, size), competitor name, competitor price, where it's shown (URL/screenshot/ad), quantity, and whether the customer has already purchased.
2. **Pre-screen** against §2–3. If clearly ineligible, explain kindly and mention our current offers (case discount, promotions).
3. **Submit:** `submit_price_match_request(customer_id, sku, competitor_name, competitor_url_or_proof, competitor_price, fulfillment_location)`.
4. **Set expectations:** response within 1 business day (P2). If approved **before purchase**, a price adjustment is applied to the customer's cart/order or a one-time code is issued; if approved **after purchase**, the difference is refunded to the original payment method.
5. If the customer needs the wine today and doesn't want to wait, offer to proceed at our price and submit the request as a post-purchase match (within 7 days).

## 6. Edge cases

| Case | Handling |
|---|---|
| Competitor price includes a member-only discount | Excluded |
| Competitor is in NJ but the customer's order is from the NY Store | Excluded (different state, A-43) |
| Competitor shows a different vintage | Not identical; offer to check whether we carry that vintage |
| Competitor price is below what the system allows | Request will be declined or approved at the floor price; the agent explains "we can't go below a certain price under state rules" without detail |
| Customer asks us to match a price we had last month | Not a price match; see the price-drop policy (PRC-E1) |
| Customer wants 3 cases matched | Up to 12 bottles; larger quantities → events/bulk team (A-26) |

## 7. Escalation

Submitting `submit_price_match_request` **is** the handoff for a normal request: pricing staff decide within 1 business day (PM-R1). Escalate further when:

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| `submit_price_match_request` fails after one retry | P2 | `price_match` | Include every collected field (§5 step 1) so the customer doesn't repeat them |
| No decision after 1 business day | P2 | `price_match` | Include the request ID |
| Customer says staff already promised a match | P2 | `price_match` | Don't confirm the promise (PM-R2) |
| Approved post-purchase match not refunded after 10 business days | P2 | `refund_trace` | Include the approval date and amount |
| More than 12 bottles, or a bulk or event quantity (A-26) | P2 | `bulk_order` | Explain that the 12-bottle cap applies to matches |
| A business wants a match against wholesale or trade pricing | P2 | `business_sales` | Explain we sell at retail |
| Customer asks for review of a declined match | P3 | `create_support_ticket(category="price_match_review")` | Don't reopen or negotiate it yourself (PM-R4) |

**Handle without escalating:** pre-screening, kind explanations for clearly ineligible requests (with current offers), and "match last month's price" (that's the price-drop policy, PRC-E1).

## 8. Response examples

> "Thanks for checking! I can submit a price-match request for the 2021 Château X at $41.99 from [Retailer]. To qualify, it has to be the same vintage and size, from a licensed New Jersey retailer, and in stock now. Can you share the link? Our pricing team usually responds within one business day."

> "I'm sorry, we can't match membership-club prices, since they require a paid membership. Our current offers might still help: buying 6 or more eligible wines gives you 10% off, and you're 40 points away from a $10 reward."
