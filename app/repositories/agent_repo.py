"""Persistence for the agent layer's own state (sessions, messages, runs,
events, tool calls). The agent layer never touches business tables."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import AgentMessage, AgentRun, AgentRunEvent, AgentSession, AgentToolCall
from app.repositories.base import Repository


class AgentRepository(Repository):
    async def get_session(self, session_key: str, *, for_update: bool = False) -> AgentSession | None:
        stmt = select(AgentSession).where(AgentSession.session_key == session_key)
        if for_update and self.dialect == "postgresql":
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def recent_messages(self, session_id: int, limit: int) -> list[AgentMessage]:
        stmt = (
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.id.desc())
            .limit(limit)
        )
        return list(reversed(list((await self.session.execute(stmt)).scalars())))

    async def list_messages(self, session_id: int, offset: int, limit: int) -> tuple[list[AgentMessage], int]:
        total = (
            await self.session.execute(select(func.count()).where(AgentMessage.session_id == session_id))
        ).scalar_one()
        stmt = (
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars()), int(total)

    async def get_run(self, run_key: str, *, with_children: bool = False) -> AgentRun | None:
        stmt = select(AgentRun).where(AgentRun.run_key == run_key)
        if with_children:
            stmt = stmt.options(selectinload(AgentRun.events), selectinload(AgentRun.tool_calls))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_runs(self, session_id: int, offset: int, limit: int) -> tuple[list[AgentRun], int]:
        total = (await self.session.execute(select(func.count()).where(AgentRun.session_id == session_id))).scalar_one()
        stmt = (
            select(AgentRun)
            .where(AgentRun.session_id == session_id)
            .options(selectinload(AgentRun.events), selectinload(AgentRun.tool_calls))
            .order_by(AgentRun.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars()), int(total)

    async def session_key_for(self, session_id: int) -> str:
        return (
            await self.session.execute(select(AgentSession.session_key).where(AgentSession.id == session_id))
        ).scalar_one()

    def add_events(self, events: list[AgentRunEvent], tool_calls: list[AgentToolCall]) -> None:
        self.session.add_all([*events, *tool_calls])
