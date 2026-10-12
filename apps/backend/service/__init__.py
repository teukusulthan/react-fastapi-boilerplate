"""Business-logic layer.

Services are plain classes that receive repositories (and settings / Redis /
TokenStore when needed) through their constructor and are built per request by
a ``Depends`` provider — no module-level instances, no imports of pymongo /
psycopg, no FastAPI ``Request``/``Response`` objects.

:class:`CrudService` covers the boring 80% of a resource; subclass it and add
domain rules (uniqueness messages, RBAC-aware field filtering, cascades…).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from core.errors import NotFoundError, ValidationError
from db.base import Filter, Repository
from db.query import build_query_spec
from dto.common import FindDTO

MAX_HIERARCHY_DEPTH = 32


def ensure_valid_parent(repo: Repository, parent_id: str | None, *, record_id: str | None = None) -> None:
    """422 if ``parent_id`` does not exist in ``repo``, is the record itself, or is one of its descendants."""
    if parent_id is None:
        return
    if record_id is not None and parent_id == record_id:
        raise ValidationError.for_field("parentId", "A record cannot be its own parent")
    current = repo.get_by_id(parent_id)
    if current is None:
        raise ValidationError.for_field("parentId", "Parent not found")
    if record_id is None:
        return
    for _ in range(MAX_HIERARCHY_DEPTH):  # walk up: the new parent must not descend from this record
        ancestor_id = current.get("parent_id")
        if ancestor_id is None:
            return
        if ancestor_id == record_id:
            raise ValidationError.for_field("parentId", "Parent would create a cycle")
        current = repo.get_by_id(ancestor_id)
        if current is None:
            return
    raise ValidationError.for_field("parentId", "Hierarchy is too deep")


class CrudService:
    """Generic get/list/create/update/delete over one repository."""

    not_found_message = "Resource not found"

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def get(self, id: str) -> dict[str, Any]:
        record = self.repo.get_by_id(id)
        if record is None:
            raise NotFoundError(self.not_found_message)
        return record

    def list(
        self,
        query: FindDTO,
        *,
        extra_where: Iterable[Filter] = (),
        filterable: Iterable[str] | None = None,
        searchable: Iterable[str] | None = None,
        sortable: Iterable[str] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        spec = build_query_spec(
            query,
            self.repo.entity,
            filterable=filterable,
            searchable=searchable,
            sortable=sortable,
            extra_where=extra_where,
        )
        return self.repo.find(spec)

    def create(self, data: Mapping[str, Any], *, actor_id: str | None = None) -> dict[str, Any]:
        payload = dict(data)
        payload.pop("id", None)
        if actor_id is not None:
            payload["created_by"] = actor_id
        return self.repo.insert(payload)

    def update(self, id: str, changes: Mapping[str, Any]) -> dict[str, Any]:
        safe = {k: v for k, v in changes.items() if k not in {"id", "created_by", "created_at", "updated_at"}}
        record = self.repo.update(id, safe)
        if record is None:
            raise NotFoundError(self.not_found_message)
        return record

    def delete(self, id: str) -> None:
        if not self.repo.delete(id):
            raise NotFoundError(self.not_found_message)
