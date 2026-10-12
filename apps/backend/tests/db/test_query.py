from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError as PydanticValidationError

from core.errors import ValidationError
from db.base import AllOf, AnyOf, Condition, Op, SortDirection, SortSpec
from db.query import build_query_spec
from db.schema import PERMISSIONS, UPLOADS, USERS
from dto.common import FindDTO

UID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


def spec_for(entity=USERS, **body):
    return build_query_spec(FindDTO.model_validate(body), entity)


def details(exc: pytest.ExceptionInfo) -> dict[str, str]:
    return {d["field"]: d["message"] for d in exc.value.details}


def test_defaults() -> None:
    spec = spec_for()
    assert spec.where == ()
    assert spec.sort == (SortSpec("created_at", SortDirection.DESC),)
    assert (spec.page, spec.size, spec.offset, spec.limit) == (1, 10, 0, 10)


def test_pagination_bounds() -> None:
    assert spec_for(page=3, size=20).offset == 40
    for bad in ({"page": 0}, {"size": 0}, {"size": 101}, {"order": "sideways"}):
        with pytest.raises(PydanticValidationError):
            FindDTO.model_validate(bad)


def test_max_page_size_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from core.config import get_settings

    monkeypatch.setenv("BE_MAX_PAGE_SIZE", "5")
    get_settings.cache_clear()
    with pytest.raises(PydanticValidationError):
        FindDTO(size=6)
    assert FindDTO(size=5).size == 5


def test_search_defaults_to_all_searchable_fields() -> None:
    (group,) = spec_for(search="  ann  ").where
    assert isinstance(group, AnyOf)
    assert {c.field for c in group.items} == USERS.searchable
    assert all(c.op == Op.CONTAINS and c.value == "ann" for c in group.items)


def test_search_by_camel_or_snake_and_legacy_key() -> None:
    (group,) = spec_for(search="x", searchBy=["fullname", "email"]).where
    assert [c.field for c in group.items] == ["fullname", "email"]
    (legacy,) = spec_for(search="x", search_by=["username"]).where
    assert [c.field for c in legacy.items] == ["username"]


def test_search_by_non_searchable_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        spec_for(search="x", searchBy=["passwordHash", "status"])
    assert set(details(exc)) == {"searchBy[0]", "searchBy[1]"}


def test_unknown_and_sensitive_filter_fields_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        spec_for(
            filters=[
                {"field": "password_hash", "operator": "is exist"},
                {"field": "nope", "operator": "is", "value": {"is": 1}},
                {"field": "twoFactorSecret", "operator": "is exist"},
            ]
        )
    assert set(details(exc)) == {"filters[0].field", "filters[1].field", "filters[2].field"}
    assert exc.value.status_code == 422


def test_operator_injection_rejected_by_dto() -> None:
    with pytest.raises(PydanticValidationError):
        FindDTO.model_validate({"filters": [{"field": "email", "operator": "is", "value": {"is": {"$ne": None}}}]})
    with pytest.raises(PydanticValidationError):
        FindDTO.model_validate({"filters": [{"field": "email", "operator": "$where", "value": {}}]})


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        ({"field": "status", "operator": "is", "value": {"is": "active"}}, Condition("status", Op.EQ, "active")),
        ({"field": "status", "operator": "is not", "value": {"is": "active"}}, Condition("status", Op.NE, "active")),
        (
            {"field": "status", "operator": "is one of", "value": {"isOneOf": ["a", "b"]}},
            Condition("status", Op.IN, ("a", "b")),
        ),
        (
            {"field": "status", "operator": "is not one of", "value": {"isOneOf": ["a"]}},
            Condition("status", Op.NIN, ("a",)),
        ),
        ({"field": "phone", "operator": "is exist"}, Condition("phone", Op.EXISTS)),
        ({"field": "phone", "operator": "is not exist"}, Condition("phone", Op.NOT_EXISTS)),
        ({"field": "email", "operator": "is contains", "value": {"is": "a.b"}}, Condition("email", Op.CONTAINS, "a.b")),
        (
            {"field": "email", "operator": "is not contains", "value": {"is": "x"}},
            Condition("email", Op.NOT_CONTAINS, "x"),
        ),
        (
            {"field": "emailVerified", "operator": "is", "value": {"is": "true"}},
            Condition("email_verified", Op.EQ, True),
        ),
        (
            {"field": "permissionId", "operator": "is", "value": {"is": UID.upper()}},
            Condition("permission_id", Op.EQ, UID),
        ),
    ],
)
def test_operator_mapping(item, expected) -> None:
    assert spec_for(filters=[item]).where == (expected,)


def test_range_and_datetime_coercion() -> None:
    where = spec_for(
        filters=[
            {"field": "createdAt", "operator": "greater than equals", "value": {"gte": "2024-01-01T00:00:00Z"}},
            {"field": "createdAt", "operator": "less than equals", "value": {"lte": 1735689600000}},
        ]
    ).where
    assert where[0] == Condition("created_at", Op.GTE, datetime(2024, 1, 1, tzinfo=timezone.utc))
    assert where[1] == Condition("created_at", Op.LTE, datetime(2025, 1, 1, tzinfo=timezone.utc))


def test_between_and_not_between() -> None:
    between, not_between = spec_for(
        entity=UPLOADS,
        filters=[
            {"field": "filesize", "operator": "is between", "value": {"gte": 1, "lte": "10"}},
            {"field": "filesize", "operator": "is not between", "value": {"gte": 1, "lte": 10}},
        ],
    ).where
    assert between == AllOf(Condition("filesize", Op.GTE, 1), Condition("filesize", Op.LTE, 10))
    assert not_between == AnyOf(Condition("filesize", Op.LT, 1), Condition("filesize", Op.GT, 10))


def test_list_field_all_operator() -> None:
    (cond,) = spec_for(
        entity=PERMISSIONS, filters=[{"field": "privileges", "operator": "all", "value": {"isOneOf": ["a", "b"]}}]
    ).where
    assert cond == Condition("privileges", Op.ALL, ("a", "b"))
    with pytest.raises(ValidationError):
        spec_for(filters=[{"field": "status", "operator": "all", "value": {"isOneOf": ["a"]}}])


@pytest.mark.parametrize(
    "item",
    [
        {"field": "status", "operator": "is"},  # missing operand
        {"field": "status", "operator": "is one of", "value": {}},
        {"field": "permissionId", "operator": "is", "value": {"is": "not-a-uuid"}},
        {"field": "emailVerified", "operator": "is", "value": {"is": "maybe"}},
        {"field": "createdAt", "operator": "greater than equals", "value": {"gte": "yesterday"}},
        {"field": "emailVerified", "operator": "greater than equals", "value": {"gte": 1}},
        {"field": "createdAt", "operator": "is contains", "value": {"is": "2024"}},
    ],
)
def test_invalid_operands(item) -> None:
    with pytest.raises(ValidationError):
        spec_for(filters=[item])


def test_or_group() -> None:
    where = spec_for(
        filters=[
            {"field": "status", "operator": "is", "value": {"is": "active"}},
            {"field": "username", "operator": "is", "value": {"is": "a"}, "operatorType": "or"},
            {"field": "username", "operator": "is", "value": {"is": "b"}, "operator_type": "or"},
        ]
    ).where
    assert where == (
        Condition("status", Op.EQ, "active"),
        AnyOf(Condition("username", Op.EQ, "a"), Condition("username", Op.EQ, "b")),
    )


def test_sorting() -> None:
    assert spec_for(orderBy="username", order="ASC").sort == (SortSpec("username", SortDirection.ASC),)
    with pytest.raises(ValidationError) as exc:
        spec_for(orderBy="passwordHash")
    assert "orderBy" in details(exc)


def test_endpoint_overrides_and_extra_where() -> None:
    dto = FindDTO.model_validate({"filters": [{"field": "status", "operator": "is", "value": {"is": "x"}}]})
    with pytest.raises(ValidationError):
        build_query_spec(dto, USERS, filterable={"email"})
    scope = Condition("created_by", Op.EQ, "me")
    spec = build_query_spec(FindDTO(), USERS, extra_where=[scope])
    assert spec.where == (scope,)
