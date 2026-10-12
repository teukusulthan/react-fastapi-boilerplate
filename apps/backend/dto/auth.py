"""Auth request/response DTOs (camelCase JSON, see CONTRACT "Auth API").

Validators are pure (no DB/Redis/HTTP). Password *policy* (min length from settings,
72-byte bcrypt limit) is enforced in the services so it follows ``BE_PASSWORD_MIN_LENGTH``.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import EmailStr, Field, field_validator

from dto.common import BaseSchema
from dto.user_profile import UserProfile

TwoFactorMethod = Literal["email", "totp"]

USERNAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{2,31}$"
OTP_PATTERN = r"^[0-9]{4,10}$"
_PHONE_CLEAN = re.compile(r"[\s().-]")
_PHONE_VALID = re.compile(r"^\+?[0-9]{6,15}$")

# Generous upper bounds: real limits are applied by the password policy (bytes <= 72).
PasswordStr = Annotated[str, Field(min_length=1, max_length=256)]
OtpStr = Annotated[str, Field(pattern=OTP_PATTERN, description="One-time code (digits)")]
SessionTokenStr = Annotated[str, Field(min_length=16, max_length=256)]


def _normalise_email(value: str) -> str:
    return value.strip().lower()


# ================================================================ requests
class LoginRequest(BaseSchema):
    identifier: str = Field(min_length=1, max_length=254, description="Email or username")
    password: PasswordStr

    @field_validator("identifier")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class TwoFactorVerifyRequest(BaseSchema):
    session_token: SessionTokenStr
    otp: OtpStr


class TwoFactorResendRequest(BaseSchema):
    session_token: SessionTokenStr


class TwoFactorSetupRequest(BaseSchema):
    method: TwoFactorMethod


class TwoFactorEnableRequest(BaseSchema):
    otp: OtpStr


class TwoFactorDisableRequest(BaseSchema):
    password: PasswordStr


class RegisterRequest(BaseSchema):
    username: str = Field(pattern=USERNAME_PATTERN, description="3-32 chars: letters, digits, '.', '_', '-'")
    fullname: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: PasswordStr

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _normalise_email(value)

    @field_validator("fullname")
    @classmethod
    def _fullname(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _PHONE_CLEAN.sub("", value)
        if not cleaned:
            return None
        if not _PHONE_VALID.match(cleaned):
            raise ValueError("must be a phone number (digits, optional leading +)")
        return cleaned


class EmailRequest(BaseSchema):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _normalise_email(value)


class EmailOtpRequest(EmailRequest):
    otp: OtpStr


class ResetPasswordRequest(EmailOtpRequest):
    new_password: PasswordStr


class ChangePasswordRequest(BaseSchema):
    current_password: PasswordStr
    new_password: PasswordStr


class VerifyEmailRequest(BaseSchema):
    token: str = Field(min_length=16, max_length=256)


class GoogleCallbackRequest(BaseSchema):
    code: str = Field(min_length=1, max_length=2048)
    redirect_uri: str = Field(min_length=1, max_length=2048)
    code_verifier: str | None = Field(default=None, min_length=43, max_length=128, description="PKCE verifier")


# =============================================================== responses
class AuthTokens(BaseSchema):
    access_token: str
    refresh_token: str
    expires_at: datetime = Field(description="Access-token expiry (ISO-8601, UTC)")


class LoginResponse(BaseSchema):
    """Successful login / 2FA verify / refresh / change-password: profile + token pair."""

    two_factor_required: Literal[False] = False
    user: UserProfile
    auth: AuthTokens


class TwoFactorChallengeResponse(BaseSchema):
    """Password accepted but a second factor is required (no tokens issued yet)."""

    two_factor_required: Literal[True] = True
    session_token: str
    method: TwoFactorMethod


LoginOutcome = LoginResponse | TwoFactorChallengeResponse


class TwoFactorSetupResponse(BaseSchema):
    method: TwoFactorMethod
    message: str
    # TOTP only: provisioning data for the authenticator app (pending until /2fa/enable).
    otpauth_uri: str | None = None
    qr_image_base64: str | None = Field(default=None, description="PNG, base64 (no data: prefix)")
    secret: str | None = None


class OtpValidResponse(BaseSchema):
    valid: bool
