"""Test fixtures.

Default: each test gets a fresh SQLite copy of a seeded template (fast, no
infrastructure). Set TEST_DATABASE_URL=postgresql+asyncpg://... to run the same
suite against PostgreSQL (schema is recreated + reseeded per test).
The clock is frozen at the seed reference date (2026-11-19T18:00:00Z)."""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.container import Container  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.seed import load_seed  # noqa: E402
from app.db.session import create_engine  # noqa: E402
from app.main import create_app  # noqa: E402

REFERENCE_NOW = datetime(2026, 11, 19, 18, 0, tzinfo=UTC)
SEED_SOURCE = ROOT / "_DB" / "ecommerce.db"
PG_URL = os.getenv("TEST_DATABASE_URL")


def make_settings(**overrides) -> Settings:
    base = dict(
        environment="test", log_level="WARNING", log_json=True, reference_now=REFERENCE_NOW,
        database_url=PG_URL or "sqlite+aiosqlite:///:memory:", llm_provider="rule_based", anthropic_api_key=None,
        rate_limit_tool_per_minute=10_000, rate_limit_chat_per_minute=10_000, kb_path=ROOT / "_KB",
        jwt_secret="test-secret-0123456789abcdef0123456789",
    )
    base.update(overrides)
    return Settings(_env_file=None, **base)


@pytest.fixture(scope="session")
def template_db(tmp_path_factory) -> Path | None:
    if PG_URL:
        return None
    path = tmp_path_factory.mktemp("db") / "template.db"
    settings = make_settings()

    async def build():
        engine = create_engine(settings, f"sqlite+aiosqlite:///{path}")
        await load_seed(engine, SEED_SOURCE, recreate=True)
        await engine.dispose()

    asyncio.run(build())
    return path


@pytest_asyncio.fixture
async def app_ctx(template_db, tmp_path, request):
    """(app, container) on a fresh database. Override settings with
    @pytest.mark.settings(key=value)."""
    marker = request.node.get_closest_marker("settings")
    settings = make_settings(**(marker.kwargs if marker else {}))
    if PG_URL:
        engine = create_engine(settings, PG_URL)
        await load_seed(engine, SEED_SOURCE, recreate=True)
    else:
        db_file = tmp_path / "test.db"
        shutil.copy(template_db, db_file)
        engine = create_engine(settings, f"sqlite+aiosqlite:///{db_file}")
    app = create_app(settings)
    container = Container.build(settings, app, engine=engine)
    app.state.container = container
    yield app, container
    await container.close()


@pytest_asyncio.fixture
async def client(app_ctx):
    app, _ = app_ctx
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def container(app_ctx) -> Container:
    return app_ctx[1]


@pytest.fixture
def auth(container):
    """auth("C-100005") -> customer headers; auth(staff="S-1001"); auth(agent="C-100005")."""

    def _headers(customer: str | None = None, *, staff: str | None = None, agent: str | None = None) -> dict:
        if staff:
            token = container.tokens.issue_staff_token(staff)
        elif agent:
            token = container.tokens.issue_agent_token(agent, "SESSION-TEST", "run_" + "0" * 32)
        else:
            token = container.tokens.issue_customer_token(customer)
        return {"Authorization": f"Bearer {token}"}

    return _headers


def pytest_configure(config):
    config.addinivalue_line("markers", "settings(**kwargs): override Settings for this test")
