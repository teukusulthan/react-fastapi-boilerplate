"""Provider-agnostic data-access contract.

Services only ever see :class:`Repository` (and :class:`Database` in lifespan /
health code). Records are plain ``dict`` objects with **snake_case storage keys**,
a string ``id`` and timezone-aware UTC ``created_at`` / ``updated_at``.

Filtering uses a tiny expression tree:

* :class:`Condition` — ``Condition("status", Op.EQ, "active")``
* :class:`AnyOf` / :class:`AllOf` — OR / AND groups
* a plain mapping ``{"status": "active", "email": "a@b.c"}`` is shorthand for
  equality conditions AND-ed together (``None`` means "is null").

:class:`QuerySpec` (built from a ``FindDTO`` by ``db.query.build_query_spec`` or by
hand) adds sorting and pagination for :meth:`Repository.find`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from db.schema import EntitySchema


class Op(str, Enum):
    EQ = "eq"
    NE = "ne"
    IN = "in"
    NIN = "nin"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EXISTS = "exists"  # not null (and present)
    NOT_EXISTS = "not_exists"  # null or missing
    CONTAINS = "contains"  # case-insensitive literal substring (text fields)
    NOT_CONTAINS = "not_contains"
    ALL = "all"  # list field contains every value


@dataclass(frozen=True)
class Condition:
    field: str  # storage (snake_case) field name
    op: Op
    value: Any = None


@dataclass(frozen=True, init=False)
class AnyOf:
    """OR group. An empty group matches nothing."""

    items: tuple[Filter, ...]

    def __init__(self, *items: Filter | Iterable[Filter]) -> None:
        object.__setattr__(self, "items", _flatten(items))


@dataclass(frozen=True, init=False)
class AllOf:
    """AND group. An empty group matches everything."""

    items: tuple[Filter, ...]

    def __init__(self, *items: Filter | Iterable[Filter]) -> None:
        object.__setattr__(self, "items", _flatten(items))


Filter = Condition | AnyOf | AllOf
Where = Mapping[str, Any] | Filter | Sequence[Filter] | None


def _flatten(items: Iterable[Any]) -> tuple[Filter, ...]:
    out: list[Filter] = []
    for item in items:
        if isinstance(item, (Condition, AnyOf, AllOf)):
            out.append(item)
        else:
            out.extend(item)
    return tuple(out)


def normalize_where(where: Where) -> tuple[Filter, ...]:
    """Coerce any accepted ``where`` form into a tuple of AND-ed filters."""
    if where is None:
        return ()
    if isinstance(where, (Condition, AnyOf, AllOf)):
        return (where,)
    if isinstance(where, Mapping):
        return tuple(
            Condition(key, Op.NOT_EXISTS) if value is None else Condition(key, Op.EQ, value)
            for key, value in where.items()
        )
    return tuple(where)


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True)
class SortSpec:
    field: str
    direction: SortDirection = SortDirection.DESC


@dataclass(frozen=True)
class QuerySpec:
    where: tuple[Filter, ...] = ()
    sort: tuple[SortSpec, ...] = ()
    offset: int = 0
    limit: int | None = None
    page: int = 1
    size: int | None = None

    @classmethod
    def of(
        cls,
        where: Where = None,
        *,
        sort: Sequence[SortSpec] | None = None,
        page: int = 1,
        size: int | None = None,
    ) -> QuerySpec:
        """Convenience constructor for hand-written queries."""
        offset = (page - 1) * size if size else 0
        return cls(
            where=normalize_where(where), sort=tuple(sort or ()), offset=offset, limit=size, page=page, size=size
        )

    def and_where(self, *filters: Filter) -> QuerySpec:
        """Return a copy with extra AND-ed filters (e.g. ``created_by == current user``)."""
        return QuerySpec(self.where + tuple(filters), self.sort, self.offset, self.limit, self.page, self.size)


class Repository(ABC):
    """CRUD over one entity (table / collection). Implementations must be thread-safe.

    Write methods validate keys against the entity schema (unknown field ->
    ``ValueError``, a programming error) and map unique violations to
    ``core.errors.ConflictError``.
    """

    entity: EntitySchema

    @abstractmethod
    def get_by_id(self, id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def get_many_by_ids(self, ids: Iterable[str]) -> list[dict[str, Any]]:
        """Fetch several records (order not guaranteed; missing ids skipped)."""

    @abstractmethod
    def find_one(self, where: Where) -> dict[str, Any] | None: ...

    @abstractmethod
    def find(self, spec: QuerySpec) -> tuple[list[dict[str, Any]], int]:
        """Return ``(page_items, total_matching)``."""

    @abstractmethod
    def find_all(
        self, where: Where = None, *, sort: Sequence[SortSpec] | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Unpaginated listing (always pass ``limit`` for user-facing data)."""

    @abstractmethod
    def count(self, where: Where = None) -> int: ...

    def exists(self, where: Where) -> bool:
        return self.find_one(where) is not None

    @abstractmethod
    def insert(self, data: Mapping[str, Any]) -> dict[str, Any]:
        """Insert and return the stored record. Sets ``id`` (if absent), ``created_at``, ``updated_at``."""

    @abstractmethod
    def update(self, id: str, changes: Mapping[str, Any]) -> dict[str, Any] | None:
        """Partial update (never upserts). Returns the updated record or ``None`` if not found."""

    @abstractmethod
    def update_many(self, where: Where, changes: Mapping[str, Any]) -> int:
        """Partial update of every match; returns the number of matched records."""

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete by id; ``True`` if a record was removed."""

    @abstractmethod
    def delete_many(self, where: Where) -> int: ...


class Database(ABC):
    """A connected provider (Mongo client / Postgres pool) handing out repositories."""

    provider: str

    @abstractmethod
    def repository(self, entity: EntitySchema | str) -> Repository: ...

    @abstractmethod
    def ping(self) -> None:
        """Raise if the database is unreachable."""

    @abstractmethod
    def ensure_schema(self) -> None:
        """Mongo: create indexes (idempotent). Postgres: verify migrated tables exist."""

    @abstractmethod
    def close(self) -> None: ...

    def open(self) -> None:  # noqa: B027  # optional hook, intentionally not abstract
        """Open connections eagerly (Postgres pool). Default: lazy."""
