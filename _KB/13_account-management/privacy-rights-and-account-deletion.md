---
id: KB-ACC-006
title: Privacy Rights, Data Requests and Account Deletion
category: account
subcategory: privacy
doc_type: policy
intents: [account.privacy_request, account.preferences, account.update_profile]
tools: [verify_customer_identity, submit_privacy_request, get_customer_profile, list_orders, get_loyalty_account, update_communication_preferences, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY, US]
audience: agent, privacy-team
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: privacy
status: active
depends_on_assumptions: [A-53, A-70, A-72, A-73, A-74]
related: [KB-ACC-005, KB-ACC-004, KB-DSC-004, KB-SYS-003]
---

# Privacy Rights, Data Requests and Account Deletion

> Business policy modeled on the **New Jersey Data Privacy Act** (effective Jan 15, 2025), offered to **all customers regardless of state** (A-72). Not legal advice; the privacy team owns final handling. New York has no comprehensive consumer privacy law in effect as of review, but data-security (SHIELD Act) and breach-notification laws apply.

## 1. Rights we honor (A-72)

| Right | What the customer gets | `request_type` |
|---|---|---|
| **Access / know** | Confirmation of processing and a copy of personal data | `access` |
| **Correction** | Fix inaccurate data | `correction` |
| **Deletion** | Delete personal data, subject to legal retention (A-73) | `deletion` |
| **Portability** | Data in a portable, machine-readable format | `portability` |
| **Opt out of targeted advertising** | Stop ad targeting based on activity | `opt_out_targeted_ads` |
| **Opt out of sale of personal data** | Stop any "sale" as defined by law | `opt_out_sale` |
| **Opt out of profiling** for decisions with legal or similarly significant effects | — | `opt_out_profiling` |
| **Withdraw consent** for sensitive data (we don't intentionally collect sensitive data beyond what's legally required) | — | `withdraw_consent` |
| **Appeal** a decision | Review of a denied request | `appeal` |

**Universal opt-out signals** (e.g., Global Privacy Control) are honored as opt-out requests for targeted advertising and sale on the browser/device that sends them.

## 2. Timelines

- **Target completion: 15 days** (A-72). **Legal maximum: 45 days**, extendable by 45 more when reasonably necessary (the customer is told why).
- Opt-outs of marketing communications are immediate (communication doc). Privacy opt-outs (sale/targeted ads) are processed as quickly as possible, within legal timelines.

## 3. Verification

- Requests about an account require identity verification (A-70: authenticated session or OTP).
- **Authorized agents** (someone acting for the customer) must provide written permission; the privacy team verifies (P2).
- The agent never asks for SSNs, ID images or full card numbers (A-74).

## 4. What deletion means (explain before submitting)

| Deleted | Retained (as legally required, then deleted; A-73) |
|---|---|
| Profile, taste profile, favorites, ratings | Order and transaction records needed for tax, accounting and alcohol-sale compliance |
| Marketing preferences and lists | Age-verification records required for compliance (held by the verification partner per its retention) |
| Saved addresses and payment tokens | Records needed for fraud prevention, open disputes or chargebacks, and legal claims |
| **Rewards points and rewards: forfeited** (RW-R6) | — |
| Store credit: refund or use it first (see below) | — |

**Before deletion:**
- Open orders, returns or pre-arrivals must be completed or cancelled first.
- **Store credit** balances: the customer can use them first, or request a refund of credit originating from a card refund; promotional/goodwill credit is forfeited.
- **Gift cards** aren't tied to the account and keep working.

## 5. Workflow

1. Identify the request type from the customer's words; confirm it in plain language.
2. Verify identity (A-70).
3. For deletion: explain §4 consequences; check `list_orders` (open orders?) and `get_loyalty_account` (balance?).
4. On explicit confirmation → `submit_privacy_request(customer_id, request_type, details)`.
5. Share the `request_id` and `due_by` date; explain that the privacy team may contact them to confirm.
6. For "what data do you have about me?" give a plain-language summary (categories below) and offer an access request for the full copy.

**Data categories we collect (summary for customers):** identity and contact details; date of birth and age-verification status; addresses; order and purchase history (online and linked in-store); payment tokens (not full card numbers); Rewards activity; communication preferences; taste preferences and ratings; device/usage data on our site and app; customer support conversations (including this chat).

## 6. Edge cases

| Case | Handling |
|---|---|
| Customer wants chat transcripts deleted | Included in a deletion request; may be retained if part of an open dispute |
| Request from a non-customer (e.g., got our marketing) | Accept; verify via the email/phone in question |
| Law enforcement or legal request for data | Don't handle; P1 `legal_matter` |
| Request to know "who else" bought something | Never disclose other customers' data (G10) |
| Request on behalf of a deceased person | P2 privacy team, with care |
| Appeal of a denied request | `submit_privacy_request(request_type="appeal")`; the privacy team responds within the legal timeline |

## 7. Escalation

The privacy team completes every privacy request, so for routine cases submitting with `submit_privacy_request` **is** the handoff. Escalate further when:

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Law enforcement, subpoena or other legal request for data | P1 | `legal_matter` | Don't confirm whether the person is a customer (G10) |
| Customer mentions an attorney or a regulator complaint (e.g., to the New Jersey Division of Consumer Affairs) | P1 | `legal_matter` | Submit any pending request first so its legal clock keeps running |
| Customer reports that their data was exposed or leaked by us | P1 | `security_incident` | Record what they saw and where; don't confirm or deny a breach |
| Authorized agent acting for the customer (§3) | P2 | `privacy_request` | Explain that written permission is needed; share no data with the agent |
| Request about a deceased customer | P2 | `privacy_request` | Respond with care; disclose no account details |
| Customer can't pass identity verification (lost access to email or phone) | P2 | `account_recovery` | Don't submit the request unverified |
| A submitted request is past its `due_by` date | P2 | `privacy_request` | Include the `request_id` and the original submission date |
| Deletion blocked by an open chargeback or dispute | P2 | `privacy_request` | Explain that records needed for the dispute are kept (§4) |

**Handle without escalating:** standard requests from a verified customer (submit, then share the `request_id` and `due_by` date), appeals (`request_type="appeal"`) and marketing opt-outs (immediate, see [communication-preferences.md](communication-preferences.md)).

## 8. Response examples

> "I can help you delete your account. Before I submit it, here's what happens: your profile, saved addresses, taste preferences and marketing data will be deleted, and your 380 Rewards points and $10 reward will be forfeited. We keep order records only as long as the law requires for tax and alcohol-sale compliance. You have no open orders. Would you like me to go ahead?"

> "Your data access request is submitted (#PR-11820). Our privacy team will send your data by December 4, usually sooner, and may email you first to confirm it's you."
