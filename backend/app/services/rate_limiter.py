"""Configurable rate limiting with memory or Redis storage backends.

SQLite is used for event persistence, not rate-limit counters.
In-memory storage does not share state across workers/processes.
Redis is recommended for multi-worker deployments.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Optional

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    retry_after: int | None = None


class InMemoryRateLimiter:
    """Sliding-window rate limiter backed by process-local memory."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def check(self, key: str) -> RateLimitResult:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window_seconds:
                q.popleft()

            if len(q) >= self.limit:
                oldest = q[0]
                retry = max(1, int(self.window_seconds - (now - oldest)) + 1)
                return RateLimitResult(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    reset_seconds=retry,
                    retry_after=retry,
                )

            q.append(now)
            remaining = max(0, self.limit - len(q))
            reset = self.window_seconds
            if q:
                reset = max(1, int(self.window_seconds - (now - q[0])) + 1)
            return RateLimitResult(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                reset_seconds=reset,
                retry_after=None,
            )


class RedisRateLimiter:
    """Sliding-window rate limiter using Redis sorted sets.

    Falls back to denying configuration errors clearly rather than silently
    switching to memory.
    """

    def __init__(self, limit: int, window_seconds: int, redis_url: str) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        try:
            import redis  # type: ignore[import-untyped]

            self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Redis rate-limit storage unavailable ({exc}). "
                "Set RATE_LIMIT_STORAGE=memory for single-process demos, "
                "or provide a reachable REDIS_URL."
            ) from exc

    def check(self, key: str) -> RateLimitResult:
        now = time.time()
        window_start = now - self.window_seconds
        redis_key = f"botshield:rl:{key}"
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {f"{now}": now})
        pipe.expire(redis_key, self.window_seconds + 1)
        results = pipe.execute()
        count_before = int(results[1])

        if count_before >= self.limit:
            # Remove the speculative add
            self._redis.zrem(redis_key, f"{now}")
            oldest = self._redis.zrange(redis_key, 0, 0, withscores=True)
            retry = self.window_seconds
            if oldest:
                retry = max(1, int(self.window_seconds - (now - oldest[0][1])) + 1)
            return RateLimitResult(
                allowed=False,
                limit=self.limit,
                remaining=0,
                reset_seconds=retry,
                retry_after=retry,
            )

        remaining = max(0, self.limit - count_before - 1)
        return RateLimitResult(
            allowed=True,
            limit=self.limit,
            remaining=remaining,
            reset_seconds=self.window_seconds,
            retry_after=None,
        )


class RateLimiterService:
    """Facade selecting memory or Redis backend from settings."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._backend: InMemoryRateLimiter | RedisRateLimiter | None = None
        if self.settings.rate_limit_enabled:
            self._backend = self._create_backend()

    def _create_backend(self) -> InMemoryRateLimiter | RedisRateLimiter:
        limit = self.settings.rate_limit_requests
        window = self.settings.rate_limit_window_seconds
        if self.settings.rate_limit_storage == "redis":
            return RedisRateLimiter(limit, window, self.settings.redis_url)
        return InMemoryRateLimiter(limit, window)

    def reset(self) -> None:
        if isinstance(self._backend, InMemoryRateLimiter):
            self._backend.reset()

    def check(self, client_id: str) -> RateLimitResult:
        if not self.settings.rate_limit_enabled or self._backend is None:
            return RateLimitResult(
                allowed=True,
                limit=self.settings.rate_limit_requests,
                remaining=self.settings.rate_limit_requests,
                reset_seconds=self.settings.rate_limit_window_seconds,
            )
        return self._backend.check(client_id)


_limiter: Optional[RateLimiterService] = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiterService:
    global _limiter
    with _limiter_lock:
        if _limiter is None:
            _limiter = RateLimiterService()
        return _limiter


def reset_rate_limiter(settings: Optional[Settings] = None) -> RateLimiterService:
    global _limiter
    with _limiter_lock:
        _limiter = RateLimiterService(settings)
        return _limiter


def rate_limit_headers(result: RateLimitResult) -> dict[str, str]:
    headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_seconds),
    }
    if result.retry_after is not None:
        headers["Retry-After"] = str(result.retry_after)
    return headers
