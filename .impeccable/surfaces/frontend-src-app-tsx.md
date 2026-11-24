---
version: 1
slug: "frontend-src-app-tsx"
primary_target: "frontend/src/App.tsx"
related_targets: []
---

# Surface: SipGuide AI support chat (frontend/)

Mode: Operate. A customer completes a support task (order status, refund, return, delivery, choosing a wine) in a multi-turn chat.

Audience and job: 21+ NJ/NY store customers, often on a phone and sometimes frustrated. They need an answer, or an action they confirm, without a phone call.

Constraints: Phase 1 uses mock data and localStorage only. No file uploads. The data model is conversation → ordered turns (human + AI message, each with its own ID), and earlier turns are kept as agent context. Mock replies follow the `POST /api/v1/agent/chat` ChatResponse shape.

## Direction contract

THESIS: A support chat that reads like a well-edited wine column, not a generic bot window. It refuses the bubble-on-grey messenger default: the agent's answers are set as editorial prose, and the chrome stays out of the way.

OWN-WORLD: White page, warm near-black ink, a single claret accent used only for the primary action, the current selection and focus. A slightly warm grey layer for the sidebar, with hairline rules. A self-hosted text serif for the wordmark and the AI's answers; system sans for every control, label and the customer's own words.

STORY: The customer sees their past conversations, asks in plain words, gets a concise answer with its sources and any action to confirm, and can always reach a human.

FIRST VIEWPORT: Left: a 272px sidebar with the wordmark, a "New conversation" button and history grouped by date. Right: a centered 720px reading column, with the composer pinned at the bottom. With no conversation open, a short serif greeting and four starter questions.

FORM: The editorial tasting-note answer. AI replies are set in serif with a small-caps byline (topic · sources · action status) beneath, the way a review closes with its score line. seed: none (pinned). The user's brief named both the world ("clean, minimalistic, similar to the Wine Spectator app") and the surface (sidebar history, chat window, prompt bar).

SIGNATURE: The byline under each answer. Pending actions appear inline with Confirm / Not now buttons.

## Unresolved
- Sign-in and real customer identity (Phase 2).
