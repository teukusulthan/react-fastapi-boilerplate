"""Entity declarations: the single source of truth for storage fields and query whitelists.

Each :class:`EntitySchema` lists its storage (snake_case) fields with a type and
flags that drive:

* repository write validation (unknown keys are rejected),
* Postgres JSONB handling (``json`` / ``list`` types) and uuid casting (``id``),
* Mongo / Postgres unique indexes (``unique=True``; nullable unique fields are
  partial/sparse so many ``NULL`` values are allowed),
* ``FindDTO`` whitelists (``filterable`` / ``searchable`` / ``sortable``),
* camelCase API names (``api`` defaults to ``to_camel(name)``),
* secrecy (``sensitive=True`` fields can never be filtered/sorted/searched),
* insert defaults (``default``) so Mongo documents and Postgres rows have the
  same shape (every declared field is always present).

New entity? Declare it here (or in your module with :func:`register_entity`),
add the table to ``migrations/supabase/NNN_*.sql`` and a ``BE_TABLE_*`` setting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any

from util.helper import to_camel

if TYPE_CHECKING:
    from core.config import Settings


class FieldType(str, Enum):
    ID = "id"  # uuid string (Postgres uuid column)
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    DATETIME = "datetime"  # timezone-aware UTC
    JSON = "json"  # dict / arbitrary JSON (Postgres jsonb)
    LIST = "list"  # list of scalars (Postgres jsonb array)


@dataclass(frozen=True)
class Field:
    name: str
    type: FieldType = FieldType.STR
    api: str | None = None
    unique: bool = False
    nullable: bool = True
    filterable: bool = False
    searchable: bool = False
    sortable: bool = False
    sensitive: bool = False
    # Value stored when an insert omits the field (callables are invoked, e.g. ``list``).
    default: Any = None

    @property
    def api_name(self) -> str:
        return self.api or to_camel(self.name)

    def make_default(self) -> Any:
        return self.default() if callable(self.default) else self.default


def _f(name: str, type: FieldType = FieldType.STR, *, q: str = "", **kwargs: Any) -> Field:
    """Compact field declaration: ``q`` flags = f(ilterable) s(earchable) o(rderable/sortable)."""
    return Field(
        name,
        type,
        filterable="f" in q,
        searchable="s" in q,
        sortable="o" in q,
        **kwargs,
    )


def audit_fields() -> tuple[Field, ...]:
    """``created_by`` / ``created_at`` / ``updated_at`` shared by every entity."""
    return (
        _f("created_by", q="f"),
        _f("created_at", FieldType.DATETIME, q="fo", nullable=False),
        _f("updated_at", FieldType.DATETIME, q="fo", nullable=False),
    )


@dataclass(frozen=True)
class EntitySchema:
    name: str
    table_setting: str  # Settings attribute holding the table/collection name
    fields: tuple[Field, ...]
    default_sort: str = "created_at"
    _by_name: dict[str, Field] = field(init=False, repr=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        by_name = {f.name: f for f in self.fields}
        if len(by_name) != len(self.fields):
            raise ValueError(f"Duplicate field in entity {self.name}")
        if "id" not in by_name or "created_at" not in by_name or "updated_at" not in by_name:
            raise ValueError(f"Entity {self.name} must declare id, created_at and updated_at")
        object.__setattr__(self, "_by_name", by_name)

    # ---------------------------------------------------------------- lookups
    def table(self, settings: Settings) -> str:
        return settings.table_name(self.table_setting)

    def has(self, name: str) -> bool:
        return name in self._by_name

    def get_field(self, name: str) -> Field:
        return self._by_name[name]

    def resolve(self, name: str) -> Field | None:
        """Find a field by API (camelCase) or storage (snake_case) name."""
        return self._api_index.get(name) or self._by_name.get(name)

    @cached_property
    def _api_index(self) -> dict[str, Field]:
        return {f.api_name: f for f in self.fields}

    @cached_property
    def storage_fields(self) -> frozenset[str]:
        return frozenset(self._by_name)

    @cached_property
    def filterable(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields if f.filterable and not f.sensitive)

    @cached_property
    def searchable(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields if f.searchable and not f.sensitive)

    @cached_property
    def sortable(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields if f.sortable and not f.sensitive)

    @cached_property
    def unique_fields(self) -> tuple[Field, ...]:
        return tuple(f for f in self.fields if f.unique)

    @cached_property
    def json_fields(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields if f.type in (FieldType.JSON, FieldType.LIST))

    @cached_property
    def sensitive_fields(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields if f.sensitive)

    def strip_sensitive(self, record: dict[str, Any]) -> dict[str, Any]:
        """Copy of ``record`` without sensitive fields (defence in depth; DTOs whitelist anyway)."""
        return {k: v for k, v in record.items() if k not in self.sensitive_fields}


ID = _f("id", FieldType.ID, q="f", nullable=False)

USERS = EntitySchema(
    name="users",
    table_setting="TABLE_USERS",
    fields=(
        ID,
        _f("username", q="fso", unique=True, nullable=False),
        _f("fullname", q="fso"),
        _f("email", q="fso", unique=True, nullable=False),
        _f("phone", q="fs", unique=True),
        _f("password_hash", sensitive=True),
        _f("permission_id", FieldType.ID, q="f"),
        _f("group_id", FieldType.ID, q="f"),
        _f("status", q="fo", nullable=False, default="pending"),
        _f("email_verified", FieldType.BOOL, q="f", nullable=False, default=False),
        _f("multi_login", FieldType.BOOL, q="f", nullable=False, default=True),
        _f("expired_at", FieldType.DATETIME, q="fo"),
        _f("last_login_at", FieldType.DATETIME, q="fo"),
        _f("two_factor_enabled", FieldType.BOOL, q="f", nullable=False, default=False),
        _f("two_factor_method"),
        _f("two_factor_secret", sensitive=True),
        _f("about"),
        _f("image"),
        _f("settings", FieldType.JSON),
        _f("personalization", FieldType.JSON),
        _f("additional", FieldType.JSON),
        _f("auth_provider", q="f", nullable=False, default="local"),
        _f("external_id", unique=True),
        *audit_fields(),
    ),
)

PERMISSIONS = EntitySchema(
    name="permissions",
    table_setting="TABLE_PERMISSIONS",
    fields=(
        ID,
        _f("name", q="fso", nullable=False),
        _f("alias", q="fso", unique=True),
        _f("description", q="s"),
        _f("type", q="f"),
        _f("privileges", FieldType.LIST, q="f", nullable=False, default=list),
        _f("parent_id", FieldType.ID, q="f"),
        _f("image"),
        *audit_fields(),
    ),
)

GROUPS = EntitySchema(
    name="groups",
    table_setting="TABLE_GROUPS",
    fields=(
        ID,
        _f("name", q="fso", nullable=False),
        _f("description", q="s"),
        _f("parent_id", FieldType.ID, q="f"),
        _f("settings", FieldType.JSON),
        _f("filters", FieldType.JSON),
        _f("image"),
        _f("personalization", FieldType.JSON),
        *audit_fields(),
    ),
)

ROLES = EntitySchema(
    name="roles",
    table_setting="TABLE_ROLES",
    fields=(
        ID,
        _f("name", q="fso", nullable=False),
        _f("alias", q="fso"),
        _f("description", q="s"),
        _f("role_position", FieldType.INT, q="fo"),
        _f("type", q="f"),
        _f("parent_id", FieldType.ID, q="f"),
        _f("workspace_id", q="f"),
        _f("organization_id", q="f"),
        *audit_fields(),
    ),
)

UPLOADS = EntitySchema(
    name="uploads",
    table_setting="TABLE_UPLOADS",
    fields=(
        ID,
        _f("bucket", nullable=False),
        _f("object_key", unique=True, nullable=False),
        _f("filename", q="fso", nullable=False),
        _f("mime_type", q="fo"),
        _f("filesize", FieldType.INT, q="fo"),
        _f("folder", q="fs"),
        _f("tags", FieldType.LIST, q="f", nullable=False, default=list),
        _f("widget_id", q="f"),
        _f("dashboard_id", q="f"),
        _f("workspace_id", q="f"),
        _f("connection_id", q="f"),
        *audit_fields(),
    ),
)

ENTITIES: dict[str, EntitySchema] = {e.name: e for e in (USERS, PERMISSIONS, GROUPS, ROLES, UPLOADS)}


def register_entity(entity: EntitySchema) -> EntitySchema:
    """Register an additional entity (call at import time of the owning module)."""
    existing = ENTITIES.get(entity.name)
    if existing is not None and existing is not entity:
        raise ValueError(f"Entity {entity.name!r} is already registered")
    ENTITIES[entity.name] = entity
    return entity


def get_entity(entity: EntitySchema | str) -> EntitySchema:
    if isinstance(entity, EntitySchema):
        return entity
    try:
        return ENTITIES[entity]
    except KeyError as exc:
        raise KeyError(f"Unknown entity {entity!r}; declare it in db/schema.py or register_entity()") from exc
