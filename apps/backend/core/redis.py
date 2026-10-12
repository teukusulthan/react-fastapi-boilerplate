"""Redis client factory and key naming.

One sync ``redis.Redis`` (connection-pooled, thread-safe) per process, created in
the app lifespan and exposed through ``core.deps.get_redis``. Services are sync,
so there is deliberately no asyncio client.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import redis

if TYPE_CHECKING:
    from core.config import Settings


def create_redis(settings: Settings) -> redis.Redis:
    return redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
        retry_on_timeout=True,
    )


def redis_key(settings: Settings, *parts: str) -> str:
    """Namespaced key: ``redis_key(s, "otp", "register", email)`` -> ``app:otp:register:<email>``."""
    return ":".join((settings.REDIS_KEY_PREFIX, *parts))
