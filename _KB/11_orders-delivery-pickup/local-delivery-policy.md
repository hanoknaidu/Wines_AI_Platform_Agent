---
id: KB-ORD-004
title: Local Delivery Policy
category: orders
subcategory: local-delivery
doc_type: policy
intents: [delivery.eligibility, delivery.fees_and_minimums, order.status, order.modify, feedback.complaint]
tools: [get_fulfillment_options, calculate_order_totals, get_order_status, reschedule_delivery, issue_store_credit, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: fulfillment-operations
status: active
depends_on_assumptions: [A-01, A-07, A-10, A-11, A-12, A-13, A-14, A-17, A-20, A-26, A-27, A-61, A-80, A-81, A-82]
related: [KB-ORD-006, KB-ORD-008, KB-PRC-005, KB-SYS-003]
---

# Local Delivery Policy

## 1. Service summary

| Item | Rule |
|---|---|
| Who delivers | The licensed store's own drivers, or a permitted third-party delivery service where state rules allow (NJ: transit-insignia vehicles or 2022 Third-Party Delivery Permit holders; NY: per SLA rules). Open question Q-6 |
| Area | Up to 15 miles from the fulfilling store (`get_fulfillment_options.local_delivery.eligible`) |
| Zones & fees (A-10) | Zone 1 (0–5 mi): $5.99 · Zone 2 (5–15 mi): $9.99 |
| Minimum (A-11) | $40 product subtotal (after discounts, before tax) |
| Free delivery (A-12) | Product subtotal ≥ $99 |
| Windows (A-14) | 2-hour windows, 11:00 am – 9:00 pm, within legal hours of sale (A-07) and store hours (A-80, A-81) |
| Same-day cutoff (A-13) | Order by 6:00 pm Mon–Sat, 3:00 pm Sun, subject to slot availability |
| Scheduling ahead | Up to 7 days ahead |
| Closed days (A-82) | No delivery on Thanksgiving or Christmas Day |
| Tip (A-27) | Optional, shown separately, goes to the driver |

## 2. Handoff rules (compliance)

1. **In person only** to an adult **21+** with valid photo ID (see [age-verification-at-handoff.md](age-verification-at-handoff.md)).
2. **No leave-at-door,** no lockers, no handing to minors, no handing to a visibly intoxicated person.
3. **Restricted destinations (A-20):** PO boxes, K-12 schools, college dormitories, unattended locations. Hotels only to a named 21+ guest in person (not the front desk). Parks/beaches/public spaces: not permitted (open-container and safety concerns); deliver to an address instead.
4. **Doorman/concierge buildings:** a doorman or concierge may accept only if they are 21+, show valid ID, and agree to sign; otherwise the driver will call the customer. Many buildings don't allow this. Advise customers to be available.
5. **Businesses/offices:** allowed with a 21+ recipient with ID during the window.

## 3. Workflow: "Do you deliver to me?"

1. Get the full address (or ZIP for a quick check).
2. `get_fulfillment_options(address)` → eligible? zone, fee, minimum, windows; `restricted_destination_flag`.
3. Answer: eligibility + fee + earliest window. If not eligible for local delivery, offer **in-state shipping** or **pickup**.
4. If the address is outside NJ/NY → G4.

## 4. Late or missed deliveries

| Situation | Agent action |
|---|---|
| Driver running late (ETA within 30 min after the window) | Share the live ETA; apologize |
| > 60 min after the window end, or the window was missed entirely by us | Apologize; offer reschedule or cancel (full refund, including fee); offer **goodwill credit up to $15** (A-61; once per 90 days) |
| Customer missed the driver | Failed-delivery rules (A-17) |
| Driver conduct complaint | Thank them; collect details; P2 `conduct_complaint` (P1 if safety) |
| Driver refused due to ID/intoxication | Explain the compliance reason respectfully; redelivery when an eligible adult is present (no fee for the first redelivery) |

## 5. Edge cases

- **Weather/emergencies:** the store may pause deliveries for safety; affected customers get a reschedule or cancel option.
- **Big orders** (stairs, no elevator, 10+ cases): note in delivery instructions; the bulk team may schedule (A-26).
- **Customer wants delivery "to my car" or a meeting point:** not permitted; deliver to an address.
- **Third-party marketplace orders** (if the store sells via delivery apps): those platforms' policies apply; the agent supports only our own orders.

## 6. Escalation

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Driver handed the order to someone under 21 or visibly intoxicated, or left it unattended | P1 | `handoff_compliance_incident` | Include order number, address, time and what the customer reported |
| Driver behavior that raises a safety concern (threats, harassment, unsafe driving) | P1 | `conduct_complaint` | Check the customer is safe; record the details |
| Repeated pressure to skip the ID check or to leave the order at the door after the rule is explained | P1 | `fraud_signal` | Don't change the order (G9) |
| Order dispatched more than 4 hours past its window, or status stuck with no live ETA | P2 | `fulfillment_delay` | Offer reschedule or cancel first (§4) |
| Driver conduct complaint without a safety concern | P2 | `conduct_complaint` | Thank them; collect time and details; don't promise disciplinary outcomes |
| Customer disputes a driver's ID or intoxication refusal (e.g., says a valid ID was rejected) | P2 | `conduct_complaint` | Explain the compliance reason respectfully; never overrule the driver |
| A second late delivery within 90 days, when the goodwill credit (A-61) has already been used | P2 | `policy_exception_request` | Include both order numbers and the earlier credit |
| Orders over 60 bottles or $2,500, or 10+ cases that need special handling (A-26) | P2 | `bulk_order` | Collect date, address access and stairs/elevator details |

**Handle without escalating:** eligibility and fee questions, late deliveries within the first goodwill credit, reschedules, and requests for parks, cars or meeting points (decline and offer an address).

## 7. Response examples

> "Yes, we deliver to 07302 from our NJ store. You're in Zone 1, so delivery is $5.99, free on orders of $99 or more. The earliest window today is 5–7 pm if you order by 6 pm."

> "I'm really sorry your delivery missed its window. I've added a $15 credit to your account. Would you like me to reschedule for tomorrow morning, or cancel with a full refund including the delivery fee?"
