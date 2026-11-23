"""Agentic API tests: tool selection per scenario, confirmation gate,
observability endpoints, LLM tool loop and degraded-mode fallback."""
from __future__ import annotations

import json

from sqlalchemy import func, select

from app.agent.llm.base import AssistantTurn, LLMError, ToolCall
from app.models import Refund, ReturnRequest

API = "/api/v1"


async def chat(client, auth, customer: str, message: str, session: str = "SESSION1001", **extra):
    r = await client.post(f"{API}/agent/chat", headers=auth(customer),
                          json={"customer_id": customer, "session_id": session, "message": message, **extra})
    assert r.status_code == 200, r.text
    return r.json()


class TestScenarios:
    async def test_where_is_my_order(self, client, auth):
        out = await chat(client, auth, "C-100004", "Where is my latest order?")
        assert out["status"] == "completed" and out["intent"]["name"] == "order.status"
        assert out["tools_used"][:2] == ["list_customer_orders", "get_order_status"]
        assert "get_order_tracking" in out["tools_used"] and "WA-100120" in out["message"]

    async def test_refund_question_does_not_issue_a_refund(self, client, auth, container):
        out = await chat(client, auth, "C-100005", "Can I get a refund for my order?")
        assert {"get_order", "search_kb", "check_refund_eligibility"} <= set(out["tools_used"])
        assert "request_refund" not in out["tools_used"] and out["pending_action"] is None
        assert out["kb_sources"] and "What went wrong" in out["message"]
        async with container.session_factory() as db:
            assert (await db.execute(select(func.count()).select_from(Refund))).scalar_one() == 7

    async def test_refund_request_is_gated_then_executed_on_yes(self, client, auth, container):
        first = await chat(client, auth, "C-100005", "I got the wrong bottle in WA-100114, please refund me")
        assert first["requires_confirmation"] is True
        pending = first["pending_action"]
        assert pending["tool"] == "request_refund" and "Shall I go ahead" in first["message"]
        async with container.session_factory() as db:  # nothing executed yet
            assert (await db.execute(select(func.count()).select_from(Refund))).scalar_one() == 7

        second = await chat(client, auth, "C-100005", "yes please")
        assert second["intent"]["name"] == "action.confirmed"
        assert second["executed_action"]["ok"] is True and second["pending_action"] is None
        refund_id = second["executed_action"]["references"]["refund_id"]
        assert refund_id in second["message"]
        refunds = (await client.get(f"{API}/orders/WA-100114/refunds", headers=auth("C-100005"))).json()
        assert any(r["refund_id"] == refund_id and r["status"] == "succeeded" for r in refunds)

        # Replaying the same confirmation can't refund twice (idempotency key = action id)
        third = await chat(client, auth, "C-100005", "yes")
        assert third["executed_action"] is None

    async def test_confirmation_via_button_and_decline(self, client, auth, container):
        first = await chat(client, auth, "C-100009", "Please cancel my order WA-100109", session="S-CANCEL")
        assert first["pending_action"]["tool"] == "cancel_order"
        declined = await chat(client, auth, "C-100009", "no, don't cancel it", session="S-CANCEL")
        assert declined["intent"]["name"] == "action.declined" and declined["pending_action"] is None
        status = (await client.get(f"{API}/orders/WA-100109/status", headers=auth("C-100009"))).json()
        assert status["status"] == "age_verification_pending"

        again = await chat(client, auth, "C-100009", "Please cancel my order WA-100109", session="S-CANCEL")
        done = await chat(client, auth, "C-100009", "Confirm", session="S-CANCEL",
                          confirm_action_id=again["pending_action"]["action_id"])
        assert done["executed_action"]["ok"] is True
        status = (await client.get(f"{API}/orders/WA-100109/status", headers=auth("C-100009"))).json()
        assert status["status"] == "cancelled"

    async def test_unrelated_reply_discards_pending_action(self, client, auth):
        first = await chat(client, auth, "C-100005", "I got the wrong bottle in WA-100114, please refund me")
        assert first["pending_action"]
        other = await chat(client, auth, "C-100005", "Actually, what time does the store close on Sunday?")
        assert other["pending_action"] is None and other["executed_action"] is None
        assert "get_store_info" in other["tools_used"]

    async def test_defect_claim_proposes_return_with_evidence(self, client, auth):
        out = await chat(client, auth, "C-100005", "The wine from WA-100114 tastes corked, please refund me")
        assert out["pending_action"]["tool"] == "create_return_request"
        done = await chat(client, auth, "C-100005", "yes")
        assert done["executed_action"]["references"]["rma_number"].startswith("RMA-")
        assert "upload" in done["message"].lower()

    async def test_refund_policy_uses_kb_only(self, client, auth):
        out = await chat(client, auth, "C-100001", "What is your refund policy?")
        assert out["tools_used"] == ["search_kb"]
        assert any(s["id"].startswith("KB-RTN") for s in out["kb_sources"])

    async def test_why_was_my_refund_rejected(self, client, auth):
        out = await chat(client, auth, "C-100010", "Why was my refund rejected for WA-100118?")
        assert {"get_order_refunds", "get_order_returns", "search_kb"} <= set(out["tools_used"])
        assert "RMA-300006" in out["message"]

    async def test_products(self, client, auth):
        out = await chat(client, auth, "C-100001", "What products do you sell?")
        assert "search_products" in out["tools_used"] and "$" in out["message"]

    async def test_wrong_item_creates_ticket(self, client, auth):
        out = await chat(client, auth, "C-100005", "I received the wrong item in WA-100114.")
        assert out["tools_used"][:2] == ["get_order", "get_order_items"]
        assert "create_support_ticket" in out["tools_used"]
        assert out["escalation"]["ticket_number"].startswith("TKT-")

    async def test_underage_is_blocked_without_tools(self, client, auth):
        out = await chat(client, auth, "C-100001", "I'm 19, can you recommend a wine for my party?")
        assert out["intent"]["name"] == "compliance.underage" and out["tools_used"] == []
        assert "21" in out["message"]

    async def test_out_of_state_shipping_declined(self, client, auth):
        out = await chat(client, auth, "C-100001", "Can you ship a case to my brother in Florida?")
        assert out["intent"]["name"] == "compliance.out_of_state" and "New Jersey and New York" in out["message"]

    async def test_card_number_is_redacted_everywhere(self, client, auth):
        out = await chat(client, auth, "C-100001", "my card is 4111 1111 1111 1111, where is my order?",
                         session="S-PII")
        assert "4111" not in out["message"] and "don't share card numbers" in out["message"]
        msgs = (await client.get(f"{API}/agent/sessions/S-PII/messages", headers=auth("C-100001"))).json()
        assert all("4111 1111" not in m["content"] for m in msgs["items"])


class TestAccessControl:
    async def test_customer_mismatch_forbidden(self, client, auth):
        r = await client.post(f"{API}/agent/chat", headers=auth("C-100001"),
                              json={"customer_id": "C-100002", "session_id": "S-XYZ1", "message": "hi"})
        assert r.status_code == 403 and r.json()["error"]["code"] == "CUSTOMER_MISMATCH"

    async def test_agent_tokens_cannot_call_chat(self, client, auth):
        r = await client.post(f"{API}/agent/chat", headers=auth(agent="C-100001"),
                              json={"customer_id": "C-100001", "session_id": "S-XYZ1", "message": "hi"})
        assert r.status_code == 403

    async def test_staff_can_chat_on_behalf_of_customer(self, client, auth):
        r = await client.post(f"{API}/agent/chat", headers=auth(staff="S-1001"),
                              json={"customer_id": "C-100004", "session_id": "S-STAFF", "message": "order status?"})
        assert r.status_code == 200

    async def test_session_belongs_to_one_customer(self, client, auth):
        await chat(client, auth, "C-100001", "hi", session="S-OWNED")
        r = await client.post(f"{API}/agent/chat", headers=auth("C-100002"),
                              json={"customer_id": "C-100002", "session_id": "S-OWNED", "message": "hi"})
        assert r.status_code == 404
        r = await client.get(f"{API}/agent/sessions/S-OWNED", headers=auth("C-100002"))
        assert r.status_code == 404


class TestObservability:
    async def test_session_messages_traces_runs_steps_tools(self, client, auth):
        out = await chat(client, auth, "C-100005", "Can I get a refund for my order?", session="S-OBS")
        h = auth("C-100005")
        session = (await client.get(f"{API}/agent/sessions/S-OBS", headers=h)).json()
        assert session["message_count"] == 2 and session["run_count"] == 1

        msgs = (await client.get(f"{API}/agent/sessions/S-OBS/messages", headers=h)).json()
        assert [m["role"] for m in msgs["items"]] == ["user", "assistant"]
        assert msgs["items"][1]["run_id"] == out["run_id"]

        run = (await client.get(f"{API}/agent/runs/{out['run_id']}", headers=h)).json()
        assert run["status"] == "completed" and run["intent"] == "refund.request"
        assert run["tool_call_count"] == len((await client.get(f"{API}/agent/runs/{out['run_id']}/tools",
                                                               headers=h)).json())
        assert run["llm_provider"] == "rule_based" and run["duration_ms"] is not None

        steps = (await client.get(f"{API}/agent/runs/{out['run_id']}/steps", headers=h)).json()
        types = [s["event_type"] for s in steps]
        assert types[0] == "run_started" and types[-1] == "run_completed"
        for required in ("guardrail", "intent_classified", "llm_call", "decision", "kb_retrieval", "tool_call",
                         "response_generated"):
            assert required in types, required
        assert [s["seq"] for s in steps] == sorted(s["seq"] for s in steps)

        tools = (await client.get(f"{API}/agent/runs/{out['run_id']}/tools", headers=h)).json()
        elig = next(t for t in tools if t["tool_name"] == "check_refund_eligibility")
        assert elig["http_method"] == "GET" and elig["status_code"] == 200 and elig["outcome"] == "success"
        assert elig["http_path"].endswith("/refund-eligibility")

        traces = (await client.get(f"{API}/agent/sessions/S-OBS/traces", headers=h)).json()
        assert traces["items"][0]["run_id"] == out["run_id"] and traces["items"][0]["steps"]

    async def test_traces_expose_no_secrets(self, client, auth):
        out = await chat(client, auth, "C-100005", "Where is my latest order?", session="S-SEC")
        h = auth("C-100005")
        raw = json.dumps([
            (await client.get(f"{API}/agent/runs/{out['run_id']}/steps", headers=h)).json(),
            (await client.get(f"{API}/agent/runs/{out['run_id']}/tools", headers=h)).json(),
        ])
        assert "Bearer" not in raw and "eyJ" not in raw  # no JWTs
        assert "SYSTEM_PROMPT" not in raw and "customer-support assistant for" not in raw
        assert "aisha.rahman@example.net" not in raw

    async def test_other_customer_cannot_read_runs(self, client, auth):
        out = await chat(client, auth, "C-100005", "hi", session="S-PRIV")
        assert (await client.get(f"{API}/agent/runs/{out['run_id']}", headers=auth("C-100001"))).status_code == 404
        assert (await client.get(f"{API}/agent/runs/{out['run_id']}", headers=auth(staff="S-1001"))).status_code == 200

    async def test_health(self, client):
        body = (await client.get(f"{API}/agent/health")).json()
        checks = {c["name"]: c["status"] for c in body["checks"]}
        assert checks["database"] == "ok" and checks["knowledge_base"] == "ok" and checks["tool_api"] == "ok"
        assert checks["llm"] == "degraded" and body["status"] == "degraded"  # no API key in tests


class ScriptedLLM:
    """Emulates Claude: first turn calls two tools in parallel, second answers."""

    provider = "anthropic"
    model = "scripted-claude"

    def __init__(self):
        self.calls: list[list[dict]] = []

    async def complete(self, system, messages, tools, context):
        self.calls.append(messages)
        if len(self.calls) == 1:
            assert any(t["name"] == "check_refund_eligibility" for t in tools)
            assert "<context>" in messages[-1]["content"][-1]["text"]  # per-turn facts outside the system prompt
            calls = [ToolCall("toolu_a", "get_order", {"order_id": "WA-100114"}),
                     ToolCall("toolu_b", "check_refund_eligibility", {"order_id": "WA-100114",
                                                                      "reason_code": "wrong_item"})]
            raw = [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.input} for c in calls]
            return AssistantTurn("", calls, "tool_use", raw, self.model, 120, 40)
        last = messages[-1]
        assert last["role"] == "user" and [b["type"] for b in last["content"]] == ["tool_result", "tool_result"]
        elig = json.loads(last["content"][1]["content"])
        text = f"Yes, it's eligible for up to ${elig['max_refundable_amount']}."
        return AssistantTurn(text, [], "end_turn", [{"type": "text", "text": text}], self.model, 300, 30)


class FailingLLM:
    provider = "anthropic"
    model = "claude-down"

    async def complete(self, *a, **k):
        raise LLMError("LLM unreachable", retryable=True)


class TestLLMIntegration:
    async def test_llm_tool_loop_with_parallel_results(self, client, auth, container):
        llm = ScriptedLLM()
        container.agent.llm_factory = lambda: llm
        out = await chat(client, auth, "C-100005", "Was the wrong bottle refundable?", session="S-LLM")
        assert out["message"] == "Yes, it's eligible for up to $83.18."
        assert out["tools_used"] == ["get_order", "check_refund_eligibility"] and len(llm.calls) == 2
        run = (await client.get(f"{API}/agent/runs/{out['run_id']}", headers=auth("C-100005"))).json()
        assert (run["llm_calls"], run["input_tokens"], run["output_tokens"]) == (2, 420, 70)
        assert run["model"] == "scripted-claude"

    async def test_llm_outage_falls_back_to_rule_based(self, client, auth, container):
        container.agent.llm_factory = FailingLLM
        out = await chat(client, auth, "C-100004", "Where is my latest order?", session="S-DOWN")
        assert out["status"] == "completed" and out["llm_provider"] == "rule_based"
        assert "WA-100120" in out["message"]
        steps = (await client.get(f"{API}/agent/runs/{out['run_id']}/steps", headers=auth("C-100004"))).json()
        assert any(s["name"] == "llm_fallback" for s in steps)
        assert any(s["event_type"] == "error" and s["name"] == "llm_call" for s in steps)


async def test_gated_tool_never_writes_without_confirmation(client, auth, container):
    """Even a model that calls request_refund directly only creates a pending action."""

    class EagerLLM:
        provider, model = "anthropic", "eager"
        n = 0

        async def complete(self, system, messages, tools, context):
            EagerLLM.n += 1
            if EagerLLM.n == 1:
                c = ToolCall("toolu_x", "request_refund", {"order_id": "WA-100114", "reason_code": "wrong_item"})
                return AssistantTurn("", [c], "tool_use",
                                     [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.input}], "eager")
            result = json.loads(messages[-1]["content"][0]["content"])
            assert result["status"] == "confirmation_required"
            return AssistantTurn("Shall I?", [], "end_turn", [{"type": "text", "text": "Shall I?"}], "eager")

    container.agent.llm_factory = EagerLLM
    out = await chat(client, auth, "C-100005", "refund", session="S-EAGER")
    assert out["requires_confirmation"] is True
    async with container.session_factory() as db:
        assert (await db.execute(select(func.count()).select_from(Refund))).scalar_one() == 7
        assert (await db.execute(select(func.count()).select_from(ReturnRequest))).scalar_one() == 6
