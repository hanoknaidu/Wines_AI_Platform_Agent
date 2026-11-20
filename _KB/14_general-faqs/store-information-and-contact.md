---
id: KB-FAQ-001
title: Store Information, Hours and Contact Channels
category: general
subcategory: store-info
doc_type: reference
intents: [store.info, human.request, pickup.question]
tools: [get_store_info, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: medium
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: store-operations
status: active
depends_on_assumptions: [A-06, A-07, A-63, A-80, A-81, A-82]
related: [KB-ORD-005, KB-SYS-006, KB-DSC-005]
---

# Store Information, Hours and Contact Channels

## 1. Our stores

| | NJ Store | NY Store |
|---|---|---|
| License | NJ Plenary Retail Distribution License | NY SLA retail liquor store license |
| Serves | NJ addresses (delivery/shipping) and in-store/pickup customers | NY addresses and in-store/pickup customers |
| Default hours (A-80, A-81) | Mon–Sat 9 am – 10 pm; Sun 10 am – 7 pm | Mon–Sat 9 am – 10 pm; Sun 10 am – 8 pm |
| Special assortment | Non-alcoholic wines (A-06) | — |

**Live address, phone, hours, holiday hours and events always come from `get_store_info(location)`.** Hours can change for holidays, weather or local rules (NJ hours of sale are set by each municipality; NY Sunday sales are allowed 10 am–10 pm since 2023).

## 2. Holidays (A-82)

- **Closed:** Thanksgiving Day and Christmas Day (NY retail liquor stores must close on Christmas).
- **Reduced hours:** New Year's Day, and possibly Christmas Eve/New Year's Eve (check `get_store_info`).
- Delivery and shipping cutoffs before holidays: `get_fulfillment_options`.

## 3. Contact channels

| Channel | Availability | Best for |
|---|---|---|
| AI chat assistant (this) | 24/7 | Recommendations, orders, returns, account help |
| Human support (chat handoff, email, phone) | 9 am – 9 pm ET daily | Complex issues, escalations |
| Store phone | Store hours | Same-day pickup questions, in-store availability |
| Email support | Replies within 1 business day (P3) | Non-urgent questions, documents |

Escalation priorities and SLAs: [escalation-matrix.md](../00_system/escalation-matrix.md).

## 4. In-store services (typical; confirm with `get_store_info.services`)

- Pickup counter and curbside pickup.
- Staff recommendations; tastings on scheduled days (21+, ID required).
- Gift cards; gift wrapping/bags if offered.
- Chilled wine section (if offered).
- Accessibility: step-free entrance and curbside for customers who prefer not to come inside (confirm per store).

## 5. Common questions

**"Can I buy in store what I see online?"** Generally yes, from the same store. Online stock holds back a small buffer, and some items are online- or in-store-only (STK statuses).

**"Do you have parking?"** Use `get_store_info.parking` if available; otherwise suggest calling the store.

**"Are you hiring / can I sell my wine to you / I'm a distributor."** Route: careers page; we don't buy from private sellers (BRD-R1); vendor inquiries → P3 merchandising.

## 6. Response example

> "Our NY store is open today, Sunday, from 10 am to 8 pm. If you'd like to pick up an order there today, place it by about 6 pm so it's ready in time."
