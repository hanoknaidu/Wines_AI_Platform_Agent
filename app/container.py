"""Composition root: builds every long-lived dependency once per process and
exposes them to routes through FastAPI dependencies (app.state.container)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.agent.kb.knowledge_base import KnowledgeBase
from app.agent.llm.base import LLMClient
from app.agent.llm.rule_based import RuleBasedPlanner
from app.agent.service import AgentService
from app.agent.tools.client import ToolApiClient
from app.core.clock import Clock
from app.core.config import Settings
from app.core.rate_limit import InMemoryRateLimiter, RateLimiter, RedisRateLimiter
from app.core.resilience import CircuitBreaker
from app.core.security import TokenService
from app.db.session import create_engine, create_session_factory
from app.services.payment_gateway import PaymentGateway, SimulatedPaymentGateway


@dataclass
class Container:
    settings: Settings
    clock: Clock
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    tokens: TokenService
    rate_limiter: RateLimiter
    gateway: PaymentGateway
    kb: KnowledgeBase
    tool_http: httpx.AsyncClient
    tool_client: ToolApiClient
    agent: AgentService

    @classmethod
    def build(cls, settings: Settings, asgi_app=None, *, engine: AsyncEngine | None = None,
              llm_factory: Callable[[], LLMClient] | None = None) -> Container:
        clock = Clock(settings.reference_now)
        engine = engine or create_engine(settings)
        session_factory = create_session_factory(engine)
        tokens = TokenService(settings, clock)
        limiter: RateLimiter = (RedisRateLimiter(settings.redis_url) if settings.rate_limit_backend == "redis"
                                else InMemoryRateLimiter())
        if settings.tool_api_base_url:
            transport, base_url = None, settings.tool_api_base_url.rstrip("/") + settings.api_prefix
        else:
            # In-process: full HTTP stack (auth, validation, rate limit, audit), no network hop.
            transport, base_url = httpx.ASGITransport(app=asgi_app), "http://tool-api.internal" + settings.api_prefix
        tool_http = httpx.AsyncClient(
            base_url=base_url, transport=transport, timeout=httpx.Timeout(settings.tool_api_timeout_s),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        breaker = CircuitBreaker("tool_api", settings.circuit_breaker_failure_threshold,
                                 settings.circuit_breaker_reset_s)
        tool_client = ToolApiClient(tool_http, breaker, max_retries=settings.tool_api_max_retries)
        kb = KnowledgeBase.load(settings.kb_path)
        agent = AgentService(settings=settings, clock=clock, session_factory=session_factory, tokens=tokens, kb=kb,
                             tool_client=tool_client, llm_factory=llm_factory or default_llm_factory(settings))
        return cls(settings, clock, engine, session_factory, tokens, limiter, SimulatedPaymentGateway(), kb,
                   tool_http, tool_client, agent)

    async def close(self) -> None:
        await self.tool_http.aclose()
        await self.engine.dispose()


def default_llm_factory(settings: Settings) -> Callable[[], LLMClient]:
    if settings.resolved_llm_provider == "anthropic":
        from app.agent.llm.anthropic_llm import AnthropicLLM

        llm = AnthropicLLM(settings)  # one client (connection pool) per process
        return lambda: llm
    return RuleBasedPlanner
