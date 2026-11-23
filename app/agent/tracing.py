"""Structured execution trace for one agent run.

Records decisions and audit metadata, never model chain-of-thought: event
payloads hold intents, tool names, IDs, statuses, durations, counts and
redacted arguments. Flushed to agent_run_events / agent_tool_calls when the
run ends."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from app.core.clock import Clock
from app.core.masking import redact_mapping
from app.models import AgentRunEvent, AgentToolCall

log = structlog.get_logger("agent.trace")


@dataclass
class _Event:
    seq: int
    event_type: str
    name: str | None
    status: str
    summary: str | None
    payload: dict | None
    occurred_at: datetime
    duration_ms: int | None


@dataclass
class _ToolCall:
    seq: int
    tool_call_id: str
    tool_name: str
    category: str
    arguments: dict | None
    http_method: str | None
    http_path: str | None
    status_code: int | None
    outcome: str
    error_code: str | None
    retryable: bool | None
    attempts: int
    response_summary: dict | None
    duration_ms: int
    created_at: datetime


@dataclass
class RunRecorder:
    run_key: str
    clock: Clock
    events: list[_Event] = field(default_factory=list)
    tool_calls: list[_ToolCall] = field(default_factory=list)
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    kb_retrievals: int = 0
    tools_used: list[str] = field(default_factory=list)
    kb_sources: list[dict] = field(default_factory=list)
    model: str | None = None
    _seq: int = 0
    _t0: float = field(default_factory=time.perf_counter)

    def _next(self) -> int:
        self._seq += 1
        return self._seq

    def event(self, event_type: str, name: str | None = None, *, status: str = "ok", summary: str | None = None,
              payload: dict[str, Any] | None = None, duration_ms: int | None = None) -> None:
        ev = _Event(self._next(), event_type, name, status, summary,
                    redact_mapping(payload) if payload else None, self.clock.now(), duration_ms)
        self.events.append(ev)
        log.info("agent_event", run_id=self.run_key, seq=ev.seq, event_type=event_type, name=name, status=status)

    def tool_call(self, *, tool_call_id: str, tool_name: str, category: str, arguments: dict | None,
                  http_method: str | None, http_path: str | None, status_code: int | None, outcome: str,
                  error_code: str | None, retryable: bool | None, attempts: int, response_summary: dict | None,
                  duration_ms: int) -> None:
        seq = self._next()
        self.tool_calls.append(_ToolCall(
            seq, tool_call_id, tool_name, category, redact_mapping(arguments) if arguments else None, http_method,
            http_path, status_code, outcome, error_code, retryable, attempts,
            redact_mapping(response_summary) if response_summary else None, duration_ms, self.clock.now(),
        ))
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)
        self.events.append(_Event(seq, "tool_call", tool_name, "ok" if outcome in ("success", "gated") else "error",
                                  f"{http_method or 'KB'} {http_path or ''} -> {status_code or outcome}".strip(),
                                  {"outcome": outcome, "error_code": error_code, "attempts": attempts},
                                  self.clock.now(), duration_ms))

    def llm_usage(self, model: str, input_tokens: int, output_tokens: int) -> None:
        self.llm_calls += 1
        self.model = model
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    @property
    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._t0) * 1000)

    def to_rows(self, run_db_id: int) -> tuple[list[AgentRunEvent], list[AgentToolCall]]:
        events = [AgentRunEvent(run_id=run_db_id, seq=e.seq, event_type=e.event_type, name=e.name, status=e.status,
                                summary=e.summary, payload=e.payload, occurred_at=e.occurred_at,
                                duration_ms=e.duration_ms) for e in self.events]
        calls = [AgentToolCall(run_id=run_db_id, seq=c.seq, tool_call_id=c.tool_call_id, tool_name=c.tool_name,
                               category=c.category, arguments=c.arguments, http_method=c.http_method,
                               http_path=c.http_path, status_code=c.status_code, outcome=c.outcome,
                               error_code=c.error_code, retryable=c.retryable, attempts=c.attempts,
                               response_summary=c.response_summary, duration_ms=c.duration_ms,
                               created_at=c.created_at) for c in self.tool_calls]
        return events, calls
