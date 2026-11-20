---
id: KB-ACC-004
title: Order History, Reorders, Favorites and Taste Profile
category: account
subcategory: history-personalization
doc_type: workflow
intents: [recommend.similar, account.update_profile, order.status, account.privacy_request]
tools: [list_orders, get_order, check_inventory, get_similar_products, add_to_cart, get_customer_profile, update_customer_profile, create_support_ticket, escalate_to_human, submit_privacy_request]
jurisdictions: [NJ, NY]
audience: agent
priority: medium
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: customer-support
status: active
depends_on_assumptions: [A-01, A-03, A-55, A-70, A-72, A-73, A-75]
related: [KB-TST-002, KB-ACC-006, KB-DSC-004]
---

# Order History, Reorders, Favorites and Taste Profile

## 1. Order history

- Online and app orders, plus in-store purchases linked via Rewards, appear in **Account → Orders** for **24 months** (A-75). Older records are available on request (P3 ticket).
- Each order shows items, prices paid, fulfillment, status, and a downloadable **receipt/invoice** (useful for expense reports or gift tracking).
- The agent can find orders with `list_orders` (verified customer) and show details with `get_order`.

## 2. Reorder

1. `list_orders` → identify the wine(s) ("the red I bought for Thanksgiving").
2. `check_inventory` for the **current** fulfilling store (it may differ from the original if the customer moved; A-01).
3. If available: confirm the current price (prices change; the past price isn't honored) → `add_to_cart`.
4. If unavailable or a different vintage: explain and offer similar wines or an alert.

## 3. Favorites, ratings and the taste profile

| Feature | What it does | Agent use |
|---|---|---|
| **Favorites / wishlist** | Saved products | Recommend; alert on sales if the customer opted in |
| **Ratings** (thumbs up/down or 1–5) | Customer feedback per wine | Feeds personalization |
| **Taste profile** | Saved preferences on the taste axes (e.g., dry, medium body, no heavy oak), favorite grapes/regions, dislikes, budget band | Use it to skip interview questions ("Last time you liked smooth, medium reds…") |

**Updating the taste profile:** with consent, after a conversation: "Want me to save that you prefer crisp whites and dislike oaky Chardonnay?" → `update_customer_profile(fields={taste_profile:…})`.

## 4. Personalization rules

- Use history and taste data **only for the signed-in customer** and only to help them (agent principles §8).
- **Personalization opt-out** (privacy setting): if on, recommend without using history; don't mention past purchases.
- Don't infer or record **sensitive** information (health, pregnancy, religion, recovery) in the taste profile, even if mentioned in chat.
- Purchase history is not used to determine eligibility for discounts (A-55), only for relevance.

## 5. Edge cases

| Case | Handling |
|---|---|
| "What was that wine I bought in store last year?" | Only if the purchase was linked to Rewards; otherwise suggest a receipt or a description; search by description |
| Gift orders cluttering recommendations | Customers can mark orders as gifts so they don't shape the profile |
| Shared household tastes | Suggest using separate accounts or favorites lists |
| Customer asks to delete history only | Personalization data can be deleted on request (privacy doc); legally required order records stay (A-73) |

## 6. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Orders in the history that the customer doesn't recognize | P1 | `account_takeover` | First check whether a household member or a gift order explains it. If not, follow [account-takeover-and-fraud.md](account-takeover-and-fraud.md) §2 |
| Customer wants order history or taste data deleted | P2 | `submit_privacy_request` (handled by the privacy team) | Explain what is kept by law (A-73) per [privacy-rights-and-account-deletion.md](privacy-rights-and-account-deletion.md) |
| Sensitive information (health, pregnancy, religion, recovery) was saved to the taste profile | P2 | `privacy_request`, if it can't be removed | Remove it right away with `update_customer_profile`; escalate only if that fails |
| Records older than 24 months (A-75) | P3 | `create_support_ticket(category="records_request")` | Include the approximate date and what the customer needs (receipt, wine name) |
| Invoice needed with a company name or other expense details | P3 | `create_support_ticket(category="invoice_request")` | Include the order number and the details required |
| An in-store purchase linked to Rewards is missing from the history | P3 | `create_support_ticket(category="loyalty")` | Include the store, date and receipt total; points follow [rewards-loyalty-program.md](../10_discounts-and-promotions/rewards-loyalty-program.md) |

**Handle without escalating:** reorders, a past price that no longer applies (the current price always applies), out-of-stock reorders (offer similar wines or an alert) and taste-profile updates with consent.

## 7. Response examples

> "I found it: the 2022 Côtes du Rhône you ordered on November 20 last year. It's back in stock as the 2023 vintage, $14.99. Want me to add two bottles?"

> "Got it, crisp whites, no heavy oak, under $25. Want me to save that to your taste profile so I can skip these questions next time?"
