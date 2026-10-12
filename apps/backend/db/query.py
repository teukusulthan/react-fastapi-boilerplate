"""``FindDTO`` -> provider-agnostic :class:`~db.base.QuerySpec`.

Every field referenced by ``filters`` / ``searchBy`` / ``orderBy`` must be in the
entity's whitelist (API camelCase or storage snake_case names are accepted).
Unknown or non-whitelisted fields, wrong operand shapes and values that cannot
be coerced to the field type raise ``core.errors.ValidationError`` (422) with a
``[{"field", "message"}]`` list. Search text is matched literally and
case-insensitively (translators escape it).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from core.errors import ValidationError
from db.base import AllOf, AnyOf, Condition, Filter, Op, QuerySpec, SortDirection, SortSpec
from db.schema import EntitySchema, Field, FieldType
from dto.common import FilterItem, FindDTO
from util.helper import as_utc, is_uuid

_RANGE_TYPES = {FieldType.INT, FieldType.FLOAT, FieldType.DATETIME, FieldType.STR}
_TRUE = {"true", "1", "yes"}
_FALSE = {"false", "0", "no"}


class _Errors:
    def __init__(self) -> None:
        self.items: list[dict[str, str]] = []

    def add(self, field: str, message: str) -> None:
        self.items.append({"field": field, "message": message})

    def raise_if_any(self) -> None:
        if self.items:
            raise ValidationError("Invalid query", details=self.items)


def parse_datetime(value: Any) -> datetime:
    """ISO-8601 string (``Z`` ok, date-only ok) or epoch seconds/milliseconds -> aware UTC."""
    if isinstance(value, datetime):
        return as_utc(value)  # type: ignore[return-value]
    if isinstance(value, bool):
        raise ValueError("not a datetime")
    if isinstance(value, (int, float)):
        seconds = value / 1000 if abs(value) > 100_000_000_000 else value
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if text.endswith(("Z", "z")):
            text = text[:-1] + "+00:00"
        return as_utc(datetime.fromisoformat(text))  # type: ignore[return-value]
    raise ValueError("not a datetime")


def coerce_value(field: Field, value: Any) -> Any:
    """Coerce one scalar operand to the storage type of ``field`` (raises ``ValueError``)."""
    if value is None:
        return None
    if isinstance(value, (dict, list, tuple, set)):
        raise ValueError("must be a scalar")
    kind = field.type
    if kind == FieldType.ID:
        text = str(value).strip().lower()
        if not is_uuid(text):
            raise ValueError("must be a valid id")
        return text
    if kind in (FieldType.STR, FieldType.LIST):
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)
    if kind == FieldType.BOOL:
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
        raise ValueError("must be a boolean")
    if kind == FieldType.INT:
        if isinstance(value, bool):
            raise ValueError("must be an integer")
        number = float(value)
        if not number.is_integer():
            raise ValueError("must be an integer")
        return int(number)
    if kind == FieldType.FLOAT:
        if isinstance(value, bool):
            raise ValueError("must be a number")
        return float(value)
    if kind == FieldType.DATETIME:
        return parse_datetime(value)
    return value


def _resolve_field(
    entity: EntitySchema, name: str, allowed: frozenset[str], location: str, purpose: str, errors: _Errors
) -> Field | None:
    field = entity.resolve(name)
    if field is None or field.sensitive or field.name not in allowed:
        errors.add(location, f"'{name}' is not a {purpose} field")
        return None
    return field


def _filter_to_condition(item: FilterItem, field: Field, loc: str, errors: _Errors) -> Filter | None:
    operator = item.operator
    value = item.value

    def one(raw: Any, sub: str) -> Any:
        if raw is None:
            errors.add(f"{loc}.value.{sub}", f"'{sub}' is required for operator '{operator}'")
            return None
        try:
            return coerce_value(field, raw)
        except (TypeError, ValueError) as exc:
            errors.add(f"{loc}.value.{sub}", str(exc))
            return None

    def many(raw: list[Any] | None) -> list[Any] | None:
        if raw is None:
            errors.add(f"{loc}.value.isOneOf", f"'isOneOf' is required for operator '{operator}'")
            return None
        out: list[Any] = []
        for idx, element in enumerate(raw):
            try:
                out.append(coerce_value(field, element))
            except (TypeError, ValueError) as exc:
                errors.add(f"{loc}.value.isOneOf[{idx}]", str(exc))
                return None
        return out

    name = field.name
    if operator in ("is", "is not"):
        operand = one(value.is_, "is")
        if operand is None:
            return None
        return Condition(name, Op.EQ if operator == "is" else Op.NE, operand)
    if operator in ("is one of", "is not one of"):
        operands = many(value.is_one_of)
        if operands is None:
            return None
        return Condition(name, Op.IN if operator == "is one of" else Op.NIN, tuple(operands))
    if operator == "all":
        if field.type != FieldType.LIST:
            errors.add(f"{loc}.operator", "'all' is only supported on list fields")
            return None
        operands = many(value.is_one_of)
        return None if operands is None else Condition(name, Op.ALL, tuple(operands))
    if operator in ("is exist", "is not exist"):
        return Condition(name, Op.EXISTS if operator == "is exist" else Op.NOT_EXISTS)
    if operator in ("is contains", "is not contains"):
        if field.type != FieldType.STR:
            errors.add(f"{loc}.operator", f"'{operator}' is only supported on text fields")
            return None
        operand = one(value.is_, "is")
        if operand is None:
            return None
        return Condition(name, Op.CONTAINS if operator == "is contains" else Op.NOT_CONTAINS, operand)

    # range operators
    if field.type not in _RANGE_TYPES:
        errors.add(f"{loc}.operator", f"'{operator}' is not supported on this field")
        return None
    if operator == "greater than equals":
        operand = one(value.gte, "gte")
        return None if operand is None else Condition(name, Op.GTE, operand)
    if operator == "less than equals":
        operand = one(value.lte, "lte")
        return None if operand is None else Condition(name, Op.LTE, operand)
    low, high = one(value.gte, "gte"), one(value.lte, "lte")
    if low is None or high is None:
        return None
    if operator == "is between":
        return AllOf(Condition(name, Op.GTE, low), Condition(name, Op.LTE, high))
    return AnyOf(Condition(name, Op.LT, low), Condition(name, Op.GT, high))  # is not between


def build_query_spec(
    dto: FindDTO,
    entity: EntitySchema,
    *,
    filterable: Iterable[str] | None = None,
    searchable: Iterable[str] | None = None,
    sortable: Iterable[str] | None = None,
    extra_where: Iterable[Filter] = (),
) -> QuerySpec:
    """Validate ``dto`` against the entity whitelists and build a :class:`QuerySpec`.

    ``filterable`` / ``searchable`` / ``sortable`` (storage names) narrow or
    replace the entity defaults for one endpoint. ``extra_where`` adds
    server-side conditions (e.g. scoping to the current user) that the client
    cannot remove.
    """
    allowed_filter = frozenset(filterable) if filterable is not None else entity.filterable
    allowed_search = frozenset(searchable) if searchable is not None else entity.searchable
    allowed_sort = frozenset(sortable) if sortable is not None else entity.sortable
    errors = _Errors()
    where: list[Filter] = list(extra_where)

    # ---- search
    if dto.search:
        if dto.search_by:
            fields = [
                _resolve_field(entity, name, allowed_search, f"searchBy[{i}]", "searchable", errors)
                for i, name in enumerate(dto.search_by)
            ]
            names = [f.name for f in fields if f is not None]
        else:
            names = sorted(allowed_search)
        if names:
            where.append(AnyOf(*(Condition(name, Op.CONTAINS, dto.search) for name in dict.fromkeys(names))))
        elif not dto.search_by:
            errors.add("search", "This resource does not support text search")

    # ---- filters
    or_group: list[Filter] = []
    for idx, item in enumerate(dto.filters):
        loc = f"filters[{idx}]"
        field = _resolve_field(entity, item.field, allowed_filter, f"{loc}.field", "filterable", errors)
        if field is None:
            continue
        condition = _filter_to_condition(item, field, loc, errors)
        if condition is None:
            continue
        (or_group if item.operator_type == "or" else where).append(condition)
    if or_group:
        where.append(AnyOf(*or_group))

    # ---- sort
    sort_name = dto.order_by or entity.default_sort
    sort_field = _resolve_field(entity, sort_name, allowed_sort | {entity.default_sort}, "orderBy", "sortable", errors)
    errors.raise_if_any()
    sort = (SortSpec(sort_field.name if sort_field else entity.default_sort, SortDirection(dto.order)),)

    return QuerySpec(
        where=tuple(where),
        sort=sort,
        offset=dto.offset,
        limit=dto.size,
        page=dto.page,
        size=dto.size,
    )
