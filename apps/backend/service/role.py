"""Role service — the reference CRUD module (copy this shape for new resources).

* Plain class built per request by :func:`get_role_service` (``Depends``), no
  module-level instances, repositories only (no pymongo/psycopg here).
* Inherits get/list/create/update/delete (404 handling) from ``CrudService``
  and adds the domain rules: parent must exist and must not create a cycle;
  children are detached on delete (same result in Mongo and Postgres, where the
  FK is ``on delete set null``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import Depends

from core.deps import RolesRepo
from service import CrudService, ensure_valid_parent


class RoleService(CrudService):
    not_found_message = "Role not found"

    def create(self, data: Mapping[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        ensure_valid_parent(self.repo, data.get("parent_id"))
        return super().create(data, actor_id=actor_id)

    def update(self, id: str, changes: Mapping[str, Any]) -> dict[str, Any]:
        self.get(id)  # 404 before validating references
        if "parent_id" in changes:
            ensure_valid_parent(self.repo, changes["parent_id"], record_id=id)
        return super().update(id, changes)

    def delete(self, id: str) -> None:
        self.get(id)
        self.repo.update_many({"parent_id": id}, {"parent_id": None})
        super().delete(id)


def get_role_service(roles: RolesRepo) -> RoleService:
    return RoleService(roles)


RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]
