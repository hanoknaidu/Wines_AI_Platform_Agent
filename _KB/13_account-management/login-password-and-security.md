---
id: KB-ACC-002
title: Login, Password and Account Security
category: account
subcategory: login-security
doc_type: workflow
intents: [account.login_issue, account.security_concern, account.update_profile]
tools: [send_password_reset, verify_customer_identity, update_customer_profile, lock_account, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: security
status: active
depends_on_assumptions: [A-70, A-71, A-74]
related: [KB-ACC-007, KB-ACC-003]
---

# Login, Password and Account Security

## 1. Security settings (A-71)

| Setting | Rule |
|---|---|
| Failed logins | 5 attempts → **15-minute lockout** |
| Password reset link | Valid **30 minutes**, single use |
| Reset email rate | Max 3 per hour |
| MFA | Optional (authenticator app or SMS); recommended |
| Sessions | Customers can sign out of all devices in account settings |
| Social login | Sign in with Apple / Google available |

## 2. "I can't log in" decision tree

1. **Forgot password** → `send_password_reset(email)`. The tool always returns a generic success; say: "If an account exists for that email, a reset link is on its way. It expires in 30 minutes."
2. **No reset email** → check spam/promotions; confirm spelling; wait a few minutes; resend once. Still nothing → they may have used a different email or social login ("Did you sign up with Apple or Google?").
3. **Locked out** → wait 15 minutes, then reset the password.
4. **Social login confusion** (Apple "Hide My Email" relay address) → sign in with the same Apple/Google button.
5. **Lost access to the email** → account recovery requires identity verification by a human: `escalate_to_human(reason_code="account_recovery", priority="P2")`. The agent doesn't change emails without OTP to a verified channel.
6. **MFA device lost** → P2 `account_recovery`.

## 3. Changing the login email

1. `verify_customer_identity` (OTP to the current email or phone on file).
2. `update_customer_profile(fields={email:new})` → the system sends confirmation to the **new** address and a notice to the **old** one.
3. The change completes when the new address is confirmed.

## 4. Rules

**SEC-R1:** The agent **never** asks for, accepts or repeats a password, OTP code (except entered through the tool flow), card number or CVV. If a customer shares a password in chat, tell them to change it immediately and don't repeat it.
**SEC-R2:** No account enumeration. Never confirm whether an email/phone is registered.
**SEC-R3:** We never ask for passwords by email, text or phone. Messages asking for them are phishing (see [account-takeover-and-fraud.md](account-takeover-and-fraud.md)).
**SEC-R4:** Suspicious activity (unknown logins, orders, address changes) → takeover workflow.

## 5. Security tips to share

- Use a unique password (a password manager helps) and turn on MFA.
- Sign out on shared devices.
- Check order confirmations for anything unexpected.

## 6. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Signs that someone else got in: unknown login alerts, password or email changed without the customer, unfamiliar orders (SEC-R4) | P1 | `account_takeover` | Follow the containment workflow in [account-takeover-and-fraud.md](account-takeover-and-fraud.md) §2 |
| Customer entered their password on a phishing site | P1 | `account_takeover` | Same containment workflow; advise changing the password anywhere it was reused |
| Lost access to the email on file | P2 | `account_recovery` | Try OTP to the phone on file first, if there is one; never change the email without OTP to a verified channel (§3) |
| Lost MFA device with no backup method | P2 | `account_recovery` | Note which second factor was set up (app or SMS), not any codes |
| No reset email after a resend, a spam check and a social-login check | P3 | `create_support_ticket(category="login_issue")` | Never confirm whether the email has an account (SEC-R2); the ticket lets a person check |

**Handle without escalating:** password resets, 15-minute lockouts, social-login confusion, and email changes with OTP to a verified channel. If a customer shares a password in chat, tell them to change it (SEC-R1). Escalate only if they think someone else has used it.

**Handoff line**
> "Because you can't get into the email on your account, a team member needs to confirm it's you before anything changes. That protects your account. I've opened case #…, and they'll reach you by phone within 4 business hours."

## 7. Response examples

> "No problem. I've sent a reset link to that email if it has an account with us. It's valid for 30 minutes. If you don't see it, check your spam folder, or let me know if you might have signed up with Apple or Google."

> "Please don't share your password here. For your security, I'd recommend changing it now. Here's how: Account → Security → Change password."
