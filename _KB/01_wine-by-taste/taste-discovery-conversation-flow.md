---
id: KB-TST-002
title: Taste Discovery Conversation Flow (Interview, Clarify, Refine)
category: taste
subcategory: conversation-flow
doc_type: workflow
intents: [recommend.by_taste, recommend.by_occasion, recommend.similar, refine.results, recommend.budget]
tools: [search_products, get_product_details, get_similar_products, list_orders, get_customer_profile, check_inventory, get_price, add_to_cart]
jurisdictions: [NJ, NY]
audience: agent
priority: high
version: 1.0.0
last_reviewed: 2026-11-19
review_cycle_days: 180
owner: wine-team
status: active
depends_on_assumptions: [A-03]
related: [KB-TST-001, KB-SYS-002, KB-SYS-007, KB-PRC-002]
---

# Taste Discovery Conversation Flow

## 1. Purpose

A step-by-step method to go from a vague request ("something nice") to 2–4 confident recommendations in as few turns as possible, then refine without starting over.

## 2. Principles

- **Ask at most 3 questions before showing wines.** People discover what they like by reacting to options. Show something early, then refine.
- **One question per turn**, preferably with easy choices: "Red, white, rosé or bubbly?"
- **Ask only what changes the result.** Don't ask about tannin for a white, or about body for dessert wine.
- **Use what you already know**: location, past orders, saved taste profile, items in cart.
- **Avoid the word "dry" in questions.** Ask about sensations instead ("Do you like wines that feel crisp like lemonade, or soft and round?").

## 3. The decision order

| Step | Question (only if unknown) | Why it's asked first |
|---|---|---|
| 0 | Location (ZIP or NJ/NY), needed for availability | Stock and price differ by store (A-03) |
| 1 | Style: red / white / rosé / sparkling / sweet | Decides which axes matter |
| 2 | Sweetness: "not sweet at all / a hint of sweetness / properly sweet" | Most noticeable axis |
| 3 | Branch: reds → "light and easy / in between / rich and bold"; whites/rosé/sparkling → "clean and crisp / in between / rounded and creamy" | Second most noticeable axis |
| 4 | Budget, if not given: offer bands ("under $15, $15–30, $30–60, or more?") | Hard constraint |
| 5 | Optional: occasion or food | Improves fit and "why" copy |

Skip any step the customer already answered, including indirectly. "A big Napa Cab under $50" answers steps 1, 3 and 4.

## 4. Workflow

1. **Classify** the request (`recommend.*`). Pull `get_customer_profile` if logged in (taste profile, past favorites).
2. **Fill slots** using §3. If the customer is in a hurry, ask only Step 1 (or nothing) and lean on bestsellers in stock.
3. **Map to filters** using [taste-profile-framework.md](taste-profile-framework.md) §4–6.
4. **Search** with `search_products(filters, fulfillment_location, limit=10)`.
5. **Select 2–4**: best fit first; vary producer/grape; include one value pick if the budget allows.
6. **Present** each pick: name, size, live price (`get_price`), status, and a one-line reason using the customer's words.
7. **Offer the next step**: add to cart, see more like this, or refine.
8. **Refine** on feedback (§6).

## 5. Handling difficult requests

| Situation | Handling |
|---|---|
| "I don't know anything about wine" | Reassure. Ask Step 1 with a hint: "Do you usually enjoy something light and refreshing, or rich and cozy?" Offer crowd-pleasers. |
| "Surprise me" | Ask one guardrail (red or white? budget?), then pick a well-rated, in-stock, versatile option and explain why. |
| Contradictions ("bold but light", "sweet but dry") | Name the tension kindly and offer both directions: "Do you mean full of flavor but not heavy? A juicy Grenache or Zinfandel could fit, or a lighter Pinot with lots of fruit." |
| "Dry" | Clarify once: "Do you mean not sweet, or do you also like that drying, tea-like grip?" If the customer dislikes bitterness, steer away from `tannin=grippy`. |
| Reference wine ("like Apothic Red") | Find the SKU; `get_similar_products`. Explain the shared traits ("smooth, a little sweet-fruited, hints of vanilla"). |
| Reference wine we don't carry | Use KB brand profile ([03_wine-by-brand/](../03_wine-by-brand/README.md)) to infer the profile, then search similar styles. Offer a product request. |
| Past purchase ("the one I got in March") | `list_orders` → identify → `check_inventory` → reorder or similar. |
| Group/party ("crowd-pleaser for 20 people") | Suggest one red, one white, one sparkling in Everyday/Step-up bands; quantity guidance in [sparkling-occasions-gifting-and-handling.md](../04_sparkling-champagne-prosecco/sparkling-occasions-gifting-and-handling.md); mention the case discount. |
| Gift with unknown taste | Versatile, recognizable picks: Champagne/quality sparkling, a well-known Napa Cabernet, Sancerre, Chianti Classico Riserva. Offer gift options. |
| "Best wine" | No single best. Ask budget + style, or offer a few highly rated options with sources from `accolades`. |
| Health-adjacent ("won't give me a headache") | Don't promise effects (G7). Offer lower-alcohol options or organic/low-sulfite information without claims. |

## 6. Refinement moves

| Customer says | Adjustment | Keep |
|---|---|---|
| "Lighter" | body −1 step; for reds, tannin −1 | color, budget, sweetness |
| "Bolder / more flavor" | body +1; fruit_profile → fruit_forward | color, budget |
| "Less sweet" | sweetness −1 step | everything else |
| "Sweeter" | sweetness +1 step; suggest Riesling, Moscato, Lambrusco | color if possible |
| "Smoother" | tannin → smooth; acidity → soft/fresh | body |
| "Less oaky" | oak → none/subtle | body may drop slightly |
| "More earthy / less fruity" | fruit_profile → earthy_savory; consider Old World | |
| "Cheaper" | price_max −25% or one price band down | style |
| "Something different" | change grape/region, keep axes | axes |
| "Not that one" (no reason) | Ask what they didn't like: price, grape, or style? | |

Always re-run `search_products` with updated filters. Don't just re-sort old results; stock may have changed.

## 7. Dialogue examples

**Example A: novice, quick path**
> **Customer:** I need a wine for dinner tonight, no idea what to get.
> **Agent:** Happy to help! What's for dinner? And would you prefer red or white?
> **Customer:** Roast chicken. White I guess.
> **Agent:** Roast chicken loves a white with a little richness. Here are three in stock for delivery tonight in your area:
> 1. **[Unoaked or lightly oaked Chardonnay, $X]**: round and fresh, won't overpower the chicken.
> 2. **[Côtes du Rhône Blanc, $X]**: soft, peachy and herbal, great with roasted vegetables.
> 3. **[Oregon Pinot Gris, $X]**: a bit fuller than Pinot Grigio, with pear notes.
> Want me to add one, or would you like something crisper?

**Example B: clarifying "dry"**
> **Customer:** I like dry reds.
> **Agent:** Great. Quick check: by dry, do you mean not sweet, or do you also enjoy that grippy, mouth-drying feel, like a strong black tea?
> **Customer:** Not sweet, but I don't like the drying thing.
> **Agent:** Got it: a dry red that's smooth. Merlot, Grenache-based blends or a Pinot Noir would suit you…

**Example C: refine**
> **Customer:** These look too heavy.
> **Agent:** No problem, let's go lighter. Here are three lighter-bodied reds with soft tannins: a Beaujolais-Villages, an Oregon Pinot Noir and a Sicilian Frappato…

## 8. Escalation

Taste discovery rarely needs escalation. Escalate (P3, `kb_gap`) only if a customer asks for expert guidance beyond KB scope (e.g., building a cellar investment portfolio, auction valuations). Offer a ticket to the wine team.
