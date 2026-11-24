# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + Vite + TypeScript, in `frontend/`. Chosen by the user (2026-11-23). The backend is the existing FastAPI + LangGraph service in `app/`.

## Users

Retail customers of an online wine and spirits store that delivers in New Jersey and New York (21+ only). They open the chat to get help with an order: where it is, a refund or return, a damaged or wrong item, a cancellation, delivery and pickup, account and loyalty questions. Some also want help choosing a wine by taste, region, occasion or price. Many are on a phone, and some are frustrated by a problem with an order.

## Product Purpose

SipGuide AI is the store's customer-support chat assistant. Customers ask questions in plain language and the agent answers from the knowledge base (`_KB/`) and the store's Tool APIs. It acts (refunds, cancellations, claims) only after the customer confirms, and it escalates to a human when needed. Success means the issue is resolved in the chat, correctly, without a phone call.

## Positioning

The answers come from the store's own live data (orders, stock, policies for each state) through typed tools, not from generic wine trivia. It speaks as the store ("we").

## Operating Context

- Each chat is a **conversation** with a unique Conversation ID. Its title comes from the customer's first question.
- A conversation is an ordered list of **turns**. Each turn holds one human message and one AI response, and each message has its own Message ID.
- Earlier turns are kept so they can be sent to the agent as context.
- The backend contract is `POST /api/v1/agent/chat` (`session_id`, `customer_id`, `message`, `confirm_action_id`). Its response carries `run_id`, `intent`, `kb_sources`, `pending_action`, `requires_confirmation` and `escalation` (`app/schemas/agent.py`).
- Human support hours: 9:00 am to 9:00 pm ET, 7 days. The AI agent is available 24/7.

## Capabilities and Constraints

- Delivery is phased: Phase 1 is the frontend (mock data, state saved in the browser's localStorage), Phase 2 adds backend APIs, Phase 3 adds agent orchestration (harness, agents, tools).
- **No document or file uploads in the chat**, by explicit scope decision. Return evidence goes through a separate short-lived upload link (KB rule RTN-R6).
- All business numbers in the KB are unconfirmed assumptions (A-xx). The UI must not hard-code fees, thresholds or time windows as facts.
- Undecided: authentication and customer sign-in flow, and the production deployment target.

## Brand Commitments

- Name: **SipGuide AI** (user's choice, 2026-11-23). A quick web search found no product with this name, but no trademark search has been done.
- Voice: from `_KB/00_system/agent-persona-and-tone.md`. A friendly, knowledgeable wine-shop associate who is never snobby, plain-spoken, concise and warm. It is clearly an AI and offers a human when asked.
- The user cited the Wine Spectator app as a reference for a clean, minimal feel. Never use that publication's name, logo, marks or layout as branding.

## Evidence on Hand

- `_KB/` (111 docs) and the seed DB `_DB/` hold fictional customers, orders and products. There are no real testimonials, ratings or press, and none may be fabricated.

## Product Principles

1. Resolve the customer's issue first; selling comes second, and never to a frustrated customer.
2. Never act without explicit confirmation from the customer; show what will happen before it happens.
3. Be honest about being an AI, and make the path to a human obvious.
4. Keep the history of every conversation intact and in order, so the agent always has context.

## Accessibility & Inclusion

The audience is 21+ and often on mobile. Target WCAG 2.2 AA: full keyboard use, visible focus, announced streaming replies, and no meaning carried by color alone.
