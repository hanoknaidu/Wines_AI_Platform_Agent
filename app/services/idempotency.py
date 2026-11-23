"""Request-level idempotency for state-changing endpoints.

The first successful response for (principal, Idempotency-Key) is stored in
the same transaction as the change. A retry with the same key and body gets
the stored response back (`replayed=True`); the same key with a different
body is rejected. Business-rule rejections are not stored, so a customer can
retry once the situation changes."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Awaitable, Callable
from datetime import timedelta

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.core.errors import BadRequestError, BusinessRuleError, ConflictError
from app.models import IdempotencyRecord
from app.repositories.misc_repo import IdempotencyRepository
from app.services.context import ServiceContext

_KEY = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
TTL = timedelta(hours=24)


def validate_key(key: str | None) -> str:
    if not key or not _KEY.match(key):
        raise BadRequestError(
            "Idempotency-Key header is required (8-128 chars: letters, digits, . _ : -)",
            code="IDEMPOTENCY_KEY_REQUIRED",
        )
    return key


async def run_idempotent(
    ctx: ServiceContext,
    key: str | None,
    method: str,
    path: str,
    payload: dict,
    handler: Callable[[], Awaitable[tuple[int, BaseModel]]],
) -> tuple[int, dict, bool]:
    key = validate_key(key)
    request_hash = hashlib.sha256(
        json.dumps({"path": path, "body": payload}, sort_keys=True, default=str).encode()
    ).hexdigest()
    repo = IdempotencyRepository(ctx.session)
    principal_ref = ctx.principal.rate_limit_key

    existing = await repo.get(principal_ref, key)
    if existing is not None:
        if existing.request_hash != request_hash:
            raise BusinessRuleError(
                "This Idempotency-Key was already used with a different request",
                code="IDEMPOTENCY_KEY_REUSED",
            )
        return existing.status_code, existing.response_body, True

    status_code, model = await handler()
    body = model.model_dump(mode="json")
    ctx.session.add(
        IdempotencyRecord(
            principal_ref=principal_ref,
            idempotency_key=key,
            method=method,
            path=path,
            request_hash=request_hash,
            status_code=status_code,
            response_body=body,
            created_at=ctx.now,
            expires_at=ctx.now + TTL,
        )
    )
    try:
        await ctx.session.commit()
    except IntegrityError as exc:
        await ctx.session.rollback()
        raise ConflictError(
            "A request with this Idempotency-Key is already being processed; retry shortly",
            code="IDEMPOTENCY_IN_PROGRESS",
        ) from exc
    return status_code, body, False
