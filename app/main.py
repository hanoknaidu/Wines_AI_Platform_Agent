"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import tool_rate_limit
from app.api.v1 import agent as agent_api
from app.api.v1 import business, customers, orders
from app.container import Container
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

DESCRIPTION = """
Agentic customer-support backend for a licensed NJ + NY wine retailer.

* **Tool APIs** (customers, orders, refunds/returns, catalog, shipping, stores, support): typed business
  endpoints the AI agent calls as tools, with ownership checks, idempotent writes and audit logging.
* **Agentic APIs** (`/agent/*`): chat with the LangGraph agent and inspect sessions, runs, steps and tool calls.

Authenticate with `Authorization: Bearer <JWT>` (locally: `POST /api/v1/auth/dev-token`).
Money values are decimal strings in USD; IDs are public business keys (C-100001, WA-100101).
"""


def create_app(settings: Settings | None = None, *, container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_json)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = container or Container.build(settings, app)
        yield
        if container is None:
            await app.state.container.close()

    app = FastAPI(
        title=settings.app_name, version="0.2.0", description=DESCRIPTION, lifespan=lifespan,
        docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json",
    )
    if container is not None:  # tests inject a pre-built container
        app.state.container = container
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type",
                                                                     "Idempotency-Key", "X-Request-ID"],
                       expose_headers=["X-Request-ID", "Idempotent-Replayed", "Retry-After"])
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    tools = APIRouter(dependencies=[Depends(tool_rate_limit)])
    tools.include_router(customers.router)
    tools.include_router(orders.router)
    tools.include_router(business.catalog)
    tools.include_router(business.shipping)
    tools.include_router(business.stores)
    tools.include_router(business.support)
    app.include_router(tools, prefix=settings.api_prefix)
    app.include_router(agent_api.router, prefix=settings.api_prefix)
    app.include_router(business.auth, prefix=settings.api_prefix)

    @app.get("/healthz", include_in_schema=False)
    async def liveness():
        return {"status": "ok"}

    return app


app = create_app()
