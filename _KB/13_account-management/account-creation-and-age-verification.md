---
id: KB-ACC-001
title: Account Creation and Age Verification
category: account
subcategory: creation-verification
doc_type: policy
intents: [account.create, account.age_verification, compliance.underage]
tools: [get_age_verification_status, start_age_verification, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: compliance
status: active
depends_on_assumptions: [A-04, A-05, A-52, A-53, A-72, A-73, A-74, A-75, A-76]
related: [KB-SYS-003, KB-ORD-001, KB-ORD-006, KB-ACC-006]
---

# Account Creation and Age Verification

## 1. Creating an account

| Field | Required | Notes |
|---|---|---|
| First and last name | Yes | Use your legal name as on your ID (pickup and verification match it) |
| Email | Yes | Login and receipts |
| Password (or Sign in with Apple/Google) | Yes | Minimum 12 characters recommended; see the security doc |
| Date of birth | Yes | **Must be 21+** (A-04); under-21 sign-ups are blocked |
| Mobile phone | Optional (required for delivery coordination at checkout) | SMS marketing is a separate opt-in (A-76) |
| Default address / store | Optional at sign-up | Sets the NJ or NY store experience |
| Rewards enrollment | Optional, default on | Free (A-53) |
| Marketing email opt-in | Optional | — |

- **Account required to order** (A-75); no guest checkout.
- **One account per person.** Duplicate accounts to reuse first-order offers violate the terms (A-52).
- New accounts get the first-order offer if eligible (A-52).

## 2. Age verification (A-05)

| Stage | What happens |
|---|---|
| Sign-up | DOB self-declared; under 21 blocked |
| Before the first order is released | **Third-party ID verification** in the secure app/web flow: photo of a valid government ID, sometimes a selfie match; some customers are verified instantly from data checks |
| Every handoff | ID check by driver/staff/carrier ([age-verification-at-handoff.md](../11_orders-delivery-pickup/age-verification-at-handoff.md)) |

**Statuses (`get_age_verification_status`):** `not_started`, `pending`, `verified`, `failed`, `manual_review`.

**Why we verify:** alcohol retailers must make sure they sell only to adults 21+. A checkbox isn't enough, so we verify once online and again at handoff.

## 3. Verification troubleshooting

| Issue | Agent response |
|---|---|
| "Why do I need to upload my ID?" | Explain §2; mention it's a one-time check through a secure partner, and we never ask for ID in chat |
| Photo rejected (glare, blur, cropped) | Tips: flat surface, good light, no glare, all four corners visible; send a new link (`start_age_verification`) |
| ID expired | Must use a valid, unexpired ID (any accepted type) |
| Name mismatch (married name, etc.) | Update the profile name to match the ID, or use another ID; if still failing → P2 |
| `failed` after a retry | `escalate_to_human(reason_code="id_verification_failure", priority="P2")`; the order stays on hold; the agent can't override |
| `manual_review` | Typically resolved within 1 business day; the order stays on hold |
| Customer refuses to verify | Respect it; explain we can't release alcohol orders without verification; offer to cancel with a full refund |
| Under 21 in DOB (data error) | Don't change it. P2 for a DOB correction with ID proof; if the person is truly under 21 → G1 |

## 4. Rules

**AC-R1:** The agent never edits a date of birth. DOB corrections require ID-based human review.
**AC-R2:** The agent never accepts ID images, numbers or photos in chat (A-74). If a customer pastes ID details, ask them not to share them in chat, and don't repeat them.
**AC-R3:** Verification data is handled by the verification partner and retained only as required for compliance (privacy notice; A-73).
**AC-R4:** Accounts found to belong to someone under 21 are suspended; open orders cancelled and refunded; P1 (G1).

## 5. Escalation

The agent can't override age verification or edit identity data. Hand off using the [escalation matrix](../00_system/escalation-matrix.md) (§4 workflow, §5 summary template) in these cases:

| Situation | Priority | Reason code | Before handing off |
|---|---|---|---|
| Customer says or implies they are under 21 and has an account or open order | P1 | `underage_risk` | Stop the sale flow (G1). Leave open orders to the team, which suspends the account and cancels and refunds (AC-R4). Flag any order already out for delivery so the store can stop it |
| The account on file shows an under-21 DOB (sign-up should have blocked it) | P1 | `age_data_anomaly` | Don't change or discuss the DOB; include the customer ID |
| Signs that someone else's ID is being used, or a request to verify on behalf of another person | P1 | `fraud_signal` | Don't send a verification link; stay neutral ("I need a team member to help with this") |
| Verification `failed` after one retry link | P2 | `id_verification_failure` | Confirm the order is on hold; include the failure reason if the tool returns one |
| Name mismatch still failing after the profile name was updated or another ID was tried | P2 | `id_verification_failure` | Record which fix was tried |
| `manual_review` unresolved after 1 business day | P2 | `id_verification_failure` | Include the verification start date and the held order number |
| Customer says their DOB was entered incorrectly (AC-R1) | P2 | `account_recovery` | Explain that a team member corrects it with ID through a secure process, never in chat |

**Handle without escalating**
- Rejected photos, expired IDs and a first failure: give the tips in §3 and send one new link (`start_age_verification`).
- A customer who refuses to verify: offer to cancel the order with a full refund.
- A customer who pastes ID details in chat: ask them not to (AC-R2) and don't repeat the details.

**Handoff line**
> "I can't override the ID check myself, so I've passed this to our verification team (ticket #…). Your order stays safely on hold, and they'll contact you within 4 business hours."

## 6. Response examples

> "To finish your first order, we just need a one-time ID check. It's a secure link (not this chat) and takes about a minute. I've sent it to your email. After that, future orders only need an ID check when your wine is handed over."

> "It looks like the ID photo had some glare. Here's a new link. Try placing the ID on a dark, flat surface away from overhead lights, with all four corners visible."
