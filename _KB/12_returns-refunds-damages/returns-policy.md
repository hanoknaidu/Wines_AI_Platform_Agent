---
id: KB-RTN-001
title: Returns Policy (Master Policy and Decision Tree)
category: returns
subcategory: policy
doc_type: policy
intents: [return.change_of_mind, claim.damaged, claim.flawed_wine, claim.wrong_or_missing]
tools: [get_order, create_return_request, request_evidence_upload, get_return_status, issue_refund, issue_store_credit, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: customer-support
status: active
depends_on_assumptions: [A-10, A-25, A-28, A-30, A-31, A-32, A-33, A-34, A-35, A-36, A-56, A-60, A-62]
related: [KB-RTN-002, KB-RTN-003, KB-RTN-004, KB-RTN-005, KB-STK-002, KB-ORG-003]
---

# Returns Policy

## 1. Principles

1. **If it's our fault or the product is faulty, we make it right in both states**: damage, defects, wrong items, catalog misinformation, unauthorized substitutions.
2. **Change-of-mind returns depend on the state** of the fulfilling store, because practice and rules differ, and because we can't verify how wine was stored after it left us.
3. **Consumers can't ship alcohol back by carrier.** Returns go back to the store in person, or through a pickup/return label we arrange.

## 2. Policy rules

**RTN-R1: Our error and product faults (both states).** Covered at no cost, no restocking fee:
- Damaged or broken on arrival: report within **48 hours** (A-30).
- Wrong or missing item: within **7 days** (A-31).
- Defective (corked, oxidized, heat-damaged before delivery, cork failure, leaking seal, flat sparkling): within **30 days** (A-32).
- Product listing error that affected the purchase (wrong vintage, size, certification, or a claim shown in error): within **30 days**.
- Substitution made in violation of policy (VIN-R2), or a "substitute similar" item the customer doesn't want (unopened, 7 days).

**RTN-R2: NJ Store change-of-mind returns (A-34).**
- Unopened, sealed capsule, label intact, resaleable condition, not heat-exposed.
- Within **14 days** of delivery/pickup, with the order number.
- Remedy: **full value as store credit**, or **refund to the original payment minus a 15% restocking fee**.
- Returned in person to the NJ Store, or via a scheduled return pickup (the delivery fee for the zone is deducted, A-10).

**RTN-R3: NY Store change-of-mind returns (A-35).** **Not accepted.** Wine sales are final except under RTN-R1. (Exceptions only with human approval for exceptional circumstances; see §6.)

**RTN-R4: Never returnable for change of mind (both states):**
- Opened bottles (that are not defective).
- Special orders (A-28), pre-arrivals/futures (A-25), allocated and collectible/older-vintage items, items marked `final_sale`.
- Large formats ≥ 3 L.
- Gift cards (A-56).
- Items damaged after delivery (dropped, stored hot, frozen).

**RTN-R5: Proof of purchase.** Order number (online) or receipt (in-store). Account history counts as proof.

**RTN-R6: Evidence.** Damage and defect claims need photos (bottle, label, fill level/cork, packaging) through `request_evidence_upload`. The agent never asks for photos of people or IDs.

**RTN-R7: Refund method.** Original payment method, or store credit if the customer prefers (instant). Timing per A-36. See [refunds-and-store-credit.md](refunds-and-store-credit.md).

**RTN-R8: Discount recalculation.** Refunds reflect discounts allocated to returned items; if a return drops an order below a discount tier or code minimum, the lost discount is deducted from the refund (customer-initiated returns only, never for RTN-R1 claims).

**RTN-R9: Abuse prevention.** Accounts with unusual claim frequency (e.g., more than 3 claims in 90 days) are routed to human review (A-62). The agent stays neutral and doesn't accuse.

## 3. Decision tree

```
1. Is the issue damage, defect, wrong/missing item, listing error, or a policy-violating substitution?
   └─ YES → RTN-R1 path → check the window (48h / 7d / 30d) → evidence → remedy (see sub-docs)
   └─ NO (change of mind) ↓
2. Which store fulfilled the order?
   ├─ NY Store → RTN-R3: not accepted → offer helpful alternatives (§5)
   └─ NJ Store ↓
3. Is the item excluded (RTN-R4)?  → YES → not accepted
4. Unopened, resaleable, within 14 days, order number?  → NO → not accepted
   └─ YES → offer: full store credit OR refund minus 15% → create_return_request(reason="change_of_mind")
            → arrange drop-off or return pickup
```

## 4. Workflow (all return types)

1. Identify the order (`get_order`); confirm items, quantities, delivery date and fulfilling store.
2. Classify the reason (RTN-R1 type or change of mind) and check the window.
3. Explain eligibility and remedy options **before** creating anything.
4. On explicit confirmation → `create_return_request(order_id, items, reason_code, evidence_refs, customer_notes)`.
5. If evidence is needed → `request_evidence_upload` → wait for the upload (the tool updates `eligibility`).
6. Handle the tool result:
   - `auto_approved` → issue the remedy (refund/credit/replacement) within authority (A-60).
   - `needs_review` → tell the customer it's with the team and give the SLA (P2: 4 business hours).
   - `ineligible` → explain `ineligible_reason` kindly; offer alternatives.
7. Confirm the RMA number, the next steps (pickup/drop-off), and the refund timing.

## 5. Helpful alternatives when a return isn't possible

- **Didn't like the taste:** offer tips (serve slightly cooler/warmer, decant, pair with food), and future recommendations tuned to their feedback (update the taste profile with consent).
- **Bought too much for a party (NY):** suggest storage tips (most wines keep well unopened).
- **Gift they didn't want:** in NJ, store credit at full value within 14 days if unopened.

## 6. Exceptions (human approval only, P2 `policy_exception_request`)

Consider: outside window with a documented reason (hospitalization, our delayed notification), first-time customer with a large unopened party order in NY (exception requests are reviewed by compliance first; Q-2), bereavement. The agent can **submit** the request but can't promise approval.

## 7. Response examples

> "I'm sorry the Malbec wasn't to your taste. Since it was opened and isn't faulty, we can't take it back. But tell me what you didn't enjoy, and I'll find you something you'll like better next time."

> "Your order came from our NJ store, and the 4 bottles are unopened and within 14 days, so you can return them. You can choose full store credit of $96.00, or a refund of $81.60 to your card (that includes a 15% restocking fee). You can drop them at the store, or we can pick them up for $5.99. Which works best?"

> "Our New York store isn't able to accept returns of wine unless there's a problem with the bottle or our order. If anything was damaged, wrong or faulty, I'll fix it right away."
