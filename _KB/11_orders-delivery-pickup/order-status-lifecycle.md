---
id: KB-ORD-002
title: Order Status Lifecycle
category: orders
subcategory: status
doc_type: reference
intents: [order.status, order.modify, order.cancel, delivery.failed, pickup.question]
tools: [get_order_status, get_order, track_shipment]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: fulfillment-operations
status: active
depends_on_assumptions: [A-16, A-17, A-18, A-19, A-21, A-23, A-24, A-36, A-61]
related: [KB-ORD-003, KB-ORD-008, KB-STK-003, KB-SYS-006]
---

# Order Status Lifecycle

## 1. Status flow

```
placed → age_verification_pending* → confirmed → picking → [substitution_pending*] →
   ├─ ready_for_pickup → picked_up → completed
   ├─ out_for_delivery → delivered → completed
   │                    └─ delivery_failed → redelivery_scheduled | returned_to_store
   └─ label_created → in_transit → delivered → completed
                                  └─ delivery_exception → returned_to_sender
Split shipments: in_transit → partially_fulfilled (some shipments delivered, others pending) → delivered → completed
Side states: on_hold (weather / fraud review / bulk review / address issue), cancelled
(* only when applicable)
```

**Payment status is separate.** `get_order_status` also returns `payment_status`: `pending`, `authorized`, `partially_paid`, `paid`, `partially_refunded`, `refunded`, `voided`, `failed`. An order can be `completed` and `partially_refunded` at the same time. Answer "where's my order?" from `status`, and "where's my money?" from `payment_status` plus `get_return_status`.

## 2. Status reference

| Status | Meaning | Customer can still… | Typical SLA | Agent says |
|---|---|---|---|---|
| `placed` | Order received, payment authorized | Edit, cancel (free) | Minutes | "We've got your order." |
| `age_verification_pending` | Waiting for first-order ID check | Complete verification; cancel | Until verified | "Your order is waiting on a quick ID check. Here's the link." |
| `confirmed` | Verified; queued for picking | Edit, cancel (free) | Pick starts ~1–2 h before window | "Confirmed and in line for packing." |
| `picking` | Staff are gathering items | Request cancel (not guaranteed, A-21); respond to substitutions | 15–60 min | "Your order is being packed right now." |
| `substitution_pending` | A decision is needed on a short item | Approve/decline (24 h or same-day cutoff) | — | Present options (STK-003) |
| `ready_for_pickup` | Packed, at the store | Pick up within 7 days (A-16) | — | "Ready! Bring your ID." |
| `out_for_delivery` | Driver en route | Contact via tracking link; cannot cancel | Within window | "Your driver is on the way; ETA [time]." |
| `label_created` | Shipping label created; awaiting carrier scan | Cancellation not guaranteed | 1 business day | "Packed and waiting for carrier pickup." |
| `in_transit` | With UPS/FedEx | Manage with carrier (hold, reschedule) | 1–3 business days | Give the tracking link |
| `partially_fulfilled` | Order split into several shipments; some delivered, the rest still on the way (e.g., a backordered line) | Track each shipment; report problems on delivered items | Per shipment | "Part of your order has arrived; the rest is on its way. Here's tracking for each box." |
| `delivery_exception` | Carrier issue (no adult present, address problem, weather) | Reschedule with carrier | — | Explain the next attempt (A-18) |
| `delivered` / `picked_up` | Handed to a 21+ adult with ID | Report problems (48 h damage, 7 days wrong/missing, 30 days defect) | — | "Delivered at [time]." |
| `delivery_failed` | Local delivery not completed | Schedule redelivery (1 free, A-17) | — | See failed-delivery doc |
| `returned_to_store` / `returned_to_sender` | Back at the store/sender | Pick up within 7 days, or receive refund minus fees | — | See failed-delivery doc |
| `on_hold` | Weather (A-19), fraud review, bulk review, address verification | Depends on reason | Varies | Explain the reason in general terms (don't reveal fraud-rule details) |
| `cancelled` | Cancelled by the customer or the Store | — | Refund started within 1 business day | Refund timeline (A-36) |
| `completed` | Closed | Returns/claims within windows | — | — |

## 3. "Where is my order?" workflow

1. Get the order number (or `list_orders` for a verified customer).
2. `get_order_status(order_id)`.
3. If shipping: `track_shipment(order_id)` for carrier events.
4. Answer with the status, ETA window, and the one thing the customer can do now.
5. **Late?** Compare with the promised window:
   - Local delivery > 30 min past the window end → apologize; check `driver_status`; if > 60 min late or the window was missed, offer goodwill credit (A-61) and reschedule options.
   - Shipping > 2 business days past the carrier estimate → `escalate_to_human(reason_code="fulfillment_delay", priority="P2")` or carrier trace.
6. **Status looks stuck** (e.g., `picking` for > 3 hours, `ready_for_pickup` with no notification): P2 `fulfillment_delay`.

## 4. Response examples

> "Your order #10482 is out for delivery. The driver's ETA is 4:20–4:40 pm, within your 4–6 pm window. Please have a 21+ ID ready; they can't leave it at the door."

> "Your shipment is with UPS and scheduled for delivery tomorrow. Since it needs an adult signature, if no one will be home you can reschedule or redirect it with UPS using this tracking link: …"
