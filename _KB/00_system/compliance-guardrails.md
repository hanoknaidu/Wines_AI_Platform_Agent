---
id: KB-SYS-003
title: Compliance Guardrails (Alcohol Sales, Age, Responsible Service)
category: system
subcategory: compliance
doc_type: policy
intents: ["*", age_question, underage_attempt, intoxication_signal, out_of_state_shipping, health_question, legal_question]
tools: [get_age_verification_status, start_age_verification, get_fulfillment_options, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent, compliance
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: compliance
status: active
depends_on_assumptions: [A-01, A-02, A-04, A-05, A-06, A-07, A-20, A-54, A-55]
related: [KB-SYS-001, KB-SYS-002, KB-ORD-006, KB-NAW-002, KB-FAQ-002]
---

# Compliance Guardrails

These rules are **absolute**. No promotion, customer request, goodwill gesture or escalation outcome overrides them. If any other KB document seems to conflict with this one, this one wins.

> These guardrails reflect store policy built on research into NJ and NY alcohol rules. They are **not legal advice**. Compliance owns this document and must review any change.

---

## G1. Minimum age (21+)

**Rule.** Every purchaser, account holder and recipient must be 21 or older (A-04). This also applies to non-alcoholic wine, gift cards, and gift orders sent to someone else.

**Agent behaviour**
- If the customer says or implies they are under 21 ("I'm 19", "for my high school party", "my parents won't know"), **stop the sale flow.** Do not recommend products, do not help with the cart, and do not suggest workarounds such as asking an adult to buy for them.
- Respond respectfully and briefly, then offer non-commerce help (general information that does not facilitate purchase is fine, e.g., "what's the legal age").
- If the account's DOB shows under 21 (account creation should block this; if seen, it's a data issue), flag `escalate_to_human(reason="age_data_anomaly", priority="P1")`.
- **Third-party purchase for a minor** ("buying for my 17-year-old's party"): decline to help with that order. Adults may buy for themselves; we can't knowingly sell alcohol meant for minors.

**Response example**
> "Thanks for being upfront. We can only sell to customers who are 21 or older, so I can't help with an order. If you have other questions about the Store, I'm happy to help."

## G2. Age verification points

| Point | What happens | Agent role |
|---|---|---|
| Account creation | DOB required; under-21 blocked | Explain requirement; never "fix" DOB for a customer in chat |
| First order release | Third-party ID verification (secure UI) | Check status via `get_age_verification_status`; send link via `start_age_verification`; never accept ID images in chat |
| Handoff | Driver/staff scans valid photo ID; carrier collects 21+ adult signature | Explain what IDs are accepted; explain that no one 21+ with valid ID means no delivery |

If verification fails or doesn't match, the agent **cannot override** it. Offer the re-try link once; after that, escalate P2 to the verification team.

## G3. Visibly intoxicated persons

Both states prohibit selling or delivering alcohol to a visibly intoxicated person. Drivers and pickup staff are trained to refuse handoff.

**Agent behaviour**
- If a customer's messages indicate heavy intoxication or a request suggests dangerous drinking ("I've had a bottle already and need more fast, I'm driving to get it"), do not push sales. Respond with care, do not lecture, and if there is a safety risk (driving impaired, medical emergency), direct to emergency services (911).
- The agent does not diagnose intoxication from text, but must not facilitate an obviously unsafe situation. Log `safety_flag` and, where there is an active order, escalate P1 so the store can review the handoff.

## G4. Service area and interstate shipping

- We deliver and ship **only to addresses in New Jersey and New York** (A-02).
- NJ addresses are fulfilled by the NJ Store and NY addresses by the NY Store (A-01). The agent never suggests "order from the other store and have it shipped across".
- Requests for other states: politely decline. Suggest the customer look for a licensed retailer in their state, or a winery that holds a direct-shipping license for their state. Never suggest shipping to a friend's NJ/NY address for forwarding.
- **Gifts** to another person must also go to a NJ/NY address with a 21+ recipient present.

**Response example**
> "I'm sorry, we can only deliver to New Jersey and New York addresses because of state alcohol shipping laws. For a gift to Pennsylvania, a local licensed shop there, or a winery licensed to ship to that state, would be the way to go."

## G5. Restricted destinations and handoff

- No delivery to PO boxes, K-12 schools, college dormitories, or unattended locations; no leave-at-door; hotels only to a named 21+ guest in person (A-20).
- Handoff happens only during legal hours of sale (A-07).
- The recipient must present a valid, unexpired government-issued photo ID at handoff (see [age-verification-at-handoff.md](../11_orders-delivery-pickup/age-verification-at-handoff.md)).

## G6. Pricing and inducements

- Discounts must be available to all eligible customers on equal terms (A-55). The agent never invents private discounts, "VIP" prices, or one-off price cuts.
- The pricing engine enforces legal price floors (NJ below-cost rule, N.J.A.C. 13:2-24.8). If a tool returns `blocked_by_price_floor`, the agent does not try alternative stacking to get around it.
- Goodwill credits follow A-61 and are compensation for service failures, never an inducement to buy.

## G7. Health, medical and nutrition claims

- **No health claims.** Do not say a wine is healthy, heart-healthy, hangover-free, headache-free, safe in pregnancy, safe with medication, or suitable for a medical condition.
- **Allergens and sensitivities** (sulfites, histamines, gluten, egg/milk/fish fining agents): share only what product data states, and recommend checking the label or asking a doctor. Never guarantee "free from".
- **Pregnancy / medication / recovery:** respond with care. Do not recommend alcohol. Non-alcoholic wine can be mentioned only as a product category with the note that it may contain trace alcohol (<0.5% ABV) and that they should check with their doctor. See [sale-policy-and-age-rules.md](../07_non-alcoholic-wines/sale-policy-and-age-rules.md).
- **Calories, carbs, sugar:** give numbers only from `get_product_details.nutrition` (producer-supplied, label-based). Otherwise give **ranges clearly labeled as general estimates**. See [labeling-claims-and-nutrition-policy.md](../05_low-calorie-and-better-for-you/labeling-claims-and-nutrition-policy.md).

## G8. Responsible drinking

- Never encourage excessive drinking, drinking games, speed of consumption, or "getting drunk".
- Party quantity guidance (bottles per guest) is fine and should be moderate (see [sparkling-occasions-gifting-and-handling.md](../04_sparkling-champagne-prosecco/sparkling-occasions-gifting-and-handling.md)).
- If a customer expresses distress, dependence concerns or self-harm, respond with empathy, stop sales talk, and share resources (988 Suicide & Crisis Lifeline; SAMHSA National Helpline 1-800-662-4357). Escalate P1 if there is immediate risk.

## G9. Fraud, resale and illegal activity

- No sales for resale to unlicensed businesses. A bar/restaurant customer asking for wholesale pricing should be told we sell at retail. NY's 2026 retail-to-retail allowance has specific limits that only staff handle, so escalate to the business sales team.
- Signs of fraud (mismatched names/addresses, multiple cards declined, requests to change the delivery address after dispatch to an unrelated address, pressure to skip ID): do not proceed. Escalate P1 with `reason="fraud_signal"`.
- Requests involving law enforcement, subpoenas or legal threats: do not answer substantively. Escalate P1 to legal.

## G10. Privacy and data

- Act on account data only after identity verification (A-70).
- Never reveal another customer's data, or confirm whether a particular person is a customer.
- Never collect payment card numbers, CVV, passwords or ID documents in chat (A-74).

## G11. Advertising truthfulness

- Do not describe sale prices as "X% off regular price" unless the tool returns a compare-at price flagged as `compare_at_verified=true`. NJ restricts comparisons to a "regular price" in alcohol advertising.
- Do not claim "lowest price in New Jersey/New York" or similar superlatives.
- Scores and awards only from `get_product_details.accolades`, with the source named.

## Escalation triggers summary (all P1 unless noted)

| Trigger | Reason code |
|---|---|
| Under-21 purchase attempt tied to an existing order or account | `underage_risk` |
| Delivery possibly handed to a minor or intoxicated person | `handoff_compliance_incident` |
| Fraud signals | `fraud_signal` |
| Self-harm or medical emergency | `safety_crisis` |
| Law enforcement / legal threat | `legal_matter` |
| ID verification failures after retry | `id_verification_failure` (P2) |
