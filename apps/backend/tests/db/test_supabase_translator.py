"""SQL composition (no database needed): asserts rendered SQL + bound params."""

from __future__ import annotations

import pytest

from db.base import AllOf, AnyOf, Condition, Op, SortDirection, SortSpec
from db.schema import PERMISSIONS, USERS
from db.supabase.translator import SqlTranslator, escape_like

UID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


def render(*filters, entity=USERS):
    params: list = []
    composed = SqlTranslator(entity).where(filters, params)
    return composed.as_string(), params


def test_empty_is_true() -> None:
    assert render() == ("TRUE", [])


@pytest.mark.parametrize(
    ("cond", "sql", "params"),
    [
        (Condition("status", Op.EQ, "active"), '"status" = %s', ["active"]),
        (Condition("status", Op.NE, "active"), '"status" IS DISTINCT FROM %s', ["active"]),
        (Condition("status", Op.IN, ("a", "b")), '"status" IN (%s, %s)', ["a", "b"]),
        (Condition("status", Op.NIN, ("a",)), '("status" IS NULL OR "status" NOT IN (%s))', ["a"]),
        (Condition("status", Op.IN, ()), "FALSE", []),
        (Condition("status", Op.NIN, ()), "TRUE", []),
        (Condition("created_at", Op.GTE, 5), '"created_at" >= %s', [5]),
        (Condition("phone", Op.EXISTS), '"phone" IS NOT NULL', []),
        (Condition("phone", Op.NOT_EXISTS), '"phone" IS NULL', []),
        (Condition("email", Op.CONTAINS, "50%_off\\"), "\"email\" ILIKE %s ESCAPE '\\'", ["%50\\%\\_off\\\\%"]),
        (
            Condition("email", Op.NOT_CONTAINS, "x"),
            '("email" IS NULL OR "email" NOT ILIKE %s ESCAPE \'\\\')',
            ["%x%"],
        ),
        (Condition("permission_id", Op.EQ, UID), '"permission_id" = %s', [UID]),
        (Condition("permission_id", Op.EQ, "not-a-uuid"), "FALSE", []),
        (Condition("permission_id", Op.NE, "not-a-uuid"), "TRUE", []),
        (Condition("id", Op.IN, (UID, "junk")), '"id" IN (%s)', [UID]),
    ],
)
def test_conditions(cond, sql, params) -> None:
    assert render(cond) == (sql, params)


def test_list_fields_use_jsonb_operators() -> None:
    assert render(Condition("privileges", Op.EQ, "x"), entity=PERMISSIONS) == ('"privileges" ? %s', ["x"])
    assert render(Condition("privileges", Op.IN, ("x", "y")), entity=PERMISSIONS) == (
        '"privileges" ?| %s::text[]',
        [["x", "y"]],
    )
    assert render(Condition("privileges", Op.ALL, ("x",)), entity=PERMISSIONS) == (
        '"privileges" ?& %s::text[]',
        [["x"]],
    )
    assert render(Condition("privileges", Op.NIN, ("x",)), entity=PERMISSIONS) == (
        'NOT COALESCE("privileges" ?| %s::text[], FALSE)',
        [["x"]],
    )


def test_groups_preserve_param_order() -> None:
    sql, params = render(
        Condition("status", Op.EQ, "active"),
        AnyOf(
            Condition("username", Op.EQ, "a"), AllOf(Condition("email", Op.EQ, "b"), Condition("fullname", Op.EQ, "c"))
        ),
    )
    assert sql == '("status" = %s AND ("username" = %s OR ("email" = %s AND "fullname" = %s)))'
    assert params == ["active", "a", "b", "c"]
    assert render(AnyOf()) == ("FALSE", [])


def test_identifiers_are_whitelisted_and_quoted() -> None:
    with pytest.raises(ValueError, match="Unknown field"):
        render(Condition('email" OR 1=1 --', Op.EQ, "x"))
    with pytest.raises(ValueError):
        render(Condition("email", Op.EQ, {"$ne": None}))


def test_order_by_adds_id_tiebreaker() -> None:
    translator = SqlTranslator(USERS)
    assert translator.order_by([SortSpec("username", SortDirection.ASC)]).as_string() == (
        ' ORDER BY "username" ASC NULLS FIRST, "id" ASC'
    )
    assert translator.order_by([]).as_string() == ""


def test_escape_like() -> None:
    assert escape_like("a%b_c\\") == "a\\%b\\_c\\\\"
