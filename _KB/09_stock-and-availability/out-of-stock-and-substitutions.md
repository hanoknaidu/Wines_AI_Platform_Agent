---
id: KB-STK-003
title: Out-of-Stock Handling, Substitutions and Partial Fulfillment
category: stock
subcategory: out-of-stock
doc_type: workflow
intents: [stock.availability, stock.back_in_stock, order.substitution_response, order.status]
tools: [check_inventory, get_similar_products, subscribe_back_in_stock, get_order, respond_to_substitution, cancel_order, issue_refund, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: inventory-operations
status: active
depends_on_assumptions: [A-12, A-21, A-22, A-23, A-24, A-36, A-50, A-60]
related: [KB-STK-001, KB-STK-002, KB-ORD-002, KB-RTN-005]
---

# Out-of-Stock Handling, Substitutions and Partial Fulfillment

## 1. Two moments when "out of stock" happens

| Moment | Cause | Handling |
|---|---|---|
| **Before ordering** (search/cart) | Live inventory shows none | Alternatives + back-in-stock alert (§2) |
| **After ordering, during picking** | Last bottle sold in store, breakage in the stockroom, inventory count error | Substitution preference (§3), partial fulfillment and refund (§4) |

## 2. Before ordering: workflow

1. `check_inventory` shows `out_of_stock` / `discontinued` / `waitlist`.
2. Tell the customer plainly, with `next_arrival_estimate` if present (labeled as an estimate).
3. Offer **both**:
   - `subscribe_back_in_stock(customer_id, sku, location, channel)` (not for discontinued items).
   - 2–3 alternatives via `get_similar_products(sku, constraints{price_band, color, exclude_skus})`, explaining what's similar and what's different.
4. Check **other sizes and vintages** of the same wine (375 ml, magnum, adjacent vintage).
5. If the customer specifically needs that wine for an event with a date, check the special-order route (`special_order` status) and lead time.

**Alternative-quality rules**
- Same color and style; same sweetness level; price within ±20% unless the customer allows otherwise.
- Prefer the same grape/region first, then same style from another region.
- Don't present an alternative as "the same wine".

## 3. During picking: substitution preferences (A-24)

At checkout, every order line carries a substitution preference (default **"Contact me"**):

| Preference | What staff do when an item is short | Customer experience |
|---|---|---|
| **Contact me** (default) | Propose a substitute via `substitution_pending`; customer approves/declines within **24 hours** (shorter for same-day orders: until 30 min before the delivery window) | Notification; the agent can capture the decision via `respond_to_substitution` |
| **Substitute a similar wine** | Staff choose a same-style wine within ±10% of the price; if it costs more, the customer pays the **original** price | Noted on the receipt; the customer may return the substitute unopened for a full refund within 7 days (treated as our action) |
| **Do not substitute** | Remove the item; refund | Refund notification |

**Vintage-only changes** follow [vintage-policy.md](vintage-policy.md) (automatic under $25; consent at $25+).

**Never substitute:** vintage-specific, allocated, collectible, pre-arrival or gift-box items, or non-alcoholic ↔ alcoholic, or a different color/style, without explicit customer consent, regardless of preference.

## 4. Partial fulfillment and refunds

- If items are removed, the rest of the order proceeds unless the customer asks to cancel (A-21 status rules apply).
- **Refund:** the removed item's price, minus the share of order-level discounts allocated to it; plus tax on it. Card refunds post in 5–10 business days (A-36).
- **Threshold effects:** if removing an item drops the order below the **free-delivery threshold** (A-12) or below **6 bottles** for the mixed-case discount (A-50), **we do not charge the difference**. The customer keeps the original fee waiver/discount.
- If the whole order can't be fulfilled, cancel and fully refund, including fees.

## 5. Agent workflow: customer asks about a pending substitution

1. `get_order(order_id)` → identify lines with `substitution_pending` and the deadline.
2. Present original vs proposed: name, vintage, size, price, why it's similar.
3. Ask: approve, choose a different alternative (`get_similar_products`), or remove.
4. `respond_to_substitution(order_id, line_id, decision)` after explicit confirmation.
5. Confirm the updated total and delivery timing.

## 6. Edge cases

| Case | Handling |
|---|---|
| Customer missed the 24-hour window and the item was removed | Apologize; offer to place a new order for the proposed substitute if still available |
| Substitute customer didn't like (preference "Substitute similar") | Return unopened within 7 days, full refund, no restocking fee (both states; treated as our action) |
| Multiple items short in one order | Present all at once; let the customer decide per item |
| Same-day order, short item, no response | Remove the item at the cutoff and deliver the rest on time |
| Gift order (recipient ≠ purchaser) | Contact the **purchaser** for decisions |

## 7. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Alcoholic wine substituted for non-alcoholic wine (or the reverse), and the customer has drunk it and reports a health concern | P1 | `safety_crisis` | Suggest medical attention; stop any sales talk |
| A substitution broke the never-substitute list (§3) or the vintage consent rule (A-23) | P2 | `policy_violation` | Offer a full refund or return regardless of state, as [vintage-policy.md](vintage-policy.md) requires |
| `respond_to_substitution` fails before the decision deadline | P2 | `tool_failure` | Include the line ID and the customer's decision, so the store applies it in time |
| Several items short on an order for a dated event or gift, and no alternative suits the customer | P2 | `fulfillment_delay` | Offer alternatives and other sizes or vintages first (§2); include the event date |
| After an out-of-stock removal, the customer was charged the delivery fee or lost the case discount (contrary to §4) | P2 | `pricing_dispute` | Within A-60, refund the difference yourself with `issue_refund`; escalate only above $150 |
| The same item showed in stock but was removed on 2 or more of the customer's orders | P3 | `create_support_ticket(category="inventory_accuracy")` | Include the SKU and the order numbers |

**Handle without escalating:** out-of-stock alternatives, back-in-stock alerts, pending substitution decisions, missed substitution windows (offer a new order), and partial-fulfillment refunds the tools calculate. Gift-order decisions go to the purchaser.

## 8. Response examples

> "That Rioja is sold out right now, with more expected around the 25th (an estimate). Want me to text you when it's back? In the meantime, two close matches in stock are a Ribera del Duero Crianza (a bit bolder) and another Rioja Reserva from a traditional producer (very similar style)."

> "While packing your order, the store ran out of the Sancerre. You chose 'Contact me', so here's the suggested swap: a Pouilly-Fumé from the same area, same grape, $2 less. Would you like that, or should I remove it and refund $34.99 plus tax?"
