---
id: KB-ACC-005
title: Communication Preferences (Email, SMS, Push)
category: account
subcategory: communications
doc_type: policy
intents: [account.preferences, discount.current_offers]
tools: [verify_customer_identity, get_customer_profile, update_communication_preferences, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY, US]
audience: agent
priority: medium
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: marketing
status: active
depends_on_assumptions: [A-70, A-72, A-76]
related: [KB-ACC-006, KB-DSC-005]
---

# Communication Preferences

## 1. Message types

| Type | Examples | Can opt out? |
|---|---|---|
| **Transactional** | Order confirmation, ID-verification link, substitution requests, "ready for pickup", delivery ETA, refund notices | Not while an order is active (needed to fulfill it). Delivery SMS can be switched to email-only |
| **Security** | Password reset, new login alerts, email change notices | No |
| **Marketing: email** | Newsletters, sales, new arrivals, events | Yes, anytime (one-click unsubscribe; processed within 10 business days; A-76) |
| **Marketing: SMS** | Flash sales, event reminders | Yes; requires prior **express written consent**; reply **STOP**; sent 9 am–8 pm ET only (A-76) |
| **Push notifications** | App alerts | Yes, in the app/device settings |
| **Back-in-stock / price alerts** | Customer-requested alerts | Yes, per alert |
| **Personalized offers** | Based on purchase history | Yes; opting out of personalization keeps generic marketing if subscribed |

## 2. Rules

**CP-R1: Consent first.** The agent turns **on** marketing email or SMS only with explicit consent in the conversation ("Yes, sign me up for texts"). SMS opt-in shows the required disclosure (message frequency, "msg & data rates may apply", STOP/HELP).
**CP-R2: Opt-out immediately.** Opt-out requests are processed right away (`update_communication_preferences`). The agent doesn't try to talk the customer out of it.
**CP-R3: Responsible marketing.** Marketing never targets people under 21 and never encourages excessive drinking.
**CP-R4: Data-sharing opt-outs** (sale/targeted advertising) are privacy rights; see [privacy-rights-and-account-deletion.md](privacy-rights-and-account-deletion.md).

## 3. Workflow

1. Verify identity (A-70), unless the customer is just replying STOP (handled automatically by the SMS system).
2. `get_customer_profile` → current preferences.
3. Confirm the exact change ("Turn off promotional emails and texts, but keep order updates?").
4. `update_communication_preferences(customer_id, prefs)` → confirm.

## 4. Edge cases

| Case | Handling |
|---|---|
| "Stop all messages" | Turn off all marketing; explain transactional messages for open orders still arrive |
| Still getting emails after unsubscribing | Can take up to 10 business days; check for a second email address/account; P3 if it persists |
| Texts at night | Shouldn't happen for marketing (A-76); transactional delivery updates may arrive during evening windows; P3 investigate |
| Someone else's number receiving our texts | Remove the number immediately (no verification needed to **opt out** a number); don't reveal account details |

## 5. Escalation

Opt-outs are never delayed by an escalation. **Apply the opt-out first, then hand off.**

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Customer mentions a lawsuit, attorney or regulator complaint (e.g., about unwanted texts) | P1 | `legal_matter` | Opt them out; don't discuss liability or admit fault |
| Marketing texts the customer says they never agreed to, or marketing texts outside 9 am–8 pm ET (A-76) | P2 | `marketing_consent_issue` | Opt the number out; record the date, time and message content |
| A parent or guardian says a minor is receiving our marketing | P2 | `marketing_consent_issue` | Remove the number or email now (no verification needed to opt out); don't reveal account details (CP-R3) |
| `update_communication_preferences` fails after one retry | P2 | `tool_failure` | Don't say the opt-out is done; say a team member will process it and confirm |
| Marketing emails continue more than 10 business days after unsubscribing (A-76), and no second address or account explains it | P3 | `create_support_ticket(category="communications")` | Re-apply the opt-out; include the sending address and dates |
| Transactional texts at night not tied to an evening delivery window | P3 | `create_support_ticket(category="communications")` | Include the order number and times |

**Handle without escalating:** standard opt-ins with consent (CP-R1), opt-outs, STOP replies, push-notification settings, and removing a number that belongs to someone else. Requests to opt out of data sale or targeted ads follow [privacy-rights-and-account-deletion.md](privacy-rights-and-account-deletion.md).

## 6. Response examples

> "Done. You're unsubscribed from promotional emails and texts. You'll still get order and delivery updates while you have an active order."

> "I can sign you up for text alerts about sales and events. You'd get up to 4 messages a month; message and data rates may apply; reply STOP anytime to cancel. Want me to turn that on?"
