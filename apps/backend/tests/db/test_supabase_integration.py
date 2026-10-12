"""PostgresRepository + migrations against a REAL Postgres.

Skipped unless ``TEST_POSTGRES_DSN`` points at a disposable database, e.g.::

    TEST_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/app_test pytest -m integration

The test applies ``migrations/supabase/001_init.sql`` (twice, to prove idempotency)
after dropping the app tables in that database.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.errors import ConflictError, ValidationError
from db.base import Condition, Op, QuerySpec, SortDirection, SortSpec
from db.query import build_query_spec
from db.schema import PERMISSIONS, UPLOADS, USERS
from dto.common import FindDTO
from util.helper import is_uuid

DSN = os.environ.get("TEST_POSTGRES_DSN")
pytestmark = [pytest.mark.integration, pytest.mark.skipif(not DSN, reason="TEST_POSTGRES_DSN not set")]
MIGRATION = Path(__file__).resolve().parents[2] / "migrations" / "supabase" / "001_init.sql"


@pytest.fixture
def pg(make_settings):
    import psycopg

    from db.supabase import PostgresDatabase

    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute(
            "DROP TABLE IF EXISTS public.users, public.uploads, public.roles, public.groups, public.permissions CASCADE"
        )
        sql_text = MIGRATION.read_text()
        conn.execute(sql_text)
        conn.execute(sql_text)  # idempotent
    database = PostgresDatabase(make_settings(DB_PROVIDER="supabase", SUPABASE_DB_URL=DSN, SUPABASE_DB_POOL_MIN=0))
    database.open()
    database.ensure_schema()
    database.ping()
    yield database
    database.close()


def test_crud_roundtrip(pg) -> None:
    users = pg.repository(USERS)
    perms = pg.repository(PERMISSIONS)
    perm = perms.insert({"name": "Admin", "alias": "admin", "privileges": ["a", "b"]})
    assert perm["privileges"] == ["a", "b"] and is_uuid(perm["id"])
    user = users.insert(
        {
            "username": "u1",
            "email": "u1@x.io",
            "status": "active",
            "permission_id": perm["id"],
            "settings": {"theme": "dark", "at": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        }
    )
    assert set(user) == USERS.storage_fields
    assert user["created_at"].tzinfo is not None
    assert user["settings"] == {"theme": "dark", "at": "2024-01-01T00:00:00+00:00"}
    assert users.get_by_id(user["id"]) == user
    assert users.get_by_id("not-a-uuid") is None

    updated = users.update(user["id"], {"fullname": "New"})
    assert updated["fullname"] == "New" and updated["updated_at"] >= user["updated_at"]
    assert users.update("00000000-0000-4000-8000-000000000000", {"fullname": "x"}) is None
    assert users.find_one({"email": "u1@x.io"})["id"] == user["id"]
    assert users.count({"phone": None}) == 1
    assert users.delete(user["id"]) and not users.delete(user["id"])


def test_constraints_map_to_app_errors(pg) -> None:
    users = pg.repository(USERS)
    users.insert({"username": "u1", "email": "u1@x.io"})
    users.insert({"username": "u2", "email": "u2@x.io"})  # NULL phone twice is fine
    with pytest.raises(ConflictError) as exc:
        users.insert({"username": "u1", "email": "other@x.io"})
    assert exc.value.details == [{"field": "username", "message": "already exists"}]
    with pytest.raises(ValidationError) as fk:
        users.insert({"username": "u3", "email": "u3@x.io", "permission_id": "00000000-0000-4000-8000-000000000000"})
    assert fk.value.details[0]["field"] == "permissionId"
    with pytest.raises(ValidationError) as check:
        users.insert({"username": "u4", "email": "u4@x.io", "status": "weird"})
    assert check.value.details[0]["field"] == "status"


def test_find_and_filters_match_mongo_semantics(pg) -> None:
    users = pg.repository(USERS)
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(5):
        users.insert(
            {
                "username": f"u{i}",
                "email": f"u{i}@x.io",
                "fullname": "Ann 50%" if i == 1 else f"N{i}",
                "status": "active" if i % 2 else "blocked",
                "created_at": base + timedelta(days=i),
            }
        )
    items, total = users.find(QuerySpec.of(sort=[SortSpec("created_at", SortDirection.DESC)], page=2, size=2))
    assert total == 5 and [u["username"] for u in items] == ["u2", "u1"]

    spec = build_query_spec(FindDTO.model_validate({"search": "50%", "searchBy": ["fullname"]}), USERS)
    assert [u["username"] for u in users.find(spec)[0]] == ["u1"]
    ne = build_query_spec(
        FindDTO.model_validate({"filters": [{"field": "status", "operator": "is not", "value": {"is": "active"}}]}),
        USERS,
    )
    assert users.find(ne)[1] == 3
    rng = build_query_spec(
        FindDTO.model_validate(
            {
                "filters": [
                    {
                        "field": "createdAt",
                        "operator": "is between",
                        "value": {"gte": "2024-01-02", "lte": "2024-01-03T00:00:00Z"},
                    }
                ]
            }
        ),
        USERS,
    )
    assert sorted(u["username"] for u in users.find(rng)[0]) == ["u1", "u2"]
    assert users.count(Condition("permission_id", Op.EQ, "junk")) == 0
    assert users.update_many({"status": "blocked"}, {"status": "active"}) == 3
    assert users.delete_many({"status": "active"}) == 5


def test_list_fields(pg) -> None:
    uploads = pg.repository(UPLOADS)
    for i, tags in enumerate([["x", "y"], ["y"], []]):
        uploads.insert({"bucket": "b", "object_key": f"k{i}", "filename": f"f{i}", "tags": tags})

    def keys(cond):
        return sorted(u["object_key"] for u in uploads.find_all([cond]))

    assert keys(Condition("tags", Op.EQ, "x")) == ["k0"]
    assert keys(Condition("tags", Op.IN, ("x", "y"))) == ["k0", "k1"]
    assert keys(Condition("tags", Op.ALL, ("x", "y"))) == ["k0"]
    assert keys(Condition("tags", Op.NIN, ("x",))) == ["k1", "k2"]
    assert len(uploads.get_many_by_ids([u["id"] for u in uploads.find_all()])) == 3
