---
id: KB-ORD-008
title: Failed Delivery, Redelivery and Returned-to-Store Orders
category: orders
subcategory: failed-delivery
doc_type: workflow
intents: [delivery.failed, order.status, refund.status]
tools: [get_order_status, track_shipment, reschedule_delivery, cancel_order, issue_refund, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: fulfillment-operations
status: active
depends_on_assumptions: [A-16, A-17, A-18, A-36, A-60, A-61]
related: [KB-ORD-004, KB-ORD-006, KB-ORD-007, KB-RTN-005]
---

# Failed Delivery, Redelivery and Returned-to-Store Orders

## 1. Local delivery (A-17)

| Step | What happens |
|---|---|
| 1st failed attempt | Driver calls/texts; waits up to **10 minutes**; order returns to the store; status `delivery_failed` |
| Redelivery | **One redelivery is free.** The customer books a new window (`reschedule_delivery`) or switches to pickup |
| 2nd failed attempt | Order returns to the store (`returned_to_store`) and is held for **pickup for 7 days** |
| After 7 days unclaimed | Cancelled; refund of products and tax **minus the delivery fee** (if one was charged) |

**Fee waivers:** if the failure was caused by us (wrong address entered by staff, driver error, late beyond the window), all fees are waived and the attempt doesn't count. Goodwill credit may apply (A-61).

## 2. Carrier shipping (A-18)

| Step | What happens |
|---|---|
| Attempts | Carrier typically tries up to **3 times** (notice left; customer can reschedule/redirect via tracking) |
| Returned to sender | Store receives the parcel; inspects it |
| Refund | Product total + tax **minus the original shipping charge**; **return shipping waived the first time** (subsequent returns: return shipping also deducted) |
| Reship option | Instead of a refund, the customer may pay the shipping again to resend |

## 3. Compliance refusals

If the handoff was refused for compliance reasons (no valid ID, under 21, intoxication; see [age-verification-at-handoff.md](age-verification-at-handoff.md)), the same steps apply, with **no restocking fee**. Suspected supply-to-minors refusals have **no automatic redelivery**; they're escalated P1.

## 4. Workflow

1. `get_order_status` / `track_shipment` → confirm the failure and reason.
2. Explain what happened in one sentence, without blame.
3. Offer options in order: **redeliver** (free once) → **pickup** → **cancel/refund** (with fee deductions explained).
4. Act on the customer's choice after confirmation.
5. If the customer disputes the failure ("I was home!"), check driver notes; if unclear, waive the fee as a courtesy once (counts as goodwill within A-61) or escalate P2 for repeated issues.

## 5. Edge cases

| Case | Handling |
|---|---|
| Perishable concern (wine sat on a truck) | Store inspects returned parcels; heat-exposed returns are refunded or replaced per damage policy if the customer reports problems after redelivery |
| Customer moves between attempts | Change the address within the same state (OC-R5); otherwise cancel |
| Gift recipient unavailable repeatedly | Contact the purchaser; offer pickup by the recipient or refund |
| Customer requests "leave it with a neighbor" | Only if the neighbor is 21+ with ID and the customer names them in instructions; driver's discretion |

## 6. Escalation

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Handoff refused because the driver or carrier suspected the alcohol was for a minor (§3) | P1 | `handoff_compliance_incident` | Don't offer a redelivery; don't argue with the driver's decision |
| Tracking shows a signature from someone the customer doesn't know | P1 | `handoff_compliance_incident` | Follow [wrong-or-missing-items.md](../12_returns-refunds-damages/wrong-or-missing-items.md) §5 |
| Driver behaved unsafely or threateningly during the attempt | P1 | `conduct_complaint` | Record time, address and what happened; check the customer is safe |
| Customer says the driver never tried, driver notes don't settle it, and the one courtesy waiver (A-61) was already used | P2 | `conduct_complaint` | Include the driver notes and the earlier waiver date |
| Parcel shown as returned to sender, but the store hasn't received it after 5 business days | P2 | `fulfillment_delay` | Include tracking number and carrier events |
| Refund after deductions is over $150 (A-60), or `issue_refund` returns `requires_approval` | P2 | `refund_over_limit` | Show the customer the calculation you submitted |

**Handle without escalating:** the free redelivery, switching to pickup, cancel-and-refund with deductions explained, one courtesy fee waiver, and refusals for missing ID or intoxication (explain respectfully; redeliver when an eligible adult is present).

## 7. Response examples

> "Our driver tried to deliver at 3:15 pm but couldn't reach anyone, so your order is back at the store. You get one free redelivery. Would you like tomorrow 11–1 or 5–7? Or you can pick it up at the store anytime this week."

> "Your package was returned after three delivery attempts. I can refund $96.12, which is your order total minus the $14.99 shipping charge (we've waived the return shipping), or reship it for $14.99. Which would you prefer?"
