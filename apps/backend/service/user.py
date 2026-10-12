"""User administration + self-service profile.

Rules enforced here (routers only wire HTTP):

* Passwords are hashed with ``core.security`` and never returned; responses are
  built with ``service.user_profile`` (``UserResponse``).
* ``permission_id`` / ``group_id`` must reference existing records (422).
* username / email / phone are unique (409; the DB unique index is the real guarantee).
* Lockout guards: an admin cannot delete themselves or remove their own admin
  access, and the last active superuser can never be deleted, blocked,
  expired or demoted (409).
* Blocking/expiring a user, resetting a password or deleting a user revokes
  every token issued to that user (``TokenStore.revoke_all_for_user``).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Annotated, Any, Literal

from fastapi import Depends
from loguru import logger

from core.config import Settings
from core.deps import CurrentUser, GroupsRepo, PermissionsRepo, SettingsDep, TokenStoreDep, UsersRepo
from core.errors import BadRequestError, ConflictError, NotFoundError, ValidationError
from core.security import TokenStore, hash_password, validate_password_policy
from db.base import AnyOf, Condition, Filter, Op, Repository
from dto.common import FindDTO, MessageData
from dto.user import (
    CheckAvailabilityResponse,
    CreateUserDTO,
    ResetPasswordDTO,
    UpdateProfileDTO,
    UpdateUserDTO,
)
from dto.user_profile import UserResponse
from service import CrudService
from service.user_profile import load_user_profile, load_user_profiles
from util.helper import as_utc

UniqueField = Literal["username", "email", "phone"]
UNIQUE_FIELDS: tuple[UniqueField, ...] = ("username", "email", "phone")
MAX_SUPERUSER_PERMISSIONS = 100


# ------------------------------------------------------------ superuser helpers
def superuser_permission_ids(permissions: Repository, settings: Settings) -> list[str]:
    """Ids of permissions whose alias is in ``BE_SUPERUSER_ALIASES``."""
    aliases = tuple(settings.SUPERUSER_ALIASES)
    if not aliases:
        return []
    records = permissions.find_all(Condition("alias", Op.IN, aliases), limit=MAX_SUPERUSER_PERMISSIONS)
    return [p["id"] for p in records]


def count_active_superusers(
    users: Repository,
    permission_ids: list[str],
    *,
    exclude_user_id: str | None = None,
) -> int:
    """Active, non-expired users holding one of ``permission_ids`` (optionally excluding one user)."""
    if not permission_ids:
        return 0
    where: list[Filter] = [
        Condition("permission_id", Op.IN, tuple(permission_ids)),
        Condition("status", Op.EQ, "active"),
        AnyOf(Condition("expired_at", Op.NOT_EXISTS), Condition("expired_at", Op.GT, datetime.now(timezone.utc))),
    ]
    if exclude_user_id is not None:
        where.append(Condition("id", Op.NE, exclude_user_id))
    return users.count(where)


def _is_expired(user: Mapping[str, Any], now: datetime) -> bool:
    expired_at = as_utc(user.get("expired_at"))
    return expired_at is not None and expired_at <= now


def is_active_superuser(user: Mapping[str, Any], superuser_permission_ids: list[str]) -> bool:
    return (
        user.get("status") == "active"
        and user.get("permission_id") in superuser_permission_ids
        and not _is_expired(user, datetime.now(timezone.utc))
    )


# ----------------------------------------------------------------- service
class UserService(CrudService):
    not_found_message = "User not found"

    def __init__(
        self,
        users: Repository,
        permissions: Repository,
        groups: Repository,
        settings: Settings,
        tokens: TokenStore,
    ) -> None:
        super().__init__(users)
        self.permissions = permissions
        self.groups = groups
        self.settings = settings
        self.tokens = tokens

    # ------------------------------------------------------------- reads
    def _profile(self, record: Mapping[str, Any]) -> UserResponse:
        return load_user_profile(record, self.permissions, self.groups, model=UserResponse)

    def get_user(self, id: str) -> UserResponse:
        return self._profile(self.get(id))

    def get_by_username(self, username: str) -> UserResponse:
        record = self.repo.find_one({"username": username.strip()})
        if record is None:
            raise NotFoundError(self.not_found_message)
        return self._profile(record)

    def list_users(self, query: FindDTO) -> tuple[list[UserResponse], int]:
        records, total = self.list(query)
        return load_user_profiles(records, self.permissions, self.groups, model=UserResponse), total

    def check_availability(self, field: UniqueField, value: str) -> CheckAvailabilityResponse:
        normalized = value.strip().lower() if field == "email" else value.strip()
        exists = bool(normalized) and self.repo.exists({field: normalized})
        return CheckAvailabilityResponse(field=field, exists=exists, available=not exists)

    # ------------------------------------------------------------ checks
    def _check_references(self, values: Mapping[str, Any]) -> None:
        errors: list[dict[str, str]] = []
        if values.get("permission_id") is not None and self.permissions.get_by_id(values["permission_id"]) is None:
            errors.append({"field": "permissionId", "message": "Permission not found"})
        if values.get("group_id") is not None and self.groups.get_by_id(values["group_id"]) is None:
            errors.append({"field": "groupId", "message": "Group not found"})
        if errors:
            raise ValidationError(errors[0]["message"], details=errors)

    def _check_unique(self, values: Mapping[str, Any], *, exclude_id: str | None = None) -> None:
        conflicts = [
            field
            for field in UNIQUE_FIELDS
            if values.get(field) is not None
            and (existing := self.repo.find_one({field: values[field]})) is not None
            and existing["id"] != exclude_id
        ]
        if conflicts:
            raise ConflictError(
                f"{conflicts[0]} already exists",
                details=[{"field": field, "message": "already exists"} for field in conflicts],
            )

    def _guard_superuser_loss(self, current: Mapping[str, Any], after: Mapping[str, Any], actor: CurrentUser) -> None:
        """409 if the change would lock the actor out or leave the system without an active superuser."""
        su_ids = superuser_permission_ids(self.permissions, self.settings)
        if not is_active_superuser(current, su_ids) or is_active_superuser(after, su_ids):
            return
        if current["id"] == actor.id:
            raise ConflictError("You cannot remove your own administrator access")
        if count_active_superusers(self.repo, su_ids, exclude_user_id=current["id"]) == 0:
            raise ConflictError("Cannot remove the last active administrator")

    def _password_hash(self, password: str | None, field: str) -> str | None:
        if self.settings.AUTH_PROVIDER == "supabase":
            if password is not None:
                raise ValidationError.for_field(field, "Passwords are managed by Supabase Auth")
            return None
        if password is None:
            raise ValidationError.for_field(field, "Password is required")
        validate_password_policy(password, self.settings, field_name=field)
        return hash_password(password)

    def _revoke_sessions(self, user_id: str, reason: str) -> None:
        self.tokens.revoke_all_for_user(user_id)
        logger.info("Revoked all sessions of user {} ({})", user_id, reason)

    # ------------------------------------------------------------ writes
    def create_user(self, dto: CreateUserDTO, actor: CurrentUser) -> UserResponse:
        data = dto.to_storage(exclude_unset=False, exclude={"password"})
        if "permission_id" not in dto.model_fields_set:  # omitted -> same default as self-registration
            default = self.permissions.find_one({"alias": self.settings.DEFAULT_PERMISSION_ALIAS})
            data["permission_id"] = default["id"] if default else None
        self._check_references(data)
        self._check_unique(data)
        data["password_hash"] = self._password_hash(dto.password, "password")
        data["auth_provider"] = "supabase" if self.settings.AUTH_PROVIDER == "supabase" else "local"
        record = self.create(data, actor_id=actor.id)
        logger.info("User {} created by {}", record["id"], actor.id)
        return self._profile(record)

    def update_user(self, dto: UpdateUserDTO, actor: CurrentUser) -> UserResponse:
        current = self.get(dto.id)
        changes = dto.to_storage(exclude_unset=True, exclude={"id"})  # only the fields the client sent
        if not changes:
            return self._profile(current)
        self._check_references(changes)
        self._check_unique(changes, exclude_id=current["id"])
        after = {**current, **changes}
        self._guard_superuser_loss(current, after, actor)
        record = self.update(current["id"], changes)
        lost_access = after.get("status") != "active" or _is_expired(after, datetime.now(timezone.utc))
        if lost_access and ("status" in changes or "expired_at" in changes):
            self._revoke_sessions(current["id"], "access removed")
        return self._profile(record)

    def delete_user(self, id: str, actor: CurrentUser) -> None:
        if id == actor.id:
            raise ConflictError("You cannot delete your own account")
        current = self.get(id)
        self._guard_superuser_loss(current, {**current, "status": "deleted"}, actor)
        self.delete(id)
        self._revoke_sessions(id, "deleted")
        logger.info("User {} deleted by {}", id, actor.id)

    def reset_password(self, dto: ResetPasswordDTO, actor: CurrentUser) -> MessageData:
        if self.settings.AUTH_PROVIDER == "supabase":
            raise BadRequestError("Passwords are managed by Supabase Auth")
        current = self.get(dto.id)
        password_hash = self._password_hash(dto.new_password, "newPassword")
        self.update(current["id"], {"password_hash": password_hash})
        self._revoke_sessions(current["id"], "password reset")
        logger.info("Password of user {} reset by {}", current["id"], actor.id)
        return MessageData(message="Password has been reset")

    def update_profile(self, actor: CurrentUser, dto: UpdateProfileDTO) -> UserResponse:
        """Self-service: only the whitelisted fields of ``UpdateProfileDTO`` can change."""
        changes = dto.to_storage(exclude_unset=True)
        if not changes:
            return self.get_user(actor.id)
        self._check_unique(changes, exclude_id=actor.id)
        return self._profile(self.update(actor.id, changes))


def get_user_service(
    users: UsersRepo,
    permissions: PermissionsRepo,
    groups: GroupsRepo,
    settings: SettingsDep,
    tokens: TokenStoreDep,
) -> UserService:
    return UserService(users, permissions, groups, settings, tokens)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
