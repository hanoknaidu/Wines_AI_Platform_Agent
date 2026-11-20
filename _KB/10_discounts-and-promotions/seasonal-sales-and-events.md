---
id: KB-DSC-005
title: Seasonal Sales, Featured Promotions and In-Store Events
category: discounts
subcategory: seasonal
doc_type: guide
intents: [discount.current_offers, recommend.by_occasion, events.corporate, store.info]
tools: [get_active_promotions, get_store_info, update_communication_preferences, search_products]
jurisdictions: [NJ, NY]
audience: agent
priority: medium
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: marketing
status: active
depends_on_assumptions: [A-03, A-06, A-13, A-19, A-55, A-82]
related: [KB-DSC-001, KB-SPK-005, KB-FAQ-005, KB-ACC-005]
---

# Seasonal Sales, Featured Promotions and In-Store Events

## 1. Typical promotional calendar (planning guide)

Promotions vary by year and store (A-03). This calendar tells the agent **what kinds** of promotions are typical; **what's actually running** comes only from `get_active_promotions`.

| Period | Typical focus | Agent notes |
|---|---|---|
| January | "Dry January" NA features (NJ), low-calorie features, post-holiday clearance | NA wine is NJ Store only (A-06) |
| February | Valentine's sparkling and rosé, red wine for dinner | Gift boxes |
| March | St. Patrick's; Spring rosé arrivals start | New-vintage rosé |
| April | Passover kosher wines; Easter; Earth Month organic/biodynamic features | Kosher for Passover attribute |
| May | Mother's Day, graduations, Memorial Day | Peak gifting/sparkling |
| June | Father's Day (bold reds), weddings, summer rosé | Bulk orders |
| July–August | Summer whites and rosé, chillable reds, July 4th | Weather shipping holds (A-19) |
| September | Labor Day, harvest season, new fall releases | Futures offers (Bordeaux campaigns are usually spring) |
| October | Fall reds, Halloween | — |
| November | Beaujolais Nouveau (3rd Thursday), Thanksgiving, Black Friday/Cyber Monday | Delivery slots fill Wed before Thanksgiving; stores closed Thanksgiving Day (A-82) |
| December | Champagne and sparkling, holiday gifting, corporate gifts, New Year's Eve | Closed Christmas Day (A-82); order early |

## 2. Rules

**SS-R1: No forecasting.** The agent doesn't promise or predict future sales ("wait until next week, it'll be on sale"). If asked: "I can't share future promotions, but you can opt in to our emails or texts to hear about sales first." Then offer `update_communication_preferences` (with explicit consent).

**SS-R2: Store-specific.** Always check the promotion's location; NJ and NY promotions differ.

**SS-R3: End times** are in store local time (Eastern). Orders placed before the end time get the promotion even if fulfilled later.

**SS-R4: Event-day early access** (Insider tier) is access-only; prices are the same for everyone (A-55).

**SS-R5: Holiday cutoffs.** Delivery and shipping cutoffs for holidays come from `get_fulfillment_options`. The agent recommends ordering early during peaks.

## 3. In-store events and tastings

- Stores may host **tastings** (producer visits, themed flights) and classes. Details (date, time, cost, RSVP) come from `get_store_info(location).events`.
- Tastings follow state rules (e.g., sample sizes and limits are set by state regulations; attendees must be 21+ with ID).
- **Agent:** share upcoming events, help RSVP if supported, mention that ID is required.
- Private tastings or corporate events → [events-tastings-and-corporate-orders.md](../14_general-faqs/events-tastings-and-corporate-orders.md).

## 4. Response examples

> "This week at our NJ store: 20% off select Italian reds and a Champagne feature through Sunday at 11:59 pm. There's also a free Saturday tasting of Oregon Pinot Noir from 2–5 pm (ID required). Would you like me to show you the Italian reds on sale?"

> "I can't share upcoming sales, but if you'd like a heads-up, I can turn on promotional emails for you. Want me to?"
