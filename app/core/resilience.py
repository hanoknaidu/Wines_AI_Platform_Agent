"""Resilience primitives for outbound dependencies: circuit breaker and
retry-with-backoff. Used by the agent's Tool API client."""
from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import TypeVar

T = TypeVar("T")


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    """Opens after `failure_threshold` consecutive failures; after `reset_s`
    lets one trial call through (half-open); success closes it again."""

    def __init__(self, name: str, failure_threshold: int = 5, reset_s: float = 30.0) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_s = reset_s
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if self._opened_at is None:
            return CircuitState.CLOSED
        if time.monotonic() - self._opened_at >= self.reset_s:
            return CircuitState.HALF_OPEN
        return CircuitState.OPEN

    async def before_call(self) -> None:
        async with self._lock:
            if self.state == CircuitState.OPEN:
                raise CircuitOpenError(self.name)

    async def record_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
                self._opened_at = time.monotonic()

    def snapshot(self) -> dict:
        return {"name": self.name, "state": self.state.value, "consecutive_failures": self._failures}


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    should_retry: Callable[[BaseException | T], bool],
    base_delay_s: float = 0.2,
    max_delay_s: float = 2.0,
) -> tuple[T, int]:
    """Run fn up to `attempts` times with exponential backoff + full jitter.
    Returns (result, attempts_used). Re-raises the last exception."""
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            result = await fn()
        except Exception as exc:
            last_exc = exc
            if attempt == attempts or not should_retry(exc):
                raise
        else:
            if attempt == attempts or not should_retry(result):
                return result, attempt
        delay = min(max_delay_s, base_delay_s * 2 ** (attempt - 1))
        await asyncio.sleep(random.uniform(0, delay))
    assert last_exc is not None  # pragma: no cover
    raise last_exc
