from __future__ import annotations

import re

import pytest

from db.base import AllOf, AnyOf, Condition, Op
from db.mongo.translator import MATCH_NOTHING, translate_where


def t(*filters):
    return translate_where(filters)


def test_basic_ops() -> None:
    assert t() == {}
    assert t(Condition("id", Op.EQ, "x")) == {"_id": "x"}
    assert t(Condition("a", Op.NE, 1)) == {"a": {"$ne": 1}}
    assert t(Condition("a", Op.IN, ("x", "y"))) == {"a": {"$in": ["x", "y"]}}
    assert t(Condition("a", Op.NIN, ["x"])) == {"a": {"$nin": ["x"]}}
    assert t(Condition("a", Op.GTE, 1), Condition("a", Op.LT, 5)) == {"$and": [{"a": {"$gte": 1}}, {"a": {"$lt": 5}}]}
    assert t(Condition("a", Op.EXISTS)) == {"a": {"$ne": None}}
    assert t(Condition("a", Op.NOT_EXISTS)) == {"a": None}
    assert t(Condition("tags", Op.ALL, ("x",))) == {"tags": {"$all": ["x"]}}


def test_contains_is_escaped_literal() -> None:
    query = t(Condition("email", Op.CONTAINS, "a.b+(c)*"))
    assert query == {"email": {"$regex": re.escape("a.b+(c)*"), "$options": "i"}}
    negated = t(Condition("email", Op.NOT_CONTAINS, ".*"))["email"]["$not"]
    assert negated.pattern == re.escape(".*") and negated.flags & re.IGNORECASE


def test_groups() -> None:
    query = t(AnyOf(Condition("a", Op.EQ, 1), AllOf(Condition("b", Op.EQ, 2), Condition("c", Op.EQ, 3))))
    assert query == {"$or": [{"a": 1}, {"$and": [{"b": 2}, {"c": 3}]}]}
    assert t(AnyOf()) == MATCH_NOTHING
    assert t(AllOf()) == {}


def test_object_values_rejected() -> None:
    with pytest.raises(ValueError):
        t(Condition("a", Op.EQ, {"$ne": None}))
    with pytest.raises(ValueError):
        t(Condition("a", Op.IN, "not-a-list"))
