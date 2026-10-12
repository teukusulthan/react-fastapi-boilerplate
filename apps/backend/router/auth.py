"""Auth endpoints (CONTRACT "Auth API").

Exported routers (wired by the registry in ``router/__init__.py``):

* ``router``        — always mounted: ``GET /auth/me``, ``POST /auth/logout``.
* ``local_router``  — ``BE_AUTH_PROVIDER=local`` only: login, refresh, 2FA, register,
  forgot/change password, email verification.
* ``google_router`` — local auth AND ``BE_GOOGLE_CLIENT_ID``/``SECRET`` set: ``POST /auth/google/callback``.

Successful authentication (login, 2FA verify, refresh, change-password, Google) always
returns the same body ``{twoFactorRequired: false, user: UserProfile, auth: {accessToken,
refreshToken, expiresAt}}`` and sets the httpOnly ``token`` / ``refresh_token`` cookies.
All public endpoints are rate limited per client IP (``BE_RATE_LIMIT_AUTH`` per
``BE_RATE_LIMIT_AUTH_WINDOW``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from core.deps import CurrentUserDep, GroupsRepo, PermissionsRepo, SettingsDep
from core.rate_limit import client_ip, rate_limit
from core.responses import ApiResponse, created, ok
from core.security import clear_auth_cookies, set_auth_cookies
from dto.auth import (
    ChangePasswordRequest,
    EmailOtpRequest,
    EmailRequest,
    GoogleCallbackRequest,
    LoginOutcome,
    LoginRequest,
    LoginResponse,
    OtpValidResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TwoFactorChallengeResponse,
    TwoFactorDisableRequest,
    TwoFactorEnableRequest,
    TwoFactorResendRequest,
    TwoFactorSetupRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    VerifyEmailRequest,
)
from dto.common import MessageData
from dto.user_profile import UserProfile
from service.auth.deps import (
    EmailVerificationServiceDep,
    GoogleClientDep,
    GoogleServiceDep,
    LoginServiceDep,
    PasswordServiceDep,
    RegistrationServiceDep,
    SessionServiceDep,
    TwoFactorServiceDep,
)
from service.auth.tokens import AuthResult
from service.auth.two_factor import Challenge
from service.user_profile import load_user_profile

router = APIRouter(prefix="/auth", tags=["auth"])
local_router = APIRouter(prefix="/auth", tags=["auth"])
google_router = APIRouter(prefix="/auth", tags=["auth"])


def _limited(name: str, factor: int = 1) -> list:
    """Per-IP rate limit dependency (``factor`` x the sensitive-endpoint budget)."""
    return [Depends(rate_limit(f"auth:{name}", limit=lambda s: s.RATE_LIMIT_AUTH * factor))]


def _authenticated(result: AuthResult, response: Response, settings: SettingsDep, message: str) -> ApiResponse:
    set_auth_cookies(response, result.pair, settings)
    return ok(result.to_response(), message)


def _outcome(result: AuthResult | Challenge, response: Response, settings: SettingsDep) -> ApiResponse:
    if isinstance(result, Challenge):
        challenge = TwoFactorChallengeResponse(session_token=result.session_token, method=result.method)
        return ok(challenge, "Two-factor authentication required")
    return _authenticated(result, response, settings, "Login successful")


# ================================================================ always
@router.get("/me", response_model=ApiResponse[UserProfile])
def me(user: CurrentUserDep, permissions: PermissionsRepo, groups: GroupsRepo):
    """Profile of the authenticated user (local JWT or Supabase JWT)."""
    return ok(load_user_profile(user.record or {"id": user.id}, permissions, groups))


@router.post("/logout", response_model=ApiResponse[MessageData])
def logout(request: Request, response: Response, settings: SettingsDep, sessions: SessionServiceDep):
    """Revoke the presented tokens (local provider) and clear auth cookies. Always 200."""
    if settings.AUTH_PROVIDER == "local":
        sessions.logout(request)
    clear_auth_cookies(response, settings)
    return ok(MessageData(message="Logged out"))


# ============================================================ local: login
@local_router.post("/login", response_model=ApiResponse[LoginOutcome], dependencies=_limited("login"))
def login(dto: LoginRequest, request: Request, response: Response, settings: SettingsDep, service: LoginServiceDep):
    result = service.login(dto.identifier, dto.password, client_ip(request, settings))
    return _outcome(result, response, settings)


@local_router.post("/refresh", response_model=ApiResponse[LoginResponse], dependencies=_limited("refresh", 6))
def refresh(request: Request, response: Response, settings: SettingsDep, sessions: SessionServiceDep):
    """Rotate the refresh token (``refresh_token`` cookie or ``Authorization: Bearer <refresh>``)."""
    return _authenticated(sessions.refresh(request), response, settings, "Token refreshed")


# ============================================================== local: 2FA
@local_router.post("/2fa/verify", response_model=ApiResponse[LoginResponse], dependencies=_limited("2fa-verify"))
def two_factor_verify(dto: TwoFactorVerifyRequest, response: Response, settings: SettingsDep, service: LoginServiceDep):
    return _authenticated(
        service.complete_two_factor(dto.session_token, dto.otp), response, settings, "Login successful"
    )


@local_router.post("/2fa/resend", response_model=ApiResponse[MessageData], dependencies=_limited("2fa-resend"))
def two_factor_resend(dto: TwoFactorResendRequest, service: TwoFactorServiceDep):
    service.resend_challenge(dto.session_token)
    return ok(MessageData(message="A new code has been sent"))


@local_router.post("/2fa/setup", response_model=ApiResponse[TwoFactorSetupResponse], dependencies=_limited("2fa-setup"))
def two_factor_setup(dto: TwoFactorSetupRequest, user: CurrentUserDep, service: TwoFactorServiceDep):
    result = service.setup(user.record or {}, dto.method)
    return ok(
        TwoFactorSetupResponse(
            method=result.method,
            message=result.message,
            otpauth_uri=result.otpauth_uri,
            qr_image_base64=result.qr_image_base64,
            secret=result.secret,
        )
    )


@local_router.post("/2fa/enable", response_model=ApiResponse[UserProfile], dependencies=_limited("2fa-enable"))
def two_factor_enable(
    dto: TwoFactorEnableRequest, user: CurrentUserDep, service: TwoFactorServiceDep, sessions: SessionServiceDep
):
    updated = service.enable(user.record or {}, dto.otp)
    return ok(sessions.profile(updated), "Two-factor authentication enabled")


@local_router.post("/2fa/disable", response_model=ApiResponse[UserProfile], dependencies=_limited("2fa-disable"))
def two_factor_disable(
    dto: TwoFactorDisableRequest, user: CurrentUserDep, service: TwoFactorServiceDep, sessions: SessionServiceDep
):
    updated = service.disable(user.record or {}, dto.password)
    return ok(sessions.profile(updated), "Two-factor authentication disabled")


# ========================================================= local: register
@local_router.post(
    "/register", status_code=201, response_model=ApiResponse[MessageData], dependencies=_limited("register")
)
def register(dto: RegisterRequest, service: RegistrationServiceDep):
    return created(MessageData(message=service.register(dto)))


@local_router.post(
    "/register/verify", response_model=ApiResponse[MessageData], dependencies=_limited("register-verify")
)
def register_verify(dto: EmailOtpRequest, service: RegistrationServiceDep):
    service.verify(dto.email, dto.otp)
    return ok(MessageData(message="Your account is verified; you can now sign in"))


@local_router.post(
    "/register/resend", response_model=ApiResponse[MessageData], dependencies=_limited("register-resend")
)
def register_resend(dto: EmailRequest, service: RegistrationServiceDep):
    return ok(MessageData(message=service.resend(dto.email)))


# ======================================================== local: passwords
@local_router.post(
    "/forgot-password/request", response_model=ApiResponse[MessageData], dependencies=_limited("forgot-request")
)
def forgot_password_request(dto: EmailRequest, service: PasswordServiceDep):
    return ok(MessageData(message=service.request_reset(dto.email)))


@local_router.post(
    "/forgot-password/verify", response_model=ApiResponse[OtpValidResponse], dependencies=_limited("forgot-verify")
)
def forgot_password_verify(dto: EmailOtpRequest, service: PasswordServiceDep):
    return ok(OtpValidResponse(valid=service.verify_reset_code(dto.email, dto.otp)))


@local_router.post(
    "/forgot-password/reset", response_model=ApiResponse[MessageData], dependencies=_limited("forgot-reset")
)
def forgot_password_reset(dto: ResetPasswordRequest, service: PasswordServiceDep):
    service.reset(dto.email, dto.otp, dto.new_password)
    return ok(MessageData(message="Your password has been reset; please sign in again"))


@local_router.post(
    "/change-password", response_model=ApiResponse[LoginResponse], dependencies=_limited("change-password")
)
def change_password(
    dto: ChangePasswordRequest,
    response: Response,
    user: CurrentUserDep,
    settings: SettingsDep,
    service: PasswordServiceDep,
):
    """Change the password; other sessions are revoked and the caller gets a fresh session."""
    result = service.change(user.record or {}, dto.current_password, dto.new_password)
    return _authenticated(result, response, settings, "Password changed")


# =================================================== local: email verification
@local_router.post(
    "/verify-email/request", response_model=ApiResponse[MessageData], dependencies=_limited("verify-email-request")
)
def verify_email_request(user: CurrentUserDep, service: EmailVerificationServiceDep):
    return ok(MessageData(message=service.request(user.record or {})))


@local_router.post("/verify-email", response_model=ApiResponse[MessageData], dependencies=_limited("verify-email"))
def verify_email(dto: VerifyEmailRequest, service: EmailVerificationServiceDep):
    service.confirm(dto.token)
    return ok(MessageData(message="Your email address is verified"))


# ================================================================== google
@google_router.post("/google/callback", response_model=ApiResponse[LoginOutcome], dependencies=_limited("google"))
def google_callback(
    dto: GoogleCallbackRequest,
    response: Response,
    settings: SettingsDep,
    client: GoogleClientDep,
    google: GoogleServiceDep,
    login_service: LoginServiceDep,
):
    """Exchange a Google authorization code; same result shapes as ``/auth/login``."""
    identity = client.authenticate(dto.code, dto.redirect_uri, dto.code_verifier)
    user = google.resolve_user(identity)
    return _outcome(login_service.continue_after_sso(user), response, settings)
