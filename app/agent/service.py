"""Agent orchestration service (Category 2 business logic).

chat(): validate caller -> load/create session -> open run -> mint delegated
agent token -> run the LangGraph workflow -> persist messages, trace, pending
action -> respond. Owns only agent_* tables."""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.graph import GRAPH, AgentDeps
from app.agent.kb.knowledge_base import KnowledgeBase
from app.agent.llm.base import LLMClient
from app.agent.tools.client import ToolApiClient
from app.agent.tools.executor import ToolExecutor, ToolRuntime
from app.agent.tracing import RunRecorder
from app.core.clock import Clock
from app.core.config import Settings
from app.core.errors import BusinessRuleError, NotFoundError, PermissionDeniedError
from app.core.masking import redact_text
from app.core.request_context import get_request_id
from app.core.security import Principal, TokenService
from app.models import AgentMessage, AgentRun, AgentSession
from app.repositories.agent_repo import AgentRepository
from app.schemas.agent import (
    ChatRequest,
    ChatResponse,
    EscalationOut,
    HealthCheck,
    HealthOut,
    IntentOut,
    KbSource,
    MessageOut,
    PendingActionOut,
    RunEventOut,
    RunOut,
    RunTrace,
    SessionOut,
    ToolCallOut,
)
from app.schemas.common import Page, PageParams

log = structlog.get_logger(__name__)
RUN_TIMEOUT_S = 150


@dataclass
class AgentService:
    settings: Settings
    clock: Clock
    session_factory: async_sessionmaker[AsyncSession]
    tokens: TokenService
    kb: KnowledgeBase
    tool_client: ToolApiClient
    llm_factory: Callable[[], LLMClient]

    # ------------------------------------------------------------------ chat
    async def chat(self, principal: Principal, req: ChatRequest) -> ChatResponse:
        if principal.role == "agent":
            raise PermissionDeniedError("Agent tokens cannot start agent runs", code="FORBIDDEN_ROLE")
        if not principal.can_access_customer(req.customer_id):
            raise PermissionDeniedError("customer_id does not match the signed-in customer",
                                        code="CUSTOMER_MISMATCH")
        now = self.clock.now()
        async with self.session_factory() as db:
            repo = AgentRepository(db)
            session = await repo.get_session(req.session_id, for_update=True)
            if session is None:
                session = AgentSession(session_key=req.session_id, customer_number=req.customer_id,
                                       channel=req.channel, status="active", created_at=now, last_activity_at=now)
                db.add(session)
                await db.flush()
            elif session.customer_number != req.customer_id:
                raise NotFoundError("Session not found", code="SESSION_NOT_FOUND")
            elif session.status != "active":
                raise BusinessRuleError("This chat session is closed; start a new session", code="SESSION_CLOSED")
            history = [
                {"role": m.role, "content": m.content}
                for m in await repo.recent_messages(session.id, self.settings.agent_history_turns * 2)
            ]
            run = AgentRun(
                run_key=f"run_{uuid.uuid4().hex}", session_id=session.id, customer_number=req.customer_id,
                status="running", question=redact_text(req.message) or "", llm_provider="pending",
                request_id=get_request_id(), started_at=now,
            )
            db.add(run)
            await db.flush()
            db.add(AgentMessage(session_id=session.id, run_id=run.id, role="user",
                                content=redact_text(req.message) or "", created_at=now))
            pending = session.pending_action
            await db.commit()  # the run is visible as "running" while the graph executes

            llm: LLMClient = self.llm_factory()
            run.llm_provider = llm.provider
            recorder = RunRecorder(run.run_key, self.clock)
            recorder.event("run_started", "chat", summary=f"session {req.session_id}",
                           payload={"channel": req.channel, "history_messages": len(history),
                                    "pending_action": bool(pending), "llm_provider": llm.provider})
            runtime = ToolRuntime(
                customer_number=req.customer_id, session_key=req.session_id, run_key=run.run_key,
                token=self.tokens.issue_agent_token(req.customer_id, req.session_id, run.run_key),
                client=self.tool_client, kb=self.kb, recorder=recorder, kb_top_k=self.settings.kb_top_k,
                pending_action=None,
            )
            executor = ToolExecutor(runtime)
            deps = AgentDeps(llm=llm, executor=executor, recorder=recorder, settings=self.settings, clock=self.clock)
            state_in = {
                "customer_number": req.customer_id, "raw_message": req.message, "history": history,
                "confirm_action_id": req.confirm_action_id, "pending_action": pending,
            }
            status, error_code, error_message, final = "completed", None, None, {}
            try:
                final = await asyncio.wait_for(GRAPH.ainvoke(state_in, config={"configurable": {"deps": deps}}),
                                               timeout=RUN_TIMEOUT_S)
                answer = final.get("final_text") or ""
            except TimeoutError:
                status, error_code, error_message = "failed", "AGENT_TIMEOUT", "The agent run timed out"
                answer = "I'm sorry, that took too long on my side. Please try again in a moment."
            except Exception as exc:  # never leak internals to the customer
                log.exception("agent_run_failed", run_id=run.run_key)
                status, error_code, error_message = "failed", "AGENT_ERROR", type(exc).__name__
                answer = ("I'm sorry, something went wrong on my side and I couldn't complete that. Please try "
                          "again, or ask me to connect you with our team.")
            if status == "failed":
                recorder.event("error", "run", status="error", summary=error_code,
                               payload={"error_type": error_message})

            # Pending action carried to the next turn: newly gated one, or none.
            new_pending = runtime.pending_action
            session.pending_action = new_pending
            completed_at = self.clock.now()
            recorder.event("run_completed", status, status="ok" if status == "completed" else "error",
                           summary=f"{len(recorder.tool_calls)} tool calls",
                           duration_ms=recorder.elapsed_ms)
            run.status, run.error_code, run.error_message = status, error_code, error_message
            run.final_response = answer
            run.intent, run.intent_confidence = final.get("intent"), final.get("confidence")
            run.model = recorder.model or llm.model
            run.llm_provider = deps.llm.provider
            run.llm_calls, run.tool_call_count = recorder.llm_calls, len(recorder.tool_calls)
            run.kb_retrieval_count = recorder.kb_retrievals
            run.input_tokens, run.output_tokens = recorder.input_tokens, recorder.output_tokens
            run.completed_at, run.duration_ms = completed_at, recorder.elapsed_ms
            db.add(AgentMessage(session_id=session.id, run_id=run.id, role="assistant", content=answer,
                                metadata_={"intent": run.intent, "tools": recorder.tools_used,
                                           "pending_action_id": new_pending["action_id"] if new_pending else None},
                                created_at=completed_at))
            session.message_count += 2
            session.run_count += 1
            session.last_activity_at = completed_at
            events, calls = recorder.to_rows(run.id)
            repo.add_events(events, calls)
            await db.commit()

        escalation = final.get("escalation")
        return ChatResponse(
            session_id=req.session_id, run_id=run.run_key, status=status, message=answer,
            intent=IntentOut(name=final["intent"], confidence=final["confidence"]) if final.get("intent") else None,
            tools_used=recorder.tools_used,
            kb_sources=[KbSource(**s) for s in recorder.kb_sources[:6]],
            pending_action=_pending_out(new_pending),
            requires_confirmation=new_pending is not None,
            executed_action=_executed_out(final.get("executed_action")),
            escalation=EscalationOut(**escalation) if escalation else None,
            llm_provider=deps.llm.provider,
            duration_ms=recorder.elapsed_ms,
        )

    # ------------------------------------------------------------------ observability
    async def _owned_session(self, repo: AgentRepository, principal: Principal, session_key: str) -> AgentSession:
        session = await repo.get_session(session_key)
        if session is None or not principal.can_access_customer(session.customer_number):
            raise NotFoundError("Session not found", code="SESSION_NOT_FOUND")
        return session

    async def get_session(self, principal: Principal, session_key: str) -> SessionOut:
        async with self.session_factory() as db:
            s = await self._owned_session(AgentRepository(db), principal, session_key)
            return SessionOut(
                session_id=s.session_key, customer_id=s.customer_number, channel=s.channel, status=s.status,
                message_count=s.message_count, run_count=s.run_count, pending_action=_pending_out(s.pending_action),
                created_at=s.created_at, last_activity_at=s.last_activity_at,
            )

    async def list_messages(self, principal: Principal, session_key: str, page: PageParams) -> Page[MessageOut]:
        async with self.session_factory() as db:
            repo = AgentRepository(db)
            s = await self._owned_session(repo, principal, session_key)
            messages, total = await repo.list_messages(s.id, page.offset, page.page_size)
            run_keys = {}
            for m in messages:
                if m.run_id and m.run_id not in run_keys:
                    run = await db.get(AgentRun, m.run_id)
                    run_keys[m.run_id] = run.run_key if run else None
            items = [MessageOut(role=m.role, content=m.content, run_id=run_keys.get(m.run_id),
                                created_at=m.created_at) for m in messages]
            return Page(items=items, page=page.page, page_size=page.page_size, total=total,
                        has_more=page.offset + len(items) < total)

    async def list_traces(self, principal: Principal, session_key: str, page: PageParams) -> Page[RunTrace]:
        async with self.session_factory() as db:
            repo = AgentRepository(db)
            s = await self._owned_session(repo, principal, session_key)
            runs, total = await repo.list_runs(s.id, page.offset, page.page_size)
            items = [_trace(r, s.session_key) for r in runs]
            return Page(items=items, page=page.page, page_size=page.page_size, total=total,
                        has_more=page.offset + len(items) < total)

    async def _owned_run(self, db: AsyncSession, principal: Principal, run_key: str) -> tuple[AgentRun, str]:
        repo = AgentRepository(db)
        run = await repo.get_run(run_key, with_children=True)
        if run is None or not principal.can_access_customer(run.customer_number):
            raise NotFoundError("Run not found", code="RUN_NOT_FOUND")
        return run, await repo.session_key_for(run.session_id)

    async def get_run(self, principal: Principal, run_key: str) -> RunOut:
        async with self.session_factory() as db:
            run, session_key = await self._owned_run(db, principal, run_key)
            return _run_out(run, session_key)

    async def run_steps(self, principal: Principal, run_key: str) -> list[RunEventOut]:
        async with self.session_factory() as db:
            run, _ = await self._owned_run(db, principal, run_key)
            return [RunEventOut.model_validate(e) for e in run.events]

    async def run_tools(self, principal: Principal, run_key: str) -> list[ToolCallOut]:
        async with self.session_factory() as db:
            run, _ = await self._owned_run(db, principal, run_key)
            return [ToolCallOut.model_validate(c) for c in run.tool_calls]

    async def health(self) -> HealthOut:
        checks: list[HealthCheck] = []
        try:
            async with self.session_factory() as db:
                await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=3)
            checks.append(HealthCheck(name="database", status="ok"))
        except Exception as exc:
            checks.append(HealthCheck(name="database", status="down", detail={"error": type(exc).__name__}))
        kb = self.kb.stats()
        checks.append(HealthCheck(name="knowledge_base", status="ok" if kb["chunks"] else "down", detail=kb))
        provider = self.settings.resolved_llm_provider
        checks.append(HealthCheck(
            name="llm", status="ok" if provider == "anthropic" else "degraded",
            detail={"provider": provider, "model": self.settings.anthropic_model if provider == "anthropic"
                    else "rule-based-planner-v1",
                    "note": None if provider == "anthropic" else "No LLM configured: deterministic planner in use"},
        ))
        tool_ok = await self.tool_client.health()
        breaker = self.tool_client.breaker.snapshot()
        checks.append(HealthCheck(name="tool_api", status="ok" if tool_ok and breaker["state"] == "closed"
                                  else "degraded" if tool_ok else "down", detail={"circuit_breaker": breaker}))
        worst = "down" if any(c.status == "down" for c in checks) else (
            "degraded" if any(c.status == "degraded" for c in checks) else "ok")
        return HealthOut(status=worst, checks=checks, checked_at=self.clock.now())


def _pending_out(p: dict | None) -> PendingActionOut | None:
    if not p:
        return None
    return PendingActionOut(action_id=p["action_id"], tool=p["tool"], summary=p["summary"], expires_at=p["expires_at"])


def _executed_out(e: dict | None) -> dict | None:
    if not e:
        return None
    result = e.get("result") if isinstance(e.get("result"), dict) else {}
    refs = {k: result.get(k) for k in ("order_id", "ticket_number", "status") if result.get(k)}
    if isinstance(result.get("refund"), dict):
        refs["refund_id"] = result["refund"].get("refund_id")
        refs["amount"] = result["refund"].get("amount")
    if isinstance(result.get("rma"), dict):
        refs["rma_number"] = result["rma"].get("rma_number")
    return {"action_id": e["action_id"], "tool": e["tool"], "ok": e["ok"], "references": refs}


def _run_out(r: AgentRun, session_key: str) -> RunOut:
    return RunOut(
        run_id=r.run_key, session_id=session_key, customer_id=r.customer_number, status=r.status,
        question=r.question, final_response=r.final_response, intent=r.intent, intent_confidence=r.intent_confidence,
        llm_provider=r.llm_provider, model=r.model, llm_calls=r.llm_calls, tool_call_count=r.tool_call_count,
        kb_retrieval_count=r.kb_retrieval_count, input_tokens=r.input_tokens, output_tokens=r.output_tokens,
        request_id=r.request_id, error_code=r.error_code, error_message=r.error_message, started_at=r.started_at,
        completed_at=r.completed_at, duration_ms=r.duration_ms,
    )


def _trace(r: AgentRun, session_key: str) -> RunTrace:
    return RunTrace(**_run_out(r, session_key).model_dump(),
                    steps=[RunEventOut.model_validate(e) for e in r.events],
                    tool_calls=[ToolCallOut.model_validate(c) for c in r.tool_calls])
