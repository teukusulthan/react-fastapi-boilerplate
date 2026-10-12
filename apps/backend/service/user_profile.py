"""Assemble :class:`~dto.user_profile.UserProfile` / ``UserResponse`` from storage records.

``build_*`` are pure; ``load_*`` fetch the related permission/group through the
repositories (batched for lists — no N+1).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from db.base import Repository
from dto.user_profile import GroupSummary, PermissionSummary, UserProfile, UserResponse

ProfileT = TypeVar("ProfileT", bound=UserProfile)

_NEVER_EXPOSE = frozenset({"password_hash", "two_factor_secret"})


def _permission_summary(permission: Mapping[str, Any] | None) -> PermissionSummary | None:
    if not permission:
        return None
    return PermissionSummary(
        id=permission["id"],
        name=permission.get("name") or "",
        alias=permission.get("alias"),
        privileges=list(permission.get("privileges") or []),
    )


def _group_summary(group: Mapping[str, Any] | None) -> GroupSummary | None:
    if not group:
        return None
    return GroupSummary(id=group["id"], name=group.get("name") or "")


def build_user_profile(
    user: Mapping[str, Any],
    permission: Mapping[str, Any] | None = None,
    group: Mapping[str, Any] | None = None,
    *,
    model: type[ProfileT] = UserProfile,  # type: ignore[assignment]
) -> ProfileT:
    """Pure mapping: storage user record (+ related records) -> profile DTO."""
    data = {k: v for k, v in user.items() if k not in _NEVER_EXPOSE}
    perm = _permission_summary(permission)
    data["permission"] = perm
    data["group"] = _group_summary(group)
    data["role"] = perm.alias if perm else None
    return model.model_validate(data)


def load_user_profile(
    user: Mapping[str, Any],
    permissions: Repository,
    groups: Repository,
    *,
    model: type[ProfileT] = UserProfile,  # type: ignore[assignment]
) -> ProfileT:
    permission = permissions.get_by_id(user["permission_id"]) if user.get("permission_id") else None
    group = groups.get_by_id(user["group_id"]) if user.get("group_id") else None
    return build_user_profile(user, permission, group, model=model)


def load_user_profiles(
    users: Sequence[Mapping[str, Any]],
    permissions: Repository,
    groups: Repository,
    *,
    model: type[ProfileT] = UserResponse,  # type: ignore[assignment]
) -> list[ProfileT]:
    """Batch version for list endpoints (2 extra queries total)."""
    perm_ids = {u["permission_id"] for u in users if u.get("permission_id")}
    group_ids = {u["group_id"] for u in users if u.get("group_id")}
    perms = {p["id"]: p for p in permissions.get_many_by_ids(perm_ids)} if perm_ids else {}
    grps = {g["id"]: g for g in groups.get_many_by_ids(group_ids)} if group_ids else {}
    return [
        build_user_profile(u, perms.get(u.get("permission_id") or ""), grps.get(u.get("group_id") or ""), model=model)
        for u in users
    ]
