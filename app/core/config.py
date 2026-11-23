"""Environment-based configuration (12-factor). Every setting can be overridden by
an environment variable of the same name (case-insensitive) or by `.env`."""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- application -------------------------------------------------------
    app_name: str = "Wines AI Platform Agent"
    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: str = "INFO"
    log_json: bool = True
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    # Seed scenarios are written relative to 2026-11-19. Freeze the clock for demos
    # and tests; leave empty in production so the real time is used.
    reference_now: datetime | None = None

    # --- database ----------------------------------------------------------
    database_url: str = "postgresql+asyncpg://wines:wines@localhost:5432/wines_agent"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout_s: float = 10.0
    db_echo: bool = False

    # --- auth --------------------------------------------------------------
    jwt_secret: SecretStr = SecretStr("change-me-in-every-environment-0123456789")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "wines-ai-platform"
    jwt_audience: str = "wines-ai-api"
    access_token_ttl_s: int = 3600
    agent_token_ttl_s: int = 300
    enable_dev_auth: bool = True  # POST /auth/dev-token; must be False in production

    # --- rate limiting -----------------------------------------------------
    rate_limit_backend: Literal["memory", "redis"] = "memory"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_tool_per_minute: int = 240
    rate_limit_chat_per_minute: int = 30

    # --- knowledge base ----------------------------------------------------
    kb_path: Path = ROOT_DIR / "_KB"
    kb_top_k: int = 4

    # --- tool API client (agent -> Category 1 APIs) ------------------------
    tool_api_base_url: str | None = None  # None = in-process ASGI transport
    tool_api_timeout_s: float = 8.0
    tool_api_max_retries: int = 2
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_reset_s: float = 30.0

    # --- LLM ---------------------------------------------------------------
    llm_provider: Literal["auto", "anthropic", "rule_based"] = "auto"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    anthropic_max_tokens: int = 16000
    anthropic_timeout_s: float = 90.0
    anthropic_max_retries: int = 2
    anthropic_fallbacks_enabled: bool = True
    agent_max_iterations: int = 8
    agent_history_turns: int = 10

    # Placeholder host for signed claim-photo upload links (object storage front end)
    evidence_upload_base_url: str = "https://uploads.example.com/claims"

    # --- business authority limits (mirror DB CHECKs; KB A-60 / A-61) -------
    agent_refund_limit_cents: int = 15000
    agent_goodwill_limit_cents: int = 1500

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def resolved_llm_provider(self) -> Literal["anthropic", "rule_based"]:
        if self.llm_provider == "auto":
            return "anthropic" if self.anthropic_api_key else "rule_based"
        return self.llm_provider


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production:
        if settings.enable_dev_auth:
            raise RuntimeError("ENABLE_DEV_AUTH must be false in production")
        if settings.jwt_secret.get_secret_value().startswith("change-me"):
            raise RuntimeError("JWT_SECRET must be set in production")
    return settings
