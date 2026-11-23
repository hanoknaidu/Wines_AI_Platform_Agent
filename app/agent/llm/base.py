"""Provider-neutral LLM interface used by the LangGraph nodes. Messages use the
Anthropic Messages format (role + content blocks), which the rule-based
planner also reads, so both implementations drive the same graph."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class AssistantTurn:
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str  # end_turn | tool_use | max_tokens | refusal | pause_turn
    raw_content: list[Any]  # provider-native content blocks, appended to history unchanged
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    tool_selection_note: str | None = None  # structured, non-CoT description of the decision


@dataclass
class PlannerContext:
    """Deterministic facts the graph already knows (never the model's reasoning)."""

    customer_number: str
    intent: str
    confidence: float
    entities: dict = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    today: str = ""
    executed_action: dict | None = None
    action_declined: bool = False
    pending_action: dict | None = None


class LLMError(Exception):
    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMClient(Protocol):
    provider: str
    model: str

    async def complete(
        self, system: str, messages: list[dict], tools: list[dict], context: PlannerContext
    ) -> AssistantTurn: ...
