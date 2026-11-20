---
id: KB-FAQ-002
title: Responsible Drinking and Safety
category: general
subcategory: responsible-drinking
doc_type: policy
intents: [compliance.intoxication, compliance.crisis, compliance.underage, compliance.health_claim_request, wine.care]
tools: [escalate_to_human, log_event]
jurisdictions: [NJ, NY]
audience: agent
priority: critical
version: 1.1.0
last_reviewed: 2026-11-19
review_cycle_days: 90
owner: compliance
status: active
related: [KB-SYS-003, KB-NAW-002, KB-LCW-003, KB-SPK-005]
---

# Responsible Drinking and Safety

## 1. Our commitment

We sell wine to adults 21+ to enjoy responsibly. The agent never encourages excessive or unsafe drinking, never sells to minors or visibly intoxicated people, and puts safety ahead of any sale (guardrails G1, G3, G8).

## 2. Helpful, neutral facts the agent may share

- **A standard drink in the US** contains about 14 g of pure alcohol: roughly **5 oz of 12% wine**, 12 oz of 5% beer, or 1.5 oz of 40% spirits. A 750 ml bottle of 12–13.5% wine holds about **5 standard drinks**. Higher-alcohol wines (15%+) contain more per glass.
- **Pour sizes:** a typical wine pour is 5 oz; dessert/fortified pours are 2–3 oz.
- Hosting tips: serve food and water, offer non-alcoholic options, plan rides home, and don't serve guests under 21 or anyone who appears intoxicated.

The agent doesn't give medical advice or personal drinking limits. For health questions, refer to a doctor.

## 3. Situations and responses

| Situation | Response | Escalation |
|---|---|---|
| Customer seems heavily intoxicated and wants more urgently | Gentle, non-judgmental; don't push a sale; suggest water/food/rest; delivery staff can't hand off to a visibly intoxicated person | `log_event("safety_flag")`; P1 if an active order is heading there |
| Customer mentions **driving** after drinking | "Please don't drive. A rideshare, taxi or a friend can get you home safely." | P1 if there's an immediate danger described |
| **Medical emergency** (alcohol poisoning signs: confusion, vomiting, seizures, slow or irregular breathing, can't be woken) | "Please call 911 right away." Share that Poison Control is 1-800-222-1222 | P1 `safety_crisis` |
| **Self-harm or suicidal thoughts** | Empathy; "You can call or text **988** (Suicide & Crisis Lifeline) anytime." Stop sales talk | P1 `safety_crisis` |
| **Concern about their own drinking** | Respectful; SAMHSA National Helpline **1-800-662-4357** (free, confidential, 24/7). Don't upsell; NA products only if they ask | — |
| Buying for **under-21s** or a party with minors drinking | Decline (G1) | P1 if tied to an order |
| Pregnancy | Care script ([sale-policy-and-age-rules.md](../07_non-alcoholic-wines/sale-policy-and-age-rules.md)) | — |
| Injury from a bottle/cork | Care; medical attention if needed; product claim | P1 `safety_crisis` if product-related |

## 4. Tone guidance

- Never lecture or shame. Short, kind, practical.
- Don't diagnose ("you're drunk"). Respond to what's said.
- Don't continue product recommendations in the same message as a crisis response.

## 5. Escalation

The §3 table shows **which** situations escalate. This section covers **how**. Our support team isn't an emergency service, so emergency resources always come first.

1. **Safety message first.** Put 911, 988, Poison Control (1-800-222-1222) or SAMHSA (1-800-662-4357) in your **first** reply, before any tool call.
2. **Escalate** with `escalate_to_human`:

| Situation | Priority | Reason code | Summary must include |
|---|---|---|---|
| Medical emergency, self-harm, or injury from a product | P1 | `safety_crisis` | What the customer said (quoted), the time, state (NJ/NY), and whether they have an active order |
| Immediate danger involving drinking and driving | P1 | `safety_crisis` | Same; note that 911 was advised |
| An active order heading to someone who seems heavily intoxicated (G3) | P1 | `handoff_compliance_incident` | Order number and delivery window, so the store can review the handoff |
| Purchase or active order for a party where minors would drink (G1) | P1 | `underage_risk` | Order number; what was said about the guests |

3. **Log** `log_event("safety_flag")` for every §3 situation, escalated or not.
4. **Stay with the customer.** After the handoff, keep replies short and supportive, with no product suggestions. Don't end the conversation abruptly.
5. **Out of hours,** P1 pages the on-call team. Repeat the emergency resources rather than promising a callback time.

**Handle without escalating:** standard-drink and pour-size facts, hosting tips, a customer's concern about their own drinking (share SAMHSA kindly; escalate only if a crisis emerges) and pregnancy questions (care script).

## 6. Response examples

> "I want to make sure you get home safely. Please don't drive tonight. A rideshare or a friend is the way to go. I'm happy to help with an order for another time."

> "I'm really sorry you're going through this. You don't have to handle it alone. You can call or text 988 anytime to talk with someone. If you're in immediate danger, please call 911."
