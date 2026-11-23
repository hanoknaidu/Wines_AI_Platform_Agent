"""Executes tool calls chosen by the LLM (or the rule-based planner).

Pipeline per call: lookup -> Pydantic validation -> confirmation gate ->
KB search or Tool API HTTP call -> normalized result -> trace record.
Tool results returned to the LLM follow the KB contract: success payload, or
{"error_code", "message", "retryable"}."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from pydantic import ValidationError

from app.agent.kb.knowledge_base import KnowledgeBase
from app.agent.tools.client import ToolApiClient, ToolApiUnavailable
from app.agent.tools.registry import TOOLS_BY_NAME, ToolSpec
from app.agent.tracing import RunRecorder
from app.core.clock import iso

MAX_RESULT_CHARS = 14_000
PENDING_ACTION_TTL = timedelta(minutes=30)


@dataclass
class ToolOutcome:
    name: str
    ok: bool
    content: dict | list
    gated: bool = False

    def as_text(self) -> str:
        text = json.dumps(self.content, default=str, separators=(",", ":"))
        if len(text) > MAX_RESULT_CHARS:
            text = text[:MAX_RESULT_CHARS] + '…"(truncated)"'
        return text


@dataclass
class ToolRuntime:
    """Per-run tool context. Holds the delegated token; never shown to the LLM."""

    customer_number: str
    session_key: str
    run_key: str
    token: str
    client: ToolApiClient
    kb: KnowledgeBase
    recorder: RunRecorder
    intent: str | None = None
    kb_top_k: int = 4
    pending_action: dict | None = None
    executed_actions: list[dict] = field(default_factory=list)


class ToolExecutor:
    def __init__(self, runtime: ToolRuntime) -> None:
        self.rt = runtime

    @staticmethod
    def _error(name: str, code: str, message: str, retryable: bool = False) -> ToolOutcome:
        return ToolOutcome(name, False, {"error_code": code, "message": message, "retryable": retryable})

    async def execute(self, name: str, arguments: dict[str, Any], tool_call_id: str) -> ToolOutcome:
        started = time.perf_counter()
        spec = TOOLS_BY_NAME.get(name)
        if spec is None:
            outcome = self._error(name, "UNKNOWN_TOOL", f"No tool named {name!r}")
            self._record(tool_call_id, name, "read", arguments, None, None, None, outcome, 1, started)
            return outcome
        try:
            args = spec.input_model.model_validate(arguments or {})
        except ValidationError as exc:
            issues = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()[:5])
            outcome = self._error(name, "INVALID_TOOL_INPUT", issues)
            self.rt.recorder.event("validation", name, status="error", summary=issues)
            self._record(tool_call_id, name, spec.category, arguments, None, None, None, outcome, 1, started)
            return outcome

        if spec.requires_confirmation:
            return self._gate(spec, args, tool_call_id, started)
        if spec.category == "kb":
            return self._search_kb(spec, args, tool_call_id, started)
        return await self._http(spec, args, tool_call_id, started)

    async def execute_confirmed(self, action: dict) -> ToolOutcome:
        """Run a previously gated action after explicit customer confirmation.
        Deterministic: no LLM involved; Idempotency-Key = action id."""
        started = time.perf_counter()
        spec = TOOLS_BY_NAME[action["tool"]]
        args = spec.input_model.model_validate(action["arguments"])
        outcome = await self._http(spec, args, f"confirmed:{action['action_id']}", started,
                                   idempotency_key=action["action_id"])
        self.rt.executed_actions.append({"action_id": action["action_id"], "tool": spec.name, "ok": outcome.ok})
        return outcome

    # ------------------------------------------------------------------ internals
    def _gate(self, spec: ToolSpec, args, tool_call_id: str, started: float) -> ToolOutcome:
        now = self.rt.recorder.clock.now()
        summary = spec.confirm_summary(args) if spec.confirm_summary else spec.name
        action = {
            "action_id": f"act_{uuid.uuid4().hex}",
            "tool": spec.name,
            "arguments": args.model_dump(mode="json", exclude_none=True),
            "summary": summary,
            "created_at": iso(now),
            "expires_at": iso(now + PENDING_ACTION_TTL),
            "proposed_in_run": self.rt.run_key,
        }
        self.rt.pending_action = action
        self.rt.recorder.event("action_gated", spec.name, summary=f"Awaiting explicit confirmation: {summary}",
                               payload={"action_id": action["action_id"], "tool": spec.name})
        outcome = ToolOutcome(spec.name, True, {
            "status": "confirmation_required",
            "action_id": action["action_id"],
            "summary": summary,
            "instructions": "Nothing has been done yet. Tell the customer exactly what will happen (amount and "
                            "method where known) and ask them to reply 'yes' to confirm. Do not say it is done.",
        }, gated=True)
        self._record(tool_call_id, spec.name, spec.category, action["arguments"], spec.method, None, None,
                     outcome, 1, started, outcome_label="gated")
        return outcome

    def _search_kb(self, spec: ToolSpec, args, tool_call_id: str, started: float) -> ToolOutcome:
        hits = self.rt.kb.search(args.query, top_k=self.rt.kb_top_k, category=args.category, intent=self.rt.intent)
        results = [h.as_dict() for h in hits]
        self.rt.recorder.kb_retrievals += 1
        for h in hits:
            src = {"id": h.doc_id, "title": h.title, "section": h.section}
            if src not in self.rt.recorder.kb_sources:
                self.rt.recorder.kb_sources.append(src)
        self.rt.recorder.event("kb_retrieval", "search_kb", summary=f"{len(hits)} chunks",
                               payload={"query": args.query, "category": args.category,
                                        "hits": [{"id": h.doc_id, "section": h.section, "score": round(h.score, 2)}
                                                 for h in hits]},
                               duration_ms=int((time.perf_counter() - started) * 1000))
        content = {"results": results} if results else {"results": [], "note": "No matching KB content. Do not "
                                                         "improvise policy; offer a follow-up ticket (kb_gap)."}
        outcome = ToolOutcome(spec.name, True, content)
        self._record(tool_call_id, spec.name, "kb", args.model_dump(exclude_none=True), None, None, None, outcome,
                     1, started, response_summary={"hits": [h.doc_id for h in hits]})
        return outcome

    async def _http(self, spec: ToolSpec, args, tool_call_id: str, started: float,
                    idempotency_key: str | None = None) -> ToolOutcome:
        path = spec.path(args, self.rt.customer_number)
        params = spec.params(args) if spec.params else None
        body = spec.body(args) if spec.body else ({} if spec.method == "POST" else None)
        if spec.method == "POST" and idempotency_key is None:
            idempotency_key = f"{self.rt.run_key}:{tool_call_id}"[:128]
        try:
            res = await self.rt.client.request(self.rt.token, spec.method, path, params=params, json=body,
                                               idempotency_key=idempotency_key)
        except ToolApiUnavailable as exc:
            outcome = self._error(spec.name, "TOOL_API_UNAVAILABLE",
                                  "The service is temporarily unavailable. Don't guess; offer to retry or open a "
                                  "ticket.", retryable=True)
            self._record(tool_call_id, spec.name, spec.category, args.model_dump(exclude_none=True), spec.method,
                         path, None, outcome, exc.attempts, started)
            return outcome
        if res.ok:
            outcome = ToolOutcome(spec.name, True, res.body)
        else:
            err = (res.body or {}).get("error", {}) if isinstance(res.body, dict) else {}
            outcome = ToolOutcome(spec.name, False, {
                "error_code": err.get("code", f"HTTP_{res.status_code}"),
                "message": err.get("message", "Request failed"),
                "retryable": bool(err.get("retryable", res.status_code >= 500)),
                **({"details": err["details"]} if err.get("details") else {}),
            })
        self._record(tool_call_id, spec.name, spec.category, args.model_dump(exclude_none=True), spec.method, path,
                     res.status_code, outcome, res.attempts, started, response_summary=_summarize(res.body))
        return outcome

    def _record(self, tool_call_id, name, category, arguments, method, path, status_code, outcome: ToolOutcome,
                attempts, started, *, outcome_label: str | None = None, response_summary: dict | None = None):
        content = outcome.content if isinstance(outcome.content, dict) else {}
        self.rt.recorder.tool_call(
            tool_call_id=tool_call_id, tool_name=name, category=category, arguments=arguments,
            http_method=method, http_path=path, status_code=status_code,
            outcome=outcome_label or ("success" if outcome.ok else "error"),
            error_code=None if outcome.ok else content.get("error_code"),
            retryable=None if outcome.ok else content.get("retryable"), attempts=attempts,
            response_summary=response_summary, duration_ms=int((time.perf_counter() - started) * 1000),
        )


def _summarize(body: Any) -> dict:
    """Small, structural summary of a tool response for the trace store."""
    if isinstance(body, list):
        return {"type": "list", "count": len(body)}
    if not isinstance(body, dict):
        return {"type": type(body).__name__}
    keys = ("order_id", "status", "payment_status", "decision", "eligible", "total", "refund_id", "rma_number",
            "ticket_number", "stock_status", "requires_human_approval", "cancelled")
    summary = {k: body[k] for k in keys if k in body and not isinstance(body[k], (dict, list))}
    if "items" in body and isinstance(body["items"], list):
        summary["item_count"] = len(body["items"])
    if "error" in body:
        summary["error_code"] = body["error"].get("code")
    summary["keys"] = sorted(body)[:15]
    return summary
