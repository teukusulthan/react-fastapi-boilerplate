"""Role DTOs.

Reference module: the smallest complete CRUD resource in the backend. Copy
``dto/role.py`` + ``service/role.py`` + ``router/role.py`` (+ tests in ``tests/modules/test_groups_roles.py``, and register the module in
``tests/modules/conftest.py`` / ``tests/modules/test_rbac.py``)
when adding a new resource.

Pattern:
* ``XDTO`` (create): required fields required, ``extra="forbid"``.
* ``UpdateXDTO``: ``id`` + every other field optional; the service applies only
  the fields the client sent (PATCH semantics). Required columns reject an
  explicit ``null``.
* ``FindXDTO(FindDTO)``: list query; whitelists live on the entity in ``db/schema.py``.
* ``XResponse``: what the API returns (``response_model`` drops anything else).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import ConfigDict, Field, StringConstraints, field_validator

from dto.common import BaseSchema, FindDTO

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Alias = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Description = Annotated[str, StringConstraints(max_length=500)]
Kind = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Position = Annotated[int, Field(ge=0, le=1_000_000)]
EntityId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
ExternalRef = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]

STRICT = ConfigDict(extra="forbid")


def _not_null(value: Any) -> Any:
    if value is None:
        raise ValueError("cannot be null")
    return value


class RoleDTO(BaseSchema):
    """``POST /role/add`` (admin)."""

    model_config = STRICT

    name: Name
    alias: Alias | None = None
    description: Description | None = None
    role_position: Position | None = None
    type: Kind | None = None
    parent_id: EntityId | None = None
    workspace_id: ExternalRef | None = None
    organization_id: ExternalRef | None = None


class UpdateRoleDTO(BaseSchema):
    """``PUT /role/update`` (admin). PATCH semantics: only sent fields change."""

    model_config = STRICT

    id: EntityId
    name: Name | None = None
    alias: Alias | None = None
    description: Description | None = None
    role_position: Position | None = None
    type: Kind | None = None
    parent_id: EntityId | None = None
    workspace_id: ExternalRef | None = None
    organization_id: ExternalRef | None = None

    _required = field_validator("name", mode="before")(_not_null)


class FindRoleDTO(FindDTO):
    """``POST /role/get-all`` body (whitelists: ``db.schema.ROLES``)."""


class RoleResponse(BaseSchema):
    id: str
    name: str
    alias: str | None = None
    description: str | None = None
    role_position: int | None = None
    type: str | None = None
    parent_id: str | None = None
    workspace_id: str | None = None
    organization_id: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
