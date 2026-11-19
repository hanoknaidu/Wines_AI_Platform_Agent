---
id: KB-SYS-005
title: Intent Taxonomy and Routing Map
category: system
subcategory: intents
doc_type: reference
intents: ["*"]
tools: [search_kb]
jurisdictions: [NJ, NY]
audience: agent, ai-platform
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: ai-platform
status: active
related: [KB-SYS-002, KB-SYS-004, KB-SYS-006]
---

# Intent Taxonomy and Routing Map

## 1. How to use this map

The intent classifier assigns **one primary intent** (and optionally secondary intents) to each customer turn. Each intent maps to:
- the **KB folder(s)** to search, used as a `search_kb` filter to raise retrieval precision;
- the **tools** usually needed;
- whether the intent is **transactional** (changes state; confirmation required) or **informational**.

Naming: `domain.action`. Intents are stable identifiers. Add new ones here first, then tag documents' `intents:` frontmatter.

**Confidence handling**
- Confidence ≥ 0.75: route directly.
- 0.50–0.75: route, but confirm understanding in the reply ("Just to check, are you asking about…").
- Below 0.50, or two intents tied: ask one clarifying question.
- Any compliance-flag intent (`compliance.*`) **overrides** other intents in the same turn.

## 2. Intent catalog

### 2.1 Discovery and recommendation (informational → may become transactional)

| Intent | Example utterances | KB folders | Tools |
|---|---|---|---|
| `recommend.by_taste` | "Something smooth and not too sweet", "a crisp white" | 01 | `search_products`, `get_product_details` |
| `recommend.by_occasion` | "Wine for Thanksgiving", "gift for my boss" | 01, 04, 14 | `search_products` |
| `recommend.by_food` | "What goes with salmon?" | 01 (food-pairing) | `search_products` |
| `recommend.by_region` | "Do you have Italian reds?", "Napa Cabernet under $50" | 02 | `search_products` |
| `recommend.by_brand` | "Anything like Meiomi?", "Do you carry Caymus?" | 03 | `search_products`, `get_similar_products` |
| `recommend.sparkling` | "Champagne vs Prosecco?", "brut for mimosas" | 04 | `search_products` |
| `recommend.low_calorie` | "Low-cal wine", "keto friendly", "low sugar" | 05 | `search_products(filters.calories_max)` |
| `recommend.organic_natural` | "Organic wine", "no added sulfites", "biodynamic" | 06 | `search_products(filters.certifications)` |
| `recommend.non_alcoholic` | "Alcohol-free wine", "NA bubbly" | 07 | `search_products(is_non_alcoholic=true)` |
| `recommend.budget` | "Best wine under $20" | 08 (price bands), 01 | `search_products(price_max)` |
| `recommend.similar` | "Like the one I bought last time" | 01, 13 | `list_orders`, `get_similar_products` |
| `refine.results` | "Something lighter", "cheaper", "less oaky" | 01 | `search_products` (re-ranked) |
| `education.wine_question` | "What's the difference between Pinot Grigio and Sauvignon Blanc?" | 01, 02, 04, 00 (glossary) | none / `search_kb` |

### 2.2 Product, price and stock (informational)

| Intent | Example | KB | Tools |
|---|---|---|---|
| `product.details` | "What's the ABV of…", "Is it vegan?" | 03, 05, 06 | `get_product_details` |
| `price.inquiry` | "How much is…" | 08 | `get_price` |
| `price.discrepancy` | "Price was different yesterday / in store" | 08 | `get_price`, `get_order` |
| `price.match_request` | "X store has it cheaper" | 08 | `submit_price_match_request` |
| `stock.availability` | "Is it in stock?" | 09 | `check_inventory` |
| `stock.back_in_stock` | "Tell me when it's back" | 09 | `subscribe_back_in_stock` |
| `stock.vintage_question` | "Which vintage will I get?" | 09 | `get_product_details`, `check_inventory` |
| `stock.pre_arrival` | "When does the 2024 Bordeaux arrive?" | 09 | `check_inventory`, `get_order` |
| `stock.product_request` | "Can you get X for me?" | 09 | `submit_product_request` |
| `stock.bulk_quantity` | "I need 10 cases for a wedding" | 09, 14 | `check_inventory`, `create_support_ticket` |

### 2.3 Discounts and loyalty

| Intent | Example | KB | Tools |
|---|---|---|---|
| `discount.current_offers` | "Any sales?" | 10 | `get_active_promotions` |
| `discount.case_discount` | "Do you do case discounts?" | 10 | `calculate_order_totals` |
| `discount.promo_code_issue` | "My code isn't working" | 10 | `validate_promo_code` |
| `loyalty.balance` | "How many points do I have?" | 10 | `get_loyalty_account` |
| `loyalty.missing_points` | "I didn't get points" | 10 | `get_order`, `adjust_loyalty_points` |
| `loyalty.redeem` | "Use my reward" | 10 | `redeem_reward` |

### 2.4 Orders, delivery and pickup (transactional)

| Intent | Example | KB | Tools |
|---|---|---|---|
| `order.place_help` | "How do I order?", "checkout problem" | 11 | `get_cart`, `calculate_order_totals` |
| `order.status` | "Where is my order?" | 11 | `get_order_status`, `track_shipment` |
| `order.modify` | "Add a bottle", "change delivery time" | 11 | `modify_order`, `reschedule_delivery` |
| `order.cancel` | "Cancel my order" | 11 | `cancel_order` |
| `order.substitution_response` | "Yes, the 2022 is fine" | 09, 11 | `respond_to_substitution` |
| `delivery.eligibility` | "Do you deliver to 07030?" | 11 | `get_fulfillment_options` |
| `delivery.fees_and_minimums` | "Delivery fee?" | 11, 08 | `get_fulfillment_options` |
| `delivery.failed` | "Driver came and left" | 11 | `get_order_status`, `reschedule_delivery` |
| `pickup.question` | "When can I pick up?" | 11 | `get_order_status`, `get_store_info` |
| `shipping.question` | "Can you ship to Buffalo?", "to Florida?" | 11, 00 | `get_fulfillment_options` |
| `gift.order` | "Send a bottle to my sister" | 11 | `get_fulfillment_options` |

### 2.5 Returns and problems (transactional)

| Intent | Example | KB | Tools |
|---|---|---|---|
| `return.change_of_mind` | "Can I return unopened wine?" | 12 | `get_order`, `create_return_request` |
| `claim.damaged` | "Bottle arrived broken" | 12 | `create_return_request`, `request_evidence_upload` |
| `claim.flawed_wine` | "Wine tastes like wet cardboard" | 12 | `create_return_request` |
| `claim.wrong_or_missing` | "Wrong wine delivered" | 12 | `create_return_request` |
| `refund.status` | "Where is my refund?" | 12 | `get_return_status` |

### 2.6 Account

| Intent | Example | KB | Tools |
|---|---|---|---|
| `account.create` | "How do I sign up?" | 13 | none |
| `account.login_issue` | "Can't log in", "reset password" | 13 | `send_password_reset` |
| `account.age_verification` | "Why do I need to verify my ID?" | 13, 00 | `get_age_verification_status` |
| `account.update_profile` | "Change my email/address" | 13 | `verify_customer_identity`, `update_customer_profile`, `manage_address` |
| `account.payment_methods` | "Remove my old card" | 13 | `remove_payment_method` |
| `account.preferences` | "Stop texting me" | 13 | `update_communication_preferences` |
| `account.privacy_request` | "Delete my account", "what data do you have?" | 13 | `submit_privacy_request` |
| `account.security_concern` | "Someone ordered on my account" | 13 | `lock_account`, `escalate_to_human` |

### 2.7 General

| Intent | Example | KB | Tools |
|---|---|---|---|
| `store.info` | "What time do you close Sunday?" | 14 | `get_store_info` |
| `giftcard.question` | "Gift card balance" | 14 | `get_gift_card_balance` |
| `events.corporate` | "Corporate gifting / tasting" | 14 | `create_support_ticket` |
| `wine.care` | "How long does open wine last?" | 14 | none |
| `feedback.complaint` | "Your driver was rude" | 00 (escalation), 11 | `create_support_ticket` |
| `human.request` | "Talk to a person" | 00 | `escalate_to_human` |
| `chitchat` | "Hi", "thanks" | — | none |
| `out_of_scope` | Non-wine topics, medical/legal advice | 14 (out-of-scope) | none |

### 2.8 Compliance flags (override other intents)

| Intent | Signal | KB | Action |
|---|---|---|---|
| `compliance.underage` | States/implies under 21, or buying for a minor | 00 | Stop sale; G1 |
| `compliance.intoxication` | Signals of heavy intoxication + urgency/driving | 00, 14 | G3; safety-first |
| `compliance.out_of_state` | Delivery outside NJ/NY | 00, 11 | Decline; G4 |
| `compliance.resale` | Wholesale/resale request | 00 | Escalate to business team |
| `compliance.health_claim_request` | "Which wine is healthiest / safe in pregnancy?" | 00, 05 | G7 |
| `compliance.crisis` | Self-harm, dependence distress | 14 | G8; resources; P1 |

## 3. Multi-intent examples

| Utterance | Primary | Secondary | Handling |
|---|---|---|---|
| "My order came with a broken bottle and I want a replacement Prosecco for tomorrow" | `claim.damaged` | `recommend.sparkling` | Resolve the claim first, then find a Prosecco with tomorrow's delivery window |
| "Is the Caymus in stock and can I use my 20% code?" | `stock.availability` | `discount.promo_code_issue` | Check stock, then `validate_promo_code` (sale items are often excluded) |
| "I'm 20, what's a good wine for my mom's birthday?" | `compliance.underage` | `recommend.by_occasion` | Compliance overrides: no purchase help. We can't sell to under 21 even for a gift. |
| "Delete my account but first tell me my points" | `account.privacy_request` | `loyalty.balance` | Show the balance and warn that deletion forfeits points (see privacy doc), then confirm |
