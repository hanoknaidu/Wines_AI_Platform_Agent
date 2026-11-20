---
id: KB-ORD-006
title: Age Verification at Handoff (Accepted IDs and Refusals)
category: orders
subcategory: id-at-handoff
doc_type: policy
intents: [account.age_verification, delivery.failed, pickup.question, compliance.underage, compliance.intoxication]
tools: [get_order_status, reschedule_delivery, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent, drivers, store-staff
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 60
owner: compliance
status: active
depends_on_assumptions: [A-04, A-05, A-07, A-15, A-17, A-18, A-20, A-29b]
related: [KB-SYS-003, KB-ORD-004, KB-ORD-005, KB-ORD-007, KB-ORD-008]
---

# Age Verification at Handoff

## 1. Rule

Every alcohol and non-alcoholic wine order is handed over **only** to a person who:
1. is **21 or older**,
2. presents a **valid, unexpired, government-issued photo ID** (scanned or inspected),
3. is **not visibly intoxicated**,
4. is at a **permitted destination** during **legal hours** (A-07, A-20),
5. for pickup, is the purchaser or the named alternate (A-29b); for named-recipient gift orders, is the named recipient.

## 2. Accepted IDs

| Accepted (valid, unexpired, photo, date of birth) | Not accepted |
|---|---|
| US state/territory driver's license | Expired IDs of any kind |
| US state/territory non-driver photo ID card | Photocopies, photos of IDs on a phone |
| US passport or passport card | Student IDs, work badges |
| US military ID | Paper temporary licenses **without** the prior photo ID |
| Foreign passport | Mobile/digital driver's licenses (until compliance approves; Q-4) |
| Canadian provincial driver's license (NY practice; confirm for NJ) | Birth certificates, Social Security cards |

**Vertical "under-21" licenses** (issued to people under 21 in many states, including NY) remain valid until expiration. Accept them if the date of birth shows the person is now 21+ and the license is unexpired. Staff should take extra care.

## 3. How the check works

- **Local delivery & pickup:** staff/driver scan the ID barcode in the delivery/POS app (validates format, expiry, DOB), visually match the photo, and capture a signature. Scan data is used only for verification and compliance records (privacy notice).
- **Carrier shipping:** UPS/FedEx **adult signature (21+)** service; the carrier checks ID at the door (A-15).

## 4. Refusal reasons (what drivers/staff refuse, and what the agent says)

| Refusal reason | Customer explanation | Next step |
|---|---|---|
| No ID / expired ID | "The driver couldn't release the order without a valid, unexpired photo ID." | One free redelivery (A-17) or pickup |
| Recipient under 21 | "The person receiving must be 21 or older." | Redelivery to a 21+ adult |
| Visibly intoxicated | "Our staff can't hand alcohol to someone who appears intoxicated. It's a legal requirement." | Redelivery at a later time, at the store's discretion |
| Suspected purchase for minors (e.g., a group of minors present and the recipient appears to be passing it on) | "The driver had concerns about the delivery and couldn't complete it." | Escalate P1 `handoff_compliance_incident`; no automatic redelivery |
| Restricted destination | "We're unable to deliver alcohol to that location." | Change the address / pickup |
| Outside legal hours | Rare; system prevents | Reschedule |

**Agent rules:** be respectful, non-accusatory and brief. Never argue with the driver's compliance decision or promise an override. Refused-handoff orders follow the failed-delivery rules (A-17, A-18); **no restocking fee** applies to compliance refusals.

## 5. Complaints about ID checks

- "I'm obviously over 21!" → "Thanks for understanding. We check ID for every alcohol delivery, regardless of age; it's required for us to sell alcohol."
- "The driver scanned my ID; what happens to my data?" → Used only to verify age and keep compliance records; see the privacy notice ([privacy-rights-and-account-deletion.md](../13_account-management/privacy-rights-and-account-deletion.md)).
- Reports of discriminatory treatment → P2 `conduct_complaint` (P1 if threatening).

## 6. Escalation

| Trigger | Priority |
|---|---|
| Report or suspicion of an order delivered to a minor/intoxicated person | P1 `handoff_compliance_incident` |
| Report of a fake ID / identity theft involving the account | P1 `fraud_signal` |
| Repeated refusals on the same account | P2 review |

## 7. Response examples

> "I'm sorry for the hassle. The driver couldn't release your order because the ID was expired. You have one free redelivery. Would you like to book a window when someone with a valid ID will be home, or pick it up at the store instead?"

> "Yes, any adult 21 or older at the address can accept the delivery, as long as they show a valid photo ID."
