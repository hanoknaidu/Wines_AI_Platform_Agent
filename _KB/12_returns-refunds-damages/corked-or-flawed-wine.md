---
id: KB-RTN-003
title: Corked or Flawed Wine (Fault Identification and Claims)
category: returns
subcategory: defects
doc_type: workflow
intents: [claim.flawed_wine, wine.care, education.wine_question]
tools: [get_order, get_product_details, create_return_request, request_evidence_upload, issue_refund, issue_store_credit, escalate_to_human, create_support_ticket]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: customer-support
status: active
depends_on_assumptions: [A-32, A-33, A-36, A-60, A-62]
related: [KB-RTN-001, KB-RTN-005, KB-ORG-004, KB-FAQ-003, KB-SPK-001]
---

# Corked or Flawed Wine

## 1. Policy (A-32, A-33)

- Report within **30 days** of delivery or pickup.
- **Keep the bottle with at least 75% of the wine**, cork or cap back in. Retailers ask this because the bottle may be returned to the supplier for credit, and an empty bottle can't be evaluated. (We won't accept empty bottles.)
- Remedy: **replacement** of the same wine (if available), or **refund / store credit**. No restocking fee in either state.
- **Older-vintage exception (A-33):** wines **more than 10 years past vintage**, or listed as "library", "collectible" or "sold as-is", are sold at the buyer's risk for cork condition and natural aging variation. Claims are accepted only for clear storage/handling problems before sale.
- **Authority (A-60):** the agent may approve defect claims up to $150 per order, max **2 bottles per customer per 60 days**; beyond that → human review.

## 2. Is it faulty? Help the customer tell

| Fault | What the customer notices | Likely cause | Covered? |
|---|---|---|---|
| **Cork taint (TCA, "corked")** | Musty, wet cardboard, damp basement; fruit muted | Contaminated cork/winery | **Yes** |
| **Oxidation** | Brownish color (white turns gold/brown, red turns brick), sherry-like/nutty, flat taste in a young wine | Failed seal, storage | **Yes** (young wines); older wines: A-33 |
| **Heat damage ("cooked")** | Stewed/jammy, flat; pushed cork, sticky capsule, leakage | Heat exposure before sale | **Yes** if before delivery |
| **Volatile acidity / acetic** | Vinegar, nail-polish remover | Bacteria | **Yes** |
| **Unintended refermentation** | A still wine fizzy with a pushed cork, cloudy, yeasty | Microbial | **Yes** (except styles meant to be spritzy) |
| **Flat sparkling** | No bubbles when opened (with an intact cork/cage) | Seal failure | **Yes** |
| **Light strike** | Wet wool, cabbage in Champagne/whites in clear glass | Light exposure | **Yes** |
| **Mousiness** (natural wines) | A cracker-like, mousy aftertaste | Microbial (low-sulfite wines) | **Yes** (review if a known style) |
| **Brettanomyces** | Barnyard, band-aid, smoky | Yeast | Case by case: some styles show a little "Brett" by design; strong → yes |
| **Reduction** | Struck match, rotten egg | Lack of oxygen | Usually **not a fault**: decant/swirl and it often fades; if persistent → yes |

**Not faults (explain kindly; not covered):**
- **Tartrate crystals** ("wine diamonds"): harmless, natural, look like glass or sugar; common in whites chilled cold.
- **Sediment** in older or unfiltered reds; haze in natural wines.
- **Light spritz** in young whites (Vinho Verde, some Albariño, pét-nat).
- **Crumbly cork in old bottles** (A-33); use an Ah-So/two-prong opener or strain.
- **"I just don't like it"**: a matter of taste, not a fault.

## 3. Workflow

1. `get_order` → item, delivery date (≤ 30 days?), vintage (A-33 check via `get_product_details.vintage`, `older_vintage`).
2. Ask **what they notice** (smell/taste/appearance) and when the bottle was opened. Use §2 to classify; avoid leading questions ("Does it smell like wet cardboard?" is fine only after they describe it).
3. If it's likely a non-fault (§2 bottom), explain gently and offer tips (decant, chill, wait). If the customer still believes it's faulty, proceed with the claim. **Customer good faith matters.**
4. Ask them to **re-cork and keep the bottle** (≥ 75% full) and upload a photo showing the label and fill level (`request_evidence_upload`).
5. `create_return_request(order_id, items, reason_code="corked_or_flawed", evidence_refs, customer_notes=<description>)`.
6. If `auto_approved` (within A-60 limits) → remedy: replacement (`add_to_cart` at $0 / next delivery) or refund/store credit.
7. Bottle collection: the store may ask the customer to **drop it off within 14 days** or collect it with the next delivery. If it isn't collected/returned, it doesn't affect the refund for claims ≤ $50; for higher amounts, the store may require the bottle (`pickup_required`).
8. Confirm the RMA and next steps.

## 4. Edge cases

| Case | Handling |
|---|---|
| Several bottles from the same case seem corked | Possible batch issue: replace all affected; escalate P3 to purchasing to check the lot |
| Customer already poured it out | Covered only with human review (P2); explain the keep-the-wine rule for next time |
| Collectible/old vintage | A-33; claims → human review (P2 `collectible_dispute`) |
| Bought in store (not online) | Same policy; receipt or account purchase history |
| Restaurant/event consumption (corked at a party) | Same policy, same evidence |
| Customer reports feeling unwell after drinking | P1 `safety_crisis` (product safety); suggest medical attention; don't speculate |

## 5. Escalation

| Situation | Priority | Reason code / route | Before handing off |
|---|---|---|---|
| Customer feels unwell after drinking the wine | P1 | `safety_crisis` | Suggest medical attention; don't speculate about the cause; ask them to keep the bottle |
| Claim over $150 for the order (A-60) | P2 | `refund_over_limit` | Create the return request with evidence first, so the reviewer has everything |
| More than 2 faulty bottles for this customer within 60 days (A-60) | P2 | `claim_review` | Include the earlier RMA numbers |
| Customer already poured the wine out (§1 keep-the-wine rule) | P2 | `claim_review` | Explain the rule kindly for next time; don't refuse the claim yourself |
| Wine more than 10 years past vintage, or sold as library, collectible or as-is (A-33) | P2 | `collectible_dispute` | Include the vintage, the customer's description and any storage notes |
| Reported after 30 days with a credible reason (e.g., bottle opened late for a planned occasion) | P2 | `policy_exception_request` | Include the delivery date and the reason |
| Several bottles from the same lot seem faulty | P3 | `create_support_ticket(category="lot_quality")` | Replace the affected bottles first within your authority; include SKU, vintage and lot if visible |

**Handle without escalating:** classifying faults, explaining non-faults kindly (tartrates, sediment, reduction), and approving claims within A-60 and the 2-bottle limit.

## 6. Response examples

> "Thanks for describing it. A musty, wet-cardboard smell is the classic sign of a 'corked' bottle. That's a cork fault, not something you did. Please put the cork back in and keep the bottle. Could you upload a photo showing the label and how full it is? Then I'll set up a replacement or refund, whichever you prefer."

> "Those little clear crystals are tartrates, sometimes called 'wine diamonds'. They're a natural, harmless part of wine that can form when it gets cold, and they don't affect the taste. If you'd like, pour slowly or through a fine strainer. Does anything else about the wine seem off?"

> "Because this 2008 Bordeaux is more than 10 years past its vintage, it was sold as-is for natural aging and cork condition. I've passed your description to our fine wine team, who review these cases individually, and they'll be in touch within 4 business hours."
