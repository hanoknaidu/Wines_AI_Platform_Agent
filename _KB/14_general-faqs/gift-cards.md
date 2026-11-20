---
id: KB-FAQ-004
title: Gift Cards
category: general
subcategory: gift-cards
doc_type: policy
intents: [giftcard.question, gift.order]
tools: [get_gift_card_balance, create_support_ticket, escalate_to_human]
jurisdictions: [NJ, NY]
audience: agent
priority: medium
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: finance
status: active
depends_on_assumptions: [A-04, A-51, A-53, A-56, A-74]
related: [KB-ORD-009, KB-RTN-005, KB-DSC-001]
---

# Gift Cards

## 1. Summary (A-56)

| Item | Rule |
|---|---|
| Types | **Digital** (emailed, $10–$500) and **physical** (in store, $10–$500) |
| Who can buy | Account holders **21+** (A-04) |
| Recipients | Must be 21+ to **redeem** on alcohol purchases (the account and age rules apply at redemption) |
| Expiry & fees | **Never expire; no fees** |
| Where to use | Online and in both stores (NJ and NY) |
| Combine | Multiple gift cards + one payment card per order; works with discounts and Rewards (gift cards are payment, not a discount) |
| Discounts on gift cards | Gift cards can't be bought with promo codes or discounts and don't earn Rewards points (A-51, A-53) |
| Cash out | Not redeemable for cash except where required by law |
| Returns | Gift cards are non-returnable; refunds of orders paid by gift card go back to the gift card (RTN-R7) |

## 2. Workflows

**Check balance:** the customer enters the card number and PIN in the **secure balance form** (never in chat; A-74), which returns a token → `get_gift_card_balance(gift_card_token)`. Or the balance shows in the account if the card is saved.

**Send a digital gift card:** in the gift card page: amount, recipient email, message, delivery date (can be scheduled). The agent can guide but not take payment in chat.

**Didn't receive a digital card:** check the recipient email spelling and the scheduled date, check spam, then resend from the order page. If still missing → P3 ticket with the order number.

**Lost or stolen card:**
- **Digital:** can be resent to the original recipient email.
- **Physical:** registered cards (linked to an account) can be frozen and replaced with the remaining balance; unregistered cards are like cash, so replacement requires the original purchase receipt (P2 finance).

## 3. Edge cases

| Case | Handling |
|---|---|
| Recipient lives outside NJ/NY | The gift card can be used in store or for NJ/NY delivery only; suggest a different gift |
| Recipient is under 21 | Don't sell for an under-21 recipient (G1) |
| Gift card scam (someone told the customer to pay a "bill" with gift cards) | Explain we never request payment by gift card; advise contacting local authorities/FTC; if our cards are involved, P1 `fraud_signal` (§4) |
| Corporate bulk gift cards | Corporate team ([events-tastings-and-corporate-orders.md](events-tastings-and-corporate-orders.md)) |

## 4. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Customer bought our gift cards for a scammer, or a scammer has the card details | P1 | `fraud_signal` | Time matters: the balance may still be frozen. Include the card's last 4 digits only (A-74) and when it was shared |
| Balance used by someone the customer doesn't know | P1 | `fraud_signal` | Include the expected vs current balance from `get_gift_card_balance` |
| Lost or stolen registered card (freeze and replace) | P2 | `create_support_ticket(category="gift_card")` | Include the account and last 4 digits |
| Lost or stolen unregistered card, with the purchase receipt | P2 | `create_support_ticket(category="gift_card")` | Include the receipt details; without a receipt, explain it works like cash |
| Customer says the law requires a cash payout of the balance | P3 | `create_support_ticket(category="gift_card")` | Don't decide it; finance checks the applicable rule |
| Digital card not received after resend and a spam check | P3 | `create_support_ticket(category="gift_card")` | Include the order number and recipient email |
| Bulk or corporate gift cards | P2 | `create_support_ticket(category="corporate_gifting")` | See [events-tastings-and-corporate-orders.md](events-tastings-and-corporate-orders.md) §3 |

**Handle without escalating:** balance checks through the secure form, how to send a digital card, expiry and fee questions (none), and gift cards for recipients under 21 or outside NJ/NY (decline or suggest another gift).

## 5. Response examples

> "Our gift cards never expire and have no fees. You can send a digital card by email, even scheduled for their birthday, for any amount from $10 to $500. The recipient will need to be 21+ to use it on wine."

> "To check your balance securely, please enter the card number and PIN here [secure link]. I'm not able to take card details in chat."
