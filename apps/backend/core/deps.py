"""FastAPI dependencies: settings, clients, repositories, principal resolution and RBAC.

Everything here is a sync ``def`` dependency (FastAPI runs it in the threadpool),
because repositories, Redis and JWKS fetching are blocking.

Typical wiring::

    def get_widget_service(repo: Repository = Depends(get_repository(WIDGETS))) -> WidgetService:
        return WidgetService(repo)

    WidgetServiceDep = Annotated[WidgetService, Depends(get_widget_service)]

    @router.post("/add", status_code=201, response_model=ApiResponse[WidgetResponse])
    def add(dto: WidgetDTO, service: WidgetServiceDep, user: AdminUserDep):
        return created(service.create(dto.to_storage(), actor_id=user.id))
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import Depends, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field
from redis import Redis

from core.config import Settings
from core.errors import (
    AuthenticationError,
    ConflictError,
    PermissionDeniedError,
    ServiceUnavailableError,
)
from core.rate_limit import RateLimiter
from core.security import (
    ACCESS,
    INTERNAL_TOKEN_HEADER,
    SupabaseTokenVerifier,
    TokenStore,
    access_token_from_request,
    decode_token,
    verify_internal_token,
)
from db.base import Database, Repository
from db.schema import GROUPS, PERMISSIONS, ROLES, UPLOADS, USERS, EntitySchema, get_entity
from util.helper import as_utc, censor_email, is_uuid, new_id

# ===================================================== infrastructure deps


def get_app_settings(request: Request) -> Settings:
    """Settings the app was built with (use this in routes, not ``core.config.get_settings``)."""
    return request.app.state.settings


def get_database(request: Request) -> Database:
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise ServiceUnavailableError("Database is not initialised")
    return database


def get_redis(request: Request) -> Redis:
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        raise ServiceUnavailableError("Redis is not initialised")
    return redis


def get_repository(entity: EntitySchema | str) -> Callable[..., Repository]:
    """Dependency factory: ``Depends(get_repository(USERS))`` -> that entity's repository."""
    name = entity.name if isinstance(entity, EntitySchema) else entity

    def dependency(database: Database = Depends(get_database)) -> Repository:
        return database.repository(get_entity(entity))

    dependency.__name__ = f"get_{name}_repo"
    return dependency


get_users_repo = get_repository(USERS)
get_permissions_repo = get_repository(PERMISSIONS)
get_groups_repo = get_repository(GROUPS)
get_roles_repo = get_repository(ROLES)
get_uploads_repo = get_repository(UPLOADS)


def get_token_store(
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_app_settings),
) -> TokenStore:
    return TokenStore(redis, settings)


def get_rate_limiter(
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_app_settings),
) -> RateLimiter:
    return RateLimiter(redis, settings)


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
DatabaseDep = Annotated[Database, Depends(get_database)]
RedisDep = Annotated[Redis, Depends(get_redis)]
UsersRepo = Annotated[Repository, Depends(get_users_repo)]
PermissionsRepo = Annotated[Repository, Depends(get_permissions_repo)]
GroupsRepo = Annotated[Repository, Depends(get_groups_repo)]
RolesRepo = Annotated[Repository, Depends(get_roles_repo)]
UploadsRepo = Annotated[Repository, Depends(get_uploads_repo)]
TokenStoreDep = Annotated[TokenStore, Depends(get_token_store)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]

# ============================================================ principal

INTERNAL_PRINCIPAL_ID = "internal"


class CurrentUser(BaseModel):
    """The authenticated principal for this request."""

    model_config = ConfigDict(frozen=True)

    id: str
    username: str | None = None
    email: str | None = None
    role: str | None = None  # permission alias, e.g. "admin"
    privileges: frozenset[str] = frozenset()
    permission_id: str | None = None
    group_id: str | None = None
    is_superuser: bool = False
    is_internal: bool = False
    multi_login: bool = True
    auth_provider: str | None = None
    session_id: str | None = None
    token_jti: str | None = None
    token_expires_at: datetime | None = None
    # Full storage record (includes secrets such as password_hash) — never return it.
    record: dict[str, Any] | None = Field(default=None, repr=False, exclude=True)

    def has_privilege(self, privilege: str) -> bool:
        return self.is_superuser or privilege in self.privileges

    @classmethod
    def internal(cls) -> CurrentUser:
        return cls(id=INTERNAL_PRINCIPAL_ID, role="internal", is_internal=True)


def build_principal(
    user: dict[str, Any],
    permission: dict[str, Any] | None,
    settings: Settings,
    *,
    session_id: str | None = None,
    token_jti: str | None = None,
    token_expires_at: datetime | None = None,
) -> CurrentUser:
    alias = (permission or {}).get("alias")
    return CurrentUser(
        id=user["id"],
        username=user.get("username"),
        email=user.get("email"),
        role=alias,
        privileges=frozenset((permission or {}).get("privileges") or ()),
        permission_id=user.get("permission_id"),
        group_id=user.get("group_id"),
        is_superuser=bool(alias) and str(alias).lower() in settings.SUPERUSER_ALIASES,
        multi_login=bool(user.get("multi_login", True)),
        auth_provider=user.get("auth_provider"),
        session_id=session_id,
        token_jti=token_jti,
        token_expires_at=token_expires_at,
        record=user,
    )


def ensure_user_can_authenticate(user: dict[str, Any] | None) -> dict[str, Any]:
    """Reject missing, non-active or expired accounts (generic message: no enumeration)."""
    if user is None or user.get("status") != "active":
        raise AuthenticationError("Account is not active")
    expired_at = as_utc(user.get("expired_at"))
    if expired_at is not None and expired_at <= datetime.now(timezone.utc):
        raise AuthenticationError("Account has expired")
    return user


def _load_permission(user: dict[str, Any], permissions: Repository) -> dict[str, Any] | None:
    permission_id = user.get("permission_id")
    return permissions.get_by_id(permission_id) if permission_id else None


def _local_principal(
    token: str, settings: Settings, users: Repository, permissions: Repository, redis: Redis
) -> CurrentUser:
    claims = decode_token(token, settings, ACCESS)
    store = TokenStore(redis, settings)
    if store.is_revoked(claims):
        raise AuthenticationError("Token has been revoked")
    user = ensure_user_can_authenticate(users.get_by_id(claims.sub))
    if not user.get("multi_login", True) and not store.is_session_current(user["id"], claims.session_id):
        raise AuthenticationError("Session is no longer active")
    return build_principal(
        user,
        _load_permission(user, permissions),
        settings,
        session_id=claims.session_id,
        token_jti=claims.jti,
        token_expires_at=claims.expires_at,
    )


_USERNAME_SAFE = re.compile(r"[^a-z0-9._-]")


def _link_preprovisioned_user(users: Repository, email: str, sub: str) -> dict[str, Any] | None:
    """Attach a Supabase identity to a row an admin created ahead of time (``/user/add`` in supabase mode).

    Only rows that are explicitly ``auth_provider="supabase"`` and not yet linked (``external_id`` null)
    are claimed; a local-password account with the same email is never taken over.
    """
    candidate = users.find_one({"email": email, "auth_provider": "supabase", "external_id": None})
    if candidate is None:
        return None
    linked = users.update(candidate["id"], {"external_id": sub, "email_verified": True})
    if linked is not None:
        logger.info("Linked Supabase identity to existing user {}", censor_email(email))
    return linked


def provision_supabase_user(
    claims: dict[str, Any], users: Repository, permissions: Repository, settings: Settings
) -> dict[str, Any]:
    """Find (by id / external_id), link (pre-created supabase row with the same email) or create the users row."""
    sub = str(claims["sub"])
    user = users.get_by_id(sub) if is_uuid(sub) else None
    if user is None:
        user = users.find_one({"external_id": sub, "auth_provider": "supabase"})
    if user is not None:
        return user

    email = str(claims.get("email") or "").strip().lower()
    if not email:
        raise AuthenticationError("Token has no email claim")
    linked = _link_preprovisioned_user(users, email, sub)
    if linked is not None:
        return linked
    metadata = claims.get("user_metadata") if isinstance(claims.get("user_metadata"), dict) else {}
    local_part = _USERNAME_SAFE.sub("", email.split("@", 1)[0])[:30] or "user"
    default_permission = permissions.find_one({"alias": settings.DEFAULT_PERMISSION_ALIAS})
    data = {
        "id": sub if is_uuid(sub) else new_id(),
        "username": f"{local_part}-{sub.replace('-', '')[:8]}",
        "fullname": metadata.get("full_name") or metadata.get("name") or local_part,
        "email": email,
        "phone": claims.get("phone") or None,
        "status": "active",
        "email_verified": True,
        "auth_provider": "supabase",
        "external_id": sub,
        "permission_id": default_permission["id"] if default_permission else None,
        "created_by": "supabase",
    }
    try:
        created = users.insert(data)
        logger.info("Provisioned local user for Supabase identity {}", censor_email(email))
        return created
    except ConflictError:
        # Concurrent first request, or the email/phone belongs to an existing local account.
        existing = users.get_by_id(data["id"]) or users.find_one({"external_id": sub, "auth_provider": "supabase"})
        if existing is not None:
            return existing
        raise ConflictError("An account with this email already exists") from None


def _supabase_principal(
    request: Request, token: str, settings: Settings, users: Repository, permissions: Repository
) -> CurrentUser:
    verifier: SupabaseTokenVerifier | None = getattr(request.app.state, "supabase_verifier", None)
    if verifier is None:
        verifier = SupabaseTokenVerifier(settings)
        request.app.state.supabase_verifier = verifier
    claims = verifier.verify(token)
    user = ensure_user_can_authenticate(provision_supabase_user(claims, users, permissions, settings))
    exp = claims.get("exp")
    return build_principal(
        user,
        _load_permission(user, permissions),
        settings,
        session_id=claims.get("session_id"),
        token_jti=claims.get("jti"),
        token_expires_at=datetime.fromtimestamp(exp, tz=timezone.utc) if isinstance(exp, (int, float)) else None,
    )


def get_current_user_optional(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    users: Repository = Depends(get_users_repo),
    permissions: Repository = Depends(get_permissions_repo),
    redis: Redis = Depends(get_redis),
) -> CurrentUser | None:
    """Resolve the principal, or ``None`` when no credentials were sent.

    Order: ``X-Internal-Token`` header (if present it must be valid) ->
    ``Authorization: Bearer`` -> ``token`` cookie. Invalid credentials always
    raise 401 (never silently downgrade to anonymous).
    """
    internal = request.headers.get(INTERNAL_TOKEN_HEADER)
    if internal is not None:
        if not verify_internal_token(internal, settings):
            raise AuthenticationError("Invalid internal token")
        return CurrentUser.internal()
    token = access_token_from_request(request)
    if not token:
        return None
    if settings.AUTH_PROVIDER == "supabase":
        return _supabase_principal(request, token, settings, users, permissions)
    return _local_principal(token, settings, users, permissions, redis)


def get_current_user(principal: CurrentUser | None = Depends(get_current_user_optional)) -> CurrentUser:
    """Any authenticated principal: a user OR the internal service principal."""
    if principal is None:
        raise AuthenticationError()
    return principal


def require_auth(principal: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """An authenticated *user* (internal-token calls are rejected)."""
    if principal.is_internal:
        raise PermissionDeniedError("User authentication required")
    return principal


def require_admin(user: CurrentUser = Depends(require_auth)) -> CurrentUser:
    """A user whose permission alias is in ``BE_SUPERUSER_ALIASES``."""
    if not user.is_superuser:
        raise PermissionDeniedError()
    return user


def require_privilege(
    *privileges: str, any_of: bool = False, allow_internal: bool = False
) -> Callable[..., CurrentUser]:
    """Superuser OR holds the privilege(s). ``any_of=True`` -> one of them is enough."""
    if not privileges:
        raise ValueError("require_privilege() needs at least one privilege")

    def dependency(principal: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if principal.is_internal:
            if allow_internal:
                return principal
            raise PermissionDeniedError("User authentication required")
        if principal.is_superuser:
            return principal
        check = any if any_of else all
        if not check(p in principal.privileges for p in privileges):
            raise PermissionDeniedError()
        return principal

    dependency.__name__ = "require_privilege_" + "_".join(p.replace(":", "_") for p in privileges)
    return dependency


def require_internal_token(
    request: Request,
    settings: Settings = Depends(get_app_settings),
) -> CurrentUser:
    """Only system-to-system calls carrying a valid ``X-Internal-Token``."""
    if not verify_internal_token(request.headers.get(INTERNAL_TOKEN_HEADER), settings):
        if not settings.internal_token_configured:
            logger.warning("Internal-token route called but BE_INTERNAL_TOKEN is not configured")
        raise AuthenticationError("Invalid internal token")
    return CurrentUser.internal()


def require_user_or_internal(principal: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return principal


OptionalUserDep = Annotated[CurrentUser | None, Depends(get_current_user_optional)]
PrincipalDep = Annotated[CurrentUser, Depends(get_current_user)]
CurrentUserDep = Annotated[CurrentUser, Depends(require_auth)]
AdminUserDep = Annotated[CurrentUser, Depends(require_admin)]
InternalDep = Annotated[CurrentUser, Depends(require_internal_token)]
UserOrInternalDep = Annotated[CurrentUser, Depends(require_user_or_internal)]
