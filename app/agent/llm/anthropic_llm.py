"""Claude adapter (official `anthropic` SDK, async).

* model: claude-opus-5-5 by default (ANTHROPIC_MODEL), adaptive thinking is
  always on for this model; depth is set with output_config.effort.
* server-side refusal fallbacks enabled by default (`fallbacks: "default"`).
* the stable system prompt + tool list are cached (cache_control).
* response.content is returned unchanged so the tool loop appends it as-is
  (thinking blocks must be passed back untouched within a turn).
* thinking text is never surfaced: only `text` blocks reach the customer.
"""
from __future__ import annotations

import anthropic

from app.agent.llm.base import AssistantTurn, LLMError, PlannerContext, ToolCall
from app.core.config import Settings

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicLLM:
    provider = "anthropic"

    def __init__(self, settings: Settings) -> None:
        key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
        self._client = anthropic.AsyncAnthropic(
            api_key=key, timeout=settings.anthropic_timeout_s, max_retries=settings.anthropic_max_retries
        )
        self.model = settings.anthropic_model
        self._effort = settings.anthropic_effort
        self._max_tokens = settings.anthropic_max_tokens
        self._fallbacks = settings.anthropic_fallbacks_enabled

    async def complete(
        self, system: str, messages: list[dict], tools: list[dict], context: PlannerContext
    ) -> AssistantTurn:
        request = {
            "model": self.model,
            "max_tokens": self._max_tokens,
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "tools": tools,
            "messages": messages,
            "output_config": {"effort": self._effort},
        }
        try:
            if self._fallbacks:
                response = await self._client.beta.messages.create(
                    **request, betas=[FALLBACK_BETA], fallbacks="default"
                )
            else:
                response = await self._client.messages.create(**request)
        except anthropic.RateLimitError as exc:
            raise LLMError("LLM rate limited", retryable=True) from exc
        except anthropic.BadRequestError as exc:
            raise LLMError(f"LLM rejected the request: {exc.message}", retryable=False) from exc
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise LLMError("LLM credentials rejected", retryable=False) from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"LLM error {exc.status_code}", retryable=exc.status_code >= 500) from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError("LLM unreachable", retryable=True) from exc

        text = "".join(b.text for b in response.content if b.type == "text")
        calls = [ToolCall(b.id, b.name, dict(b.input or {})) for b in response.content if b.type == "tool_use"]
        usage = response.usage
        return AssistantTurn(
            text=text,
            tool_calls=calls,
            stop_reason=response.stop_reason or "end_turn",
            raw_content=list(response.content),
            model=response.model,
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            tool_selection_note=(f"selected {', '.join(c.name for c in calls)}" if calls else None),
        )
