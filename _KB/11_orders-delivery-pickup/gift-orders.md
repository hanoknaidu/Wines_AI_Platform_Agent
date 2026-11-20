---
id: KB-ORD-009
title: Gift Orders (Sending Wine to Someone Else)
category: orders
subcategory: gifts
doc_type: policy
intents: [gift.order, recommend.by_occasion, order.status]
tools: [get_fulfillment_options, search_products, add_to_cart, modify_order, get_order_status, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: fulfillment-operations
status: active
depends_on_assumptions: [A-01, A-02, A-04, A-20, A-23, A-24, A-26, A-34, A-35, A-56]
related: [KB-SYS-003, KB-SPK-005, KB-FAQ-004, KB-ORD-006, KB-FAQ-005]
---

# Gift Orders

## 1. Rules

**GF-R1: Recipient location.** The recipient's address must be in **NJ or NY** and is fulfilled by the store in that state (A-01, A-02). The purchaser can live anywhere, but must be 21+ with an account.

**GF-R2: Recipient age and presence.** The recipient (or another 21+ adult at the address) must be present with a valid ID. Gift orders can be marked **"named recipient only"**: only the named person may accept.

**GF-R3: Restricted destinations** (A-20) apply. No office mailrooms that won't sign; no dorms; no schools.

**GF-R4: Phone number.** A recipient phone number is required for delivery coordination (and is used only for that).

**GF-R5: Gift message & receipt.** A gift message (up to 250 characters) is printed on a card. The packing slip **doesn't show prices**. No alcohol-related content in messages that targets minors or encourages excessive drinking (staff may decline offensive messages).

**GF-R6: Decisions and returns belong to the purchaser.** Substitution approvals (A-24), vintage consents (A-23), redelivery decisions and refunds go to the **purchaser**. A recipient with a damaged/defective bottle can report it, and the remedy (replacement to the recipient, or refund to the purchaser) is coordinated with the purchaser.

**GF-R7: Gift packaging.** Options shown at checkout (e.g., producer gift boxes as separate SKUs, gift bags if offered). Shipped gifts use standard protective shippers; presentation packaging goes inside.

**GF-R8: Surprise gifts.** Alcohol can't be left unattended. For surprises, coordinate a window with someone at the address, or ship to the recipient's workplace.

## 2. Workflow

1. Recipient address → `get_fulfillment_options(address)` (eligibility, method, windows).
2. Wine selection (budget, recipient's taste if known; versatile picks otherwise) → `search_products` for the **recipient's** fulfilling store.
3. Add gift details: message, named-recipient flag, recipient phone, delivery instructions.
4. Choose the delivery date (before the occasion; peak seasons fill up).
5. Explain handoff requirements: "Someone 21+ with ID needs to receive it."

## 3. Edge cases

| Case | Handling |
|---|---|
| Purchaser in NJ, recipient in NY | Order is placed with the **NY Store** (catalog/prices from NY) |
| Recipient outside NJ/NY | Not available (G4) |
| Recipient under 21 | Not allowed (G1) |
| Corporate gifting to many recipients | Corporate team: bulk addresses, invoicing (see [events-tastings-and-corporate-orders.md](../14_general-faqs/events-tastings-and-corporate-orders.md)) |
| Gift card instead | Digital gift cards can be sent to anyone 21+ by email (A-56; [gift-cards.md](../14_general-faqs/gift-cards.md)) |
| Recipient wants to exchange the gift | NJ: unopened, within 14 days, store credit at full value to the **purchaser** (or a gift-receipt credit to the recipient if issued) (A-34). NY: not available (A-35) |
| Gift delivery failed | Purchaser is contacted; redelivery/pickup per failed-delivery rules |

## 4. Escalation

Gift orders involve two people, so protect both: **decisions go to the purchaser (GF-R6), and the recipient never sees prices or the purchaser's account details.**

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| A gift that was delivered was accepted by someone under 21, or the recipient reports a minor received it | P1 | `handoff_compliance_incident` | Include the order number and what the recipient or purchaser reported |
| Signs the gift is meant for someone under 21 ("for my nephew's 18th", a high-school address) on an existing order | P1 | `underage_risk` | Decline (G1); don't suggest changing the recipient's name or age. With no order yet, just decline |
| Many gifts to unrelated addresses from a new account, or repeated pressure to skip the ID check after the rule is explained (G9) | P1 | `fraud_signal` | Don't place or change the order; stay neutral |
| Corporate or multi-recipient gifting over 60 bottles or $2,500 (A-26) | P2 | `bulk_order` | Collect recipient count, budget and dates; see [events-tastings-and-corporate-orders.md](../14_general-faqs/events-tastings-and-corporate-orders.md) §3 |
| A delay on our side means the gift will miss the occasion date the customer gave | P2 | `fulfillment_delay` | Offer pickup by the recipient or a new window first; include the occasion date |
| Recipient reports damage or a wrong item, and the purchaser can't be reached within 2 business days | P3 | `create_support_ticket(category="gift_issue")` | Take the recipient's contact details and photos; promise only that the team will follow up |
| Exchange or return outside the NJ 14-day window (A-34) with a credible reason | P2 | `policy_exception_request` | NY has no change-of-mind returns (A-35); don't promise an exception |

**Handle without escalating:** recipient-address checks, NJ vs NY routing, gift messages and named-recipient flags, failed gift deliveries (contact the purchaser per [failed-delivery-and-redelivery.md](failed-delivery-and-redelivery.md)) and NJ exchanges within policy.

**Handoff line (recipient contacting us)**
> "Thank you for letting us know, and I'm sorry the gift arrived like this. Because the order belongs to the person who sent it, our team will sort out the replacement with them and keep you updated. I've opened ticket #… with your photos."

## 5. Response examples

> "Lovely idea! Since your sister lives in Hoboken, the gift will come from our NJ store. I can add a note card, and the packing slip won't show prices. Someone 21 or older will need to be home with ID to receive it. What day should it arrive?"

> "For a surprise, the safest option is delivering to her office, if someone there can sign, or coordinating a time with her roommate. We can't leave wine at the door."
