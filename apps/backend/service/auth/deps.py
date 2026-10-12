"""FastAPI dependency providers for the auth services (built per request, no globals).

App-scoped singletons that are expensive to build (the email sender, the Google OAuth
client with its JWKS cache) live on ``app.state`` and are created lazily. Tests override
:func:`get_email_sender` / :func:`get_google_client` via ``app.dependency_overrides``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import BackgroundTasks, Depends, Request
from redis import Redis

from core.config import Settings
from core.deps import (
    get_app_settings,
    get_groups_repo,
    get_permissions_repo,
    get_redis,
    get_token_store,
    get_users_repo,
)
from core.security import TokenStore
from db.base import Repository
from service.auth.google import GoogleAuthService, GoogleOAuthClient
from service.auth.login import LoginAttempts, LoginService
from service.auth.otp import OtpService
from service.auth.password import PasswordService
from service.auth.registration import EmailVerificationService, RegistrationService
from service.auth.tokens import SessionService
from service.auth.two_factor import TwoFactorService
from util.email import EmailSender, Mailer, build_email_sender
from util.email_templates import EmailTemplates


def get_email_sender(request: Request, settings: Settings = Depends(get_app_settings)) -> EmailSender:
    sender = getattr(request.app.state, "email_sender", None)
    if sender is None:
        sender = build_email_sender(settings)
        request.app.state.email_sender = sender
    return sender


def get_mailer(
    background: BackgroundTasks,
    settings: Settings = Depends(get_app_settings),
    sender: EmailSender = Depends(get_email_sender),
) -> Mailer:
    return Mailer(sender, EmailTemplates.from_settings(settings), settings, background)


def get_otp_service(redis: Redis = Depends(get_redis), settings: Settings = Depends(get_app_settings)) -> OtpService:
    return OtpService(redis, settings)


def get_session_service(
    users: Repository = Depends(get_users_repo),
    permissions: Repository = Depends(get_permissions_repo),
    groups: Repository = Depends(get_groups_repo),
    store: TokenStore = Depends(get_token_store),
    settings: Settings = Depends(get_app_settings),
) -> SessionService:
    return SessionService(users, permissions, groups, store, settings)


def get_two_factor_service(
    users: Repository = Depends(get_users_repo),
    redis: Redis = Depends(get_redis),
    mailer: Mailer = Depends(get_mailer),
    settings: Settings = Depends(get_app_settings),
) -> TwoFactorService:
    return TwoFactorService(users, redis, mailer, settings)


def get_login_service(
    users: Repository = Depends(get_users_repo),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_app_settings),
    sessions: SessionService = Depends(get_session_service),
    two_factor: TwoFactorService = Depends(get_two_factor_service),
) -> LoginService:
    return LoginService(users, LoginAttempts(redis, settings), sessions, two_factor)


def get_registration_service(
    users: Repository = Depends(get_users_repo),
    permissions: Repository = Depends(get_permissions_repo),
    otp: OtpService = Depends(get_otp_service),
    mailer: Mailer = Depends(get_mailer),
    settings: Settings = Depends(get_app_settings),
) -> RegistrationService:
    return RegistrationService(users, permissions, otp, mailer, settings)


def get_email_verification_service(
    users: Repository = Depends(get_users_repo),
    redis: Redis = Depends(get_redis),
    otp: OtpService = Depends(get_otp_service),
    mailer: Mailer = Depends(get_mailer),
    settings: Settings = Depends(get_app_settings),
) -> EmailVerificationService:
    return EmailVerificationService(users, redis, otp, mailer, settings)


def get_password_service(
    users: Repository = Depends(get_users_repo),
    otp: OtpService = Depends(get_otp_service),
    sessions: SessionService = Depends(get_session_service),
    mailer: Mailer = Depends(get_mailer),
    settings: Settings = Depends(get_app_settings),
) -> PasswordService:
    return PasswordService(users, otp, sessions, mailer, settings)


def get_google_client(request: Request, settings: Settings = Depends(get_app_settings)) -> GoogleOAuthClient:
    client = getattr(request.app.state, "google_client", None)
    if client is None:
        client = GoogleOAuthClient(settings)
        request.app.state.google_client = client
    return client


def get_google_service(
    users: Repository = Depends(get_users_repo),
    permissions: Repository = Depends(get_permissions_repo),
    settings: Settings = Depends(get_app_settings),
) -> GoogleAuthService:
    return GoogleAuthService(users, permissions, settings)


MailerDep = Annotated[Mailer, Depends(get_mailer)]
SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
TwoFactorServiceDep = Annotated[TwoFactorService, Depends(get_two_factor_service)]
LoginServiceDep = Annotated[LoginService, Depends(get_login_service)]
RegistrationServiceDep = Annotated[RegistrationService, Depends(get_registration_service)]
EmailVerificationServiceDep = Annotated[EmailVerificationService, Depends(get_email_verification_service)]
PasswordServiceDep = Annotated[PasswordService, Depends(get_password_service)]
GoogleClientDep = Annotated[GoogleOAuthClient, Depends(get_google_client)]
GoogleServiceDep = Annotated[GoogleAuthService, Depends(get_google_service)]
