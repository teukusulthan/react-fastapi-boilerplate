"""Permission DTOs (RBAC: a user's ``permission_id`` -> ``{name, alias, privileges}``).

``alias`` is the machine name used as the user's ``role`` (aliases listed in
``BE_SUPERUSER_ALIASES`` make a superuser). ``privileges`` is a list of strings
such as ``"user:write"`` checked by ``core.deps.require_privilege``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BeforeValidator, ConfigDict, Field, StringConstraints, field_validator

from dto.common import BaseSchema, FindDTO

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
# Lowercased BEFORE the pattern check (StringConstraints checks the pattern on the raw input).
Alias = Annotated[
    str,
    BeforeValidator(lambda v: v.strip().lower() if isinstance(v, str) else v),
    StringConstraints(min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$"),
]
Description = Annotated[str, StringConstraints(max_length=500)]
Kind = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Privilege = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100, pattern=r"^\S+$")]
Privileges = Annotated[list[Privilege], Field(max_length=200)]
EntityId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
ImageRef = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048)]

STRICT = ConfigDict(extra="forbid")


def _dedupe(value: list[str] | None) -> list[str] | None:
    return list(dict.fromkeys(value)) if value is not None else None


def _not_null(value: Any) -> Any:
    if value is None:
        raise ValueError("cannot be null")
    return value


class PermissionDTO(BaseSchema):
    """``POST /permission/add`` (admin)."""

    model_config = STRICT

    name: Name
    alias: Alias | None = None
    description: Description | None = None
    type: Kind | None = None
    privileges: Privileges = Field(default_factory=list)
    parent_id: EntityId | None = None
    image: ImageRef | None = None

    _privileges = field_validator("privileges")(_dedupe)


class UpdatePermissionDTO(BaseSchema):
    """``PUT /permission/update`` (admin). PATCH semantics: only sent fields change."""

    model_config = STRICT

    id: EntityId
    name: Name | None = None
    alias: Alias | None = None
    description: Description | None = None
    type: Kind | None = None
    privileges: Privileges | None = None
    parent_id: EntityId | None = None
    image: ImageRef | None = None

    _privileges = field_validator("privileges")(_dedupe)
    _required = field_validator("name", "privileges", mode="before")(_not_null)


class UpdatePrivilegesDTO(BaseSchema):
    """``PUT /permission/update-partial`` (admin): add/remove individual privileges atomically per request."""

    model_config = STRICT

    id: EntityId
    add_privileges: Privileges = Field(default_factory=list)
    remove_privileges: Privileges = Field(default_factory=list)


class FindPermissionDTO(FindDTO):
    """``POST /permission/get-all`` body (whitelists: ``db.schema.PERMISSIONS``)."""


class PermissionResponse(BaseSchema):
    id: str
    name: str
    alias: str | None = None
    description: str | None = None
    type: str | None = None
    privileges: list[str] = Field(default_factory=list)
    parent_id: str | None = None
    image: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
