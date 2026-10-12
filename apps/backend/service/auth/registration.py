"""Self-service registration (local provider) and email-link verification.

Registration:
* The password is policy-checked and bcrypt-hashed BEFORE anything is stored; the plain
  password never reaches Redis or the database.
* The account is stored with ``status="pending"`` (cannot log in) and a 6-digit code is
  emailed (purpose ``register``). ``/register/verify`` activates it.
* Re-registering a still-pending email updates the pending record (latest submission
  wins — the email owner always ends up with the data of the registration they verify
  from the most recent email) and re-sends a code (subject to the resend cooldown).
* An email that already belongs to a non-pending account gets the same generic 201
  response; the owner receives an "account exists" notice instead (no enumeration).
* Username / phone held by a *stale* pending account (older than
  ``BE_REGISTRATION_PENDING_TTL``) are released; otherwise 409.

Email verification link (for accounts created by an admin / Google etc.):
``/auth/verify-email/request`` (authenticated) emails ``<PUBLIC_WEB_URL><EMAIL_VERIFY_PATH>?token=…``;
``/auth/verify-email`` consumes the token (stored hashed, single use, ``BE_EMAIL_VERIFY_TTL``).
"""

from __future__ import annotations

import json
import secrets
from datetime import timedelta
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from loguru import logger
from redis import Redis

from core.errors import BadRequestError, ConflictError, PermissionDeniedError, RateLimitedError
from core.redis import redis_key
from core.security import hash_password, validate_password_policy
from db.base import Repository
from dto.auth import RegisterRequest
from service.auth.otp import OtpService, digest
from util.email import Mailer
from util.helper import as_utc, censor_email, new_id, utc_now

if TYPE_CHECKING:
    from core.config import Settings

REGISTER_PURPOSE = "register"
INVALID_CODE = "Invalid or expired code"
REGISTER_MESSAGE = "If the details are valid, a verification code has been sent to your email address"
RESEND_MESSAGE = "If a pending account exists for this email, a new verification code has been sent"


def web_url(settings: Settings, path: str) -> str:
    """Absolute link into the web app: ``<PUBLIC_WEB_URL><path>``."""
    return settings.PUBLIC_WEB_URL.rstrip("/") + "/" + path.lstrip("/")


class RegistrationService:
    def __init__(
        self,
        users: Repository,
        permissions: Repository,
        otp: OtpService,
        mailer: Mailer,
        settings: Settings,
    ) -> None:
        self.users = users
        self.permissions = permissions
        self.otp = otp
        self.mailer = mailer
        self.settings = settings

    # ------------------------------------------------------------ helpers
    def _is_stale_pending(self, user: dict[str, Any]) -> bool:
        if user.get("status") != "pending":
            return False
        updated = as_utc(user.get("updated_at") or user.get("created_at"))
        return updated is not None and updated < utc_now() - timedelta(seconds=self.settings.REGISTRATION_PENDING_TTL)

    def _claim(self, field: str, value: str | None, own_id: str | None, message: str) -> None:
        """Ensure ``field=value`` is free (releasing it from a stale pending account)."""
        if not value:
            return
        other = self.users.find_one({field: value})
        if other is None or other["id"] == own_id:
            return
        if self._is_stale_pending(other):
            logger.info("Removing stale pending account {} to release its {}", other["id"], field)
            self.users.delete(other["id"])
            return
        raise ConflictError(message, details=[{"field": field, "message": message}])

    def _default_permission_id(self) -> str | None:
        permission = self.permissions.find_one({"alias": self.settings.DEFAULT_PERMISSION_ALIAS})
        return permission["id"] if permission else None

    def _send_code(self, user: dict[str, Any]) -> None:
        code = self.otp.issue(REGISTER_PURPOSE, user["email"])
        if code is None:  # resend cooldown: the previous code is still valid
            return
        self.mailer.send(
            "register_otp",
            user["email"],
            fullname=user.get("fullname") or user["username"],
            username=user["username"],
            code=code,
            ttl_minutes=self.otp.ttl_minutes,
        )

    # --------------------------------------------------------------- flows
    def register(self, dto: RegisterRequest) -> str:
        if not self.settings.REGISTRATION_ENABLED:
            raise PermissionDeniedError("Registration is disabled")
        validate_password_policy(dto.password, self.settings)
        self.mailer.require_available()
        password_hash = hash_password(dto.password)  # hashed before any lookup/storage
        email = dto.email

        existing = self.users.find_one({"email": email})
        if existing is not None and existing.get("status") != "pending":
            if self.otp.start_cooldown("account-exists", email):
                self.mailer.send(
                    "account_exists",
                    email,
                    fullname=existing.get("fullname") or existing.get("username") or "",
                    login_url=web_url(self.settings, self.settings.WEB_LOGIN_PATH),
                )
            logger.info("Registration attempt for existing account {}", censor_email(email))
            return REGISTER_MESSAGE

        own_id = existing["id"] if existing else None
        self._claim("username", dto.username, own_id, "Username is already taken")
        self._claim("phone", dto.phone, own_id, "Phone number is already registered")
        fields = {
            "username": dto.username,
            "fullname": dto.fullname,
            "phone": dto.phone,
            "password_hash": password_hash,
        }
        if existing is not None:
            user = self.users.update(existing["id"], fields) or {**existing, **fields}
        else:
            user_id = new_id()
            user = self.users.insert(
                {
                    "id": user_id,
                    **fields,
                    "email": email,
                    "status": "pending",
                    "email_verified": False,
                    "auth_provider": "local",
                    "permission_id": self._default_permission_id(),
                    "created_by": user_id,
                }
            )
            logger.info("Pending account created for {}", censor_email(email))
        self._send_code(user)
        return REGISTER_MESSAGE

    def resend(self, email: str) -> str:
        self.mailer.require_available()
        user = self.users.find_one({"email": email})
        if user is not None and user.get("status") == "pending":
            self._send_code(user)
        return RESEND_MESSAGE

    def verify(self, email: str, code: str) -> dict[str, Any]:
        if not self.otp.verify(REGISTER_PURPOSE, email, code):
            raise BadRequestError(INVALID_CODE)
        user = self.users.find_one({"email": email})
        if user is None or user.get("status") != "pending":
            raise BadRequestError(INVALID_CODE)
        activated = self.users.update(user["id"], {"status": "active", "email_verified": True})
        logger.info("Account activated for {}", censor_email(email))
        return activated or user


class EmailVerificationService:
    def __init__(self, users: Repository, redis: Redis, otp: OtpService, mailer: Mailer, settings: Settings) -> None:
        self.users = users
        self.redis = redis
        self.otp = otp
        self.mailer = mailer
        self.settings = settings

    def _key(self, token: str) -> str:
        return redis_key(self.settings, "auth", "verify-email", digest(token))

    def request(self, user: dict[str, Any]) -> str:
        if user.get("email_verified"):
            return "Email address is already verified"
        self.mailer.require_available()
        if not self.otp.start_cooldown("verify-email", user["id"]):
            raise RateLimitedError(
                "Please wait before requesting another email",
                retry_after=self.otp.cooldown_remaining("verify-email", user["id"]),
            )
        token = secrets.token_urlsafe(32)
        payload = json.dumps({"user_id": user["id"], "email": user["email"]})
        self.redis.set(self._key(token), payload, ex=self.settings.EMAIL_VERIFY_TTL)
        self.mailer.send(
            "verify_email_link",
            user["email"],
            fullname=user.get("fullname") or user.get("username") or "",
            link=f"{web_url(self.settings, self.settings.EMAIL_VERIFY_PATH)}?{urlencode({'token': token})}",
            ttl_hours=max(self.settings.EMAIL_VERIFY_TTL // 3600, 1),
        )
        return "A verification link has been sent to your email address"

    def confirm(self, token: str) -> dict[str, Any]:
        raw = self.redis.getdel(self._key(token))
        if not raw:
            raise BadRequestError("Invalid or expired link")
        data = json.loads(raw)
        user = self.users.get_by_id(data.get("user_id", ""))
        if user is None or user.get("email") != data.get("email"):
            raise BadRequestError("Invalid or expired link")
        updated = self.users.update(user["id"], {"email_verified": True}) or user
        logger.info("Email verified for {}", censor_email(user.get("email")))
        return updated
