"""Shared DTO building blocks.

* :class:`BaseSchema` — every request/response model: camelCase JSON aliases,
  snake_case attribute names, accepts either on input, serialises by alias.
* :class:`FindDTO` — the body of every ``POST /x/get-all``. Parse it into a
  provider-agnostic ``QuerySpec`` with ``db.query.build_query_spec``.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import Query
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from core.config import get_settings
from core.context import get_max_page_size

DEFAULT_PAGE_SIZE = 10
MAX_SEARCH_LENGTH = 200
MAX_FILTERS = 50
MAX_FILTER_LIST = 200

Scalar = str | int | float | bool | None

FilterOperator = Literal[
    "is",
    "is not",
    "is one of",
    "is not one of",
    "greater than equals",
    "less than equals",
    "is between",
    "is not between",
    "is exist",
    "is not exist",
    "is contains",
    "is not contains",
    "all",
]


class BaseSchema(BaseModel):
    """Base for all DTOs: ``created_at`` attribute <-> ``createdAt`` JSON."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
        from_attributes=True,
    )

    def to_storage(self, *, exclude_unset: bool = True, exclude: set[str] | None = None) -> dict[str, Any]:
        """snake_case dict for repositories (``exclude_unset`` -> only fields the client sent)."""
        return self.model_dump(by_alias=False, exclude_unset=exclude_unset, exclude=exclude)


class FilterValue(BaseSchema):
    """Operand container (legacy vocabulary). Only scalars / lists of scalars are accepted."""

    model_config = ConfigDict(extra="ignore")

    is_: Scalar = Field(default=None, alias="is")
    is_one_of: list[Scalar] | None = Field(default=None, max_length=MAX_FILTER_LIST)
    gte: str | int | float | None = None
    lte: str | int | float | None = None


class FilterItem(BaseSchema):
    model_config = ConfigDict(extra="ignore")

    field: str = Field(min_length=1, max_length=64)
    operator: FilterOperator
    value: FilterValue = Field(default_factory=FilterValue)
    # Legacy: filters flagged "or" are OR-ed together (as one group) instead of AND-ed.
    operator_type: Literal["and", "or"] = Field(
        default="and", validation_alias=AliasChoices("operatorType", "operator_type")
    )


class FindDTO(BaseSchema):
    """List query: pagination + search + whitelisted filters/sort."""

    model_config = ConfigDict(extra="ignore")

    page: int = Field(default=1, ge=1, le=100_000)
    size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1)
    search: str | None = Field(default=None, max_length=MAX_SEARCH_LENGTH)
    search_by: list[str] = Field(
        default_factory=list,
        max_length=20,
        validation_alias=AliasChoices("searchBy", "search_by"),
    )
    order_by: str | None = Field(default=None, max_length=64)
    order: Literal["asc", "desc"] = "desc"
    filters: list[FilterItem] = Field(default_factory=list, max_length=MAX_FILTERS)

    @field_validator("size")
    @classmethod
    def _max_page_size(cls, value: int) -> int:
        # The serving app's limit (bound per request by RequestContextMiddleware); the
        # global settings are only a fallback for use outside a request (scripts, tests).
        limit = get_max_page_size()
        if limit is None:
            limit = get_settings().MAX_PAGE_SIZE
        if value > limit:
            raise ValueError(f"must be less than or equal to {limit}")
        return value

    @field_validator("search")
    @classmethod
    def _blank_search(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("order", mode="before")
    @classmethod
    def _order_case(cls, value: Any) -> Any:
        return value.lower() if isinstance(value, str) else value

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class IdQuery(BaseSchema):
    """``?id=...`` query model (``Annotated[IdQuery, Query()]``)."""

    id: str = Field(min_length=1, max_length=64)


# Plain query param alias for the very common ``?id=`` parameter.
IdParam = Annotated[str, Query(min_length=1, max_length=64, description="Resource id")]


class MessageData(BaseSchema):
    message: str
