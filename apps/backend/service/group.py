"""Group service: CRUD + parent validation; deleting a group still assigned to users is refused (409)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import Depends

from core.deps import GroupsRepo, UsersRepo
from core.errors import ConflictError
from db.base import Repository
from service import CrudService, ensure_valid_parent


class GroupService(CrudService):
    not_found_message = "Group not found"

    def __init__(self, groups: Repository, users: Repository) -> None:
        super().__init__(groups)
        self.users = users

    def create(self, data: Mapping[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        ensure_valid_parent(self.repo, data.get("parent_id"))
        return super().create(data, actor_id=actor_id)

    def update(self, id: str, changes: Mapping[str, Any]) -> dict[str, Any]:
        self.get(id)
        if "parent_id" in changes:
            ensure_valid_parent(self.repo, changes["parent_id"], record_id=id)
        return super().update(id, changes)

    def delete(self, id: str) -> None:
        self.get(id)
        members = self.users.count({"group_id": id})
        if members:
            raise ConflictError(
                f"Group is assigned to {members} user(s); reassign them first",
                details=[{"field": "id", "message": f"referenced by {members} user(s)"}],
            )
        self.repo.update_many({"parent_id": id}, {"parent_id": None})
        super().delete(id)


def get_group_service(groups: GroupsRepo, users: UsersRepo) -> GroupService:
    return GroupService(groups, users)


GroupServiceDep = Annotated[GroupService, Depends(get_group_service)]
