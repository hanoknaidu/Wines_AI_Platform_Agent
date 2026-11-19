---
id: KB-SYS-001
title: Business Profile and Assumptions Register
category: system
subcategory: business-profile
doc_type: reference
intents: ["*"]
tools: []
jurisdictions: [NJ, NY]
audience: agent, kb-maintainers, compliance
priority: critical
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: operations-and-compliance
status: active
related: [KB-SYS-002, KB-SYS-003, KB-SYS-006, KB-SYS-009]
---

# Business Profile and Assumptions Register

## 1. Why this document exists

Every business-specific number or rule in this knowledge base (fees, thresholds, time windows, discount rates, approval limits) is an **assumption**. The research did not find one industry standard for these values, so each was chosen by combining practices from established retailers (see [research-references.md](research-references.md)).

This register is the **single source of truth for assumed values**. Every assumption has an ID (`A-xx`). Any KB document that relies on one lists it in a "Depends on" line. When the business changes a value:

1. Update the value here.
2. `grep -r "A-xx" _KB/` to find every dependent document.
3. Update those documents and bump their `version` and `last_reviewed`.

> **Agent rule:** Live data from tools (price, stock, order status, fees returned by `calculate_order_totals`) **always overrides** the values written here. These values describe policy, not live state. Never quote a fee or threshold from the KB if a tool can return the live value.

---

## 2. Business profile

| Item | Value |
|---|---|
| Business | "the Store": an online wine and spirits platform. The deployment brand name replaces "the Store" in customer-facing text. Agents speak as "we". |
| Primary category | Wine: still, sparkling, fortified, dessert, low-calorie, organic, non-alcoholic. Spirits and beer may be sold but are out of scope for this KB version. |
| Operating model | Licensed retailer as seller of record. Every order is fulfilled from a physical licensed store's inventory. This is the three-tier-compliant model used by City Hive-powered stores. |
| Fulfilling locations | **NJ Store**: New Jersey Plenary Retail Distribution licensee. **NY Store**: New York State Liquor Authority (SLA) retail liquor store licensee. They are affiliated stores, each separately licensed. |
| Service area | Addresses in **New Jersey and New York only**. |
| Customer support | AI agent 24/7; human support team 9:00 am – 9:00 pm ET, 7 days (holiday exceptions per `get_store_info`). |
| Legal drinking / purchase age | 21 in both states. |

---

## 3. Assumptions register

### 3.1 Licensing, jurisdiction and compliance

| ID | Assumption | Rationale / source pattern |
|---|---|---|
| A-01 | Orders are fulfilled by the licensed store **in the delivery state**: NJ addresses by the NJ Store, NY addresses by the NY Store. Cross-state transfer of alcoholic beverages between the stores does not happen. | Three-tier compliance; NY's direct-shipping statute (ABC Law §79-c) covers out-of-state *wineries*, not out-of-state retailers. |
| A-02 | **No shipping outside NJ and NY.** Requests to ship to other states are declined politely. | NY SLA has enforced against retailers shipping to other states (Empire Wine, 2014). This is the conservative choice. |
| A-03 | Prices, stock, promotions and assortment **can differ between the NJ Store and the NY Store**. | Separate licenses, wholesaler pricing and taxes per state. |
| A-04 | Customers must be **21+** to create an account, purchase, or receive any order. That includes non-alcoholic wine and gift cards. | Store policy. Age rules for NA products are unclear and inconsistent across states, so one rule avoids mistakes. |
| A-05 | Age is verified at three points: (1) date of birth at account creation, (2) third-party ID verification before the first order is released, (3) ID check at handoff (delivery, pickup, carrier adult signature). | Industry multipoint verification (City Hive, Persona guidance; carriers require an adult signature for alcohol). |
| A-06 | **Non-alcoholic (NA) wine is sold through the NJ Store only.** NY addresses cannot receive NA wine until compliance confirms NY law allows it. NY wine/liquor stores are, as of research date, generally not permitted to sell NA versions of alcoholic beverages; bills such as A6726 were pending. | Conservative. **Compliance review required. Re-check every review cycle.** |
| A-07 | Delivery and pickup handoffs happen only during legal hours of sale. Store delivery windows run 11:00 am – 9:00 pm, which falls inside both states' retail hours (NY Sunday retail hours are 10 am – 10 pm since Oct 2023). | NY ABC Law §105 (2023 amendment); NJ hours are set by municipality. |

### 3.2 Fulfillment: delivery, pickup, shipping

| ID | Assumption | Value |
|---|---|---|
| A-10 | Local delivery zones (per store) | Zone 1: 0–5 miles, fee **$5.99**. Zone 2: 5–15 miles, fee **$9.99**. |
| A-11 | Local delivery order minimum | **$40.00** product subtotal (after discounts, before tax). |
| A-12 | Free local delivery threshold | **$99.00** product subtotal (after discounts, before tax). |
| A-13 | Same-day delivery order cutoff | **6:00 pm** Mon–Sat; **3:00 pm** Sunday (store local time). |
| A-14 | Delivery windows | 2-hour windows from 11:00 am to 9:00 pm. |
| A-15 | In-state ground shipping (outside delivery zones) | Adult-signature carrier service. **$14.99** (1–6 bottles), **$19.99** (7–12 bottles), +$5.00 per additional 6 bottles; **free over $199** product subtotal. Business days only. |
| A-16 | In-store / curbside pickup | Free. Ready in **2 hours** during store hours (notification sent when ready). Held for **7 days**, then cancelled and refunded. |
| A-17 | Failed local delivery | One redelivery free. After a second failed attempt the order returns to the store, is held for pickup for 7 days, then cancelled; refund minus the delivery fee. |
| A-18 | Failed carrier shipment | Carrier makes up to 3 attempts, then returns the parcel. Refund = product total minus original shipping; first-time return shipping waived. |
| A-19 | Weather hold for shipping | Shipments may be held when origin or destination forecasts exceed **85°F** or fall below **28°F**. Customer is notified; may opt into insulated/expedited shipping at extra cost or wait. |
| A-20 | Restricted delivery destinations | No delivery to PO boxes, K-12 schools, college dormitories, or unattended locations. Hotels only if a named 21+ guest receives in person. No leave-at-door. |

### 3.3 Orders, cancellations, substitutions

| ID | Assumption | Value |
|---|---|---|
| A-21 | Free cancellation window | Any time before the order reaches `picking` status. Between `picking` and `dispatched`: cancellable on request, no fee, but not guaranteed. After `dispatched`: cannot cancel; refusal at the door is a failed delivery (A-17/A-18). |
| A-22 | Vintage substitution: automatic | Item price **under $25** and listing not marked vintage-specific: an adjacent vintage (±2 years) of the **same producer, same wine, same bottle size** may be substituted and noted on the receipt. |
| A-23 | Vintage substitution: consent required | Item **$25+**, or listing is vintage-specific (vintage Champagne, scored/collectible, older vintages): never substituted without consent. Customer is contacted and has **24 hours** to approve, otherwise the item is removed and refunded. |
| A-24 | Substitution preference at checkout | "Contact me" (default) · "Substitute a similar wine" (agent/staff may choose a same-style wine within ±10% of price) · "Do not substitute". |
| A-25 | Pre-arrival (futures) orders | Paid in full at order. Cancellable within **14 days** of order; after that, non-cancellable unless arrival is more than **90 days** later than the published estimate, in which case full refund is available. |
| A-26 | Purchase limits | Default max **36 bottles per SKU per order** unless the product shows a lower allocation limit. Orders over **$2,500** or **60 bottles** route to the events/bulk team (manual review). |

### 3.4 Returns, refunds, damages

| ID | Assumption | Value |
|---|---|---|
| A-30 | Damaged or broken on arrival | Report within **48 hours** of delivery with photo. Full refund or replacement; no need to return broken glass. |
| A-31 | Wrong or missing item | Report within **7 days**. We correct at no cost (redeliver or refund). The customer keeps or returns a wrong item as instructed; return pickup is free. |
| A-32 | Defective (corked, oxidized, cork failure, leaking seal) | Report within **30 days** of delivery or pickup. Bottle must be kept with **at least 75%** of contents, cork reinserted. Remedy: replacement of the same wine, or refund / store credit. |
| A-33 | Older-vintage exception | Wines **more than 10 years past vintage**, or listed as "library", "collectible" or "sold as-is", are sold at the buyer's risk for cork and natural ageing variation. Claims accepted only for clear storage/handling damage before sale. (Modeled on NYC retailer practice.) |
| A-34 | Change-of-mind returns: NJ Store | Unopened, resaleable, within **14 days**, with order number. Refund to the original payment method minus a **15% restocking fee**, or **full value as store credit**. Excludes special orders, pre-arrivals, allocated items, "final sale", large formats ≥ 3 L, and orders that were temperature-held by the customer. |
| A-35 | Change-of-mind returns: NY Store | **Not accepted.** All sales final except defective, damaged, or our error. (Matches common NY retailer practice such as "all sales are final on wines". Legal to confirm whether this is legally required or a policy choice.) |
| A-36 | Refund timing | Initiated within 1 business day of approval. Card refunds post in **5–10 business days** depending on bank. Store credit is instant. |

### 3.5 Pricing

| ID | Assumption | Value |
|---|---|---|
| A-40 | Price lock | Price is locked when the order is placed, except for obvious pricing errors (A-41). |
| A-41 | Pricing error | If a price was displayed in clear error (e.g., more than 50% below the item's regular price with no active promotion), we may cancel unfulfilled items with notice and full refund. Fulfilled orders are honored. |
| A-42 | Post-purchase price drops | No retroactive adjustment after fulfillment. Before fulfillment, the customer may cancel and re-order at the new price if stock allows. |
| A-43 | Price matching | Available on an **identical** item (same producer, wine, vintage, size) from a **licensed retailer in the same state**, in stock and publicly verifiable. Excludes marketplaces, auctions, membership-warehouse pricing, club/subscription, bundled and clearance prices. Requires human pricing approval; a match can never set a price below legal minimums (NJ below-cost rule). |
| A-44 | Price bands | Everyday under $15 · Step-up $15–$29.99 · Premium $30–$59.99 · Luxury $60–$149.99 · Collectible $150+ (per 750 ml). |

### 3.6 Discounts, promotions, loyalty

| ID | Assumption | Value |
|---|---|---|
| A-50 | Mixed-case discount | **10% off** 6–11 eligible 750 ml wines; **15% off** 12+. Mix and match. A 1.5 L bottle counts as 2; 375 ml counts as 0.5. Excludes sale-priced items, pre-arrival, allocated, gift cards, boxed/canned wine. |
| A-51 | Promo code stacking | One promo code per order. Codes do **not** combine with the mixed-case discount unless the code says "stackable". Codes never apply to taxes, gift cards, or (unless a free-delivery code) fees. |
| A-52 | First-order offer | **$10 off** first order of $75+ product subtotal, one per person/household/payment method. |
| A-53 | Loyalty program ("Rewards") | Free to join; open to all 21+ account holders. **1 point per $1** of eligible spend (after discounts, before tax/fees). **250 points = $10 reward.** Rewards expire **90 days** after issue; points expire after **12 months of account inactivity**. Insider tier at **$750** rolling 12-month spend: 1.25 pts/$ plus early access. |
| A-54 | Discounts must never reduce a price below legal minimums | The pricing engine enforces cost floors (NJ N.J.A.C. 13:2-24.8 below-cost prohibition). If a combination is blocked, the tool returns `blocked_by_price_floor` and the agent explains without blaming law in detail. |
| A-55 | Equal availability | Every discount or program is available to all eligible 21+ customers on the same terms. No private, unadvertised or "special group" pricing. |
| A-56 | Gift cards | Digital and physical. **Never expire, no fees.** Purchasable by 21+ only. Not redeemable for cash except where law requires. |

### 3.7 Agent authority and support

| ID | Assumption | Value |
|---|---|---|
| A-60 | Agent may refund autonomously | Damaged/broken/missing/wrong item claims up to **$150 per order** with required evidence. |
| A-61 | Agent may issue goodwill store credit | Up to **$15**, max once per customer per **90 days**, for service failures (late delivery, missed window). |
| A-62 | Requires human approval | Refunds over $150; any refund without required evidence; second claim within 60 days; price matches; returns outside window; account ownership disputes; all legal, privacy-deletion, safety, fraud or law-enforcement matters. |
| A-63 | Human support SLAs | **P1** (safety, fraud, account takeover, delivery to a minor or intoxicated person, injury): immediate live handoff during support hours, on-call page outside hours. **P2** (claims over $150, pricing disputes, privacy requests): first response within 4 business hours. **P3** (general): within 1 business day. |

### 3.8 Accounts and privacy

| ID | Assumption | Value |
|---|---|---|
| A-70 | Identity check before account actions | The agent acts on account data only in an authenticated session, or after a one-time passcode (OTP) to the email/phone on file via `verify_customer_identity`. |
| A-71 | Login security | Lockout after 5 failed attempts for 15 minutes. Password reset links expire after 30 minutes. MFA optional (recommended). |
| A-72 | Privacy rights | Access, correction, deletion, portability, and opt-out of targeted advertising / sale / profiling are offered to **all customers regardless of state** (modeled on the New Jersey Data Privacy Act, effective Jan 15, 2025). Target completion: 15 days; legal maximum 45 days (+45 extension). |
| A-73 | Record retention after deletion | Order, tax and age-verification records are retained as required by law, then deleted. Marketing and taste-profile data are deleted on request. |
| A-74 | Payment data | The agent never collects, reads back or stores full card numbers, CVV or ID images in chat. Payment and ID entry happen only in the secure UI. |

### 3.9 Store information (defaults; live hours via `get_store_info`)

| ID | Assumption | Value |
|---|---|---|
| A-80 | NJ Store hours | Mon–Sat 9:00 am – 10:00 pm; Sun 10:00 am – 7:00 pm (subject to municipal rules). |
| A-81 | NY Store hours | Mon–Sat 9:00 am – 10:00 pm; Sun 10:00 am – 8:00 pm. |
| A-82 | Closed / limited days | Closed Thanksgiving Day and Christmas Day (NY retail stores are required to close on Christmas). Reduced hours on New Year's Day. |

---

## 4. Open compliance questions (review before launch)

| # | Question | Affects |
|---|---|---|
| Q-1 | Can the NY Store sell non-alcoholic wine yet (status of A6726 / S3836-type bills)? | A-06, `07_non-alcoholic-wines/` |
| Q-2 | Is NY's "no change-of-mind returns" practice required by law or a policy choice? | A-35, `12_returns-refunds-damages/returns-policy.md` |
| Q-3 | Does the NJ Division of ABC have current guidance on loyalty points and coupon redemption against the below-cost rule (see Advisory Notice 2026-10 on coupons)? | A-50 to A-54 |
| Q-4 | Are mobile/digital driver's licenses acceptable ID for alcohol handoff in each state? | `11_orders-delivery-pickup/age-verification-at-handoff.md` |
| Q-5 | Status of TTB "Alcohol Facts" labeling rule (Notice No. 237, proposed Jan 2025). Do not claim it is final. | `05_low-calorie-and-better-for-you/` |
| Q-6 | Does the NJ Store use a 2022 NJ Third-Party Delivery Permit holder, its own drivers with transit insignia, or both? | `11_orders-delivery-pickup/local-delivery-policy.md` |

## 5. Change log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-11-19 | Initial register created from industry research. |
