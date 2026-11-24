# SipGuide AI — chat frontend (Phase 1)

The customer-support chat UI for the store. React 19 + Vite + TypeScript. In Phase 1 every reply comes from a local mock agent, and conversations are saved in the browser's localStorage.

## Run

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm test           # unit tests (Vitest)
npm run build      # typecheck + production build into dist/
```

## What it does

- **Sidebar** with conversation history, grouped Today / Yesterday / Previous 7 days / Older. Delete one conversation (with an inline confirmation) or clear everything.
- **Chat window** with multi-turn conversations. Under each AI answer, a status byline shows a verdict when one applies (**Needs you**, **Resolved**, **With our team**), the topic, the time and the KB guides it used.
- **Proposed actions** (cancel, return, refund) get a card with verb buttons ("Cancel order" / "Keep order"), when the offer expires, and a clear state once answered, closed or expired. Typing an unambiguous "yes" or "no" answers the offer, as the backend allows; any other message closes it. Only an explicit "yes", "yes please" or "go ahead" confirms any action: a casual "ok" or "sure" is held in the prompt bar with a hint instead of being sent. A closed or expired offer can't be reopened directly: **Ask our team to reopen** sends it to the team as a review ticket, and nothing changes until they approve it.
- **Outcomes**: finished actions get a receipt (return/order/ticket numbers). Tickets live in one place: a panel under the header lists each one (a request for a person, or a review to reopen an offer) with its status, how the team will reply and whether they're online now (support hours are in `src/config.ts`). History items are marked when they wait on the customer or have a ticket.
- **Returns** are offered only after SipGuide has the order number, the bottle and its condition, and has checked them against the Returns Policy (not collected yet, opened, or unknown orders are explained instead).
- **Talk to a person** is always available under the prompt bar and on error messages, even while an answer is pending (it stops that answer first). A **Stop** button replaces Send while SipGuide is answering. Once a ticket is open, the link becomes **Add a note to TKT-…**, which sends the next message to that ticket; asking for a person again also adds to it instead of opening a new one. Old failed messages offer **Ask again**.
- **Prompt bar**: Enter sends, Shift+Enter adds a new line, 4,000-character limit (the same as the backend).
- Pending (with a "taking longer" note after 5 s, also announced), stopped, error (with **Try again** on the latest message only, and whether anything changed), empty and mobile drawer states.
- Accessibility: one polite screen-reader announcement per reply, focus kept on a sensible element after every decision, starter, delete and retry, action cards named in every state, the page behind the mobile drawer made inert, a skip link to the message box, and 44px touch targets on touch screens.
- No file uploads, by scope decision.

## Data model (`src/types.ts`)

```
Conversation  id = conv_<32 hex>   ← Conversation ID, sent to the backend as session_id
  title                            ← generated from the first question (src/lib/title.ts)
  turns[]                          ← ordered
    Turn       id = turn_<32 hex>
      human    Message id = msg_<32 hex>
      ai       Message id = msg_<32 hex> | null while pending
               meta = run_id, intent, tools_used, kb_sources, pending_action, escalation …
      status   pending | complete | error
```

A conversation is only created when its first message is sent, so empty conversations never reach the history. `buildAgentContext()` (`src/lib/context.ts`) turns the earlier completed turns into the ordered `{message_id, role, content}` list that goes to the agent with each new message. It keeps the last 10 turns, set by `contextTurnLimit` in `src/config.ts`.

In dev builds a **Developer IDs** disclosure under each turn shows the conversation, turn, message and run IDs.

## Mock agent (`src/mock/mockAgent.ts`)

Keyword rules return the exact `ChatResponse` shape of `POST /api/v1/agent/chat`, using fictional seed customer **C-100005** (Aisha) and orders **WA-100105** / **WA-100114** from `_DB/`. Things to try:

| Ask | You get |
|---|---|
| "Where is my latest order?" | Order status and pickup details |
| "I'd like to return a bottle", then "WA-100114", then "the rosé, unopened" | Details are collected, the policy is checked, then a return is offered (try "WA-100105" for a not-eligible order) |
| "Cancel my order", then "yes" | A proposed cancellation, then the typed yes confirms it |
| "Something arrived broken" | A damaged-item claim reply |
| "Suggest a red wine for a steak dinner" | Three catalog picks |
| "Do you deliver to Philadelphia?" | NJ/NY-only answer |
| "I want to talk to a human" | Escalation with a ticket number |
| "simulate error" / "simulate slow" | The error + retry state / a 6-second pending state |

## Phase 2 hand-off

`src/api/agentClient.ts` is the only seam. Add an HTTP client there that POSTs to `/api/v1/agent/chat` with the customer JWT, then switch `agentClient` to it. Two backend points to settle:

1. `ChatRequest` has `extra="forbid"`, so it rejects a `context` field today. Either add one, or let the backend rebuild context from the session's stored messages (it already saves them per `session_id`).
2. History lives only in the browser today. To show it across devices, load it from `GET /agent/sessions/{id}/messages`; a "list my sessions" endpoint doesn't exist yet.

3. **Typed confirmations.** `AFFIRM_RE` in `app/agent/intent.py` confirms any pending action when a message merely *starts* with yes/ok/sure/… (up to 120 characters). The UI holds casual replies to a cancellation, but a client that sends them would still cancel. Align the backend: require an explicit yes (or `confirm_action_id`) for `cancel_order`.
4. `executed_action` is read as `{action_id, tool, ok, references}` (`_executed_out` in `app/agent/service.py`); the receipt shows `references.order_id`, `rma_number` and the refund `amount`, and an `ok: false` result as a failure.

Change the brand name in `src/config.ts` (`appName`).
