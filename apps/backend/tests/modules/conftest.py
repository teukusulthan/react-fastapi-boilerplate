"""Fixtures for the CRUD module tests (user, group, permission, role, upload, seed).

* Mounts the five module routers.
* ``database`` is parametrized: every module test runs against the Mongo fake
  (mongomock) and — when ``TEST_POSTGRES_DSN`` is set — against a real Postgres
  with ``migrations/supabase/*.sql`` applied (tables truncated per test). The
  Postgres variant carries the ``integration`` marker::

      TEST_POSTGRES_DSN=postgresql://postgres@127.0.0.1:5432/app_test pytest tests/modules

* ``fake_storage`` replaces S3 with an in-memory fake through
  ``app.dependency_overrides[get_storage_factory]``.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from core.config import Settings
from db.mongo import MongoDatabase
from router import HEALTH, ROUTERS
from service.upload import get_storage_factory
from util.s3 import S3Storage

MODULES = ("user", "group", "permission", "role", "upload")
PG_DSN = os.environ.get("TEST_POSTGRES_DSN")
MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations" / "supabase"
APP_TABLES = "public.users, public.uploads, public.roles, public.groups, public.permissions"


@pytest.fixture
def app_routers():
    return [HEALTH, *[spec for spec in ROUTERS if spec.name in MODULES]]


# ------------------------------------------------------------- providers
@pytest.fixture(scope="session")
def pg_database() -> Iterator[Any]:
    import psycopg

    from db.supabase import PostgresDatabase

    assert PG_DSN
    with psycopg.connect(PG_DSN, autocommit=True) as conn:
        conn.execute(f"DROP TABLE IF EXISTS {APP_TABLES} CASCADE")
        for migration in sorted(MIGRATIONS.glob("*.sql")):
            conn.execute(migration.read_text())
    pg_settings = Settings(_env_file=None, DB_PROVIDER="supabase", SUPABASE_DB_URL=PG_DSN, SUPABASE_DB_POOL_MIN=0)  # type: ignore[call-arg]
    database = PostgresDatabase(pg_settings)
    database.open()
    database.ensure_schema()
    yield database
    database.close()


# The Postgres variant only exists when TEST_POSTGRES_DSN is set (no skip noise otherwise).
PROVIDERS = [
    pytest.param("mongo", id="mongo"),
    *([pytest.param("postgres", id="postgres", marks=pytest.mark.integration)] if PG_DSN else []),
]


@pytest.fixture(params=PROVIDERS)
def database(request: pytest.FixtureRequest, settings: Settings, mongo_client: Any) -> Any:
    if request.param == "mongo":
        db = MongoDatabase(settings, client=mongo_client)
        db.ensure_schema()
        return db
    import psycopg

    pg = request.getfixturevalue("pg_database")
    with psycopg.connect(PG_DSN, autocommit=True) as conn:  # type: ignore[arg-type]
        conn.execute(f"TRUNCATE {APP_TABLES} CASCADE")
    return pg


# --------------------------------------------------------------- storage
@dataclass
class FakeS3Client:
    objects: dict[str, dict[str, Any]] = field(default_factory=dict)
    deleted: list[str] = field(default_factory=list)

    def upload_fileobj(self, fileobj, bucket, key, ExtraArgs=None, Config=None):  # noqa: N803  # boto3 names
        self.objects[key] = {"bucket": bucket, "body": fileobj.read(), **(ExtraArgs or {})}

    def delete_object(self, Bucket, Key):  # noqa: N803
        self.deleted.append(Key)
        self.objects.pop(Key, None)

    def generate_presigned_url(self, operation, Params, ExpiresIn):  # noqa: N803
        return f"https://s3.test/{Params['Bucket']}/{Params['Key']}?expires={ExpiresIn}"


@pytest.fixture
def fake_s3() -> FakeS3Client:
    return FakeS3Client()


@pytest.fixture
def with_storage(fake_s3: FakeS3Client) -> Callable[[FastAPI], FastAPI]:
    """Install the fake S3 on an app (``with_storage(make_app(...))``)."""
    storage = S3Storage(client=fake_s3, bucket="test-bucket", presign_ttl=60)

    def install(app: FastAPI) -> FastAPI:
        app.dependency_overrides[get_storage_factory] = lambda: lambda: storage
        return app

    return install


@pytest.fixture
def fake_storage(app: FastAPI, with_storage: Callable[[FastAPI], FastAPI], fake_s3: FakeS3Client) -> FakeS3Client:
    with_storage(app)
    return fake_s3
