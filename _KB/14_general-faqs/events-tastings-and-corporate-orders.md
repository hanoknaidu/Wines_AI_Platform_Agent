---
id: KB-FAQ-005
title: Events, Tastings and Corporate Orders
category: general
subcategory: events-corporate
doc_type: workflow
intents: [events.corporate, stock.bulk_quantity, gift.order, recommend.by_occasion]
tools: [get_store_info, create_support_ticket, search_products, check_inventory, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: medium
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: events-and-corporate
status: active
depends_on_assumptions: [A-01, A-02, A-26, A-29, A-50, A-55]
related: [KB-STK-007, KB-SPK-005, KB-ORD-009, KB-FAQ-004, KB-SYS-003]
---

# Events, Tastings and Corporate Orders

## 1. In-store tastings

- Scheduled tastings and classes are listed in `get_store_info(location).events` (date, time, theme, price, RSVP).
- **21+ only; ID required.** Tasting sizes and quantities follow state rules; staff may refuse service to anyone who appears intoxicated.
- The agent can share upcoming events and, if supported, RSVP the customer.

## 2. Private events (weddings, parties, fundraisers)

**What we offer:** wine selection help, quantity planning, reserved stock, scheduled delivery to an NJ/NY address (A-01, A-02), and mixed-case pricing on eligible wines (A-50). **What we don't offer** (unless a program exists): bartending/serving staff, glassware rentals, ice, or on-site sales. Venues may require licensed caterers/bartenders; customers should check their venue's rules.

**Intake** (`create_support_ticket(category="event_order", priority="P2")`):
- Event type, date, venue address, guest count, delivery date/window and on-site 21+ contact.
- Preferred styles/budget or a request for recommendations.
- Whether non-alcoholic options are needed (NJ Store only).
- Return expectations: share NJ/NY return rules **before** ordering (STK-007 §5).

**Quantity guidance:** [sparkling-occasions-gifting-and-handling.md](../04_sparkling-champagne-prosecco/sparkling-occasions-gifting-and-handling.md) and [price-bands-and-budget-guidance.md](../08_pricing/price-bands-and-budget-guidance.md).

## 3. Corporate gifting

| Service | Details |
|---|---|
| Multi-recipient gifts | Upload a recipient list (NJ/NY addresses only, 21+ recipients); each gift follows gift-order rules |
| Gift cards in bulk | Digital or physical, invoiced |
| Branded notes | Custom message cards; producer gift boxes |
| Invoicing | Available via the corporate team only (A-29); terms set by finance |
| Tax-exempt organizations | Handled by the corporate team with documentation |
| Lead time | Ideally 2+ weeks; December peaks need 3–4 weeks |

**Compliance notes:** recipients must be 21+ and present with ID; no gifts to recipients outside NJ/NY; no gifts intended for minors; gifts to government employees/clients may be subject to the recipient organization's rules (the purchaser is responsible). Pricing for corporate orders follows published programs (A-55); no private discounts.

## 4. Business purchases for resale

On-premises licensees (restaurants, bars) or other businesses buying **for resale**: we can't process them through consumer checkout (PL-R4, G9). NY's 2026 retail-to-retail allowance has limits; staff handle eligible requests. Route to the business team (P2).

## 5. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| At an in-store tasting, someone appeared to be served while under 21 or intoxicated | P1 | `handoff_compliance_incident` | Include store, date, time and what the customer saw |
| Signs the event involves guests under 21 drinking (e.g., a high-school graduation party) | P1 if an order exists | `underage_risk` | Decline (G1); with no order yet, just decline |
| Private event over 60 bottles or $2,500 (A-26), or any event needing reserved stock | P2 | `create_support_ticket(category="event_order")` | Collect the §2 intake details |
| Corporate gifting: recipient lists, invoicing, tax-exempt documentation, bulk gift cards | P2 | `create_support_ticket(category="corporate_gifting")` | Include the recipient count, budget, deadline and whether any recipients are outside NJ/NY |
| Event within 7 days and the event ticket has no response after 4 business hours | P2 | `bulk_order` | Live handoff; include the ticket ID and event date |
| Business purchase for resale (§4) | P2 | `business_sales` | Don't process it through consumer checkout |
| Complaint about tasting or events staff | P2 (P1 if safety) | `conduct_complaint` | Thank them and record the details |

**Handle without escalating:** listing upcoming tastings, quantity planning, style and budget recommendations, and explaining what we don't provide (bartending, glassware, ice).

## 6. Response examples

> "Congratulations on the wedding! For 120 guests, our events team will put together a plan with you: quantities, a red/white/sparkling mix in your budget, and a scheduled delivery to the venue. I've sent them your details (ticket #E-8840), and they'll be in touch within 4 business hours."

> "For client gifts to 40 people, our corporate team can handle the recipient list, gift notes and invoicing. Just note that we can only deliver to New Jersey and New York addresses, and each recipient needs to be 21+ and available to sign."
