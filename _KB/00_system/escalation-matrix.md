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
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: customer-support
status: active
depends_on_assumptions: [A-60, A-61, A-62, A-63]
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
| Safety | Injury, crisis, self-harm, medical emergency | P1 | `safety_crisis` |
| Fraud | Suspected stolen card, account takeover, suspicious address change after dispatch | P1 | `fraud_signal` / `account_takeover` |
| Refunds | Refund request > $150 (A-60), or no evidence, or 2nd claim within 60 days | P2 | `refund_over_limit` / `claim_review` |
| Returns | Outside window but customer has a credible reason (e.g., hospital stay, delivery we confirmed late) | P2 | `policy_exception_request` |
| Pricing | Price match request; pricing error dispute; customer charged different than shown | P2 | `price_match` / `pricing_dispute` |
| Orders | Order stuck in a status beyond SLA (e.g., `ready_for_pickup` not notified, `dispatched` > 4 h late) | P2 | `fulfillment_delay` |
| Orders | Bulk/event order > $2,500 or > 60 bottles (A-26) | P2 | `bulk_order` |
| Account | Ownership dispute, can't access email/phone on file, name/DOB correction | P2 | `account_recovery` |
| Account | Account deletion or data access request (agent submits; humans verify) | P2 | `privacy_request` |
| Verification | ID verification failed after one retry | P2 | `id_verification_failure` |
| Product | Pre-arrival delay > 90 days; allocation dispute | P2 | `pre_arrival_issue` |
| Product | Special order / new product request | P3 | `product_request` |
| Service | Complaint about staff/driver conduct | P2 (P1 if safety) | `conduct_complaint` |
| Knowledge | Question not answerable from KB/tools | P3 | `kb_gap` (also `log_event`) |
| Customer | Requests a human twice, or is clearly frustrated | P2 | `customer_requested_human` |
| Tools | Tool error persists after one retry on a transactional step | P2 | `tool_failure` |

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
