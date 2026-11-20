---
id: KB-STK-005
title: Special Orders and Product Requests ("Can you get X for me?")
category: stock
subcategory: special-orders
doc_type: workflow
intents: [stock.product_request, stock.bulk_quantity, recommend.by_brand]
tools: [search_products, check_inventory, submit_product_request, create_support_ticket, get_similar_products, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: merchandising
status: active
depends_on_assumptions: [A-01, A-26, A-28, A-34, A-35]
related: [KB-BRD-001, KB-STK-006, KB-STK-007, KB-STK-001]
---

# Special Orders and Product Requests

## 1. Two request types

| Type | When | Outcome |
|---|---|---|
| **Special order** (`stock_status=special_order`) | The product is in the **distributor's catalog** for our state, but we don't stock it | We order it for the customer: prepaid, with a lead time |
| **Product request** | The product isn't in our catalog at all, or availability in our state is unknown | Buyers research it; we may stock it, offer a special order, or decline |

## 2. Policy rules

**SO-R1: In-state distribution only (A-01).** We can source only through licensed wholesalers in the fulfilling store's state. A wine sold only by the winery, only in other states, or only abroad may be unobtainable.

**SO-R2: No promises.** The agent never promises that we'll get an item, a price or a date until the buyer confirms.

**SO-R3: Special-order terms (A-28).** Prepaid in full; **final sale** except damaged/defective (excluded from NJ change-of-mind returns, A-34; NY has none, A-35); the customer is notified on arrival and has 30 days to schedule delivery/pickup.

**SO-R4: Lead times (typical, not guaranteed).** Distributor stock in-state: **3–10 business days**. Distributor must import or the item is on "order-by-request" from a supplier: **4–12 weeks**. Some distributors sell only in **full cases** (6 or 12 bottles); the customer is told before paying.

**SO-R5: Case-only items.** If the distributor requires a full case, the customer can buy the case or decline. (In NY, wholesalers may charge retailers split-case fees, so pricing for less than a case may be higher; the buyer quotes the final price.)

**SO-R6: Price.** Special-order pricing is quoted by the buyer and follows standard retail pricing rules (equal pricing, legal floors).

## 3. Workflow

1. **Confirm the exact item:** producer, wine/cuvée, vintage (or "any"), size, quantity, needed-by date.
2. **Search first:** `search_products` (also other sizes/vintages). It may be in stock, or orderable as `special_order`.
3. **If `special_order`:** share the typical lead time and terms (SO-R3–R5); create the order after confirmation, or submit a request if the buyer must quote.
4. **If not found:** `submit_product_request(customer_id, product_description, quantity, fulfillment_location, contact_ok=true)`. Give `expected_response_by` (typically 2–3 business days).
5. **Offer alternatives now:** `get_similar_products` by style so the customer isn't left empty-handed.
6. **Event deadline:** if the needed-by date is within 10 business days, tell the customer it may not arrive in time and suggest a back-up wine.

## 4. How requests influence our assortment

Requests are tracked. Frequently requested products are considered for permanent listing using criteria in [new-product-onboarding-and-catalog-standards.md](new-product-onboarding-and-catalog-standards.md) (demand, in-state availability, catalog gaps, quality, price fit). The agent may say: "Customer requests help our buyers decide what to stock."

## 5. Edge cases

| Case | Handling |
|---|---|
| Winery-direct-only wine (mailing list) | Explain; suggest similar; no workaround |
| Out-of-state retailer has it | We can't buy from another retailer for resale; and we can't ship across states |
| Large formats (3 L+), rare vintages | Special order/request; often case-by-case pricing; collectible rules apply |
| Customer wants us to bring wine back from travel | Not possible (licensing) |
| Request for spirits/beer | Route to the correct catalog (out of KB scope); create a ticket P3 |
| Request for 10+ cases | Bulk/event path (A-26, [purchase-limits-and-bulk-orders.md](purchase-limits-and-bulk-orders.md)) |

## 6. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Special order not arrived 5 business days after the quoted lead time | P2 | `fulfillment_delay` | Include the order date and quoted lead time |
| Customer wants to cancel a prepaid special order (final sale, SO-R3) because of a credible change (e.g., event cancelled) | P2 | `policy_exception_request` | Don't promise a refund; the team checks whether the distributor order can still be stopped |
| Charged price differs from the buyer's quote | P2 | `pricing_dispute` | Include the quote and the charged amount |
| 10 or more cases, or over $2,500 (A-26) | P2 | `bulk_order` | Follow [purchase-limits-and-bulk-orders.md](purchase-limits-and-bulk-orders.md) §3 |
| A business wants a special order for resale | P2 | `business_sales` | Don't place it (G9) |
| No reply to a product request by its `expected_response_by` date | P3 | `product_request` | Include the request ID |
| Spirits or beer request | P3 | `create_support_ticket(category="product_request")` | Outside this KB's scope |

**Handle without escalating:** search, special-order placement with terms explained, product requests and alternatives. Winery-direct-only wines and requests to buy from out-of-state retailers are declined, not escalated.

## 7. Response examples

> "We don't stock that Jura Savagnin right now, but I've sent a request to our buyers (request #R-20931). They'll reply by Thursday with availability and price. In the meantime, if you like that nutty, savory style, here's a Fino Sherry and an aged white Rioja you might enjoy."

> "Good news: we can special-order that Barolo through our New Jersey distributor. It typically takes 3–10 business days, it's prepaid, and like all special orders it's final sale unless there's a problem with the bottle. Want me to place it?"
