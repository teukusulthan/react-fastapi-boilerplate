"""One-time codes and attempt-bounded Redis challenges.

:class:`OtpService` — codes bound to ``(purpose, subject)`` (subject = lowercased email,
user id, …):

* code: ``secrets``-based digits (``BE_OTP_LENGTH``), never stored — only an HMAC
  binding it to ``(purpose, subject)`` (``core.security.hash_otp``);
* one live code per ``(purpose, subject)``: issuing a new one replaces the old one;
* lifetime ``BE_OTP_TTL``; at most ``BE_OTP_MAX_ATTEMPTS`` verifications, then the code is
  burnt; successful verification consumes it (unless ``consume=False``);
* resend cooldown ``BE_OTP_RESEND_COOLDOWN`` per ``(purpose, subject)``.

Redis keys hold a SHA-256 of the subject (no emails in key names).

:func:`attempt` — the shared "load hash, count attempt, check, consume" primitive
(optimistic ``WATCH``/``MULTI`` so concurrent guesses cannot exceed the limit and a
code/challenge can be consumed only once).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import TYPE_CHECKING

from loguru import logger
from redis import Redis
from redis.exceptions import WatchError

from core.redis import redis_key
from core.security import generate_otp, hash_otp, verify_otp

if TYPE_CHECKING:
    from core.config import Settings

ATTEMPTS_FIELD = "attempts"
_MAX_WATCH_RETRIES = 10


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def attempt(
    redis: Redis,
    key: str,
    check: Callable[[dict[str, str]], bool],
    *,
    max_attempts: int,
    consume: bool = True,
) -> dict[str, str] | None:
    """Count one attempt against the Redis hash at ``key`` and run ``check`` on its fields.

    Returns the hash (before consumption) when ``check`` passes, else ``None``. The hash is
    deleted when the check passes and ``consume`` is set, or when the attempt budget is
    exhausted. A missing/expired key is a failure. The key's TTL is preserved.
    """
    for _ in range(_MAX_WATCH_RETRIES):
        with redis.pipeline() as pipe:
            try:
                pipe.watch(key)
                data = pipe.hgetall(key)
                if not data:
                    return None
                attempts = int(data.get(ATTEMPTS_FIELD, 0)) + 1
                if attempts > max_attempts:
                    pipe.multi()
                    pipe.delete(key)
                    pipe.execute()
                    return None
                passed = check(data)
                pipe.multi()
                if (passed and consume) or (not passed and attempts >= max_attempts):
                    pipe.delete(key)
                else:
                    pipe.hset(key, ATTEMPTS_FIELD, attempts)
                pipe.execute()
                return data if passed else None
            except WatchError:
                continue
    logger.warning("Too much contention on a one-time challenge; rejecting attempt")
    return None


class OtpService:
    def __init__(self, redis: Redis, settings: Settings) -> None:
        self.redis = redis
        self.settings = settings

    def _key(self, kind: str, purpose: str, subject: str) -> str:
        return redis_key(self.settings, "otp", kind, purpose, digest(subject.lower()))

    def cooldown_remaining(self, purpose: str, subject: str) -> int:
        ttl = self.redis.ttl(self._key("cooldown", purpose, subject))
        return max(int(ttl), 0) if ttl and int(ttl) > 0 else 0

    def start_cooldown(self, purpose: str, subject: str) -> bool:
        """Start the resend cooldown; ``False`` if one is already running."""
        cooldown = self.settings.OTP_RESEND_COOLDOWN
        if cooldown <= 0:
            return True
        return bool(self.redis.set(self._key("cooldown", purpose, subject), "1", ex=cooldown, nx=True))

    def issue(self, purpose: str, subject: str, *, respect_cooldown: bool = True) -> str | None:
        """New code (replacing any previous one), or ``None`` while the resend cooldown runs."""
        if respect_cooldown and not self.start_cooldown(purpose, subject):
            return None
        code = generate_otp(self.settings.OTP_LENGTH)
        key = self._key("code", purpose, subject)
        pipe = self.redis.pipeline(transaction=True)
        pipe.delete(key)
        pipe.hset(
            key,
            mapping={
                "hash": hash_otp(code, self.settings, purpose=purpose, subject=subject.lower()),
                ATTEMPTS_FIELD: 0,
            },
        )
        pipe.expire(key, self.settings.OTP_TTL)
        pipe.execute()
        return code

    def verify(self, purpose: str, subject: str, code: str, *, consume: bool = True) -> bool:
        def check(data: dict[str, str]) -> bool:
            return verify_otp(code, data.get("hash"), self.settings, purpose=purpose, subject=subject.lower())

        return (
            attempt(
                self.redis,
                self._key("code", purpose, subject),
                check,
                max_attempts=self.settings.OTP_MAX_ATTEMPTS,
                consume=consume,
            )
            is not None
        )

    def invalidate(self, purpose: str, subject: str) -> None:
        self.redis.delete(self._key("code", purpose, subject), self._key("cooldown", purpose, subject))

    @property
    def ttl_minutes(self) -> int:
        return max(self.settings.OTP_TTL // 60, 1)
