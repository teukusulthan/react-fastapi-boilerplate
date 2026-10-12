"""Password login with account lockout and the 2FA gate.

* Lookup by email (case-insensitive, stored lowercased) or exact username.
* The password is ALWAYS checked with bcrypt (dummy hash for unknown users / SSO-only
  accounts) so response time does not reveal whether an account exists.
* Lockout: ``BE_ACCOUNT_LOCK_MAX_ATTEMPTS`` failures per (identifier, client IP) within
  ``BE_ACCOUNT_LOCK_SECONDS`` lock that pair only — someone else cannot lock a user out
  from another IP. Unknown user, wrong password and locked all return the same 401
  ``"Invalid credentials"``; while locked the password is not evaluated at all.
* Account state is only disclosed AFTER a correct password: pending (unverified) ->
  401 ``ACCOUNT_NOT_VERIFIED``; blocked/deleted -> "Account is not active"; expired.
* 2FA-enabled accounts get a challenge (``twoFactorRequired``) instead of tokens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from redis import Redis

from core.deps import ensure_user_can_authenticate
from core.errors import AuthenticationError
from core.redis import redis_key
from core.security import verify_password
from db import AnyOf, Condition, Op
from db.base import Repository
from service.auth.otp import digest
from service.auth.tokens import AuthResult, SessionService
from service.auth.two_factor import Challenge, TwoFactorService
from util.helper import censor_email

if TYPE_CHECKING:
    from core.config import Settings

INVALID_CREDENTIALS = "Invalid credentials"
ACCOUNT_NOT_VERIFIED = "ACCOUNT_NOT_VERIFIED"


class LoginAttempts:
    """Failed-login counter per (identifier, IP) in Redis (fixed window)."""

    def __init__(self, redis: Redis, settings: Settings) -> None:
        self.redis = redis
        self.settings = settings

    def _key(self, identifier: str, ip: str) -> str:
        return redis_key(self.settings, "auth", "login-fail", digest(identifier.lower()), ip)

    def is_locked(self, identifier: str, ip: str) -> bool:
        value = self.redis.get(self._key(identifier, ip))
        return value is not None and int(value) >= self.settings.ACCOUNT_LOCK_MAX_ATTEMPTS

    def record_failure(self, identifier: str, ip: str) -> int:
        key = self._key(identifier, ip)
        pipe = self.redis.pipeline(transaction=True)
        pipe.set(key, 0, ex=self.settings.ACCOUNT_LOCK_SECONDS, nx=True)
        pipe.incr(key)
        _, count = pipe.execute()
        return int(count)

    def reset(self, identifier: str, ip: str) -> None:
        self.redis.delete(self._key(identifier, ip))


def find_by_identifier(users: Repository, identifier: str) -> dict[str, Any] | None:
    ident = identifier.strip()
    if "@" in ident:
        return users.find_one({"email": ident.lower()})
    return users.find_one(AnyOf(Condition("username", Op.EQ, ident), Condition("email", Op.EQ, ident.lower())))


def check_account_state(user: dict[str, Any]) -> dict[str, Any]:
    """Status checks after the password was verified (safe to be specific here)."""
    if user.get("status") == "pending":
        raise AuthenticationError("Email address has not been verified yet", error_code=ACCOUNT_NOT_VERIFIED)
    return ensure_user_can_authenticate(user)


class LoginService:
    def __init__(
        self,
        users: Repository,
        attempts: LoginAttempts,
        sessions: SessionService,
        two_factor: TwoFactorService,
    ) -> None:
        self.users = users
        self.attempts = attempts
        self.sessions = sessions
        self.two_factor = two_factor

    def authenticate(self, identifier: str, password: str, ip: str) -> dict[str, Any]:
        """Verify credentials; returns the active user or raises the generic 401."""
        if self.attempts.is_locked(identifier, ip):
            verify_password(password, None)  # same cost as a real check
            raise AuthenticationError(INVALID_CREDENTIALS)
        user = find_by_identifier(self.users, identifier)
        if not verify_password(password, user.get("password_hash") if user else None) or user is None:
            failures = self.attempts.record_failure(identifier, ip)
            if failures == self.attempts.settings.ACCOUNT_LOCK_MAX_ATTEMPTS:
                logger.warning("Login locked for identifier hash {} from {}", digest(identifier.lower())[:12], ip)
            raise AuthenticationError(INVALID_CREDENTIALS)
        self.attempts.reset(identifier, ip)
        return check_account_state(user)

    def login(self, identifier: str, password: str, ip: str) -> AuthResult | Challenge:
        user = self.authenticate(identifier, password, ip)
        if self.two_factor.is_required(user):
            logger.debug("2FA challenge issued for {}", censor_email(user.get("email")))
            return self.two_factor.create_challenge(user)
        return self.sessions.start(user)

    def complete_two_factor(self, session_token: str, code: str) -> AuthResult:
        user = self.two_factor.verify_challenge(session_token, code)
        return self.sessions.start(check_account_state(user))

    def continue_after_sso(self, user: dict[str, Any]) -> AuthResult | Challenge:
        """Identity proven by an external provider (Google): same 2FA gate as password login."""
        user = check_account_state(user)
        if self.two_factor.is_required(user):
            return self.two_factor.create_challenge(user)
        return self.sessions.start(user)
