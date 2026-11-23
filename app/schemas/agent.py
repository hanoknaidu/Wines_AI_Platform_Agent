from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas.common import ApiModel, UtcDateTime


class ChatRequest(ApiModel):
    customer_id: str = Field(..., pattern=r"^C-\d{6}$", examples=["C-100005"])
    session_id: str = Field(..., pattern=r"^[A-Za-z0-9_-]{4,100}$", examples=["SESSION1001"])
    message: str = Field(..., min_length=1, max_length=4000, examples=["Where is my latest order?"])
    confirm_action_id: str | None = Field(
        None, pattern=r"^act_[0-9a-f]{32}$",
        description="Set when the customer clicks 'Confirm' on a pending action returned by a previous turn",
    )
    channel: Literal["web_chat", "mobile_app", "sms"] = "web_chat"


class IntentOut(ApiModel):
    name: str
    confidence: float


class KbSource(ApiModel):
    id: str
    title: str
    section: str


class PendingActionOut(ApiModel):
    action_id: str
    tool: str
    summary: str
    expires_at: str


class EscalationOut(ApiModel):
    ticket_number: str | None
    priority: str | None
    reason_code: str | None


class ChatResponse(ApiModel):
    session_id: str
    run_id: str
    status: Literal["completed", "failed"]
    message: str
    intent: IntentOut | None
    tools_used: list[str]
    kb_sources: list[KbSource]
    pending_action: PendingActionOut | None
    requires_confirmation: bool
    executed_action: dict[str, Any] | None
    escalation: EscalationOut | None
    llm_provider: str
    duration_ms: int


class SessionOut(ApiModel):
    session_id: str
    customer_id: str
    channel: str
    status: str
    message_count: int
    run_count: int
    pending_action: PendingActionOut | None
    created_at: UtcDateTime
    last_activity_at: UtcDateTime


class MessageOut(ApiModel):
    role: str
    content: str
    run_id: str | None
    created_at: UtcDateTime


class RunEventOut(ApiModel):
    seq: int
    event_type: str
    name: str | None
    status: str
    summary: str | None
    payload: dict | None
    occurred_at: UtcDateTime
    duration_ms: int | None


class ToolCallOut(ApiModel):
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
    created_at: UtcDateTime


class RunOut(ApiModel):
    run_id: str
    session_id: str
    customer_id: str
    status: str
    question: str
    final_response: str | None
    intent: str | None
    intent_confidence: float | None
    llm_provider: str
    model: str | None
    llm_calls: int
    tool_call_count: int
    kb_retrieval_count: int
    input_tokens: int
    output_tokens: int
    request_id: str | None
    error_code: str | None
    error_message: str | None
    started_at: UtcDateTime
    completed_at: UtcDateTime | None
    duration_ms: int | None


class RunTrace(RunOut):
    steps: list[RunEventOut]
    tool_calls: list[ToolCallOut]


class HealthCheck(ApiModel):
    name: str
    status: Literal["ok", "degraded", "down"]
    detail: dict[str, Any] = Field(default_factory=dict)


class HealthOut(ApiModel):
    status: Literal["ok", "degraded", "down"]
    checks: list[HealthCheck]
    checked_at: UtcDateTime
