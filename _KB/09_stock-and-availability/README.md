---
id: KB-STK-000
title: Stock and Availability: Folder Index
category: stock
subcategory: index
doc_type: index
intents: [stock.availability, stock.back_in_stock, stock.vintage_question, stock.pre_arrival, stock.product_request, stock.bulk_quantity, order.substitution_response]
tools: [check_inventory, subscribe_back_in_stock, get_similar_products, submit_product_request, respond_to_substitution]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: inventory-operations
status: active
related: [KB-ORD-000, KB-BRD-001]
---

# Stock and Availability: Folder Index

## Scope

How the agent reads and explains stock levels, vintage changes, substitutions, pre-arrivals and allocations, special orders and product requests, how new products are added to the catalog, and quantity limits. **Stock is always live from `check_inventory`**, which reads the fulfilling store's inventory (POS-synced). The KB only explains what each status means and what to do.

## Files

| File | Answers |
|---|---|
| [inventory-status-definitions.md](inventory-status-definitions.md) | Every `stock_status` value, what to tell the customer, what actions are allowed |
| [vintage-policy.md](vintage-policy.md) | Vintage display, vintage changes, automatic vs consent-based substitution |
| [out-of-stock-and-substitutions.md](out-of-stock-and-substitutions.md) | Out-of-stock at search vs during picking, substitution preferences, partial fulfillment, alerts |
| [pre-arrivals-futures-and-allocations.md](pre-arrivals-futures-and-allocations.md) | Futures/en primeur, pre-arrivals, allocations, waitlists, cancellations, arrival |
| [special-orders-and-product-requests.md](special-orders-and-product-requests.md) | "Can you get X?": request workflow, lead times, special-order terms |
| [new-product-onboarding-and-catalog-standards.md](new-product-onboarding-and-catalog-standards.md) | How new products are evaluated, registered, tagged and launched; catalog data standards |
| [purchase-limits-and-bulk-orders.md](purchase-limits-and-bulk-orders.md) | Per-SKU limits, allocation caps, bulk/event orders, resale prevention |

## Golden rules

1. Never say "in stock" without `check_inventory` for the **customer's fulfilling location** and **quantity**.
2. Never reveal exact unit counts. Use `qty_bucket` language ("plenty", "only a few left").
3. Never promise restock dates beyond `next_arrival_estimate`, and always call it an estimate.
