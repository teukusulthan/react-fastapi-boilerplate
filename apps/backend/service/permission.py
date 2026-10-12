"""Permission service: CRUD + privilege add/remove + lockout and reference guards.

* ``alias`` is unique (409; pre-checked for a friendly error, the unique index is the guarantee).
* Changing the alias of a superuser permission (``BE_SUPERUSER_ALIASES``) is
  refused when the caller holds it or it would leave no active superuser.
* Deleting a permission still assigned to users is refused (409); child
  permissions are detached (``parent_id`` -> null), matching Postgres' FK.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import Depends

from core.config import Settings
from core.deps import CurrentUser, PermissionsRepo, SettingsDep, UsersRepo
from core.errors import ConflictError
from db.base import Repository
from dto.permission import PermissionDTO, UpdatePermissionDTO, UpdatePrivilegesDTO
from service import CrudService, ensure_valid_parent
from service.user import count_active_superusers, superuser_permission_ids


class PermissionService(CrudService):
    not_found_message = "Permission not found"

    def __init__(self, permissions: Repository, users: Repository, settings: Settings) -> None:
        super().__init__(permissions)
        self.users = users
        self.settings = settings

    def _is_superuser_alias(self, alias: str | None) -> bool:
        return bool(alias) and str(alias).lower() in self.settings.SUPERUSER_ALIASES

    def _guard_alias_change(self, current: Mapping[str, Any], new_alias: str | None, actor: CurrentUser) -> None:
        if not self._is_superuser_alias(current.get("alias")) or self._is_superuser_alias(new_alias):
            return
        if actor.permission_id == current["id"]:
            raise ConflictError("You cannot remove your own administrator access")
        remaining = [pid for pid in superuser_permission_ids(self.repo, self.settings) if pid != current["id"]]
        if count_active_superusers(self.users, remaining) == 0:
            raise ConflictError("Cannot remove the last active administrator")

    def _check_alias_free(self, alias: str | None, *, exclude_id: str | None = None) -> None:
        existing = self.repo.find_one({"alias": alias}) if alias else None
        if existing is not None and existing["id"] != exclude_id:
            raise ConflictError("alias already exists", details=[{"field": "alias", "message": "already exists"}])

    def create_permission(self, dto: PermissionDTO, actor: CurrentUser) -> dict[str, Any]:
        data = dto.to_storage(exclude_unset=False)
        ensure_valid_parent(self.repo, data.get("parent_id"))
        self._check_alias_free(data.get("alias"))
        return self.create(data, actor_id=actor.id)

    def update_permission(self, dto: UpdatePermissionDTO, actor: CurrentUser) -> dict[str, Any]:
        current = self.get(dto.id)
        changes = dto.to_storage(exclude_unset=True, exclude={"id"})
        if not changes:
            return current
        if "parent_id" in changes:
            ensure_valid_parent(self.repo, changes["parent_id"], record_id=current["id"])
        if "alias" in changes:
            self._check_alias_free(changes["alias"], exclude_id=current["id"])
            self._guard_alias_change(current, changes["alias"], actor)
        return self.update(current["id"], changes)

    def update_privileges(self, dto: UpdatePrivilegesDTO) -> dict[str, Any]:
        current = self.get(dto.id)
        removed = set(dto.remove_privileges)
        privileges = [p for p in current.get("privileges") or [] if p not in removed]
        privileges += [p for p in dto.add_privileges if p not in privileges and p not in removed]
        return self.update(current["id"], {"privileges": privileges})

    def delete_permission(self, id: str) -> None:
        self.get(id)
        holders = self.users.count({"permission_id": id})
        if holders:
            raise ConflictError(
                f"Permission is assigned to {holders} user(s); reassign them first",
                details=[{"field": "id", "message": f"referenced by {holders} user(s)"}],
            )
        self.repo.update_many({"parent_id": id}, {"parent_id": None})
        self.delete(id)


def get_permission_service(permissions: PermissionsRepo, users: UsersRepo, settings: SettingsDep) -> PermissionService:
    return PermissionService(permissions, users, settings)


PermissionServiceDep = Annotated[PermissionService, Depends(get_permission_service)]
