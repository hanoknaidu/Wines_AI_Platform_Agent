---
id: KB-ACC-003
title: Profile, Saved Addresses and Payment Methods
category: account
subcategory: profile
doc_type: workflow
intents: [account.update_profile, account.payment_methods, delivery.eligibility]
tools: [verify_customer_identity, get_customer_profile, update_customer_profile, manage_address, remove_payment_method, get_fulfillment_options, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: customer-support
status: active
depends_on_assumptions: [A-01, A-02, A-20, A-29, A-70, A-74, A-75]
related: [KB-ACC-001, KB-ACC-002, KB-ORD-003]
---

# Profile, Saved Addresses and Payment Methods

## 1. What the agent can change (after identity verification, A-70)

| Field | Agent can change? | Notes |
|---|---|---|
| Phone number | ✅ | OTP to the new number confirms it |
| Name (spelling/legal change) | ⚠️ | Allowed, but may trigger **re-verification** of age/ID if it no longer matches the verified ID |
| Email | ✅ via the email-change flow | See [login-password-and-security.md](login-password-and-security.md) |
| Date of birth | ❌ | Human review with ID (AC-R1) |
| Saved addresses (add/edit/remove) | ✅ `manage_address` | Restricted destinations flagged (A-20); up to 10 (A-75) |
| Default address / default store | ✅ | Changes the NJ/NY store experience (A-01) |
| Delivery instructions (gate codes, building notes) | ✅ | Don't store sensitive info like alarm codes |
| Payment cards | **Remove only** `remove_payment_method` | Adding or updating cards happens only in the secure checkout (A-74) |
| Taste preferences, birthday-month greeting | ✅ | See the order-history/taste doc |
| Communication preferences | ✅ | See the communication doc |

## 2. Address rules

- Addresses must be in **NJ or NY** for delivery/shipping (A-02). Other-state addresses can be saved as billing addresses only.
- The **default address determines the default store**. Customers with both NJ and NY addresses see each store's catalog when they switch.
- `manage_address` returns `restricted_destination_flag` for PO boxes, schools, dorms, etc. (A-20). Explain: "We can save it, but we can't deliver alcohol there."
- Changing the address on an **open order** follows order-change rules (OC-R5).

## 3. Payment method rules

- Supported methods: see A-29.
- The agent sees only masked details (brand, last 4, expiry).
- **To add or update a card:** "For your security, please add it in Account → Payment Methods, or at checkout. I can't take card details in chat."
- Removing a card used on an open order: allowed after the order is captured; otherwise the tool returns `in_use_by_open_order`.
- Billing address mismatch causes declines; update it in the secure UI.

## 4. Workflow: update address

1. Verify identity.
2. Collect the address (street, unit, city, ZIP, state).
3. `manage_address(customer_id, action="add"|"edit", address)` → check flags.
4. Optionally `get_fulfillment_options(address)` to tell the customer about delivery availability there.
5. Confirm: "Saved. Your default store is now our NY store."

## 5. Edge cases

| Case | Handling |
|---|---|
| Customer moving from NJ to NY | Update the default address; explain that NY Store prices, stock and promotions apply; Rewards carry over |
| Customer moving out of NJ/NY | The account stays active; delivery isn't available outside NJ/NY; offer to keep the account or delete it (privacy doc) |
| Two people share one account | Not recommended (verification is per person); suggest separate accounts |
| Customer wants to change the name on a past receipt | Receipts reflect the order; P3 for an invoice reissue |

## 6. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Profile changes the customer didn't make (new address, removed card, changed email) | P1 | `account_takeover` | Contain per [account-takeover-and-fraud.md](account-takeover-and-fraud.md) §2 |
| Request to redirect an already-dispatched order to a different, unrelated address | P1 | `fraud_signal` | Don't change it (G9, OC-R5); stay neutral with the customer |
| Date-of-birth change | P2 | `account_recovery` | Explain that a team member corrects it with ID through a secure process (AC-R1) |
| Name change triggers re-verification, and it fails after one retry | P2 | `id_verification_failure` | Note the old and new names; record no ID details |
| Can't verify identity because the phone or email on file is no longer reachable | P2 | `account_recovery` | Make no changes until identity is verified |
| `manage_address` or `update_customer_profile` errors after one retry | P2 | `tool_failure` | Tell the customer the change isn't saved yet |
| Invoice reissue with a different name | P3 | `create_support_ticket(category="invoice_request")` | Include the order number and the name required |

**Handle without escalating:** card removal (`in_use_by_open_order` just means waiting until the order is captured), restricted-destination flags (explain them), and customers moving between NJ and NY or out of state (§5).

## 7. Response examples

> "Done. I've saved your new Brooklyn address and set it as default. Just a heads-up: since it's in New York, you'll now see our NY store's prices and selection."

> "I've removed the Visa ending 1188. To add your new card, go to Account → Payment Methods. For security, card details can't be shared in chat."
