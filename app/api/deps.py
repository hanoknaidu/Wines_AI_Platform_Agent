"""FastAPI dependencies: DI container, DB session, authentication, roles,
rate limiting, and the per-request ServiceContext."""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import Container
from app.core.errors import AuthenticationError, PermissionDeniedError, RateLimitedError
from app.core.security import Principal
from app.services.context import ServiceContext

bearer = HTTPBearer(auto_error=False, description="JWT issued by the identity provider (or /auth/dev-token locally)")


def get_container(request: Request) -> Container:
    return request.app.state.container


async def get_db(container: Container = Depends(get_container)) -> AsyncIterator[AsyncSession]:
    async with container.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    container: Container = Depends(get_container),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Bearer token required", code="UNAUTHENTICATED",
                                  headers={"WWW-Authenticate": "Bearer"})
    return container.tokens.verify(credentials.credentials)


def require_roles(*roles: str) -> Callable[[Principal], Principal]:
    def _check(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role not in roles:
            raise PermissionDeniedError("This operation is not allowed for your role", code="FORBIDDEN_ROLE")
        return principal

    return _check


def _rate_limiter(bucket: str):
    async def _limit(
        request: Request,
        principal: Principal = Depends(get_principal),
        container: Container = Depends(get_container),
    ) -> None:
        s = container.settings
        limit = s.rate_limit_chat_per_minute if bucket == "chat" else s.rate_limit_tool_per_minute
        allowed, reset = await container.rate_limiter.hit(f"{bucket}:{principal.rate_limit_key}", limit)
        if not allowed:
            raise RateLimitedError("Too many requests; slow down and retry", headers={"Retry-After": str(reset)})

    return _limit


tool_rate_limit = _rate_limiter("tool")
chat_rate_limit = _rate_limiter("chat")


def get_ctx(
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
    container: Container = Depends(get_container),
) -> ServiceContext:
    return ServiceContext(
        session=db, clock=container.clock, settings=container.settings, principal=principal,
        client_ip=request.client.host if request.client else None,
    )
