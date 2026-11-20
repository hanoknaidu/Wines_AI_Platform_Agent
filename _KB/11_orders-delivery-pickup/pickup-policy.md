---
id: KB-ORD-005
title: In-Store and Curbside Pickup Policy
category: orders
subcategory: pickup
doc_type: policy
intents: [pickup.question, order.status, order.modify]
tools: [get_order_status, get_store_info, modify_order, cancel_order, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: store-operations
status: active
depends_on_assumptions: [A-05, A-16, A-28, A-29, A-29b, A-34, A-80, A-81, A-82]
related: [KB-ORD-006, KB-ORD-002, KB-FAQ-001]
---

# In-Store and Curbside Pickup Policy

## 1. Summary

| Item | Rule |
|---|---|
| Cost | Free (A-16) |
| Ready time | About **2 hours** after ordering during store hours; you'll get a "ready" notification. Orders placed near closing are ready the next morning |
| Hold period | **7 days** after "ready". Then the order is cancelled and fully refunded (no restocking fee) |
| Payment | Prepaid online (A-29) |
| Where | The store you chose: NJ Store or NY Store. Pickup counter in store, or **curbside** (tap "I'm here" in the notification or call the store) |
| Hours | Store hours (`get_store_info`; A-80, A-81); not on closed days (A-82) |

## 2. Who can pick up

- The **purchaser**, or one **alternate pickup person** named on the order (A-29b).
- Must be **21+** with a valid photo ID whose name matches the order (purchaser or alternate) (see [age-verification-at-handoff.md](age-verification-at-handoff.md)).
- Staff may also refuse if the person appears visibly intoxicated, or if it appears the alcohol is being obtained for a minor.
- Curbside: staff check ID at the car. If passengers appear underage and staff have concerns, they may refuse.

## 3. Workflow

1. **"Is my order ready?"** → `get_order_status`. If `ready_for_pickup`: share the store address, hours and curbside instructions.
2. **"Can someone else pick up?"** → if there's no alternate yet, add one via `modify_order(changes={alternate_pickup:{name}})` (identity-verified customer). Remind them about ID.
3. **"Can I pick up later than 7 days?"** → one extension of up to 7 more days on request (store discretion; stock may be released for allocated items).
4. **"Change to delivery?"** → `modify_order` to delivery; fees and windows apply.

## 4. Edge cases

| Case | Handling |
|---|---|
| Name on ID differs (married name, nickname) | Staff may accept with reasonable matching and another proof; otherwise update the alternate pickup name in advance |
| Arrives with an expired ID | Not accepted; order held for the remaining hold period |
| Customer not happy with an item at pickup (e.g., damaged label, wrong item) | Staff swap or refund on the spot; for a change of mind at the counter, items can be declined before acceptance for a refund (no restocking fee, since the sale isn't completed) |
| Ordered at the NY Store but went to the NJ Store | Orders can't be transferred between stores; direct them to the right store, or cancel and re-order |
| Unclaimed pre-arrival/special order | Follows A-28 (30 days, then delivered by default method) |

## 5. Escalation

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Order handed to someone without a valid ID, or to someone under 21 | P1 | `handoff_compliance_incident` | Include the order number and what the customer reported |
| The customer says someone they don't know collected their order | P1 | `fraud_signal` | Don't disclose who collected it; the store reviews its pickup records |
| Staff conduct that raises a safety concern | P1 | `conduct_complaint` | Check the customer is safe; record time and details |
| Status `ready_for_pickup` but the customer was never notified, or not ready more than 2 hours past the ready time during store hours | P2 | `fulfillment_delay` | Include the order time and current status |
| Customer is at the store and staff can't find the order | P2 | `fulfillment_delay` | Ask for a live handoff so the store is contacted right away |
| Customer disputes a refusal at pickup (ID, intoxication, alcohol for a minor) | P2 | `conduct_complaint` | Explain the rule (§2) respectfully; never overrule staff |
| A further extension beyond the one 7-day extension (e.g., hospital stay, travel) | P2 | `policy_exception_request` | Include the original ready date |
| Allocated item released after the hold ended, and the customer disputes it | P2 | `pre_arrival_issue` | Include the allocation and hold dates |
| Staff conduct complaint without a safety concern | P2 | `conduct_complaint` | Thank them; don't promise outcomes |

**Handle without escalating:** "is it ready?" checks, adding an alternate pickup person, requesting the one 7-day extension, switching to delivery, wrong-store visits (direct them to the right store) and items declined at the counter.

**Handoff line**
> "I'm sorry you're waiting at the counter. I've flagged this to the store team as urgent so they can find your order now. Please stay where you are; someone should be with you shortly."

## 6. Response examples

> "Your order is ready at our NJ store, held until next Friday. For curbside, tap 'I'm here' in your text and we'll bring it out. Just have your ID ready."

> "Sure, I've added Jordan Lee as your alternate pickup person. They'll need to bring a valid photo ID showing they're 21 or older, with a name that matches."
