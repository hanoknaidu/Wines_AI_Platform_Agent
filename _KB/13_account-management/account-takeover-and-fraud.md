---
id: KB-ACC-007
title: Account Takeover, Unauthorized Orders and Fraud
category: account
subcategory: fraud
doc_type: workflow
intents: [account.security_concern, order.cancel, compliance.underage]
tools: [verify_customer_identity, lock_account, send_password_reset, list_orders, get_order_status, cancel_order, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent, security
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: security
status: active
depends_on_assumptions: [A-62, A-63, A-70, A-74]
related: [KB-ACC-002, KB-SYS-003, KB-SYS-006, KB-RTN-004]
---

# Account Takeover, Unauthorized Orders and Fraud

## 1. Recognize the scenario

| Customer says | Scenario |
|---|---|
| "There's an order I didn't place" | Possible account takeover or a household member's order |
| "My password was changed" / "I got a login alert" | Account takeover |
| "My card was charged by you but I don't have an account" | Card misuse (stolen card) |
| "I got an email asking for my password / card" | Phishing |
| "Someone is using my ID" | Identity misuse (possible fake ID account) |

All are **P1** (A-63) except plain phishing reports without a compromise (P3).

## 2. Immediate containment workflow (account takeover)

1. **Stay calm and act fast.** "I'm sorry. Let's secure your account right now."
2. Verify identity via OTP to the contact on file (A-70). If the attacker changed the email/phone, **don't** verify via new contacts; go to step 5.
3. `lock_account(customer_id, reason="suspected_takeover")`: blocks logins, new orders and address changes.
4. `list_orders(status=open)` → for unauthorized orders not yet dispatched → `cancel_order(reason_code="unauthorized")`. For dispatched orders, tell the security team to contact the store/driver immediately (include it in the summary).
5. `escalate_to_human(reason_code="account_takeover", priority="P1", summary=...)`. Security restores access, resets credentials, reviews changes (addresses, cards, emails) and handles refunds for unauthorized charges after investigation.
6. Advise: change passwords elsewhere if reused; enable MFA once restored; contact the bank if card details may be exposed.

## 3. Card misuse (no account with us)

- Don't confirm or reveal any account details tied to the card.
- Advise the person to contact their **card issuer** to report fraud (the issuer handles chargebacks).
- Create a P1 ticket with the date, amount and last 4 digits (no full number, A-74) so security can cancel open orders and block the account.

## 4. Phishing

- We never ask for passwords, OTP codes, full card numbers or ID photos by email, text, phone or chat.
- Tell the customer not to click links or reply; to forward the message to our security address (from `get_store_info.contacts.security`), if available; and to delete it.
- If they already entered credentials on a fake site → takeover workflow (§2).

## 5. Fraud signals the agent should notice (G9)

- Requests to change the delivery address after dispatch, especially to an unrelated address.
- Pressure to skip ID checks or to leave the order at the door.
- Multiple cards tried in quick succession; names that don't match.
- Large orders of high-value, resaleable wines to new accounts with rush delivery.
- Gift orders to many unrelated addresses from a new account.

**Action:** don't proceed with the risky action; stay polite; `escalate_to_human(reason_code="fraud_signal", priority="P1")`. Never accuse the customer; say "I need a team member to help with this request."

## 6. Rules

- The agent never reveals fraud-detection rules or why exactly an order was held.
- Refunds for unauthorized charges are decided by security/finance (A-62), not the agent.
- Unauthorized orders delivered to someone may be a compliance issue (possible minor) → P1 `handoff_compliance_incident` too.

## 7. Escalation

Almost everything in this document is P1 (A-63). **Contain first, then hand off.** The steps in §2 (lock, cancel undispatched orders) take seconds and limit the damage, so do them before escalating unless identity can't be verified.

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Takeover confirmed or suspected (unknown orders, password or email changed by someone else, login alerts) | P1 | `account_takeover` | §2 steps 2–4; list cancelled and already-dispatched orders in the summary |
| Attacker changed the email/phone, so the customer can't pass OTP | P1 | `account_takeover` | Don't verify through the new contacts, and don't lock or cancel; describe what the customer reports |
| An unauthorized order was already delivered or handed over | P1 | `account_takeover`, naming `handoff_compliance_incident` in the summary | Compliance must check whether the recipient was 21+ (§6) |
| Card used on our site by someone else; the cardholder has no account (§3) | P1 | `fraud_signal` | Date, amount and **last 4 digits only** (A-74); advise contacting the card issuer |
| Fraud signals in the current conversation (§5, G9) | P1 | `fraud_signal` | Pause the risky action; don't explain the signal to the customer |
| "Someone is using my ID" to hold an account | P1 | `fraud_signal` | Don't confirm whether any account exists (SEC-R2) |
| Customer reports a phishing message and entered nothing | P3 | `create_support_ticket(category="security_report")` | No account action needed; ask them to forward it if a security address is available (§4) |

**Rules for these handoffs**
- `escalate_to_human` takes one `reason_code`. When several apply, use the most specific P1 code and name the others in the summary (escalation matrix §4).
- Out of hours, P1 pages the on-call team. Tell the customer the account is locked and the team will contact them. Don't promise a time beyond the `wait_estimate` the tool returns.
- Never issue refunds for unauthorized charges yourself; security and finance decide (A-62).

## 8. Response examples

> "Thank you for telling us. I've locked your account to stop any new orders or changes, and cancelled the order that hadn't shipped yet. Our security team is taking over now (case #S-3021) and will contact you within the hour to restore access. In the meantime, if you use the same password elsewhere, please change it there too."

> "That message didn't come from us. We never ask for passwords or card numbers by email or text. Please don't click the link, and delete the message. If you entered your password there, let me know right away and I'll help secure your account."
