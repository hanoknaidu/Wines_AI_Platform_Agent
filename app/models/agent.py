"""Agent orchestration state and observability. Owned by the agent layer; the
agent never reads business tables, and business services never read these."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, JSONType, UTCDateTime, in_


class AgentSession(Base):
    __tablename__ = "agent_sessions"
    __table_args__ = (CheckConstraint(in_("status", ("active", "closed")), name="status"),)

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    session_key: Mapped[str] = mapped_column(String(100), unique=True)  # client-visible session_id
    customer_number: Mapped[str] = mapped_column(String(20), index=True)
    channel: Mapped[str] = mapped_column(String(20), default="web_chat")
    status: Mapped[str] = mapped_column(String(10), default="active")
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    pending_action: Mapped[dict | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    last_activity_at: Mapped[datetime] = mapped_column(UTCDateTime)


class AgentMessage(Base):
    __tablename__ = "agent_messages"
    __table_args__ = (Index("ix_agent_messages_session", "session_id", "id"),)

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("agent_sessions.id"))
    run_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.id"))
    role: Mapped[str] = mapped_column(String(10))  # user | assistant
    content: Mapped[str] = mapped_column(Text)  # PII-redacted
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(in_("status", ("running", "completed", "failed")), name="status"),
        Index("ix_agent_runs_session", "session_id", "id"),
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    run_key: Mapped[str] = mapped_column(String(64), unique=True)  # client-visible run_id
    session_id: Mapped[int] = mapped_column(ForeignKey("agent_sessions.id"))
    customer_number: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(10), default="running")
    question: Mapped[str] = mapped_column(Text)  # PII-redacted
    final_response: Mapped[str | None] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(60))
    intent_confidence: Mapped[float | None] = mapped_column()
    llm_provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str | None] = mapped_column(String(60))
    llm_calls: Mapped[int] = mapped_column(Integer, default=0)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0)
    kb_retrieval_count: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    request_id: Mapped[str | None] = mapped_column(String(128))
    error_code: Mapped[str | None] = mapped_column(String(60))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    events: Mapped[list[AgentRunEvent]] = relationship(lazy="raise_on_sql", order_by="AgentRunEvent.seq")
    tool_calls: Mapped[list[AgentToolCall]] = relationship(lazy="raise_on_sql", order_by="AgentToolCall.seq")


class AgentRunEvent(Base):
    __tablename__ = "agent_run_events"
    __table_args__ = (UniqueConstraint("run_id", "seq"),)

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(40))
    name: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="ok")
    summary: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSONType)  # structured + redacted
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class AgentToolCall(Base):
    __tablename__ = "agent_tool_calls"
    __table_args__ = (Index("ix_agent_tool_calls_run", "run_id", "seq"),)

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"))
    seq: Mapped[int] = mapped_column(Integer)
    tool_call_id: Mapped[str] = mapped_column(String(80))
    tool_name: Mapped[str] = mapped_column(String(60), index=True)
    category: Mapped[str] = mapped_column(String(10))  # read | write | kb
    arguments: Mapped[dict | None] = mapped_column(JSONType)  # redacted
    http_method: Mapped[str | None] = mapped_column(String(10))
    http_path: Mapped[str | None] = mapped_column(String(300))
    status_code: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(20))  # success | error | gated | rejected
    error_code: Mapped[str | None] = mapped_column(String(60))
    retryable: Mapped[bool | None] = mapped_column()
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    response_summary: Mapped[dict | None] = mapped_column(JSONType)  # redacted, truncated
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
