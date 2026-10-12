"""Forgot-password (email code) and change-password.

* ``request``: always the same generic answer; a code (purpose ``password-reset``) is sent
  only to active accounts, respecting the resend cooldown silently (no enumeration).
* ``verify``: checks the code without consuming it (counts as an attempt).
* ``reset``: policy check -> consume code -> new bcrypt hash -> every existing session of
  the user is revoked (``TokenStore.revoke_all_for_user``) -> notification email.
* ``change``: requires the current password; revokes all sessions, then issues a fresh
  session for the caller so the current client stays signed in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from core.errors import BadRequestError, ValidationError
from core.security import hash_password, validate_password_policy, verify_password
from db.base import Repository
from service.auth.otp import OtpService
from service.auth.tokens import AuthResult, SessionService
from util.email import Mailer
from util.helper import censor_email

if TYPE_CHECKING:
    from core.config import Settings

RESET_PURPOSE = "password-reset"
INVALID_CODE = "Invalid or expired code"
REQUEST_MESSAGE = "If an account exists for this email, a password reset code has been sent"


class PasswordService:
    def __init__(
        self,
        users: Repository,
        otp: OtpService,
        sessions: SessionService,
        mailer: Mailer,
        settings: Settings,
    ) -> None:
        self.users = users
        self.otp = otp
        self.sessions = sessions
        self.mailer = mailer
        self.settings = settings

    def _notify_changed(self, user: dict[str, Any]) -> None:
        self.mailer.send("password_changed", user["email"], fullname=user.get("fullname") or user.get("username") or "")

    # ------------------------------------------------------- forgot password
    def request_reset(self, email: str) -> str:
        self.mailer.require_available()  # before the lookup: the 503 never depends on existence
        user = self.users.find_one({"email": email})
        if user is not None and user.get("status") == "active":
            code = self.otp.issue(RESET_PURPOSE, email)
            if code is not None:
                self.mailer.send(
                    "password_reset_otp",
                    email,
                    fullname=user.get("fullname") or user.get("username") or "",
                    code=code,
                    ttl_minutes=self.otp.ttl_minutes,
                )
        return REQUEST_MESSAGE

    def verify_reset_code(self, email: str, code: str) -> bool:
        if not self.otp.verify(RESET_PURPOSE, email, code, consume=False):
            raise BadRequestError(INVALID_CODE)
        return True

    def reset(self, email: str, code: str, new_password: str) -> None:
        validate_password_policy(new_password, self.settings, field_name="newPassword")
        password_hash = hash_password(new_password)
        if not self.otp.verify(RESET_PURPOSE, email, code, consume=True):
            raise BadRequestError(INVALID_CODE)
        user = self.users.find_one({"email": email})
        if user is None or user.get("status") != "active":
            raise BadRequestError(INVALID_CODE)
        self.users.update(user["id"], {"password_hash": password_hash})
        self.sessions.revoke_all(user["id"])
        logger.info("Password reset for {}; all sessions revoked", censor_email(email))
        self._notify_changed(user)

    # ------------------------------------------------------- change password
    def change(self, user: dict[str, Any], current_password: str, new_password: str) -> AuthResult:
        # 400 (not 401): the caller is authenticated; a 401 would make clients refresh/log out.
        if not verify_password(current_password, user.get("password_hash")):
            raise BadRequestError(
                "Current password is incorrect",
                details=[{"field": "currentPassword", "message": "Current password is incorrect"}],
            )
        validate_password_policy(new_password, self.settings, field_name="newPassword")
        if new_password == current_password:
            raise ValidationError.for_field("newPassword", "New password must differ from the current password")
        self.users.update(user["id"], {"password_hash": hash_password(new_password)})
        self.sessions.revoke_all(user["id"])
        logger.info("Password changed for {}; other sessions revoked", censor_email(user.get("email")))
        if self.mailer.available:
            self._notify_changed(user)
        refreshed = self.users.get_by_id(user["id"]) or user
        return self.sessions.start(refreshed)
