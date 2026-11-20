---
id: KB-SYS-006
title: Escalation Matrix and Human Handoff Procedure
category: system
subcategory: escalation
doc_type: workflow
intents: [human.request, feedback.complaint, "*"]
tools: [escalate_to_human, create_support_ticket, log_event]
jurisdictions: [NJ, NY]
audience: agent, support-team
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: customer-support
status: active
depends_on_assumptions: [A-26, A-33, A-60, A-61, A-62, A-63, A-75]
related: [KB-SYS-001, KB-SYS-003, KB-SYS-004]
---

# Escalation Matrix and Human Handoff Procedure

## 1. Principles

1. **Resolve when you can, escalate when you must.** The agent should fully resolve routine requests within its authority (A-60, A-61). Escalation is for safety, compliance, money above limits, judgment calls, and anything the tools refuse.
2. **Never trap the customer.** If the customer asks for a human **twice**, or once with clear frustration, escalate. Don't argue.
3. **Hand off with context.** The human agent should never have to re-ask. Every escalation includes a structured summary (§5).
4. **Set honest expectations.** Tell the customer the realistic wait (`wait_estimate`) or the ticket SLA (A-63).

## 2. Priority definitions (A-63)

| Priority | Definition | Response target | Channel |
|---|---|---|---|
| **P1** | Safety, legal/compliance incident, fraud, account takeover, delivery to a minor or intoxicated person, injury (e.g., cut from broken glass), crisis | Immediate live handoff in support hours; on-call page out of hours | `escalate_to_human(priority="P1")` |
| **P2** | Money above agent authority, pricing disputes, price-match approvals, privacy requests needing review, ID verification failures, VIP/bulk orders at risk | First response ≤ 4 business hours | `escalate_to_human` or `create_support_ticket(priority="P2")` |
| **P3** | General follow-ups, product requests, feedback, non-urgent questions the agent couldn't answer | ≤ 1 business day | `create_support_ticket(priority="P3")` |

## 3. Escalation matrix

| Domain | Trigger | Priority | Reason code |
|---|---|---|---|
| Compliance | Possible handoff to a minor or intoxicated person | P1 | `handoff_compliance_incident` |
| Compliance | Underage purchase attempt tied to an account/order | P1 | `underage_risk` |
| Compliance | Law enforcement, subpoena, legal threat, regulator mention | P1 | `legal_matter` |
| Compliance | Account on file shows an under-21 date of birth (data anomaly) | P1 | `age_data_anomaly` |
| Compliance | Order contains a product not sellable in the customer's state (e.g., NA wine on a NY order) | P2 | `compliance_order_review` |
| Compliance | Marketing sent without consent, outside permitted hours, or to a minor | P2 | `marketing_consent_issue` |
| Compliance | Customer disputes a label, certification or nutrition claim as false or misleading | P2 | `claim_dispute` |
| Compliance | Non-alcoholic product: alcohol-like effect reported, or label ABV discrepancy | P2 | `product_quality` |
| Safety | Injury, crisis, self-harm, medical emergency | P1 | `safety_crisis` |
| Fraud | Suspected stolen card, account takeover, suspicious address change after dispatch | P1 | `fraud_signal` / `account_takeover` |
| Security | Customer reports their data was exposed or leaked by us | P1 | `security_incident` |
| Fraud | Customer disputes a store-initiated cancellation or hold (fraud screening, compliance) | P2 | `order_review` |
| Refunds | Refund request > $150 (A-60), or no evidence, or 2nd claim within 60 days | P2 | `refund_over_limit` / `claim_review` |
| Refunds | Refund issued > 10 business days ago and not received, or original card closed | P2 | `refund_trace` |
| Refunds | A chargeback is open on the order (no agent refunds) | P2 | `chargeback_open` |
| Returns | Outside window but customer has a credible reason (e.g., hospital stay, delivery we confirmed late) | P2 | `policy_exception_request` |
| Pricing | Price match request; pricing error dispute; customer charged different than shown | P2 | `price_match` / `pricing_dispute` |
| Pricing | Published promotion misconfigured (fails for eligible carts, over-applies, leaked code) | P2 | `promo_config_error` |
| Sales | Business, resale or trade-pricing request (G9) | P2 | `business_sales` |
| Orders | Order stuck in a status beyond SLA (e.g., `ready_for_pickup` not notified, `dispatched` > 4 h late) | P2 | `fulfillment_delay` |
| Orders | Carrier or driver shows delivered; customer doesn't have it after household/building checks | P2 | `delivered_not_received` |
| Orders | Store broke a fulfillment policy (e.g., unconsented $25+ vintage change, never-substitute item swapped) | P2 | `policy_violation` |
| Orders | Bulk/event order > $2,500 or > 60 bottles (A-26) | P2 | `bulk_order` |
| Account | Ownership dispute, can't access email/phone on file, name/DOB correction | P2 | `account_recovery` |
| Account | Account deletion or data access request (agent submits; humans verify) | P2 | `privacy_request` |
| Verification | ID verification failed after one retry | P2 | `id_verification_failure` |
| Product | Pre-arrival delay > 90 days; allocation dispute | P2 | `pre_arrival_issue` |
| Product | Claim or vintage dispute on an older-vintage or collectible wine (A-33) | P2 | `collectible_dispute` |
| Product | Suspected counterfeit or tampered bottle | P2 (P1 if health concern) | `authenticity_concern` |
| Product | Supplier, brand rep or distributor contacts the agent | P3 | `vendor_inquiry` |
| Product | Special order / new product request | P3 | `product_request` |
| Service | Complaint about staff/driver conduct | P2 (P1 if safety) | `conduct_complaint` |
| Communications | Press or media inquiry | P2 | `media_inquiry` |
| Knowledge | Question not answerable from KB/tools | P3 | `kb_gap` (also `log_event`) |
| Customer | Requests a human twice, or is clearly frustrated | P2 | `customer_requested_human` |
| Tools | Tool error persists after one retry on a transactional step | P2 | `tool_failure` |

### 3.1 Ticket categories (`create_support_ticket.category`)

Async follow-ups use these categories, so the backend can route them to the right queue. Priority comes from §3 or from the document that opens the ticket.

| Category | Queue | Typical use |
|---|---|---|
| `bulk_order` | Events/bulk team | Orders > 60 bottles or > $2,500 (A-26) |
| `event_order` | Events/bulk team | Private events needing planning or reserved stock |
| `corporate_gifting` | Corporate team | Recipient lists, invoicing, tax-exempt documentation, bulk gift cards |
| `catalog_correction` | Catalog team | Wrong vintage, ABV, region, photo or certification tag |
| `vendor_inquiry` | Merchandising/buying team | Suppliers, brand reps or wineries pitching products |
| `product_request` | Buying team | Product requests outside the normal flow, spirits/beer requests |
| `inventory_accuracy` | Store operations | Items repeatedly shown in stock but removed at picking |
| `fulfillment_quality` | Store operations | Repeated packing errors |
| `lot_quality` | Purchasing | Several faulty bottles from one lot |
| `carrier_issue` | Shipping operations | Repeated carrier damage or loss in an area |
| `store_pricing` | Pricing team | Shelf tag vs online price mismatches |
| `price_match_review` | Pricing team | Customer asks for review of a declined match |
| `gift_issue` | Customer support | Gift-recipient reports when the purchaser can't be reached |
| `gift_card` | Finance | Lost/stolen cards, missing digital cards, cash-out questions |
| `loyalty` | Customer support | Missing points > 30 days, account merges, reward reissues |
| `invoice_request` | Customer support | Reissued invoices or receipts with business details |
| `records_request` | Customer support | Order records older than 24 months (A-75) |
| `communications` | Marketing operations | Unsubscribes not taking effect; unexpected message timing |
| `login_issue` | Customer support | Reset emails not arriving after standard checks |
| `security_report` | Security | Phishing reports with no account compromise |
| `abusive_conversation` | Customer support | Conversations ended after continued abuse (§6) |

## 4. Handoff workflow

1. **Decide** priority from §3. If several triggers apply, use the highest.
2. **Tell the customer** what you are doing and why, in one sentence.
3. **Call** `escalate_to_human(conversation_id, reason_code, priority, summary, customer_sentiment)`.
4. **Read the result**
   - `connected`: "I've connected you with [team]. They can see our conversation."
   - `queued`: give the `wait_estimate`; offer a ticket instead if the wait is long.
   - `after_hours_ticket`: "Our team is available 9 am–9 pm ET. I've created ticket #… and they'll contact you by [SLA]."
5. **Stay helpful** while waiting: answer simple questions, but do not take actions that the human now owns (e.g., don't issue a partial refund on an escalated claim).
6. **Log** `log_event("kb_gap")` if the escalation was caused by missing KB content.

## 5. Handoff summary template (sent in `summary`)

```
Customer: <name or "guest">, verified: <yes/no>, location: <NJ/NY>
Intent: <primary intent>  |  Priority: <P1-P3>  |  Reason: <reason_code>
Order/RMA: <ids>
What the customer wants: <one sentence>
What I checked: <tools called + key results>
What I already did: <actions taken + reference numbers>
Policy context: <KB doc ids and rule numbers>
Why escalated: <specific trigger>
Customer sentiment: <calm / frustrated / angry / distressed>
```

## 6. De-escalation language

- Acknowledge: "I'm sorry this happened, especially for a gift."
- Own the next step: "Here's what I'm doing right now…"
- Avoid: blaming the customer, quoting policy before empathy, "unfortunately" stacked twice, promising outcomes you can't approve.
- If the customer is abusive, stay calm. Offer the human handoff once. If abuse continues, end politely: "I want to help, and I've passed this to our team, who'll follow up by email."

## 7. Response examples

**Refund above limit**
> "I can see the case arrived with three broken bottles. Thank you for the photos. Because the refund is $186, I need a team member to approve it. I've sent everything to them (ticket #48213), and you'll hear back within 4 business hours. You won't need to send anything else."

**Customer asks for a human**
> "Of course. I'm connecting you with our support team now. The current wait is about 6 minutes, and they'll see everything we've discussed."

**After hours, P2**
> "Our team is offline until 9 am ET, so I've created ticket #50117 with all the details. Someone will contact you by 1 pm ET tomorrow."
