"""LangGraph customer-support workflow.

    input_guard -> classify -> route
        route = compliance            (minors, crisis, out-of-state: no tools that sell)
              | confirmation          (a gated action awaits a yes/no)
              | agent
    confirmation -> agent
    agent <-> tools                   (LLM chooses tools; parallel execution)
    agent -> respond                  (end_turn / iteration cap / refusal)

Runtime dependencies (LLM client, tool executor, recorder) travel in
config["configurable"]["deps"], never in graph state, so state stays plain
data and no credentials can leak into it."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.guardrails import check_input, sanitize_output
from app.agent.intent import classify, is_affirmative, is_negative
from app.agent.llm.base import LLMClient, LLMError, PlannerContext
from app.agent.llm.rule_based import RuleBasedPlanner
from app.agent.prompts import SYSTEM_PROMPT, context_block
from app.agent.tools.executor import ToolExecutor
from app.agent.tools.registry import anthropic_tool_definitions
from app.agent.tracing import RunRecorder
from app.core.clock import Clock, to_utc
from app.core.config import Settings


class AgentState(TypedDict, total=False):
    customer_number: str
    raw_message: str
    message: str
    history: list[dict]
    messages: list[dict]
    confirm_action_id: str | None
    pending_action: dict | None
    intent: str
    confidence: float
    entities: dict
    secondary_intents: list[str]
    flags: list[str]
    iterations: int
    executed_action: dict | None
    action_declined: bool
    final_text: str
    stop_reason: str
    escalation: dict | None


@dataclass
class AgentDeps:
    llm: LLMClient
    executor: ToolExecutor
    recorder: RunRecorder
    settings: Settings
    clock: Clock


def _deps(config) -> AgentDeps:
    return config["configurable"]["deps"]


def _context(state: AgentState, deps: AgentDeps) -> PlannerContext:
    return PlannerContext(
        customer_number=state["customer_number"], intent=state.get("intent", "general.question"),
        confidence=state.get("confidence", 0.0), entities=state.get("entities", {}), flags=state.get("flags", []),
        today=deps.clock.now().strftime("%A, %B %d, %Y"), executed_action=state.get("executed_action"),
        action_declined=state.get("action_declined", False), pending_action=state.get("pending_action"),
    )


# ---------------------------------------------------------------------------- nodes
async def input_guard(state: AgentState, config) -> dict:
    deps = _deps(config)
    check = check_input(state["raw_message"])
    if check.flags:
        deps.recorder.event("guardrail", "input_check", status="flagged", summary=", ".join(check.flags),
                            payload={"flags": check.flags})
    else:
        deps.recorder.event("guardrail", "input_check", summary="passed")
    return {"message": check.text, "flags": check.flags}


async def classify_node(state: AgentState, config) -> dict:
    deps = _deps(config)
    intent = classify(state["message"])
    if "out_of_state_request" in state.get("flags", []):
        intent.secondary.insert(0, intent.name)
        intent.name, intent.confidence = "compliance.out_of_state", 0.9
    deps.recorder.event("intent_classified", intent.name, summary=f"confidence {intent.confidence:.2f}",
                        payload={"intent": intent.name, "confidence": intent.confidence,
                                 "secondary": intent.secondary, "entities": intent.entities})
    deps.executor.rt.intent = intent.name
    return {"intent": intent.name, "confidence": intent.confidence, "entities": intent.entities,
            "secondary_intents": intent.secondary}


def route_after_classify(state: AgentState) -> str:
    if state["intent"].startswith("compliance."):
        return "compliance"
    if state.get("pending_action"):
        return "confirmation"
    return "agent"


async def compliance_node(state: AgentState, config) -> dict:
    deps = _deps(config)
    intent = state["intent"]
    escalation = None
    if intent == "compliance.crisis":
        outcome = await deps.executor.execute("create_support_ticket", {
            "category": "compliance", "priority": "P1", "reason_code": "safety_crisis",
            "subject": "Customer may be in crisis",
            "summary": f"Customer {state['customer_number']} expressed possible self-harm or crisis in chat. "
                       "Safety resources shared. Immediate human follow-up requested.",
            "customer_sentiment": "frustrated",
        }, "compliance:crisis")
        ticket = outcome.content.get("ticket_number") if outcome.ok and isinstance(outcome.content, dict) else None
        escalation = {"ticket_number": ticket, "priority": "P1", "reason_code": "safety_crisis"}
        text = ("I'm really sorry you're going through this. You don't have to face it alone. If you're in the US, "
                "you can call or text 988 (Suicide & Crisis Lifeline) any time, and if you're in immediate danger "
                "please call 911. I've also asked a member of our team to reach out to you"
                + (f" (reference {ticket})." if ticket else "."))
    elif intent == "compliance.underage":
        text = ("Thanks for being upfront. We can only sell to, and help with purchases for, customers who are 21 "
                "or older, and that includes gifts and non-alcoholic wine. I'm happy to answer general questions "
                "about our store.")
    else:  # out of state
        text = ("We can only deliver or ship to addresses in New Jersey and New York because of state alcohol "
                "laws. If you have an NJ or NY address (or would like to pick up in Hoboken or Chelsea), I'd be "
                "glad to help with that.")
    deps.recorder.event("decision", "compliance_override", summary=intent, payload={"intent": intent})
    return {"final_text": text, "stop_reason": "compliance", "escalation": escalation}


async def confirmation_node(state: AgentState, config) -> dict:
    """Execute a gated action only on explicit confirmation; otherwise discard it."""
    deps = _deps(config)
    pending = state["pending_action"]
    text = state["message"]
    now = deps.clock.now()
    expired = to_utc(_parse(pending.get("expires_at"))) < now if pending.get("expires_at") else False
    explicit = state.get("confirm_action_id") == pending["action_id"]
    affirmative = is_affirmative(text) and len(text) <= 120
    if expired:
        decision = "expired"
    elif explicit or affirmative:
        decision = "confirmed"
    elif is_negative(text):
        decision = "declined"
    else:
        decision = "superseded"
    deps.recorder.event("confirmation_check", pending["tool"], summary=decision,
                        payload={"action_id": pending["action_id"], "decision": decision,
                                 "via": "confirm_action_id" if explicit else "message"})
    update: dict[str, Any] = {"pending_action": None}
    if decision == "confirmed":
        outcome = await deps.executor.execute_confirmed(pending)
        deps.recorder.event("action_executed", pending["tool"], status="ok" if outcome.ok else "error",
                            summary=pending["summary"], payload={"action_id": pending["action_id"], "ok": outcome.ok})
        executed = {"action_id": pending["action_id"], "tool": pending["tool"], "summary": pending["summary"],
                    "ok": outcome.ok, "result": outcome.content}
        update["executed_action"] = executed
        if executed["ok"] and pending["tool"] in ("request_refund",) and outcome.content.get("ticket_number"):
            update["escalation"] = {"ticket_number": outcome.content["ticket_number"], "priority": "P2",
                                    "reason_code": "refund_over_limit"}
        update["intent"], update["confidence"] = "action.confirmed", 1.0
    elif decision == "declined":
        update["action_declined"] = True
        update["intent"], update["confidence"] = "action.declined", 1.0
    return update


async def agent_node(state: AgentState, config) -> dict:
    deps = _deps(config)
    iterations = state.get("iterations", 0)
    messages = list(state["messages"])
    if iterations >= deps.settings.agent_max_iterations:
        deps.recorder.event("decision", "iteration_limit", status="error",
                            summary=f"stopped after {iterations} LLM steps")
        return {"final_text": "I wasn't able to finish that just now. Would you like me to open a ticket so our "
                              "team can follow up?", "stop_reason": "iteration_limit"}
    ctx = _context(state, deps)
    llm = deps.llm
    try:
        turn = await llm.complete(SYSTEM_PROMPT, messages, anthropic_tool_definitions(), ctx)
    except LLMError as exc:
        deps.recorder.event("error", "llm_call", status="error", summary=str(exc),
                            payload={"retryable": exc.retryable, "provider": llm.provider})
        if isinstance(llm, RuleBasedPlanner):
            raise
        # Degraded mode: deterministic planner keeps the customer served.
        deps.llm = RuleBasedPlanner()
        deps.recorder.event("decision", "llm_fallback", summary="switched to rule-based planner")
        turn = await deps.llm.complete(SYSTEM_PROMPT, messages, anthropic_tool_definitions(), ctx)
    deps.recorder.llm_usage(turn.model, turn.input_tokens, turn.output_tokens)
    deps.recorder.event("llm_call", deps.llm.provider, summary=f"stop_reason={turn.stop_reason}",
                        payload={"model": turn.model, "stop_reason": turn.stop_reason,
                                 "tools_selected": [c.name for c in turn.tool_calls],
                                 "input_tokens": turn.input_tokens, "output_tokens": turn.output_tokens})
    if turn.tool_calls:
        deps.recorder.event("decision", "tool_selection", summary=turn.tool_selection_note,
                            payload={"tools": [{"name": c.name, "args": c.input} for c in turn.tool_calls]})
    messages.append({"role": "assistant", "content": turn.raw_content})
    update: dict[str, Any] = {"messages": messages, "iterations": iterations + 1, "stop_reason": turn.stop_reason}
    if turn.stop_reason == "refusal":
        update["final_text"] = ("I'm not able to help with that request. I'm happy to help with orders, deliveries, "
                                "returns or wine recommendations.")
    elif turn.stop_reason == "pause_turn":
        update["final_text"] = None
    elif not turn.tool_calls:
        update["final_text"] = turn.text or ("I'm sorry, I couldn't put an answer together. Would you like me to "
                                             "open a ticket?")
    return update


def route_after_agent(state: AgentState) -> str:
    if state.get("final_text"):
        return "respond"
    if state.get("stop_reason") == "pause_turn":
        return "agent"
    last = state["messages"][-1]["content"]
    has_tools = any((b.get("type") if isinstance(b, dict) else getattr(b, "type", None)) == "tool_use" for b in last)
    return "tools" if has_tools else "respond"


async def tools_node(state: AgentState, config) -> dict:
    deps = _deps(config)
    messages = list(state["messages"])
    blocks = [b for b in messages[-1]["content"]
              if (b.get("type") if isinstance(b, dict) else getattr(b, "type", None)) == "tool_use"]

    def field(b, key):
        return b.get(key) if isinstance(b, dict) else getattr(b, key)

    outcomes = await asyncio.gather(*[
        deps.executor.execute(field(b, "name"), dict(field(b, "input") or {}), field(b, "id")) for b in blocks
    ])
    results = [{"type": "tool_result", "tool_use_id": field(b, "id"), "content": o.as_text(),
                **({"is_error": True} if not o.ok else {})} for b, o in zip(blocks, outcomes, strict=True)]
    messages.append({"role": "user", "content": results})  # all results in ONE user message
    update: dict[str, Any] = {"messages": messages}
    for o in outcomes:
        if o.ok and o.name == "create_support_ticket" and isinstance(o.content, dict):
            update["escalation"] = {"ticket_number": o.content.get("ticket_number"),
                                    "priority": o.content.get("priority"), "reason_code": o.content.get("reason_code")}
    return update


async def respond_node(state: AgentState, config) -> dict:
    deps = _deps(config)
    text = sanitize_output(state.get("final_text") or "")
    if "payment_data_shared" in state.get("flags", []):
        text = ("For your security, please don't share card numbers in chat; I've removed it from our "
                "conversation. ") + text
    deps.recorder.event("response_generated", "final_answer", summary=f"{len(text)} chars",
                        payload={"length": len(text), "stop_reason": state.get("stop_reason"),
                                 "pending_action": bool(deps.executor.rt.pending_action)})
    return {"final_text": text}


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------- build
def build_messages(history: list[dict], message: str, context: str) -> list[dict]:
    """History (alternating user/assistant text) + the current turn with a
    <context> block. Consecutive same-role turns are merged."""
    msgs: list[dict] = []
    for h in history:
        if msgs and msgs[-1]["role"] == h["role"]:
            msgs[-1]["content"][0]["text"] += "\n\n" + h["content"]
        else:
            msgs.append({"role": h["role"], "content": [{"type": "text", "text": h["content"]}]})
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    current = [{"type": "text", "text": message}, {"type": "text", "text": context}]
    if msgs and msgs[-1]["role"] == "user":
        msgs[-1]["content"].extend(current)
    else:
        msgs.append({"role": "user", "content": current})
    return msgs


async def prepare_node(state: AgentState, config) -> dict:
    """Build the model-facing conversation once intent/flags are known."""
    deps = _deps(config)
    note = None
    executed = state.get("executed_action")
    if executed:
        note = ("confirmed_action_result: the customer confirmed and the action was executed by the system. "
                f"tool={executed['tool']} ok={executed['ok']} result="
                + json.dumps(executed["result"], default=str)[:4000]
                + "\nTell the customer the outcome with reference numbers. Do not call the action tool again.")
    elif state.get("action_declined"):
        note = "The customer declined the pending action; it was discarded. Acknowledge and offer further help."
    ctx = context_block(customer_number=state["customer_number"], today=deps.clock.now().strftime("%Y-%m-%d"),
                        intent=state["intent"], confidence=state["confidence"], entities=state.get("entities", {}),
                        flags=state.get("flags", []), pending_action=None, note=note)
    return {"messages": build_messages(state.get("history", []), state["message"], ctx), "iterations": 0}


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("input_guard", input_guard)
    g.add_node("classify", classify_node)
    g.add_node("compliance", compliance_node)
    g.add_node("confirmation", confirmation_node)
    g.add_node("prepare", prepare_node)
    g.add_node("agent", agent_node)
    g.add_node("tools", tools_node)
    g.add_node("respond", respond_node)
    g.add_edge(START, "input_guard")
    g.add_edge("input_guard", "classify")
    g.add_conditional_edges("classify", route_after_classify,
                            {"compliance": "compliance", "confirmation": "confirmation", "agent": "prepare"})
    g.add_edge("confirmation", "prepare")
    g.add_edge("prepare", "agent")
    g.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "respond": "respond", "agent": "agent"})
    g.add_edge("tools", "agent")
    g.add_edge("compliance", "respond")
    g.add_edge("respond", END)
    return g.compile()


GRAPH = build_graph()
