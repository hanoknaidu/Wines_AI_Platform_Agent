"""Correlation-ID + access-log middleware (pure ASGI, so it is cheap and works
with streaming responses)."""
from __future__ import annotations

import re
import time
import uuid

import structlog

from app.core.request_context import reset_request_id, set_request_id

log = structlog.get_logger("access")
_VALID_ID = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


class RequestContextMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        incoming = headers.get("x-request-id", "")
        request_id = incoming if _VALID_ID.match(incoming) else f"req_{uuid.uuid4().hex}"
        token = set_request_id(request_id)
        structlog.contextvars.bind_contextvars(request_id=request_id)
        started = time.perf_counter()
        status_holder = {"status": 500}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                message.setdefault("headers", [])
                message["headers"].append((b"x-request-id", request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            log.info(
                "http_request",
                method=scope.get("method"),
                path=scope.get("path"),
                status=status_holder["status"],
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
            )
            structlog.contextvars.unbind_contextvars("request_id")
            reset_request_id(token)
