"""Security primitives: passwords, JWTs, revocation, sessions, cookies, OTP hashing,
internal-token check, secrets-at-rest encryption and Supabase JWT verification.

Everything is sync (call from ``def`` routes/services, which run in the threadpool).

Token model (local provider)
----------------------------
* Claims: ``sub`` (user id), ``exp``, ``iat`` (float, sub-second), ``jti``, ``type``
  (``access`` | ``refresh`` | custom), ``iss`` (``BE_JWT_ISSUER``), ``sid`` (session id).
* One login = one session id (``sid``) shared by the access/refresh pair and kept
  across refresh rotations.
* :class:`TokenStore` (Redis) holds: revoked ``jti`` s (TTL = remaining lifetime),
  revoked sessions (whole ``sid`` family), a per-user "valid after" timestamp
  (revoke everything issued before, e.g. after a password change) and the active
  ``sid`` per user for single-session (``multi_login=false``) accounts.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import bcrypt
import jwt
from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from loguru import logger
from redis import Redis

from core.errors import AuthenticationError, ConfigurationError, ValidationError
from core.redis import redis_key
from util.crypto import build_fernet, decrypt_field, encrypt_field

if TYPE_CHECKING:
    from cryptography.fernet import Fernet

    from core.config import Settings

# ============================================================== passwords
BCRYPT_ROUNDS = 12
MAX_PASSWORD_BYTES = 72  # bcrypt hard limit; longer inputs are rejected, never truncated


@lru_cache(maxsize=1)
def _dummy_hash() -> bytes:
    return bcrypt.hashpw(secrets.token_bytes(16).hex().encode(), bcrypt.gensalt(BCRYPT_ROUNDS))


def validate_password_policy(password: str, settings: Settings, field_name: str = "password") -> None:
    """Raise a 422 ``ValidationError`` if ``password`` violates the policy."""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValidationError.for_field(
            field_name, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
        )
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValidationError.for_field(field_name, f"Password must be at most {MAX_PASSWORD_BYTES} bytes")


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        raise ValidationError.for_field("password", f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
    return bcrypt.hashpw(raw, bcrypt.gensalt(BCRYPT_ROUNDS)).decode("ascii")


def verify_password(password: str, password_hash: str | None) -> bool:
    """Constant-ish time verify. Unknown user (``None`` hash) still pays one bcrypt round."""
    raw = password.encode("utf-8")
    if password_hash and len(raw) <= MAX_PASSWORD_BYTES:
        try:
            return bcrypt.checkpw(raw, password_hash.encode("ascii"))
        except ValueError:
            logger.warning("Stored password hash is malformed")
    bcrypt.checkpw(b"timing-equaliser", _dummy_hash())
    return False


# ==================================================================== JWT
ACCESS = "access"
REFRESH = "refresh"
_REQUIRED_CLAIMS = ["exp", "iat", "sub", "jti", "type", "iss"]


def _ttl_for(token_type: str, settings: Settings) -> int:
    if token_type == ACCESS:
        return settings.JWT_ACCESS_TTL
    if token_type == REFRESH:
        return settings.JWT_REFRESH_TTL
    raise ValueError(f"No default TTL for token type {token_type!r}; pass ttl=")


@dataclass(frozen=True)
class IssuedToken:
    token: str
    jti: str
    type: str
    session_id: str | None
    issued_at: datetime
    expires_at: datetime

    @property
    def expires_in(self) -> int:
        return max(int((self.expires_at - datetime.now(timezone.utc)).total_seconds()), 0)


@dataclass(frozen=True)
class TokenPair:
    access: IssuedToken
    refresh: IssuedToken

    @property
    def session_id(self) -> str:
        return self.access.session_id or ""


@dataclass(frozen=True)
class TokenClaims:
    sub: str
    jti: str
    type: str
    issued_at: float
    expires_at: datetime
    session_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def remaining_seconds(self) -> int:
        return max(int((self.expires_at - datetime.now(timezone.utc)).total_seconds()), 0)


def new_session_id() -> str:
    return uuid.uuid4().hex


def create_token(
    subject: str,
    token_type: str,
    settings: Settings,
    *,
    session_id: str | None = None,
    ttl: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> IssuedToken:
    now = time.time()
    lifetime = ttl if ttl is not None else _ttl_for(token_type, settings)
    jti = uuid.uuid4().hex
    claims: dict[str, Any] = dict(extra_claims or {})
    claims.update(
        {
            "sub": str(subject),
            "iat": now,
            "exp": int(now + lifetime),
            "jti": jti,
            "type": token_type,
            "iss": settings.JWT_ISSUER,
        }
    )
    if session_id:
        claims["sid"] = session_id
    token = jwt.encode(claims, settings.JWT_SECRET.get_secret_value(), algorithm=settings.JWT_ALGORITHM)
    return IssuedToken(
        token=token,
        jti=jti,
        type=token_type,
        session_id=session_id,
        issued_at=datetime.fromtimestamp(now, tz=timezone.utc),
        expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc),
    )


def issue_token_pair(user_id: str, settings: Settings, *, session_id: str | None = None) -> TokenPair:
    """Access + refresh token sharing one session id (new one unless given)."""
    sid = session_id or new_session_id()
    return TokenPair(
        access=create_token(user_id, ACCESS, settings, session_id=sid),
        refresh=create_token(user_id, REFRESH, settings, session_id=sid),
    )


def decode_token(token: str, settings: Settings, expected_type: str) -> TokenClaims:
    """Verify signature, issuer, expiry, required claims AND ``type``. Raises ``AuthenticationError``."""
    if not token:
        raise AuthenticationError("Authentication required")
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            leeway=settings.JWT_LEEWAY,
            options={"require": _REQUIRED_CLAIMS},
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired") from None
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token") from None
    if payload.get("type") != expected_type:
        raise AuthenticationError("Invalid token type")
    if not isinstance(payload.get("sub"), str) or not isinstance(payload.get("jti"), str):
        raise AuthenticationError("Invalid token")
    return TokenClaims(
        sub=payload["sub"],
        jti=payload["jti"],
        type=payload["type"],
        issued_at=float(payload["iat"]),
        expires_at=datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc),
        session_id=payload.get("sid"),
        raw=payload,
    )


# ============================================================ revocation
class TokenStore:
    """Redis-backed revocation list, session families and single-session tracking."""

    def __init__(self, redis: Redis, settings: Settings) -> None:
        self.redis = redis
        self.settings = settings

    def _k(self, *parts: str) -> str:
        return redis_key(self.settings, "auth", *parts)

    # -- revocation
    def revoke_jti(self, jti: str, ttl_seconds: int) -> None:
        if ttl_seconds > 0:
            self.redis.set(self._k("revoked", "jti", jti), "1", ex=ttl_seconds)

    def revoke(self, claims: TokenClaims) -> None:
        """Revoke one token until it would have expired anyway."""
        self.revoke_jti(claims.jti, claims.remaining_seconds + self.settings.JWT_LEEWAY)

    def revoke_session(self, session_id: str) -> None:
        """Revoke every token of a login session (access + all rotated refresh tokens)."""
        ttl = self.settings.JWT_REFRESH_TTL + self.settings.JWT_LEEWAY
        self.redis.set(self._k("revoked", "sid", session_id), "1", ex=ttl)

    def revoke_all_for_user(self, user_id: str) -> None:
        """Invalidate every token issued to ``user_id`` before now (password change/reset, block)."""
        ttl = self.settings.JWT_REFRESH_TTL + self.settings.JWT_LEEWAY
        self.redis.set(self._k("valid_after", user_id), repr(time.time()), ex=ttl)
        self.redis.delete(self._k("active_sid", user_id))

    def _session_revoked(self, claims: TokenClaims, sid_flag: str | None, valid_after: str | None) -> bool:
        if claims.session_id and sid_flag:
            return True
        return bool(valid_after) and claims.issued_at < float(valid_after)  # type: ignore[arg-type]

    def is_revoked(self, claims: TokenClaims) -> bool:
        """Token revoked individually, via its session, or by ``revoke_all_for_user``."""
        jti_flag, sid_flag, valid_after = self.redis.mget(
            [
                self._k("revoked", "jti", claims.jti),
                self._k("revoked", "sid", claims.session_id or "-"),
                self._k("valid_after", claims.sub),
            ]
        )
        return bool(jti_flag) or self._session_revoked(claims, sid_flag, valid_after)

    def is_session_revoked(self, claims: TokenClaims) -> bool:
        """Session-level revocation only (ignores the token's own jti)."""
        sid_flag, valid_after = self.redis.mget(
            [self._k("revoked", "sid", claims.session_id or "-"), self._k("valid_after", claims.sub)]
        )
        return self._session_revoked(claims, sid_flag, valid_after)

    # -- refresh rotation
    def consume_refresh(self, claims: TokenClaims) -> bool:
        """Atomically mark a refresh token as used. ``False`` = reuse (session is revoked)."""
        ttl = max(claims.remaining_seconds + self.settings.JWT_LEEWAY, 1)
        first_use = self.redis.set(self._k("revoked", "jti", claims.jti), "1", ex=ttl, nx=True)
        if first_use:
            return True
        if claims.session_id:
            logger.warning("Refresh token reuse detected; revoking session family for user {}", claims.sub)
            self.revoke_session(claims.session_id)
        return False

    # -- single session (multi_login = false)
    def set_active_session(self, user_id: str, session_id: str) -> None:
        self.redis.set(self._k("active_sid", user_id), session_id, ex=self.settings.JWT_REFRESH_TTL)

    def get_active_session(self, user_id: str) -> str | None:
        value = self.redis.get(self._k("active_sid", user_id))
        return str(value) if value else None

    def clear_active_session(self, user_id: str, session_id: str | None = None) -> None:
        key = self._k("active_sid", user_id)
        if session_id is None or self.redis.get(key) == session_id:
            self.redis.delete(key)

    def is_session_current(self, user_id: str, session_id: str | None) -> bool:
        active = self.get_active_session(user_id)
        return active is not None and session_id is not None and hmac.compare_digest(active, session_id)


def rotate_refresh_token(claims: TokenClaims, store: TokenStore, settings: Settings) -> TokenPair:
    """Validate-and-rotate a decoded refresh token; returns the new pair (same session id).

    The caller must still check the user is active (and re-register the active
    session for single-session users via ``store.set_active_session``).
    """
    if claims.type != REFRESH:
        raise AuthenticationError("Invalid token type")
    if store.is_session_revoked(claims):
        raise AuthenticationError("Session has been revoked")
    # A used (or logged-out) refresh token presented again = reuse -> whole family revoked.
    if not store.consume_refresh(claims):
        raise AuthenticationError("Refresh token has already been used")
    return issue_token_pair(claims.sub, settings, session_id=claims.session_id)


# ================================================================ cookies
ACCESS_COOKIE = "token"
REFRESH_COOKIE = "refresh_token"


def set_auth_cookies(response: Response, pair: TokenPair, settings: Settings) -> None:
    common: dict[str, Any] = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "domain": settings.COOKIE_DOMAIN,
    }
    response.set_cookie(ACCESS_COOKIE, pair.access.token, max_age=settings.JWT_ACCESS_TTL, path="/", **common)
    response.set_cookie(
        REFRESH_COOKIE,
        pair.refresh.token,
        max_age=settings.JWT_REFRESH_TTL,
        path=settings.COOKIE_REFRESH_PATH,
        **common,
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    common: dict[str, Any] = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "domain": settings.COOKIE_DOMAIN,
    }
    response.delete_cookie(ACCESS_COOKIE, path="/", **common)
    response.delete_cookie(REFRESH_COOKIE, path=settings.COOKIE_REFRESH_PATH, **common)


def bearer_token(request: Request) -> str | None:
    scheme, credentials = get_authorization_scheme_param(request.headers.get("Authorization"))
    if scheme.lower() == "bearer" and credentials:
        return credentials
    return None


def access_token_from_request(request: Request) -> str | None:
    """``Authorization: Bearer`` first, then the ``token`` cookie."""
    return bearer_token(request) or request.cookies.get(ACCESS_COOKIE) or None


def refresh_token_from_request(request: Request) -> str | None:
    """``Authorization: Bearer <refresh>`` first, then the ``refresh_token`` cookie."""
    return bearer_token(request) or request.cookies.get(REFRESH_COOKIE) or None


# ======================================================== internal token
INTERNAL_TOKEN_HEADER = "X-Internal-Token"  # noqa: S105  # header name


def verify_internal_token(provided: str | None, settings: Settings) -> bool:
    expected = settings.INTERNAL_TOKEN
    if expected is None or not provided:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.get_secret_value().encode("utf-8"))


# ===================================================================== OTP
def generate_otp(length: int = 6) -> str:
    """Cryptographically random numeric code."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp(otp: str, settings: Settings, *, purpose: str, subject: str) -> str:
    """Keyed hash binding the code to (purpose, subject) — store this, never the code."""
    message = f"{purpose}:{subject.lower()}:{otp}".encode()
    return hmac.new(settings.JWT_SECRET.get_secret_value().encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_otp(otp: str, stored_hash: str | None, settings: Settings, *, purpose: str, subject: str) -> bool:
    if not stored_hash or not otp:
        return False
    return hmac.compare_digest(hash_otp(otp, settings, purpose=purpose, subject=subject), stored_hash)


# ==================================================== secrets at rest
@lru_cache(maxsize=4)
def _fernet_for(key: str) -> Fernet:
    return build_fernet(key)


def field_cipher(settings: Settings) -> Fernet | None:
    if settings.DATA_ENCRYPTION_KEY is None:
        return None
    return _fernet_for(settings.DATA_ENCRYPTION_KEY.get_secret_value())


def encrypt_secret(value: str | None, settings: Settings) -> str | None:
    """Encrypt e.g. a TOTP secret before storing it (no-op if no key configured)."""
    return encrypt_field(field_cipher(settings), value)


def decrypt_secret(value: str | None, settings: Settings) -> str | None:
    return decrypt_field(field_cipher(settings), value)


# ============================================== Supabase JWT verification
class SupabaseTokenVerifier:
    """Verifies Supabase-issued access tokens (JWKS if configured, else HS256 secret)."""

    ASYMMETRIC_ALGORITHMS = ("RS256", "ES256")

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jwks: jwt.PyJWKClient | None = None
        if settings.SUPABASE_JWKS_URL:
            self._jwks = jwt.PyJWKClient(settings.SUPABASE_JWKS_URL, cache_keys=True, lifespan=3600, timeout=5)
        elif settings.SUPABASE_JWT_SECRET is None:
            raise ConfigurationError("Supabase auth requires BE_SUPABASE_JWKS_URL or BE_SUPABASE_JWT_SECRET")

    def verify(self, token: str) -> dict[str, Any]:
        settings = self.settings
        try:
            if self._jwks is not None:
                key: Any = self._jwks.get_signing_key_from_jwt(token).key
                algorithms = list(self.ASYMMETRIC_ALGORITHMS)
            elif settings.SUPABASE_JWT_SECRET is not None:
                key = settings.SUPABASE_JWT_SECRET.get_secret_value()
                algorithms = ["HS256"]
            else:
                raise ConfigurationError("Supabase auth is not configured")
            options: dict[str, Any] = {"require": ["exp", "sub"]}
            kwargs: dict[str, Any] = {}
            if settings.SUPABASE_JWT_ISSUER:
                kwargs["issuer"] = settings.SUPABASE_JWT_ISSUER
            return jwt.decode(
                token,
                key,
                algorithms=algorithms,
                audience=settings.SUPABASE_JWT_AUDIENCE,
                leeway=settings.JWT_LEEWAY,
                options=options,
                **kwargs,
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired") from None
        except jwt.PyJWKClientError as exc:
            logger.warning("Supabase JWKS lookup failed: {}", type(exc).__name__)
            raise AuthenticationError("Invalid token") from None
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token") from None
