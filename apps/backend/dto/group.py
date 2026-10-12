"""Group DTOs (organisational grouping of users: ``users.group_id``)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import ConfigDict, Field, StringConstraints, field_validator

from dto.common import BaseSchema, FindDTO

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Description = Annotated[str, StringConstraints(max_length=500)]
EntityId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
ImageRef = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048)]
JsonObject = dict[str, Any]
# Saved filter presets (free-form JSON objects, e.g. FindDTO filter items).
Filters = Annotated[list[JsonObject], Field(max_length=100)]

STRICT = ConfigDict(extra="forbid")


def _not_null(value: Any) -> Any:
    if value is None:
        raise ValueError("cannot be null")
    return value


class GroupDTO(BaseSchema):
    """``POST /group/add`` (admin)."""

    model_config = STRICT

    name: Name
    description: Description | None = None
    parent_id: EntityId | None = None
    settings: JsonObject | None = None
    filters: Filters | None = None
    image: ImageRef | None = None
    personalization: JsonObject | None = None


class UpdateGroupDTO(BaseSchema):
    """``PUT /group/update`` (admin). PATCH semantics: only sent fields change."""

    model_config = STRICT

    id: EntityId
    name: Name | None = None
    description: Description | None = None
    parent_id: EntityId | None = None
    settings: JsonObject | None = None
    filters: Filters | None = None
    image: ImageRef | None = None
    personalization: JsonObject | None = None

    _required = field_validator("name", mode="before")(_not_null)


class FindGroupDTO(FindDTO):
    """``POST /group/get-all`` body (whitelists: ``db.schema.GROUPS``)."""


class GroupResponse(BaseSchema):
    id: str
    name: str
    description: str | None = None
    parent_id: str | None = None
    settings: JsonObject | None = None
    filters: list[JsonObject] | None = None
    image: str | None = None
    personalization: JsonObject | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
