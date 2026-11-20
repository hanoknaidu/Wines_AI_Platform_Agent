---
id: KB-ORD-007
title: In-State Shipping Policy (NJ and NY Only)
category: orders
subcategory: shipping
doc_type: policy
intents: [shipping.question, delivery.eligibility, order.status, compliance.out_of_state]
tools: [get_fulfillment_options, track_shipment, get_order_status, calculate_order_totals, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: fulfillment-operations
status: active
depends_on_assumptions: [A-01, A-02, A-15, A-18, A-19, A-20, A-30, A-31, A-60]
related: [KB-SYS-003, KB-ORD-006, KB-ORD-008, KB-RTN-002]
---

# In-State Shipping Policy

## 1. Summary

| Item | Rule |
|---|---|
| Where | Addresses **in the same state as the fulfilling store**: NJ Store → NJ addresses; NY Store → NY addresses (A-01). **No shipping outside NJ/NY** (A-02) |
| When used | Addresses outside local delivery zones (beyond 15 miles) |
| Carriers | UPS or FedEx under the store's alcohol shipping agreements; **adult signature (21+) required**; USPS cannot carry alcohol |
| Fees (A-15) | $14.99 (1–6 bottles), $19.99 (7–12), +$5 per additional 6 bottles; **free over $199** product subtotal |
| Processing | Ships within 1–2 business days of order (Mon–Fri, excluding holidays) |
| Transit | Typically 1–3 business days in-state (ground) |
| Packaging | Molded pulp or foam shippers designed for wine; bottles shipped upright or as designed |
| Tracking | Emailed when the label is created; `track_shipment` |

## 2. Why no out-of-state shipping

State laws control who may ship alcohol to consumers. New York's direct-shipping law covers licensed **wineries**, not out-of-state retailers, and New York's regulator has acted against retailers shipping to other states. To stay compliant, we deliver and ship only within NJ and NY, from the store in the same state (A-01, A-02).

**Customer-facing line:**
> "Because of state alcohol shipping laws, we can only ship within New Jersey and New York, from our store in that same state."

## 3. Adult signature and delivery attempts (A-18)

- A 21+ adult with a valid ID must sign. Carriers won't leave packages unattended.
- Carriers typically make **up to 3 attempts**, then return the parcel to the store.
- Customers can often **reschedule** or **redirect** with the carrier via the tracking link. Redirect to carrier facilities is at the carrier's discretion and requires 21+ ID at pickup. Most retail "access point" lockers cannot accept alcohol.
- Shipping to a **workplace** is a good option for people who are out during the day (21+ recipient with ID).

## 4. Weather holds (A-19)

- When forecasts at origin or destination are above **85°F** or below **28°F**, shipments may be held to protect the wine.
- Customers are notified and can: (a) wait for safe weather (no charge), (b) choose insulated/expedited shipping at the quoted extra cost, or (c) switch to pickup/local delivery if eligible.
- Heat-damage claims for shipments the customer asked to send **despite** a hold are reviewed case by case (P2), since the customer accepted the risk.

## 5. Restricted destinations (A-20)

No PO boxes, APO/FPO, K-12 schools, college dorms, or addresses outside NJ/NY. `get_fulfillment_options.restricted_destination_flag` blocks them at checkout.

## 6. Problems in transit

| Problem | Handling |
|---|---|
| Tracking hasn't moved for 2+ business days | Carrier trace: `escalate_to_human(reason_code="fulfillment_delay", priority="P2")` |
| Carrier marked "delivered" but the customer has nothing | Check the signature name in tracking; ask the customer to check with household/building; then P2 investigation (missing-item claim, A-31) |
| Box arrived wet/leaking or broken | Damage claim within 48 hours with photos (A-30; [damaged-or-broken-items.md](../12_returns-refunds-damages/damaged-or-broken-items.md)) |
| Returned to sender after failed attempts | Refund minus original shipping; first-time return shipping waived (A-18) |

## 7. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Carrier handed the package to someone under 21, left it unattended, or a signature name is unknown to the customer | P1 | `handoff_compliance_incident` | Include tracking number, signature name and delivery scan time |
| Tracking hasn't moved for 2+ business days | P2 | `fulfillment_delay` | Include tracking number and the last scan; the team opens a carrier trace |
| Carrier shows "delivered", and the customer has checked with household and building | P2 | `delivered_not_received` | Follow [wrong-or-missing-items.md](../12_returns-refunds-damages/wrong-or-missing-items.md) §5 |
| Heat or cold damage on a shipment the customer asked to send despite a weather hold (§4) | P2 | `claim_review` | Include the hold notice date and the customer's choice; don't promise a refund |
| Damage claim whose remedy is over $150 (A-60) | P2 | `refund_over_limit` | Follow [damaged-or-broken-items.md](../12_returns-refunds-damages/damaged-or-broken-items.md) |
| Repeated carrier damage or losses at the same address or area | P3 | `create_support_ticket(category="carrier_issue")` | List the affected order numbers |

**Handle without escalating:** fee quotes, weather-hold choices, rescheduling or redirecting through the carrier's tracking link, returned-to-sender refunds within A-60, and requests to ship out of state or to an NJ/NY address for forwarding. Decline those per G4; they aren't escalations.

## 8. Response examples

> "We can ship to Buffalo from our New York store. Your 4 bottles would be $14.99 to ship (free on orders over $199), arriving in about 1–3 business days after it ships. Someone 21+ will need to sign. Would a work address be easier?"

> "I'm sorry, we can't ship to Pennsylvania. State laws only allow us to ship within New Jersey and New York. For a gift there, a licensed shop in Pennsylvania would be the best option."
