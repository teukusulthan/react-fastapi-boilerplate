"""Filter tree -> parameterised SQL ``WHERE`` clause, composed only with ``psycopg.sql``.

Identifiers go through ``sql.Identifier`` (validated against the entity schema),
values are always bound parameters (``%s``). Semantics mirror the Mongo
translator:

* ``NE`` / ``NIN`` / ``NOT_CONTAINS`` also match ``NULL`` (Mongo ``$ne`` matches missing fields);
* ``list`` fields (jsonb arrays): ``EQ`` = contains element, ``IN`` = contains any, ``ALL`` = contains all;
* ``id`` fields (uuid columns): values that are not UUIDs can never match (no SQL error);
* ``CONTAINS`` is a case-insensitive literal substring (``ILIKE`` with ``%``/``_``/``\\`` escaped).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from psycopg import sql

from db.base import AllOf, AnyOf, Condition, Filter, Op, SortDirection, SortSpec
from db.schema import EntitySchema, FieldType
from util.helper import is_uuid

TRUE = sql.SQL("TRUE")
FALSE = sql.SQL("FALSE")


def escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class SqlTranslator:
    def __init__(self, entity: EntitySchema) -> None:
        self.entity = entity

    # --------------------------------------------------------------- helpers
    def column(self, name: str) -> sql.Identifier:
        if not self.entity.has(name):
            raise ValueError(f"Unknown field {name!r} for entity {self.entity.name!r}")
        return sql.Identifier(name)

    @staticmethod
    def _scalar(value: Any) -> Any:
        if isinstance(value, (dict, list, tuple, set)):
            raise ValueError("Filter values must be scalars")
        return value

    @staticmethod
    def _values(value: Any) -> list[Any]:
        if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple, set, frozenset)):
            raise ValueError("Expected a list of values")
        return list(value)

    def _type(self, name: str) -> FieldType:
        return self.entity.get_field(name).type

    # ------------------------------------------------------------ conditions
    def condition(self, cond: Condition, params: list[Any]) -> sql.Composable:
        col = self.column(cond.field)
        kind = self._type(cond.field)
        op = cond.op

        if op == Op.EXISTS:
            return sql.SQL("{} IS NOT NULL").format(col)
        if op == Op.NOT_EXISTS:
            return sql.SQL("{} IS NULL").format(col)

        if kind == FieldType.LIST:
            return self._list_condition(col, cond, params)

        if op in (Op.EQ, Op.NE):
            value = self._scalar(cond.value)
            if kind == FieldType.ID and not is_uuid(value):
                return FALSE if op == Op.EQ else TRUE
            params.append(value)
            template = "{} = %s" if op == Op.EQ else "{} IS DISTINCT FROM %s"
            return sql.SQL(template).format(col)

        if op in (Op.IN, Op.NIN):
            values = [self._scalar(v) for v in self._values(cond.value)]
            if kind == FieldType.ID:
                values = [v for v in values if is_uuid(v)]
            if not values:
                return FALSE if op == Op.IN else TRUE
            params.extend(values)
            placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in values)
            if op == Op.IN:
                return sql.SQL("{} IN ({})").format(col, placeholders)
            return sql.SQL("({} IS NULL OR {} NOT IN ({}))").format(col, col, placeholders)

        if op in (Op.GT, Op.GTE, Op.LT, Op.LTE):
            symbol = {Op.GT: ">", Op.GTE: ">=", Op.LT: "<", Op.LTE: "<="}[op]
            params.append(self._scalar(cond.value))
            return sql.SQL("{} {} %s").format(col, sql.SQL(symbol))

        if op in (Op.CONTAINS, Op.NOT_CONTAINS):
            params.append(f"%{escape_like(str(self._scalar(cond.value)))}%")
            target = col if kind == FieldType.STR else sql.SQL("{}::text").format(col)
            if op == Op.CONTAINS:
                return sql.SQL("{} ILIKE %s ESCAPE '\\'").format(target)
            return sql.SQL("({} IS NULL OR {} NOT ILIKE %s ESCAPE '\\')").format(col, target)

        raise ValueError(f"Operator {op.value!r} is not supported on field {cond.field!r}")

    def _list_condition(self, col: sql.Identifier, cond: Condition, params: list[Any]) -> sql.Composable:
        op = cond.op
        if op in (Op.EQ, Op.NE):
            params.append(str(self._scalar(cond.value)))
            if op == Op.EQ:
                return sql.SQL("{} ? %s").format(col)
            return sql.SQL("NOT COALESCE({} ? %s, FALSE)").format(col)
        if op in (Op.IN, Op.NIN, Op.ALL):
            values = [str(self._scalar(v)) for v in self._values(cond.value)]
            if not values:
                return {Op.IN: FALSE, Op.NIN: TRUE, Op.ALL: TRUE}[op]
            params.append(values)
            if op == Op.IN:
                return sql.SQL("{} ?| %s::text[]").format(col)
            if op == Op.ALL:
                return sql.SQL("{} ?& %s::text[]").format(col)
            return sql.SQL("NOT COALESCE({} ?| %s::text[], FALSE)").format(col)
        raise ValueError(f"Operator {op.value!r} is not supported on list field {cond.field!r}")

    # ---------------------------------------------------------------- groups
    def node(self, item: Filter, params: list[Any]) -> sql.Composable:
        if isinstance(item, Condition):
            return self.condition(item, params)
        if isinstance(item, AnyOf):
            if not item.items:
                return FALSE
            parts = [self.node(i, params) for i in item.items]
            return parts[0] if len(parts) == 1 else sql.SQL("({})").format(sql.SQL(" OR ").join(parts))
        if isinstance(item, AllOf):
            return self.where(item.items, params)
        raise TypeError(f"Unsupported filter node {type(item).__name__}")

    def where(self, filters: Sequence[Filter], params: list[Any]) -> sql.Composable:
        """AND the filters; ``TRUE`` when empty. Appends bound values to ``params`` in order."""
        parts = [self.node(f, params) for f in filters]
        if not parts:
            return TRUE
        return parts[0] if len(parts) == 1 else sql.SQL("({})").format(sql.SQL(" AND ").join(parts))

    def order_by(self, sort: Sequence[SortSpec]) -> sql.Composable:
        items: list[sql.Composable] = []
        names: set[str] = set()
        for spec in sort:
            direction = sql.SQL("ASC NULLS FIRST" if spec.direction == SortDirection.ASC else "DESC NULLS LAST")
            items.append(sql.SQL("{} {}").format(self.column(spec.field), direction))
            names.add(spec.field)
        if items and "id" not in names:
            last = sort[-1].direction
            items.append(sql.SQL("{} {}").format(sql.Identifier("id"), sql.SQL(last.value.upper())))
        if not items:
            return sql.SQL("")
        return sql.SQL(" ORDER BY {}").format(sql.SQL(", ").join(items))
