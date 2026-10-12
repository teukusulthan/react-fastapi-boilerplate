"""MongoRepository against mongomock (real translator + index semantics)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.errors import ConflictError
from db.base import AnyOf, Condition, Op, QuerySpec, SortDirection, SortSpec
from db.mongo.indexes import index_specs
from db.query import build_query_spec
from db.schema import USERS
from dto.common import FindDTO
from util.helper import is_uuid


def make_user(repo, n: int, **extra):
    return repo.insert(
        {"username": f"u{n}", "email": f"u{n}@x.io", "fullname": f"User {n}", "status": "active", **extra}
    )


def test_insert_sets_id_defaults_and_utc_timestamps(users_repo, mongo_client, settings) -> None:
    user = make_user(users_repo, 1)
    assert is_uuid(user["id"])
    assert user["created_at"].tzinfo is not None and user["created_at"] == user["updated_at"]
    assert user["multi_login"] is True and user["two_factor_enabled"] is False and user["auth_provider"] == "local"
    assert set(user) == USERS.storage_fields
    raw = mongo_client[settings.MONGO_DB]["users"].find_one({"_id": user["id"]})
    assert "id" not in raw
    fetched = users_repo.get_by_id(user["id"])
    assert fetched["id"] == user["id"] and fetched["created_at"].tzinfo is not None


def test_unknown_or_null_required_fields_rejected(users_repo) -> None:
    with pytest.raises(ValueError, match="Unknown field"):
        users_repo.insert({"username": "a", "email": "a@x.io", "isAdmin": True})
    with pytest.raises(ValueError, match="cannot be null"):
        users_repo.insert({"username": "a"})
    with pytest.raises(ValueError, match="Unknown field"):
        users_repo.update("x", {"$set": 1})


def test_unique_conflicts(users_repo) -> None:
    make_user(users_repo, 1, phone="+1")
    with pytest.raises(ConflictError) as exc:
        users_repo.insert({"username": "u1", "email": "other@x.io"})
    assert exc.value.status_code == 409
    with pytest.raises(ConflictError):
        users_repo.insert({"username": "other", "email": "u1@x.io"})
    with pytest.raises(ConflictError):
        make_user(users_repo, 2, phone="+1")
    # many NULL phones / external ids are fine (partial unique index)
    make_user(users_repo, 3)
    make_user(users_repo, 4)
    second = make_user(users_repo, 5)
    with pytest.raises(ConflictError):
        users_repo.update(second["id"], {"email": "u1@x.io"})


def test_conflict_names_the_duplicate_field(users_repo) -> None:
    # mongomock's DuplicateKeyError has no keyPattern/index name: the repository probes for the field.
    make_user(users_repo, 1, phone="+1")
    cases = [
        ({"username": "u1", "email": "new@x.io"}, "username"),
        ({"username": "new", "email": "u1@x.io"}, "email"),
        ({"username": "new2", "email": "new2@x.io", "phone": "+1"}, "phone"),
    ]
    for data, field in cases:
        with pytest.raises(ConflictError) as exc:
            users_repo.insert(data)
        assert exc.value.message == f"{field} already exists"
        assert exc.value.details == [{"field": field, "message": "already exists"}]
    other = make_user(users_repo, 2)
    with pytest.raises(ConflictError) as exc:
        users_repo.update(other["id"], {"email": "u1@x.io"})
    assert exc.value.details == [{"field": "email", "message": "already exists"}]


def test_index_specs_cover_unique_fields() -> None:
    names = {opts["name"] for _, opts in index_specs(USERS)}
    assert {
        "uniq_username",
        "uniq_email",
        "uniq_phone",
        "uniq_external_id",
        "idx_created_at",
        "idx_permission_id",
    } <= names
    phone = next(opts for keys, opts in index_specs(USERS) if opts["name"] == "uniq_phone")
    assert phone["partialFilterExpression"] == {"phone": {"$type": "string"}}


def test_update_is_partial_and_never_upserts(users_repo) -> None:
    user = make_user(users_repo, 1)
    updated = users_repo.update(
        user["id"], {"fullname": "New", "id": "hijack", "created_at": datetime(2000, 1, 1, tzinfo=timezone.utc)}
    )
    assert updated["fullname"] == "New" and updated["id"] == user["id"]
    assert updated["created_at"] == user["created_at"]
    assert updated["updated_at"] >= user["updated_at"]
    assert users_repo.update("missing-id", {"fullname": "x"}) is None
    assert users_repo.count() == 1


def test_find_paginates_sorts_and_counts(users_repo) -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(7):
        make_user(users_repo, i, created_at=base + timedelta(days=i))
    items, total = users_repo.find(QuerySpec.of(sort=[SortSpec("created_at", SortDirection.DESC)], page=2, size=3))
    assert total == 7
    assert [u["username"] for u in items] == ["u3", "u2", "u1"]


def test_find_with_parsed_query_and_literal_search(users_repo) -> None:
    make_user(users_repo, 1, fullname="Ann (admin) .*")
    make_user(users_repo, 2, fullname="Bob", status="blocked")
    make_user(users_repo, 3, fullname="annabel")
    spec = build_query_spec(
        FindDTO.model_validate({"search": "ANN", "searchBy": ["fullname"], "orderBy": "username", "order": "asc"}),
        USERS,
    )
    items, total = users_repo.find(spec)
    assert total == 2 and [u["username"] for u in items] == ["u1", "u3"]
    regexy = build_query_spec(FindDTO.model_validate({"search": ".*", "searchBy": ["fullname"]}), USERS)
    assert [u["username"] for u in users_repo.find(regexy)[0]] == ["u1"]
    blocked = build_query_spec(
        FindDTO.model_validate({"filters": [{"field": "status", "operator": "is not", "value": {"is": "active"}}]}),
        USERS,
    )
    assert [u["username"] for u in users_repo.find(blocked)[0]] == ["u2"]


def test_list_field_semantics(permissions_repo) -> None:
    permissions_repo.insert({"name": "a", "alias": "a", "privileges": ["x", "y"]})
    permissions_repo.insert({"name": "b", "alias": "b", "privileges": ["y"]})
    permissions_repo.insert({"name": "c", "alias": "c"})

    def names(*where):
        return sorted(p["name"] for p in permissions_repo.find_all(list(where)))

    assert names(Condition("privileges", Op.EQ, "x")) == ["a"]
    assert names(Condition("privileges", Op.IN, ("x", "y"))) == ["a", "b"]
    assert names(Condition("privileges", Op.ALL, ("x", "y"))) == ["a"]
    assert names(Condition("privileges", Op.NIN, ("x",))) == ["b", "c"]


def test_find_one_exists_count_mapping_and_groups(users_repo) -> None:
    a = make_user(users_repo, 1)
    make_user(users_repo, 2, phone="+62")
    assert users_repo.find_one({"email": "u1@x.io"})["id"] == a["id"]
    assert users_repo.exists({"username": "u2"})
    assert users_repo.count({"phone": None}) == 1
    assert users_repo.count(AnyOf(Condition("username", Op.EQ, "u1"), Condition("username", Op.EQ, "u2"))) == 2
    assert users_repo.count(AnyOf()) == 0
    assert {u["id"] for u in users_repo.get_many_by_ids([a["id"], a["id"], "missing"])} == {a["id"]}


def test_delete_and_update_many(users_repo) -> None:
    a = make_user(users_repo, 1)
    make_user(users_repo, 2)
    assert users_repo.update_many({"status": "active"}, {"status": "blocked"}) == 2
    assert users_repo.count({"status": "blocked"}) == 2
    assert users_repo.delete(a["id"]) is True
    assert users_repo.delete(a["id"]) is False
    with pytest.raises(ValueError):
        users_repo.delete_many({})
    assert users_repo.delete_many({"status": "blocked"}) == 1
