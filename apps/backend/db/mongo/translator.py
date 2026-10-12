"""Filter tree -> MongoDB query document.

Values are always placed in operator *operands* (never as operator keys), dict
values are rejected (no operator injection), and text search uses
``re.escape`` so user input is matched literally (no ReDoS).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from db.base import AllOf, AnyOf, Condition, Filter, Op

MATCH_NOTHING: dict[str, Any] = {"_id": {"$in": []}}


def mongo_field(name: str) -> str:
    return "_id" if name == "id" else name


def _scalar(value: Any) -> Any:
    if isinstance(value, dict):
        raise ValueError("Filter values must not be objects")
    return value


def _values(value: Any) -> list[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple, set, frozenset)):
        raise ValueError("Expected a list of values")
    return [_scalar(v) for v in value]


def _regex(text: Any) -> dict[str, Any]:
    return {"$regex": re.escape(str(text)), "$options": "i"}


def translate_condition(cond: Condition) -> dict[str, Any]:
    field = mongo_field(cond.field)
    op = cond.op
    if op == Op.EQ:
        return {field: _scalar(cond.value)}
    if op == Op.NE:
        return {field: {"$ne": _scalar(cond.value)}}
    if op == Op.IN:
        return {field: {"$in": _values(cond.value)}}
    if op == Op.NIN:
        return {field: {"$nin": _values(cond.value)}}
    if op in (Op.GT, Op.GTE, Op.LT, Op.LTE):
        return {field: {f"${op.value}": _scalar(cond.value)}}
    if op == Op.EXISTS:
        return {field: {"$ne": None}}
    if op == Op.NOT_EXISTS:
        return {field: None}
    if op == Op.CONTAINS:
        return {field: _regex(cond.value)}
    if op == Op.NOT_CONTAINS:
        return {field: {"$not": re.compile(re.escape(str(cond.value)), re.IGNORECASE)}}
    if op == Op.ALL:
        return {field: {"$all": _values(cond.value)}}
    raise ValueError(f"Unsupported operator {op!r}")


def translate_filter(item: Filter) -> dict[str, Any]:
    if isinstance(item, Condition):
        return translate_condition(item)
    if isinstance(item, AnyOf):
        if not item.items:
            return dict(MATCH_NOTHING)
        parts = [translate_filter(i) for i in item.items]
        return parts[0] if len(parts) == 1 else {"$or": parts}
    if isinstance(item, AllOf):
        return translate_where(item.items)
    raise TypeError(f"Unsupported filter node {type(item).__name__}")


def translate_where(filters: Sequence[Filter]) -> dict[str, Any]:
    """AND the filters together; ``{}`` when there is nothing to filter."""
    parts = [translate_filter(f) for f in filters]
    parts = [p for p in parts if p]
    if not parts:
        return {}
    return parts[0] if len(parts) == 1 else {"$and": parts}
