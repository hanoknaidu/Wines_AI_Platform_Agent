"""Category 2: Agentic APIs. The frontend talks only to these endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import chat_rate_limit, get_container, require_roles
from app.container import Container
from app.core.security import Principal
from app.schemas.agent import (
    ChatRequest,
    ChatResponse,
    HealthOut,
    MessageOut,
    RunEventOut,
    RunOut,
    RunTrace,
    SessionOut,
    ToolCallOut,
)
from app.schemas.common import ERROR_RESPONSES, Page, PageParams

router = APIRouter(prefix="/agent", tags=["Agentic APIs"], responses=ERROR_RESPONSES)
SessionId = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{4,100}$")]
RunId = Annotated[str, Path(pattern=r"^run_[0-9a-f]{32}$")]
customer_or_staff = require_roles("customer", "staff")


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(chat_rate_limit)],
             summary="Ask the customer-support agent a question")
async def chat(body: ChatRequest, principal: Principal = Depends(customer_or_staff),
               container: Container = Depends(get_container)):
    return await container.agent.chat(principal, body)


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(session_id: SessionId, principal: Principal = Depends(customer_or_staff),
                      container: Container = Depends(get_container)):
    return await container.agent.get_session(principal, session_id)


@router.get("/sessions/{session_id}/messages", response_model=Page[MessageOut])
async def get_messages(
    session_id: SessionId,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    principal: Principal = Depends(customer_or_staff),
    container: Container = Depends(get_container),
):
    return await container.agent.list_messages(principal, session_id, PageParams(page=page, page_size=page_size))


@router.get("/sessions/{session_id}/traces", response_model=Page[RunTrace],
            summary="Execution traces (structured events, no chain of thought) for every run in a session")
async def get_traces(
    session_id: SessionId,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
    principal: Principal = Depends(customer_or_staff),
    container: Container = Depends(get_container),
):
    return await container.agent.list_traces(principal, session_id, PageParams(page=page, page_size=page_size))


@router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(run_id: RunId, principal: Principal = Depends(customer_or_staff),
                  container: Container = Depends(get_container)):
    return await container.agent.get_run(principal, run_id)


@router.get("/runs/{run_id}/steps", response_model=list[RunEventOut])
async def get_run_steps(run_id: RunId, principal: Principal = Depends(customer_or_staff),
                        container: Container = Depends(get_container)):
    return await container.agent.run_steps(principal, run_id)


@router.get("/runs/{run_id}/tools", response_model=list[ToolCallOut])
async def get_run_tools(run_id: RunId, principal: Principal = Depends(customer_or_staff),
                        container: Container = Depends(get_container)):
    return await container.agent.run_tools(principal, run_id)


@router.get("/health", response_model=HealthOut, summary="Agent and dependency health (no auth)")
async def health(container: Container = Depends(get_container)):
    return await container.agent.health()

