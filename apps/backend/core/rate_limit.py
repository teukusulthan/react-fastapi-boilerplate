"""Redis fixed-window rate limiting.

Route-level (preferred; BE-AUTH applies it to login/OTP/forgot-password)::

    @router.post("/login", dependencies=[Depends(rate_limit("auth:login"))])

    # custom limits / key (e.g. per identifier as well as per IP)
    rate_limit("auth:otp", limit=lambda s: 5, window=lambda s: 300,
               key_func=lambda request: request.headers.get("x-device-id", ""))

Imperative (inside a service)::

    result = limiter.hit(f"login:{email}", limit=5, window=900)
    if not result.allowed: raise RateLimitedError(retry_after=result.reset_after)

Optional global limit: ``BE_RATE_LIMIT_GLOBAL`` > 0 enables
:class:`GlobalRateLimitMiddleware` (per client IP, health/docs exempt).

Client identity is the socket peer address; ``X-Forwarded-For`` is honoured only
when ``BE_TRUST_PROXY_HEADERS=true`` (taking the entry appended by the N-th
trusted proxy, ``BE_PROXY_TRUSTED_HOPS``) so clients cannot spoof it.

Redis failures fail *open* (request allowed, error logged).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import anyio.to_thread
from fastapi import Depends, Request
from loguru import logger
from redis import Redis
from redis.exceptions import RedisError
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from core.errors import ErrorCode, RateLimitedError, error_response
from core.middleware import DEFAULT_EXEMPT_PREFIXES, is_exempt_path
from core.redis import redis_key

if TYPE_CHECKING:
    from core.config import Settings


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_after: int  # seconds until the window resets


class RateLimiter:
    """Fixed-window counter: ``SET NX EX`` + ``INCRBY`` in one MULTI (atomic, no TTL races)."""

    def __init__(self, redis: Redis, settings: Settings) -> None:
        self.redis = redis
        self.settings = settings

    def hit(self, key: str, *, limit: int, window: int, cost: int = 1) -> RateLimitResult:
        full_key = redis_key(self.settings, "rl", key)
        try:
            pipe = self.redis.pipeline(transaction=True)
            pipe.set(full_key, 0, ex=window, nx=True)
            pipe.incrby(full_key, cost)
            pipe.ttl(full_key)
            _, count, ttl = pipe.execute()
        except RedisError as exc:
            logger.error("Rate limiter unavailable ({}); allowing request", type(exc).__name__)
            return RateLimitResult(True, limit, limit, window)
        count = int(count)
        return RateLimitResult(count <= limit, limit, max(limit - count, 0), max(int(ttl), 0))

    def reset(self, key: str) -> None:
        try:
            self.redis.delete(redis_key(self.settings, "rl", key))
        except RedisError as exc:
            logger.error("Rate limiter reset failed ({})", type(exc).__name__)

    def check(self, key: str, *, limit: int, window: int) -> RateLimitResult:
        """``hit`` and raise :class:`RateLimitedError` when over the limit."""
        result = self.hit(key, limit=limit, window=window)
        if not result.allowed:
            raise RateLimitedError(retry_after=result.reset_after)
        return result


def client_ip_from_scope(scope: Scope, settings: Settings) -> str:
    if settings.TRUST_PROXY_HEADERS:
        forwarded = Headers(scope=scope).get("x-forwarded-for")
        if forwarded:
            hops = [part.strip() for part in forwarded.split(",") if part.strip()]
            if hops:
                return hops[max(len(hops) - settings.PROXY_TRUSTED_HOPS, 0)]
    client = scope.get("client")
    return client[0] if client else "unknown"


def client_ip(request: Request, settings: Settings) -> str:
    """Best-effort client IP honouring ``BE_TRUST_PROXY_HEADERS``."""
    return client_ip_from_scope(request.scope, settings)


IntOrFactory = int | Callable[["Settings"], int]


def _resolve(value: IntOrFactory, settings: Settings) -> int:
    return value(settings) if callable(value) else int(value)


def rate_limit(
    name: str,
    *,
    limit: IntOrFactory = lambda s: s.RATE_LIMIT_AUTH,
    window: IntOrFactory = lambda s: s.RATE_LIMIT_AUTH_WINDOW,
    key_func: Callable[[Request], str] | None = None,
) -> Callable[..., None]:
    """Build a dependency enforcing ``limit`` requests per ``window`` seconds per client.

    Defaults to the "sensitive endpoint" budget (``BE_RATE_LIMIT_AUTH`` per
    ``BE_RATE_LIMIT_AUTH_WINDOW``). Disabled entirely when ``BE_RATE_LIMIT_ENABLED=false``.
    """
    from core.deps import get_app_settings, get_redis  # local import: deps imports this module

    def dependency(
        request: Request,
        settings: Settings = Depends(get_app_settings),
        redis: Redis = Depends(get_redis),
    ) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        identity = client_ip(request, settings)
        if key_func is not None:
            identity = f"{identity}:{key_func(request)}"
        RateLimiter(redis, settings).check(
            f"{name}:{identity}", limit=_resolve(limit, settings), window=_resolve(window, settings)
        )

    dependency.__name__ = f"rate_limit_{name.replace(':', '_')}"
    return dependency


class GlobalRateLimitMiddleware:
    """Per-client request budget for the whole API (``BE_RATE_LIMIT_GLOBAL``)."""

    def __init__(self, app: ASGIApp, *, settings: Settings, redis_getter: Callable[[], Redis | None]) -> None:
        self.app = app
        self.settings = settings
        self.redis_getter = redis_getter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("method") == "OPTIONS"
            or is_exempt_path(scope, DEFAULT_EXEMPT_PREFIXES)
        ):
            await self.app(scope, receive, send)
            return
        redis = self.redis_getter()
        if redis is not None:
            limiter = RateLimiter(redis, self.settings)
            key = f"global:{client_ip_from_scope(scope, self.settings)}"
            result = await anyio.to_thread.run_sync(
                lambda: limiter.hit(key, limit=self.settings.RATE_LIMIT_GLOBAL, window=self.settings.RATE_LIMIT_WINDOW)
            )
            if not result.allowed:
                response = error_response(
                    429,
                    RateLimitedError.default_message,
                    ErrorCode.RATE_LIMITED,
                    headers={"Retry-After": str(max(result.reset_after, 1))},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
