---
id: KB-STK-001
title: Inventory Status Definitions and Agent Responses
category: stock
subcategory: status-definitions
doc_type: reference
intents: [stock.availability, stock.back_in_stock, stock.pre_arrival]
tools: [check_inventory, subscribe_back_in_stock, get_similar_products, add_to_cart]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: inventory-operations
status: active
depends_on_assumptions: [A-01, A-06, A-21, A-25, A-26, A-28]
related: [KB-STK-003, KB-STK-004, KB-STK-005, KB-SYS-004]
---

# Inventory Status Definitions

## 1. How inventory works (context)

- Each store's online inventory is synced from its **point-of-sale (POS) system** in near real time. Online orders reserve stock at checkout.
- Online availability holds back a small **safety buffer** so in-store shoppers don't buy the last bottles mid-pick. A product can show "out of stock" online while one bottle sits on a shelf.
- Inventory is **per store** (A-01). The agent never combines NJ and NY stock.

## 2. Status catalog (`check_inventory.stock_status`)

| Status | Meaning | Can order? | What the agent says | Next actions |
|---|---|---|---|---|
| `in_stock` | Available above the safety buffer | Yes | "It's in stock at our [NJ/NY] store." Add "plenty available" if `qty_bucket=12+` | Offer add to cart; mention delivery options |
| `low_stock` | `qty_bucket=1-5` | Yes (up to available) | "Only a few left. I'd order soon if you want it." | If the customer wants more than available, offer the max plus similar wines |
| `out_of_stock` | None available; restock expected | No | "It's sold out right now." Give `next_arrival_estimate` if present, as an estimate | Back-in-stock alert; similar wines |
| `backorder` | Not on hand but orderable; ships when received from the distributor | Yes, if `backorder_allowed=true` | "We can order it for you. It's expected around [date], but distributor dates can shift." | Explain the order ships when it arrives; cancellable until picking (A-21) |
| `pre_arrival` | Sold before it arrives (futures or incoming import) | Yes, paid in full (A-25) | "This is a pre-arrival, expected [window]." | See [pre-arrivals-futures-and-allocations.md](pre-arrivals-futures-and-allocations.md) |
| `allocated` | Limited quantity with per-customer limit | Yes, up to `allocation_limit` | "This is a limited allocation, max [n] per customer." | Waitlist if sold out |
| `waitlist` | Allocation sold out; customers can join a waitlist | No | "It's sold out, but you can join the waitlist. If more arrives, waitlisted customers are offered it first." | `subscribe_back_in_stock(channel, waitlist=true)` |
| `coming_soon` | Listed, not yet orderable (new vintage/new product) | No | "Coming soon, expected [date]." | Alert |
| `special_order` | Not stocked; available to order from the distributor with lead time | Yes, prepaid (A-28) | "We don't stock it, but we can special-order it. Usually [lead time]." | See [special-orders-and-product-requests.md](special-orders-and-product-requests.md) |
| `discontinued` | No longer available from the producer/distributor | No | "It's been discontinued, so we won't be getting more." | Similar wines; no alerts |
| `in_store_only` | Sold only in the physical store (e.g., single bottles of library stock) | No (online) | "That one's available in store only." | Store hours/address |
| `temporarily_unavailable` | Hold (quality check, recall, inventory count, label issue) | No | "It's temporarily unavailable." Don't speculate on why | Alert; similar wines |
| `not_sellable_in_jurisdiction` (`sellable_in_jurisdiction=false`) | Legally can't be sold for this address/store (e.g., NA wine to NY, A-06) | No | Explain the specific rule if documented; otherwise "we can't sell that item for delivery to your area" | Alternatives |

## 3. Quantity language (`qty_bucket`)

| Bucket | Say |
|---|---|
| `12+` | "Plenty in stock" |
| `6-11` | "Good availability" |
| `1-5` | "Only a few left" |

Never state exact counts. If asked "how many do you have?", say "I can't share exact numbers, but I can check if we have the quantity you need. How many bottles?" Then call `check_inventory(quantity=n)`.

## 4. Workflow: "Is X in stock?"

1. Identify the SKU (size and vintage).
2. Determine the fulfilling location (ZIP/address; ask if unknown).
3. `check_inventory(sku, fulfillment_location, quantity)`.
4. Respond per the status table; for orderable statuses, offer the next step.
5. If not orderable, offer **both** an alert and 2–3 alternatives (`get_similar_products`).

## 5. Edge cases

- **Available at the other store only:** explain A-01: "Our [NY] store has it, but alcohol can't be transferred between our NJ and NY stores."
- **Customer saw it on the shelf but online says out of stock:** safety buffer or a recent sale; suggest calling or visiting the store; the agent can't reserve shelf stock unless `in_store_only` hold is supported.
- **Stock disappears during checkout:** the cart shows a warning; offer alternatives.
- **Different sizes** may have different availability. Check 375 ml and magnums when the 750 ml is out.
- **Tool returns stale or contradictory data** (e.g., `in_stock` with `qty_bucket` missing): treat it as unknown; retry once; if it persists, say you can't confirm and offer a ticket; `log_event("tool_error")`.

## 6. Response examples

> "Good news: the Veuve Clicquot Yellow Label is in stock at our NJ store, and there's plenty for your 6 bottles. Want me to add them?"

> "That Brunello is sold out right now, and the next shipment is estimated for early December (estimates can shift). I can alert you when it's back, and in the meantime, here are two similar Tuscan reds in stock: …"
