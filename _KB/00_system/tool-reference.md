---
id: KB-SYS-004
title: Tool and API Reference (Agent ↔ Backend Contract)
category: system
subcategory: tools
doc_type: reference
intents: ["*"]
tools: ["*"]
jurisdictions: [NJ, NY]
audience: agent, backend-engineering
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 30
owner: ai-platform
status: draft-contract
related: [KB-SYS-002, KB-SYS-005, KB-SYS-006]
---

# Tool and API Reference

## 1. Purpose and status

This is the **contract** between the agent and the backend. KB documents name these tools in their workflows. Status is `draft-contract`: the Backend APIs/Tools component (phase 2) implements them. When an implementation renames or reshapes a tool, update this file **and** run `grep -r "<tool_name>" _KB/` to update the workflows that use it.

**Design rules for every tool**
- The agent never touches the database directly. Everything goes through these tools.
- Every call carries `conversation_id` and, when known, `customer_id` and `fulfillment_location` (`NJ` or `NY`, derived from delivery ZIP or chosen pickup store).
- State-changing tools require `confirmed_by_customer=true` and an `idempotency_key`.
- Errors return `{error_code, message, retryable}`. On `retryable=false`, the agent does not retry; it explains and offers escalation.
- Money values are decimal strings in USD. Timestamps are ISO-8601 with timezone.

## 2. Knowledge retrieval

| Tool | Purpose | Key inputs | Key outputs |
|---|---|---|---|
| `search_kb` | RAG retrieval over this KB | `query`, optional `filters{category, intents, jurisdictions, doc_type}`, `top_k` | chunks with `id`, `title`, `section`, `text`, `score`, `last_reviewed` |

## 3. Catalog and product

| Tool | Purpose | Key inputs | Key outputs |
|---|---|---|---|
| `search_products` | Find sellable products | `query?`, `filters{color, style_tags[], sweetness, body, acidity, tannin, oak, country, region, appellation, grape[], brand, price_min, price_max, certifications[], abv_max, calories_max, is_non_alcoholic, size_ml, vintage, is_kosher, closure}`, `fulfillment_location`, `sort`, `limit` | list of `{sku, name, brand, vintage, size_ml, price, sale_price, stock_status, style_tags, taste{}, region_path}` |
| `get_product_details` | Full attributes for one SKU | `sku`, `fulfillment_location` | description, tasting notes, `taste{}`, grapes, `region_path`, ABV, `nutrition{calories, carbs_g, sugar_g, serving_ml, source}`, `certifications[{type, certifier, evidence_ref, verified_at}]`, `accolades[{source, score, vintage}]`, allergen/fining notes, closure, `vintage_specific` flag, `final_sale` flag |
| `get_similar_products` | Substitutes or alternatives | `sku` or `taste_profile`, `constraints{price_band, color, exclude_skus, certifications}`, `fulfillment_location`, `n` | ranked products with `similarity_reason` |
| `check_inventory` | Live availability | `sku`, `fulfillment_location` or `zip`, `quantity` | `stock_status` (see [inventory-status-definitions.md](../09_stock-and-availability/inventory-status-definitions.md)), `qty_bucket` (`1-5`, `6-11`, `12+`), `next_arrival_estimate`, `sellable_in_jurisdiction` (bool), `allocation_limit` |
| `subscribe_back_in_stock` | Restock alert | `customer_id`, `sku`, `fulfillment_location`, `channel` | `subscription_id` |
| `submit_product_request` | Customer asks us to carry or special-order an item | `customer_id`, `product_description`, `quantity`, `fulfillment_location`, `contact_ok` | `request_id`, `expected_response_by` |

## 4. Pricing and promotions

| Tool | Purpose | Key inputs | Key outputs |
|---|---|---|---|
| `get_price` | Live price for a SKU at a location | `sku`, `fulfillment_location`, `quantity` | `unit_price`, `sale_price?`, `sale_ends_at?`, `compare_at_price?`, `compare_at_verified`, `case_discount_eligible` |
| `get_active_promotions` | Current offers | `fulfillment_location`, `sku?`, `customer_id?` | list of `{promo_id, type, description, terms, starts_at, ends_at, stackable}` |
| `validate_promo_code` | Check a code without applying | `code`, `cart_id` | `valid`, `reason_code` (`expired`, `min_not_met`, `not_stackable`, `excluded_items`, `already_used`, `location_mismatch`, `blocked_by_price_floor`), `estimated_savings` |
| `apply_promo_code` | Apply a code to the cart | `cart_id`, `code` | updated cart totals |
| `calculate_order_totals` | Authoritative totals | `cart_id` or `order_id` | `subtotal`, `discounts[]`, `delivery_fee`, `shipping_fee`, `tax`, `total`, `free_delivery_gap` |
| `submit_price_match_request` | Human-reviewed price match | `customer_id`, `sku`, `competitor_name`, `competitor_url_or_proof`, `competitor_price`, `fulfillment_location` | `request_id`, `status=pending_review` |

## 5. Cart and orders

| Tool | Purpose | Key inputs | Key outputs |
|---|---|---|---|
| `get_cart` / `add_to_cart` / `update_cart_item` / `remove_from_cart` | Cart management | `cart_id`, `sku`, `quantity` | cart lines, totals preview, warnings (`allocation_limit`, `mixed_location`) |
| `get_fulfillment_options` | Delivery, pickup, shipping eligibility | `address` or `zip`, `cart_id` | `fulfillment_location`, `local_delivery{eligible, zone, fee, minimum, windows[]}`, `pickup{stores[], ready_by}`, `shipping{eligible, fee, est_days, weather_hold}`, `restricted_destination_flag` |
| `list_orders` | Customer's orders | `customer_id`, `limit`, `status?` | order summaries |
| `get_order` | Order details | `order_id` | lines, totals, fulfillment type, address, substitution preference, timeline |
| `get_order_status` | Current status and ETA | `order_id` | `status` (see [order-status-lifecycle.md](../11_orders-delivery-pickup/order-status-lifecycle.md)), `eta_window`, `tracking_url?`, `driver_status?` |
| `track_shipment` | Carrier tracking | `order_id` | carrier, tracking events, attempts |
| `modify_order` | Change items, window, address (limited) | `order_id`, `changes{}` | result, new totals, `not_allowed_reason?` |
| `reschedule_delivery` | New delivery window | `order_id`, `window_id` | confirmation |
| `cancel_order` | Cancel whole or part of order | `order_id`, `line_ids?`, `reason_code` | `cancelled`, `refund_amount`, `refund_method`, `not_allowed_reason?` |
| `respond_to_substitution` | Approve/decline a proposed vintage or wine substitution | `order_id`, `line_id`, `decision` | updated line |

## 6. Returns, claims and refunds

| Tool | Purpose | Key inputs | Key outputs |
|---|---|---|---|
| `create_return_request` | Start a return/claim | `order_id`, `items[{line_id, qty}]`, `reason_code` (`damaged_in_transit`, `broken_on_arrival`, `corked_or_flawed`, `leaking`, `wrong_item`, `missing_item`, `change_of_mind`, `late_delivery`), `evidence_refs[]`, `customer_notes` | `rma_id`, `eligibility` (`auto_approved`, `needs_review`, `ineligible`), `ineligible_reason?`, `remedy_options[]`, `pickup_required` |
| `request_evidence_upload` | Send the customer a secure photo upload link | `order_id`, `rma_id?` | `upload_link`, `expires_at` |
| `get_return_status` | Status of a claim | `rma_id` | status, decision, remedy |
| `issue_refund` | Refund within authority | `order_id`, `amount`, `method` (`original_payment`, `store_credit`), `reason_code`, `rma_id?` | `refund_id`, `expected_posting` |
| `issue_store_credit` | Goodwill or claim credit | `customer_id`, `amount`, `reason_code`, `expires_at?` | `credit_id` |

Authority limits are enforced **server-side** to match A-60 to A-62. If the agent requests above its limit, the tool returns `requires_human_approval` and the agent escalates.

## 7. Customer account

| Tool | Purpose | Key inputs | Key outputs |
|---|---|---|---|
| `verify_customer_identity` | Send/verify OTP | `channel` (`email`, `sms`), `contact_on_file`, `otp_code?` | `verified`, `customer_id` |
| `get_customer_profile` | Profile summary | `customer_id` | name, masked email/phone, addresses (masked), `age_verified`, loyalty summary, taste profile, preferences |
| `update_customer_profile` | Change name, phone, birthday-month greeting, taste preferences | `customer_id`, `fields{}` | result |
| `manage_address` | Add/edit/remove saved addresses | `customer_id`, `action`, `address` | result, `restricted_destination_flag` |
| `remove_payment_method` | Remove a saved card (agent cannot add cards) | `customer_id`, `payment_method_id` | result |
| `send_password_reset` | Reset link | `email` | always returns generic success (no account enumeration) |
| `get_age_verification_status` / `start_age_verification` | ID verification | `customer_id` | `status` (`not_started`, `pending`, `verified`, `failed`, `manual_review`), `verification_link` |
| `update_communication_preferences` | Marketing/SMS/email preferences | `customer_id`, `prefs{}` | result |
| `submit_privacy_request` | Access, correction, deletion, portability, opt-out | `customer_id`, `request_type`, `details` | `request_id`, `due_by` |
| `lock_account` | Emergency lock (suspected takeover) | `customer_id`, `reason` | result |

## 8. Loyalty and gift cards

| Tool | Purpose | Key inputs | Key outputs |
|---|---|---|---|
| `get_loyalty_account` | Points, tier, rewards | `customer_id` | `points`, `tier`, `rewards[{id, value, expires_at}]`, `points_expiry_date` |
| `redeem_reward` | Apply reward to cart | `customer_id`, `reward_id`, `cart_id` | updated totals |
| `adjust_loyalty_points` | Missing points correction (limited) | `customer_id`, `order_id`, `points`, `reason` | result or `requires_human_approval` |
| `get_gift_card_balance` | Balance via secure form token | `gift_card_token` | `balance` |

## 9. Store, support and escalation

| Tool | Purpose | Key inputs | Key outputs |
|---|---|---|---|
| `get_store_info` | Hours, address, holiday hours, phone | `location` | details |
| `create_support_ticket` | Async follow-up | `customer_id?`, `category`, `priority`, `summary`, `order_id?`, `attachments?` | `ticket_id`, `sla_due` |
| `escalate_to_human` | Live handoff | `conversation_id`, `reason_code`, `priority` (`P1`–`P3`), `summary`, `customer_sentiment` | `handoff_status` (`connected`, `queued`, `after_hours_ticket`), `wait_estimate` |
| `log_event` | Analytics/quality flags | `event` (`kb_conflict`, `kb_gap`, `safety_flag`, `tool_error`), `details` | ack |

## 10. Tool-selection quick map

| Customer wants… | Call first | Then |
|---|---|---|
| A recommendation | `search_products` | `get_product_details` for the top picks |
| "Do you have X?" | `search_products(query)` | `check_inventory`, `get_price` |
| "How much is X?" | `get_price` | `get_active_promotions(sku)` |
| "Where's my order?" | `get_order_status` | `track_shipment` if shipped |
| To return or report a problem | `get_order` | `create_return_request` → `request_evidence_upload` |
| A code to work | `validate_promo_code` | `apply_promo_code` |
| Account help | `verify_customer_identity` | relevant account tool |
| Delivery to an address | `get_fulfillment_options` | `calculate_order_totals` |
