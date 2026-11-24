# API Assessment, Prioritization and Consolidation

Status: proposal (input to the tool-conversion phase). Date: 2026-11-23. Scope: every API in [`API_DESIGN.md`](API_DESIGN.md). This document **does not** change any API or tool. It decides which APIs the agent should see and in what shape.

## 1. Summary

- **39 routes** exist: 31 business (Category 1) and 8 agentic (Category 2). The agentic APIs and `/auth/dev-token` are not tool candidates, which leaves **30 business APIs** to assess.
- Today **all of them** are exposed: 29 HTTP tools plus `search_kb` = **30 tools**, about 16,100 characters (~4,000 tokens) of definitions on every LLM call. A turn makes up to 8 LLM calls.
- Proposal: **13 tools**. 9 are P1, 4 are P2. 5 APIs go to the P3 backlog, and 2 redundant ones are dropped from the agent's view. Estimated definition size is ~10,000 characters (~2,500 tokens), about 38% smaller, with **no loss of coverage** for the common intents.
- **The APIs stay granular.** UIs and back-office tools use them too, so consolidation happens at the agent-facing layer. Three small API changes are proposed where a merge needs server logic (§5).

| Priority | Meaning | APIs | Agent tools |
|---|---|---|---|
| **P1** | Core: high-frequency intents, or required to resolve them safely | 16 | 9 |
| **P2** | Common but secondary, or answerable from the KB most of the time | 7 | 4 |
| **P3** | Backlog: rare, or with no action the agent can take | 5 | 0 |
| Drop | Redundant: another API already returns the same data | 2 | 0 |
| N/A | Not a tool (agentic/frontend APIs, dev-only auth) | 9 | 0 |

## 2. How priority was decided

Each API was scored on three axes:

1. **Query frequency.** No production traffic exists yet, and the 13 seeded support tickets are too few to count. Frequency is therefore estimated from the KB intent taxonomy (`_KB/00_system/intent-taxonomy.md`) and the usual pattern for e-commerce support. Post-purchase questions dominate: where is my order, refunds and returns, damaged or wrong items, cancellations. Product discovery questions dominate pre-purchase.
2. **Business value.** Does it resolve the issue without a human (a refund, a claim, a cancellation), or does it only answer a question the KB could answer?
3. **Functional necessity.** Is it a required step in a P1 flow (for example eligibility before any refund), or is its data already returned by another API?

> **Re-rank with real data.** Every tool call is already logged (`agent_tool_calls`, exposed at `GET /agent/runs/{id}/tools`). After a pilot, count calls per tool and per intent, then promote P3 items that customers ask for and demote P2 items that are never used.

## 3. API-by-API assessment

Disposition values: **Keep** (stand-alone tool), **Merge → X** (becomes part of tool X), **Drop** (redundant for the agent; the API stays for UIs), **Backlog** (P3), **Not a tool**.

### Customer

| API | Current tool | Priority | Disposition | Rationale |
|---|---|---|---|---|
| `GET /customers/{id}/orders` | `list_customer_orders` | **P1** | Keep | The entry point to almost every post-purchase flow ("my last order", "the one from last week"). |
| `GET /customers/{id}/account` | `get_account_summary` | **P2** | Keep, rename `get_account` | Loyalty points, rewards, store credit, saved cards, age-verification status. Covers `loyalty.balance` and `account.age_verification`. |
| `GET /customers/{id}/tickets` | `list_support_tickets` | **P2** | Merge → `get_support_tickets` | Customers come back to ask "any update on my ticket?" once the agent escalates. Merged with the single-ticket lookup (below). |
| `GET /customers/{id}` | `get_customer_profile` | P3 | Not a tool: preload | First name and home store are useful on *every* turn. Load them once into the session context instead of spending a tool call. Age-verification status is already in `/account`. |
| `GET /customers/{id}/addresses` | `get_customer_addresses` | P3 | Backlog | Read-only and masked. There is no address-update API, so the agent can't act on what it reads, and delivery questions are answered from a ZIP. |

### Orders

| API | Current tool | Priority | Disposition | Rationale |
|---|---|---|---|---|
| `GET /orders/{id}` | `get_order` | **P1** | Keep (anchor of the merged order tool) | Needed by status, refund, return, wrong-item and cancellation flows. |
| `GET /orders/{id}/status` | `get_order_status` | **P1** | Merge → `get_order` | "Where is my order?" is the most frequent question. `OrderDetail` already has status, payment status, hold reason and shipments. It lacks only `status_description`, the ETA window and `last_updated_at`. Add those 4 fields (§5.1) and a status question takes one call. |
| `GET /orders/{id}/tracking` | `get_order_tracking` | **P1** | Merge → `get_order(include=["tracking"])` | Needed only when shipped. Today it is a second, sequential call after status. |
| `GET /orders/{id}/items` | `get_order_items` | P1 data | **Drop** | Redundant: it returns the same `OrderLine` model (including shipped, returned and refunded quantities) that `get_order.lines` already embeds. The rule-based planner calls both in the wrong-item flow. |
| `GET /orders/{id}/payment` | `get_order_payment` | **P2** | Merge → `get_order(include=["payment"])` | "Was I charged?", "which card?". Moderate frequency. Stays audited: the audit row is written only when `payment` is requested. |
| `GET /orders/{id}/history` | `get_order_history` | P3 | Backlog | Status plus `placed_at`, `delivered_at`, `cancelled_at` and `last_updated_at` answer "when did it ship / arrive". A full timeline is rarely asked for. |
| `GET /orders/{id}/invoice` | `get_invoice` | P3 | Backlog | Receipts belong in email and the account page. Totals, discounts and tax are already in `get_order`. The agent can't deliver a document. |

### Eligibility, refunds, returns and cancellation

| API | Current tool | Priority | Disposition | Rationale |
|---|---|---|---|---|
| `GET /orders/{id}/refund-eligibility` | `check_refund_eligibility` | **P1** | Merge → `check_eligibility(action="refund")` | Must run before any refund is discussed. |
| `GET /orders/{id}/return-eligibility` | `check_return_eligibility` | **P1** | Merge → `check_eligibility(action="return")` | Same policy engine (`PolicyEngine.evaluate_claim`, only `mode` differs) and the same `EligibilityResult` response. Two tools for one engine make the model guess which applies. |
| `GET /orders/{id}/cancellation-eligibility` | `check_cancellation_eligibility` | **P1** | Merge → `check_eligibility(action="cancel")` | Same role (a read-only decision before a gated write). Different response model, dispatched by `action`. |
| `GET /orders/{id}/refunds` | `get_order_refunds` | **P1** | Merge → `get_order(include=["claims"])` | "Where is my refund?" is a top post-purchase question. The current flow always calls refunds and returns together. |
| `GET /orders/{id}/returns` | `get_order_returns` | **P1** | Merge → `get_order(include=["claims"])` | See above. |
| `POST /orders/{id}/refunds` | `request_refund` ⚠ | **P1** | Merge → `submit_claim` (gated) | Resolves damaged, corked and wrong-item claims without a human: the highest-value automated action. |
| `POST /orders/{id}/returns` | `create_return_request` ⚠ | **P1** | Merge → `submit_claim` (gated) | Today the choice between refund-only and RMA follows a rule that comes from eligibility (`evidence_required` in `approval_reasons`). That is policy, so it belongs on the server, not in the LLM (§5.2). |
| `POST /returns/{rma}/evidence-upload-link` | `request_evidence_upload` | **P1** | Fold into the `submit_claim` response | Every damage claim that needs photos makes this call right after the RMA is created. Return the link in the same response (§5.3). The endpoint stays for re-issuing expired links. |
| `POST /orders/{id}/cancellation` | `cancel_order` ⚠ | **P1** | Keep (gated) | A distinct, frequent intent with a simple schema and an irreversible effect. Kept separate so the confirmation summary stays unambiguous. |
| `GET /returns/{rma}` | `get_return_status` | P3 | Backlog | Customers almost always reference an order. The same RMA data comes back from `get_order(include=["claims"])`. |

### Catalog, fulfillment and stores

| API | Current tool | Priority | Disposition | Rationale |
|---|---|---|---|---|
| `GET /products` | `search_products` | **P1** | Keep | 12 of the taxonomy's 13 discovery intents (taste, food, region, budget, organic, NA, sparkling...) go through it. It is the core of the wine-specific value. |
| `GET /products/{sku}` | `get_product_details` | **P1** | Keep | ABV, vegan/organic evidence, nutrition and tasting notes. Already includes `prices` and `availability_by_location`. |
| `GET /products/{sku}/availability` | `check_inventory` | P1 data | **Drop** | Redundant: it returns the same `Availability` model that `get_product_details.availability_by_location` and `search_products[].availability` already embed. |
| `GET /shipping/estimate` | `get_delivery_estimate` | **P2** | Keep | "Do you deliver to 07030?" is common for an NJ/NY-only alcohol seller. The KB answers the general policy, and this tool gives the ZIP-specific zone, fee and minimum. |
| `GET /stores`, `GET /stores/{code}` | `get_store_info` | **P2** | Keep (one tool for both routes) | Hours are frequent but mostly static. The tool is needed for holiday exceptions. Option: with only 2 stores, preload hours into the cached system prompt and drop the tool. |

### Support

| API | Current tool | Priority | Disposition | Rationale |
|---|---|---|---|---|
| `POST /support/tickets` | `create_support_ticket` | **P1** | Keep | The escalation path for everything outside the agent's authority. Required by the escalation matrix and the compliance flags (crisis, fraud, human request). |
| `GET /support/tickets/{n}` | `get_support_ticket` | **P2** | Merge → `get_support_tickets(ticket_number?)` | No number lists the customer's tickets. With a number, returns that ticket's public messages. |

### Not tool candidates

| API | Reason |
|---|---|
| `POST /agent/chat`, `GET /agent/sessions/*` (3), `GET /agent/runs/*` (3), `GET /agent/health` | Category 2: these are the frontend's interface to the agent. The agent never calls them. |
| `POST /auth/dev-token` | Local/dev only. |

## 4. Proposed agent tool set

| # | Tool | Priority | Replaces (current tools) | Kind |
|---|---|---|---|---|
| 1 | `search_kb` | P1 | `search_kb` | KB (in-process) |
| 2 | `list_customer_orders` | P1 | `list_customer_orders` | read |
| 3 | `get_order(order_id, include?: [tracking, claims, payment])` | P1 (`payment` is P2) | `get_order`, `get_order_status`, `get_order_tracking`, `get_order_items`, `get_order_refunds`, `get_order_returns`, `get_order_payment` | read |
| 4 | `check_eligibility(order_id, action: refund\|return\|cancel, reason_code?)` | P1 | 3 eligibility tools | read |
| 5 | `submit_claim(order_id, reason_code, items?, remedy?)` | P1 | `request_refund`, `create_return_request`, `request_evidence_upload` | write, gated |
| 6 | `cancel_order(order_id)` | P1 | `cancel_order` | write, gated |
| 7 | `search_products` | P1 | `search_products` | read |
| 8 | `get_product_details` | P1 | `get_product_details`, `check_inventory` | read |
| 9 | `create_support_ticket` | P1 | `create_support_ticket` | write |
| 10 | `get_account` | P2 | `get_account_summary` (+ `get_customer_profile` via session preload) | read |
| 11 | `get_support_tickets(ticket_number?)` | P2 | `list_support_tickets`, `get_support_ticket` | read |
| 12 | `get_delivery_estimate` | P2 | `get_delivery_estimate` | read |
| 13 | `get_store_info` | P2 | `get_store_info` | read |

**Effect on the common flows** (tool calls when the order number is unknown):

| Flow | Today | Proposed | Change |
|---|---|---|---|
| Where is my order (shipped) | `list_customer_orders` → `get_order_status` → `get_order_tracking` | `list_customer_orders` → `get_order(include=[tracking])` | −1 call, −1 sequential step |
| Where is my refund | list → `get_order_refunds` + `get_order_returns` + `search_kb` | list → `get_order(include=[claims])` + `search_kb` | −1 call |
| Broken bottle, wants a refund | list → `get_order` + `search_kb` + eligibility → `create_return_request` → `request_evidence_upload` | list → `get_order` + `search_kb` + `check_eligibility` → `submit_claim` (link included) | −1 call, and no refund-vs-return guess |
| Wrong item | list → `get_order` + `get_order_items` + eligibility → ticket | list → `get_order` + `check_eligibility` → ticket | −1 call |
| "Is X in stock?" | `search_products` → `check_inventory` | `search_products` (availability included) | −1 call |

**On cost.** The system prompt and tool list are already prompt-cached (`anthropic_llm.py`), so after the first call the definitions are billed at the cache-read rate. The larger savings are therefore:
(a) fewer calls per turn, since each one resends the whole conversation;
(b) fewer, clearer choices, which improves tool selection (refund vs return eligibility is the clearest current case of near-duplicate tools);
(c) a smaller context window footprint.

The definition sizes above are measured for existing tools; for merged tools they are estimates. Confirm both with `count_tokens` in the next phase.

## 5. API changes the consolidation needs

Most merges are pure **tool-layer facades**: the tool calls one or more existing endpoints (in parallel where it can) and returns the combined result, with no API change. Three merges need small server changes because the logic is business policy:

1. **Enrich `GET /orders/{id}`** with `status_description`, `eta_window_start`, `eta_window_end` and `last_updated_at`, the 4 fields only `/status` has today. Keep `/status` for UIs.
2. **Add `POST /orders/{id}/claims`.** It runs `evaluate_claim` and decides on the server whether the claim is a direct refund or an RMA (today: `evidence_required` → RMA, otherwise refund). Then it calls the existing refund or return logic. It keeps the existing idempotency, confirmation and authority-cap rules (A-60/A-61). `POST /refunds` and `POST /returns` stay for staff and UIs.
3. **Return the evidence upload link** in the claim response when `evidence_required` is true, so the customer gets it in the same turn.

## 6. P3 backlog and known gaps

**Backlog (built, not exposed):** `get_customer_profile` (preloaded instead), `get_customer_addresses`, `get_order_history`, `get_invoice`, `get_return_status`, standalone `request_evidence_upload` (re-issue). **Dropped as redundant for the agent:** `get_order_items`, `check_inventory` (and `get_order_status`, once §5.1 is done).

**Not built yet.** The intent taxonomy names these, with no API today. They are listed for demand tracking, not for this phase:
- **Promotions:** `get_active_promotions`, `validate_promo_code`. "My code isn't working" is usually a common contact reason, and the `promotions` tables already exist. This is the likeliest to become P2 once there is data.
- **Order changes:** `modify_order`, `reschedule_delivery`, plus the failed-delivery follow-up.
- **Stock:** `subscribe_back_in_stock`, `get_similar_products`, `submit_product_request`.
- **Account:** `send_password_reset`, `update_communication_preferences`, `submit_privacy_request`, `lock_account`, `get_gift_card_balance`.

Until these exist, the agent answers from the KB and opens a ticket.

## 7. Notes for the next phase

- The KB names tools in its workflows. When the tool set changes, update `_KB/00_system/tool-reference.md` (KB-SYS-004) and the `Tools` column of `intent-taxonomy.md` (KB-SYS-005), then `grep -r "<old_tool_name>" _KB/`.
- Update the rule-based planner (`app/agent/llm/rule_based.py`) to the merged tools so the offline mode and the tests match the Claude path.
- Keep the confirmation gate as it is. `submit_claim` and `cancel_order` are the only gated tools.
