---
id: KB-ACC-000
title: Account Management: Folder Index
category: account
subcategory: index
doc_type: index
intents: [account.create, account.login_issue, account.age_verification, account.update_profile, account.payment_methods, account.preferences, account.privacy_request, account.security_concern]
tools: [verify_customer_identity, get_customer_profile, update_customer_profile, manage_address, remove_payment_method, send_password_reset, get_age_verification_status, start_age_verification, update_communication_preferences, submit_privacy_request, lock_account]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: customer-support
status: active
depends_on_assumptions: [A-70, A-74]
related: [KB-SYS-003, KB-DSC-004]
---

# Account Management: Folder Index

## Scope

Creating accounts and verifying age; signing in and security; profile, addresses and payment methods; order history, reorders and taste profiles; communication preferences; privacy rights and deletion; account takeover and fraud.

## Identity rule (A-70)

The agent reads or changes account data **only** in an authenticated session or after OTP verification (`verify_customer_identity`). It never confirms whether an email or phone number has an account (no account enumeration), and never collects passwords, full card numbers, CVV or ID images (A-74).

## Files

| File | Answers |
|---|---|
| [account-creation-and-age-verification.md](account-creation-and-age-verification.md) | Sign-up, 21+ DOB, one account per person, ID verification flow and failures |
| [login-password-and-security.md](login-password-and-security.md) | Can't log in, password reset, lockouts, MFA, email change |
| [profile-addresses-and-payment-methods.md](profile-addresses-and-payment-methods.md) | Name/DOB/phone changes, saved addresses and default store, cards |
| [order-history-reorders-and-taste-profile.md](order-history-reorders-and-taste-profile.md) | Past orders, receipts, reorder, favorites, taste profile, personalization |
| [communication-preferences.md](communication-preferences.md) | Email/SMS/push, marketing vs transactional, unsubscribe |
| [privacy-rights-and-account-deletion.md](privacy-rights-and-account-deletion.md) | Access, correction, deletion, portability, opt-outs, retention, appeals |
| [account-takeover-and-fraud.md](account-takeover-and-fraud.md) | Unauthorized orders, phishing, compromised accounts, card misuse |
