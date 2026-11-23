"""HTTP client the agent uses to call Category 1 Tool APIs.

* timeout per call, bounded retries with jittered backoff
  (GET always; POST only when it carries an Idempotency-Key)
* circuit breaker shared across runs: after repeated failures the agent
  fails fast with a retryable TOOL_API_UNAVAILABLE instead of piling on
* forwards a derived X-Request-ID so tool calls correlate with the chat request
"""
from __future__ import annotations

import itertools
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.request_context import get_request_id
from app.core.resilience import CircuitBreaker, CircuitOpenError, retry_async

RETRYABLE_STATUS = {429, 502, 503, 504}


@dataclass
class ToolHttpResult:
    status_code: int
    body: Any
    attempts: int
    duration_ms: int

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class ToolApiUnavailable(Exception):
    def __init__(self, message: str, attempts: int = 1) -> None:
        super().__init__(message)
        self.attempts = attempts


class ToolApiClient:
    def __init__(
        self,
        http: httpx.AsyncClient,
        breaker: CircuitBreaker,
        *,
        max_retries: int = 2,
    ) -> None:
        self._http = http
        self.breaker = breaker
        self._max_retries = max_retries
        self._seq = itertools.count(1)

    async def request(
        self,
        token: str,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        idempotency_key: str | None = None,
    ) -> ToolHttpResult:
        try:
            await self.breaker.before_call()
        except CircuitOpenError as exc:
            raise ToolApiUnavailable("Tool API circuit is open") from exc

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        rid = get_request_id()
        if rid:
            headers["X-Request-ID"] = f"{rid}.t{next(self._seq)}"[:128]
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        retry_allowed = method == "GET" or idempotency_key is not None
        started = time.perf_counter()

        async def call() -> httpx.Response:
            return await self._http.request(method, path, params=clean_params, json=json, headers=headers)

        def should_retry(outcome) -> bool:
            if not retry_allowed:
                return False
            if isinstance(outcome, BaseException):
                return isinstance(outcome, httpx.TransportError)
            return outcome.status_code in RETRYABLE_STATUS

        try:
            response, attempts = await retry_async(
                call, attempts=1 + self._max_retries, should_retry=should_retry
            )
        except httpx.TransportError as exc:
            await self.breaker.record_failure()
            raise ToolApiUnavailable(f"Tool API unreachable: {type(exc).__name__}", 1 + self._max_retries) from exc

        if response.status_code >= 500:
            await self.breaker.record_failure()
        else:
            await self.breaker.record_success()
        try:
            body = response.json()
        except ValueError:
            body = {"error": {"code": "INVALID_RESPONSE", "message": "Non-JSON response", "retryable": True}}
        return ToolHttpResult(response.status_code, body, attempts, int((time.perf_counter() - started) * 1000))

    async def health(self) -> bool:
        try:
            url = self._http.base_url.copy_with(path="/healthz", query=None)
            response = await self._http.get(str(url), timeout=3.0)
            return response.status_code == 200
        except httpx.HTTPError:
            return False
