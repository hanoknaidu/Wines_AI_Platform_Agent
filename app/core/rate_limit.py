"""Fixed-window rate limiting with pluggable backends.

memory: per-process, fine for one replica and for tests.
redis:  shared across replicas (INCR + EXPIRE), required for horizontal scale."""
from __future__ import annotations

import asyncio
import time
from typing import Protocol

import structlog

log = structlog.get_logger(__name__)


class RateLimiter(Protocol):
    async def hit(self, key: str, limit: int, window_s: int = 60) -> tuple[bool, int]:
        """Return (allowed, seconds_until_reset)."""


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, tuple[int, int]] = {}
        self._lock = asyncio.Lock()

    async def hit(self, key: str, limit: int, window_s: int = 60) -> tuple[bool, int]:
        now = int(time.time())
        window = now // window_s
        async with self._lock:
            w, count = self._buckets.get(key, (window, 0))
            if w != window:
                w, count = window, 0
            count += 1
            self._buckets[key] = (w, count)
            if len(self._buckets) > 100_000:  # bound memory
                self._buckets = {k: v for k, v in self._buckets.items() if v[0] == window}
        return count <= limit, window_s - (now % window_s)


class RedisRateLimiter:
    def __init__(self, url: str) -> None:
        from redis.asyncio import Redis

        self._redis = Redis.from_url(url, socket_timeout=0.5, socket_connect_timeout=0.5)

    async def hit(self, key: str, limit: int, window_s: int = 60) -> tuple[bool, int]:
        now = int(time.time())
        bucket = f"rl:{key}:{now // window_s}"
        try:
            pipe = self._redis.pipeline()
            pipe.incr(bucket)
            pipe.expire(bucket, window_s + 1)
            count, _ = await pipe.execute()
        except Exception as exc:  # fail open: rate limiting must not take the API down
            log.warning("rate_limiter_unavailable", error=type(exc).__name__)
            return True, window_s
        return int(count) <= limit, window_s - (now % window_s)
