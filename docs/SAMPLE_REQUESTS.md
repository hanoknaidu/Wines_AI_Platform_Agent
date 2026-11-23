# Sample requests and responses

Captured from the Docker stack (PostgreSQL + Redis, rule-based planner, clock frozen at `2026-11-19T18:00:00Z`). All data is fictional seed data. IDs such as `run_…`, `act_…` and request IDs will differ on your machine.

```bash
B=http://localhost:8000/api/v1
TOKEN=$(curl -s -X POST $B/auth/dev-token -H 'Content-Type: application/json' \
  -d '{"role":"customer","subject":"C-100005"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
H="Authorization: Bearer $TOKEN"
```

## Tool APIs

### Refund eligibility (read-only policy decision)

```bash
curl -s "$B/orders/WA-100114/refund-eligibility?reason_code=wrong_item" -H "$H"
```
```json
{
  "order_id": "WA-100114",
  "eligible": true,
  "decision": "eligible",
  "reason_code": "wrong_item",
  "reasons": [{"code": "WITHIN_WINDOW",
               "message": "Reported within the 7 days window for wrong item (ends November 21, 2026).",
               "policy_ref": "A-31"}],
  "window_ends_at": "2026-11-21T21:10:00Z",
  "max_refundable_amount": "83.18",
  "agent_can_issue": true,
  "requires_human_approval": false,
  "approval_reasons": [],
  "policy_refs": ["A-31", "RF-R3", "RTN-R1"],
  "...": "eligible_items, reason_options, next_steps"
}
```

Other decisions you can reproduce:

| Request | Decision |
|---|---|
| `WA-100114?reason_code=broken_on_arrival` (C-100005) | `ineligible`: `OUTSIDE_WINDOW` (48 h, A-30) |
| `WA-100114?reason_code=corked_or_flawed` | `requires_review`: `evidence_required` (A-62) |
| `WA-100104?reason_code=change_of_mind` (C-100004, NY) | `ineligible`: `NY_NO_CHANGE_OF_MIND` (A-35) |
| `WA-100118?reason_code=corked_or_flawed` (C-100010) | `requires_review`: `chargeback_open` (RF-R5) |
| `WA-100109` (C-100009, not yet released) | `cancel_instead` |

### Initiate a refund (idempotent, needs confirmation)

```bash
curl -s -X POST $B/orders/WA-100114/refunds -H "$H" -H 'Idempotency-Key: 7f3c2a10-refund-1' \
  -H 'Content-Type: application/json' \
  -d '{"reason_code":"wrong_item","items":[{"line_number":1,"quantity":1}],"confirmed_by_customer":true}'
```
`201 Created` (`Idempotent-Replayed: false`; repeating the call returns the same body with `true`):
```json
{
  "refund": {"refund_id": "RF-400008", "order_id": "WA-100114", "reason_code": "wrong_item",
             "method": "original_payment", "status": "succeeded", "items_amount": "22.00",
             "tax_amount": "1.46", "amount": "23.46", "requires_human_approval": false,
             "expected_posting": "Card refunds are initiated within 1 business day and post in 5-10 business days (A-36).",
             "lines": [{"line_number": 1, "sku": "WN-STL-CDP-2025-750", "quantity": 1, "amount": "23.46"}]},
  "status": "succeeded",
  "requires_human_approval": false,
  "approval_reasons": [],
  "ticket_number": null,
  "message": "Refund issued."
}
```
When the agent asks for more than $150 (A-60), the endpoint returns `202 Accepted` with `"status": "pending_approval"`, the approval reasons, and the number of a P2 ticket it opened. No money moves until a human approves.

### Error envelope

```bash
curl -s -X POST $B/orders/WA-100120/cancellation -H "$H4" -H 'Idempotency-Key: cancel-0001' \
  -H 'Content-Type: application/json' -d '{"confirmed_by_customer":true}'
```
`422`:
```json
{"error": {"code": "ORDER_NOT_CANCELLABLE",
           "message": "This order is already with the driver or carrier, so it can't be cancelled. ...",
           "retryable": false, "request_id": "req_7709f03d…",
           "details": {"decision": "ineligible", "reasons": [{"code": "ALREADY_DISPATCHED", "policy_ref": "OC-R3"}]}}}
```

## Agentic APIs

### 1. A question about a refund: the agent checks, explains and asks

```bash
curl -s -X POST $B/agent/chat -H "$H" -H 'Content-Type: application/json' \
  -d '{"customer_id":"C-100005","session_id":"SESSION1001","message":"Can I get a refund for my order?"}'
```
```json
{
  "session_id": "SESSION1001",
  "run_id": "run_3d66b07446534e7392609e655be2c744",
  "status": "completed",
  "message": "I can help with order WA-100114. Refund options depend on what happened. Right now these are still open: wrong item, missing item, corked or flawed, leaking, change of mind. What went wrong with the order?",
  "intent": {"name": "refund.request", "confidence": 0.82},
  "tools_used": ["list_customer_orders", "search_kb", "check_refund_eligibility", "get_order"],
  "kb_sources": [{"id": "KB-RTN-001", "title": "Returns Policy (Master Policy and Decision Tree)", "section": "3. Decision tree"}],
  "pending_action": null,
  "requires_confirmation": false,
  "executed_action": null,
  "escalation": null,
  "llm_provider": "rule_based",
  "duration_ms": 96
}
```

### 2. Explicit request: the action is proposed, not executed

```json
// "message": "It was the wrong bottle, please refund me"
{
  "message": "Order WA-100114 is eligible: Reported within the 7 days window for wrong item (ends November 21, 2026). I can refund order WA-100114 for wrong item to the original payment for $83.18. Shall I go ahead? Please reply \"yes\" to confirm.",
  "tools_used": ["list_customer_orders", "search_kb", "get_order", "check_refund_eligibility", "request_refund"],
  "pending_action": {"action_id": "act_ab054325a78d4f8cbe5487e853eb8bef", "tool": "request_refund",
                     "summary": "refund order WA-100114 for wrong item to the original payment",
                     "expires_at": "2026-11-19T18:30:00Z"},
  "requires_confirmation": true
}
```

### 3. Confirmation: the action executes deterministically, without the LLM

```json
// "message": "yes", "confirm_action_id": "act_ab054325a78d4f8cbe5487e853eb8bef"
{
  "run_id": "run_bb4db668ec394cf3b7279ae6c334209c",
  "message": "Done: refund RF-400008 for $83.18 has been issued. Card refunds are initiated within 1 business day and post in 5-10 business days (A-36).",
  "intent": {"name": "action.confirmed", "confidence": 1.0},
  "executed_action": {"action_id": "act_ab05…", "tool": "request_refund", "ok": true,
                      "references": {"status": "succeeded", "refund_id": "RF-400008", "amount": "83.18"}}
}
```

### 4. Trace of that run

`GET $B/agent/runs/run_bb4db668…/steps`
```
1 run_started        chat            | session SESSION1001
2 guardrail          input_check     | passed
3 intent_classified  general.question| confidence 0.45
4 confirmation_check request_refund  | confirmed
5 tool_call          request_refund  | POST /orders/WA-100114/refunds -> 201
6 action_executed    request_refund  | refund order WA-100114 for wrong item to the original payment
7 llm_call           rule_based      | stop_reason=end_turn
8 response_generated final_answer    | 138 chars
9 run_completed      completed       | 1 tool calls
```
`GET $B/agent/runs/run_bb4db668…/tools`
```
request_refund  POST /orders/WA-100114/refunds  201  success  attempts=1  101ms
```
Audit row written in the same transaction as the refund:
```
refund.request | ai_agent | ai-agent:run_bb4db668ec394cf3b7279ae6c334209c | RF-400008 | success
```

### 5. Health

`GET $B/agent/health` returns `degraded` when no LLM key is configured (the rule-based planner is in use), and `ok` with Claude:
```json
{"status": "degraded", "checks": [
  {"name": "database", "status": "ok"},
  {"name": "knowledge_base", "status": "ok", "detail": {"documents": 92, "chunks": 642}},
  {"name": "llm", "status": "degraded", "detail": {"provider": "rule_based", "note": "No LLM configured: deterministic planner in use"}},
  {"name": "tool_api", "status": "ok", "detail": {"circuit_breaker": {"state": "closed", "consecutive_failures": 0}}}]}
```
