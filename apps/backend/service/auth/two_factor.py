"""Two-factor authentication: login challenges + setup/enable/disable.

Login challenge (password already verified, no tokens issued yet):
  Redis hash ``auth:2fa:challenge:<sha256(sessionToken)>`` = ``{user_id, method, attempts, otp_hash?}``
  with TTL ``BE_TWO_FACTOR_SESSION_TTL``; at most ``BE_OTP_MAX_ATTEMPTS`` guesses, then the
  challenge is burnt (the user must log in again). ``sessionToken`` is 256 bits of randomness
  and only its hash is stored.

Methods:
  * ``email`` — a 6-digit code (``secrets``) emailed to the account; only its HMAC (bound to
    the challenge) is stored; ``/2fa/resend`` replaces it (cooldown ``BE_OTP_RESEND_COOLDOWN``).
  * ``totp`` — RFC 6238 (pyotp), ±1 step tolerance, each time step usable once per user
    (replay protection). The per-user secret is stored encrypted with ``BE_DATA_ENCRYPTION_KEY``
    (``core.security.encrypt_secret``; plaintext only when no key is configured).

Setup: ``/2fa/setup`` stores a pending configuration in Redis (``auth:2fa:setup:<user_id>``),
``/2fa/enable`` confirms it with a code; nothing is written to the user until then.
"""

from __future__ import annotations

import base64
import hmac
import io
import secrets
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pyotp
from loguru import logger
from redis import Redis

from core.errors import AuthenticationError, BadRequestError, ConflictError, RateLimitedError
from core.redis import redis_key
from core.security import decrypt_secret, encrypt_secret, generate_otp, hash_otp, verify_otp, verify_password
from db.base import Repository
from service.auth.otp import ATTEMPTS_FIELD, attempt, digest
from util.email import Mailer
from util.helper import censor_email

if TYPE_CHECKING:
    from core.config import Settings

EMAIL = "email"
TOTP = "totp"
LOGIN_PURPOSE = "2fa-login"
SETUP_PURPOSE = "2fa-setup"
TOTP_VALID_WINDOW = 1  # accept the previous/next 30 s step as well
INVALID_CODE = "Invalid or expired code"


@dataclass(frozen=True)
class Challenge:
    session_token: str
    method: str


@dataclass(frozen=True)
class SetupResult:
    method: str
    message: str
    otpauth_uri: str | None = None
    qr_image_base64: str | None = None
    secret: str | None = None


def qr_png_base64(data: str) -> str | None:
    """PNG QR code (base64) for an otpauth URI; ``None`` if qrcode/Pillow are unavailable."""
    try:
        import qrcode  # optional heavy dependency, imported lazily
    except ImportError:  # pragma: no cover - qrcode is in requirements.txt
        return None
    image = qrcode.make(data, box_size=6, border=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class TwoFactorService:
    def __init__(self, users: Repository, redis: Redis, mailer: Mailer, settings: Settings) -> None:
        self.users = users
        self.redis = redis
        self.mailer = mailer
        self.settings = settings

    # ------------------------------------------------------------ keys
    def _challenge_key(self, session_token: str) -> str:
        return redis_key(self.settings, "auth", "2fa", "challenge", digest(session_token))

    def _setup_key(self, user_id: str) -> str:
        return redis_key(self.settings, "auth", "2fa", "setup", user_id)

    def _cooldown_key(self, scope: str, ident: str) -> str:
        return redis_key(self.settings, "auth", "2fa", "cooldown", scope, ident)

    def _start_cooldown(self, scope: str, ident: str) -> None:
        cooldown = self.settings.OTP_RESEND_COOLDOWN
        if cooldown > 0 and not self.redis.set(self._cooldown_key(scope, ident), "1", ex=cooldown, nx=True):
            ttl = self.redis.ttl(self._cooldown_key(scope, ident))
            raise RateLimitedError("Please wait before requesting a new code", retry_after=max(int(ttl or 1), 1))

    def _otp_hash(self, code: str, subject: str, purpose: str) -> str:
        return hash_otp(code, self.settings, purpose=purpose, subject=subject)

    def _email_code(self, user: dict[str, Any], template: str, subject: str, purpose: str) -> str:
        """Generate a code, send it in the background and return its stored hash."""
        code = generate_otp(self.settings.OTP_LENGTH)
        self.mailer.send(
            template,
            user["email"],
            fullname=user.get("fullname") or user.get("username") or "",
            code=code,
            ttl_minutes=max(self.settings.OTP_TTL // 60, 1),
        )
        return self._otp_hash(code, subject, purpose)

    # ------------------------------------------------------------ TOTP
    def _totp_matches(self, secret: str, code: str, user_id: str) -> bool:
        totp = pyotp.TOTP(secret)
        now = time.time()
        for offset in range(-TOTP_VALID_WINDOW, TOTP_VALID_WINDOW + 1):
            counter = int(now // totp.interval) + offset
            if hmac.compare_digest(totp.generate_otp(counter), code):
                used = redis_key(self.settings, "auth", "2fa", "totp-used", user_id, str(counter))
                ttl = totp.interval * (2 * TOTP_VALID_WINDOW + 2)
                if self.redis.set(used, "1", ex=ttl, nx=True):
                    return True
                logger.warning("Replayed TOTP code rejected for user {}", user_id)
                return False
        return False

    def _user_totp_secret(self, user: dict[str, Any]) -> str | None:
        return decrypt_secret(user.get("two_factor_secret"), self.settings)

    # ------------------------------------------------------- login flow
    def is_required(self, user: dict[str, Any]) -> bool:
        return bool(user.get("two_factor_enabled")) and user.get("two_factor_method") in (EMAIL, TOTP)

    def create_challenge(self, user: dict[str, Any]) -> Challenge:
        method = str(user.get("two_factor_method"))
        if method == EMAIL:
            self.mailer.require_available()
        session_token = secrets.token_urlsafe(32)
        key = self._challenge_key(session_token)
        fields: dict[str, Any] = {"user_id": user["id"], "method": method, ATTEMPTS_FIELD: 0}
        if method == EMAIL:
            fields["otp_hash"] = self._email_code(user, "two_factor_login_otp", digest(session_token), LOGIN_PURPOSE)
            self.redis.set(
                self._cooldown_key("login", digest(session_token)),
                "1",
                ex=max(self.settings.OTP_RESEND_COOLDOWN, 1),
            )
        pipe = self.redis.pipeline(transaction=True)
        pipe.hset(key, mapping=fields)
        pipe.expire(key, self.settings.TWO_FACTOR_SESSION_TTL)
        pipe.execute()
        return Challenge(session_token=session_token, method=method)

    def verify_challenge(self, session_token: str, code: str) -> dict[str, Any]:
        """Return the user when ``code`` satisfies the challenge (challenge consumed)."""
        subject = digest(session_token)
        resolved: dict[str, Any] = {}

        def check(data: dict[str, str]) -> bool:
            method = data.get("method")
            if method == EMAIL:
                return verify_otp(code, data.get("otp_hash"), self.settings, purpose=LOGIN_PURPOSE, subject=subject)
            if method == TOTP:
                user = self.users.get_by_id(data.get("user_id", ""))
                secret = self._user_totp_secret(user) if user else None
                if not secret:
                    return False
                resolved["user"] = user
                return self._totp_matches(secret, code, user["id"])  # type: ignore[index]
            return False

        data = attempt(
            self.redis,
            self._challenge_key(session_token),
            check,
            max_attempts=self.settings.OTP_MAX_ATTEMPTS,
            consume=True,
        )
        if data is None:
            raise AuthenticationError(INVALID_CODE)
        user = resolved.get("user") or self.users.get_by_id(data["user_id"])
        if user is None or not self.is_required(user) or user.get("two_factor_method") != data.get("method"):
            raise AuthenticationError(INVALID_CODE)
        return user

    def resend_challenge(self, session_token: str) -> None:
        key = self._challenge_key(session_token)
        data = self.redis.hgetall(key)
        if not data:
            raise AuthenticationError("Two-factor session has expired, please sign in again")
        if data.get("method") != EMAIL:
            raise BadRequestError("Codes can only be resent for the email method")
        user = self.users.get_by_id(data.get("user_id", ""))
        if user is None:
            raise AuthenticationError("Two-factor session has expired, please sign in again")
        self.mailer.require_available()
        subject = digest(session_token)
        self._start_cooldown("login", subject)
        otp_hash = self._email_code(user, "two_factor_login_otp", subject, LOGIN_PURPOSE)
        # Only replace the code if the challenge still exists (never resurrect an expired one).
        if self.redis.exists(key):
            self.redis.hset(key, "otp_hash", otp_hash)

    # ---------------------------------------------------- setup/enable
    def setup(self, user: dict[str, Any], method: str) -> SetupResult:
        if user.get("two_factor_enabled"):
            raise ConflictError("Two-factor authentication is already enabled; disable it first")
        key = self._setup_key(user["id"])
        fields: dict[str, Any] = {"method": method, ATTEMPTS_FIELD: 0}
        if method == TOTP:
            secret = pyotp.random_base32()
            label = user.get("email") or user.get("username") or user["id"]
            uri = pyotp.TOTP(secret).provisioning_uri(name=label, issuer_name=self.settings.totp_issuer)
            fields["secret"] = encrypt_secret(secret, self.settings) or secret
            result = SetupResult(
                method=TOTP,
                message="Scan the QR code with your authenticator app, then confirm with a code",
                otpauth_uri=uri,
                qr_image_base64=qr_png_base64(uri),
                secret=secret,
            )
        else:
            self.mailer.require_available()
            self._start_cooldown("setup", user["id"])
            fields["otp_hash"] = self._email_code(user, "two_factor_setup_otp", user["id"], SETUP_PURPOSE)
            result = SetupResult(method=EMAIL, message="A confirmation code has been sent to your email")
        pipe = self.redis.pipeline(transaction=True)
        pipe.delete(key)
        pipe.hset(key, mapping=fields)
        pipe.expire(key, max(self.settings.OTP_TTL, 600))
        pipe.execute()
        return result

    def enable(self, user: dict[str, Any], code: str) -> dict[str, Any]:
        if user.get("two_factor_enabled"):
            raise ConflictError("Two-factor authentication is already enabled")
        pending: dict[str, str] = {}

        def check(data: dict[str, str]) -> bool:
            if data.get("method") == TOTP:
                secret = decrypt_secret(data.get("secret"), self.settings)
                pending["secret"] = secret or ""
                return bool(secret) and self._totp_matches(secret, code, user["id"])  # type: ignore[arg-type]
            return verify_otp(code, data.get("otp_hash"), self.settings, purpose=SETUP_PURPOSE, subject=user["id"])

        data = attempt(
            self.redis,
            self._setup_key(user["id"]),
            check,
            max_attempts=self.settings.OTP_MAX_ATTEMPTS,
            consume=True,
        )
        if data is None:
            raise BadRequestError(INVALID_CODE)
        method = data["method"]
        changes: dict[str, Any] = {
            "two_factor_enabled": True,
            "two_factor_method": method,
            "two_factor_secret": encrypt_secret(pending["secret"], self.settings) if method == TOTP else None,
        }
        updated = self.users.update(user["id"], changes) or {**user, **changes}
        logger.info("Two-factor ({}) enabled for {}", method, censor_email(user.get("email")))
        return updated

    def disable(self, user: dict[str, Any], password: str) -> dict[str, Any]:
        # 400 (not 401): the caller IS authenticated; a 401 would trigger client token refresh.
        if not verify_password(password, user.get("password_hash")):
            raise BadRequestError("Password is incorrect")
        self.redis.delete(self._setup_key(user["id"]))
        changes = {"two_factor_enabled": False, "two_factor_method": None, "two_factor_secret": None}
        updated = self.users.update(user["id"], changes) or {**user, **changes}
        logger.info("Two-factor disabled for {}", censor_email(user.get("email")))
        return updated
