---
id: KB-RTN-002
title: Damaged or Broken Items on Delivery
category: returns
subcategory: damage
doc_type: workflow
intents: [claim.damaged]
tools: [get_order, create_return_request, request_evidence_upload, issue_refund, issue_store_credit, add_to_cart, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: customer-support
status: active
depends_on_assumptions: [A-19, A-30, A-36, A-60, A-62]
related: [KB-RTN-001, KB-RTN-005, KB-ORD-007, KB-SYS-006]
---

# Damaged or Broken Items on Delivery

## 1. What counts as damage

| Covered (RTN-R1) | Not covered |
|---|---|
| Broken bottle(s) on arrival | Damage after handoff (dropped, frozen in a car, left in heat) |
| Leaking bottle, pushed or seeping cork, sticky capsule at delivery | Natural sediment or tartrate crystals (see corked/flawed doc) |
| Wet/soaked shipper with damaged labels (gift or collectible items) | Minor label scuffs on everyday wines (see §5) |
| Crushed gift box (gift-box SKUs) | Outer-box cosmetic dents with intact contents |
| Signs of heat exposure **before** delivery (pushed cork, leakage) | Heat damage on shipments sent **despite** a weather hold at the customer's request (reviewed case by case, A-19) |

## 2. Safety first

When a customer reports broken glass:
> "First, please be careful with the broken glass. Wear gloves or use a thick cloth, and wrap the pieces before throwing them away. You don't need to send the broken bottle back."

If the customer was **injured**, express care, suggest medical attention if needed, and escalate **P1** (`safety_crisis`).

## 3. Window and evidence

- Report within **48 hours** of delivery (A-30).
- Photos via `request_evidence_upload`: (1) the damaged bottle(s) or remaining glass/label, (2) the shipping box/inner packaging, (3) the shipping label if shipped. One clear photo of the broken bottle is enough for a simple local-delivery break.
- If the customer **can't** take photos (already discarded), the agent may still approve **one** bottle up to $50 once per 12 months (counts toward A-60); otherwise human review.

## 4. Workflow

1. `get_order` → confirm the item, delivery date (≤ 48 h) and fulfillment method.
2. Express empathy; give the safety line if glass is involved.
3. Ask which bottles are affected and the remedy preference:
   - **Replacement** (same wine, if in stock): redeliver free with the next available window, or include in the next order.
   - **Refund** to the original payment (or store credit).
4. `create_return_request(order_id, items, reason_code="broken_on_arrival"|"damaged_in_transit"|"leaking", evidence_refs)` → `request_evidence_upload` if not attached.
5. If `auto_approved` and ≤ $150 (A-60) → issue the remedy (`issue_refund` or a replacement order at $0). Over $150 or `needs_review` → escalate P2 `refund_over_limit`.
6. Confirm the RMA, the remedy and the timing. No need to return broken glass. Leaking-but-intact bottles: ask the customer not to drink them; we'll collect them with the replacement delivery or they can discard them.

## 5. Edge cases

| Case | Handling |
|---|---|
| Leak stained other bottles' labels | Covered for gift/collectible; for everyday wines, offer a replacement if the customer is unhappy |
| Reported after 48 hours | Over 48 h but within 7 days → human review (P2) with photos; beyond 7 days → generally ineligible unless also defective |
| Entire shipment arrived crushed | Refuse delivery if possible (driver/carrier); otherwise full claim; carrier claim handled internally |
| Damaged gift (recipient reports) | Remedy coordinated with the purchaser (GF-R6); replacement goes to the recipient |
| Replacement out of stock | Offer similar wine at the same price, or refund |
| Multiple damage claims recently | RTN-R9 human review |

## 6. Escalation

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Customer was injured by broken glass or a pushed cork | P1 | `safety_crisis` | Express care and suggest medical attention first; the product claim can wait |
| Remedy over $150 (A-60), or the return request comes back `needs_review` | P2 | `refund_over_limit` | Attach the photos and RMA number |
| Reported after 48 hours but within 7 days (A-30) | P2 | `claim_review` | Ask for photos before handing off |
| No photos, and the one no-photo approval (1 bottle up to $50 per 12 months) is used or doesn't cover the claim | P2 | `claim_review` | Note why photos aren't available |
| Several recent damage claims on the account (RTN-R9) | P2 | `claim_review` | Don't mention the claim history to the customer; process the current claim normally |
| Heat damage on a shipment sent despite a weather hold at the customer's request (A-19) | P2 | `claim_review` | Include the hold notice and the customer's choice |

**Handle without escalating:** safety guidance, approved claims up to $150 (refund or free replacement), cosmetic-damage explanations, and replacements that are out of stock (offer a similar wine or a refund). Damaged gifts follow [gift-orders.md](../11_orders-delivery-pickup/gift-orders.md).

## 7. Response examples

> "I'm so sorry a bottle broke. Please be careful with the glass, and no need to send it back. Could you upload a quick photo here? [link]. Once it's in, I can send a replacement Prosecco with tomorrow's 11–1 delivery, or refund $16.99 to your card. Which would you prefer?"

> "Thanks for the photos. I've approved the refund of $47.98 for the two broken bottles (RMA #R-55102). You'll see it on your card in 5–10 business days."
