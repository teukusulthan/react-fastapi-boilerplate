"""Shared test fixtures (reused by tests/core, tests/db, tests/auth, tests/modules).

No external services: MongoDB is ``mongomock`` (behind the real ``MongoRepository``)
and Redis is ``fakeredis``. Settings never read ``apps/backend/.env``.

Key fixtures
------------
* ``make_settings(**overrides)`` / ``settings``      -> ``Settings`` for tests
* ``database`` / ``redis_client``                     -> injected providers
* ``app_routers``                                     -> registry subset mounted by ``app``
  (override it in your test package: ``@pytest.fixture def app_routers(): return [HEALTH, AUTH...]``)
* ``make_app(settings=None, routers=None)`` / ``app`` / ``client`` (TestClient, lifespan run)
* ``users_repo`` / ``permissions_repo`` / ``groups_repo`` / ``roles_repo`` / ``uploads_repo``
* ``permission_factory(**fields)``, ``user_factory(password=..., permission=..., **fields)``
* ``admin_permission`` / ``user_permission`` / ``admin_user`` / ``regular_user``
* ``login(user) -> AuthSession`` (tokens issued + single-session registered),
  ``auth_headers(user)`` / ``admin_headers`` / ``user_headers`` / ``internal_headers``
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any

# Isolate from the developer's .env and environment BEFORE importing app modules.
for _key in [k for k in os.environ if k.startswith("BE_")]:
    del os.environ[_key]
TEST_ENV: dict[str, str] = {
    "BE_ENV_FILE": "/nonexistent/.env.test",
    "BE_ENVIRONMENT": "test",
    "BE_JWT_SECRET": "test-secret-0123456789abcdef0123456789abcdef",
    "BE_JWT_ISSUER": "test-issuer",
    "BE_COOKIE_SECURE": "false",
    "BE_INTERNAL_TOKEN": "internal-test-token-0123456789abcdef0123",
    "BE_MONGO_DB": "app_test",
    "BE_LOG_LEVEL": "WARNING",
    "BE_ACCESS_LOG": "false",
}
os.environ.update(TEST_ENV)

import fakeredis
import mongomock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import core.security as security
from core.app_factory import create_app
from core.config import Settings, get_settings
from core.security import INTERNAL_TOKEN_HEADER, TokenPair, TokenStore, hash_password, issue_token_pair
from db.base import Repository
from db.mongo import MongoDatabase
from db.schema import GROUPS, PERMISSIONS, ROLES, UPLOADS, USERS
from router import HEALTH, RouterSpec

TEST_PASSWORD = "Sup3r-Secret-pass"


@pytest.fixture(autouse=True)
def _fast_bcrypt_and_fresh_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """bcrypt cost 4 in tests; reset the cached global settings around each test."""
    monkeypatch.setattr(security, "BCRYPT_ROUNDS", 4)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --------------------------------------------------------------- settings
@pytest.fixture
def make_settings() -> Callable[..., Settings]:
    def factory(**overrides: Any) -> Settings:
        return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]

    return factory


@pytest.fixture
def settings(make_settings: Callable[..., Settings]) -> Settings:
    return make_settings()


# -------------------------------------------------------------- providers
@pytest.fixture
def mongo_client() -> mongomock.MongoClient:
    return mongomock.MongoClient(tz_aware=True)


@pytest.fixture
def database(settings: Settings, mongo_client: mongomock.MongoClient) -> MongoDatabase:
    db = MongoDatabase(settings, client=mongo_client)
    db.ensure_schema()
    return db


@pytest.fixture
def redis_client() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def users_repo(database: MongoDatabase) -> Repository:
    return database.repository(USERS)


@pytest.fixture
def permissions_repo(database: MongoDatabase) -> Repository:
    return database.repository(PERMISSIONS)


@pytest.fixture
def groups_repo(database: MongoDatabase) -> Repository:
    return database.repository(GROUPS)


@pytest.fixture
def roles_repo(database: MongoDatabase) -> Repository:
    return database.repository(ROLES)


@pytest.fixture
def uploads_repo(database: MongoDatabase) -> Repository:
    return database.repository(UPLOADS)


# -------------------------------------------------------------------- app
@pytest.fixture
def app_routers() -> Sequence[RouterSpec]:
    """Routers mounted by ``app``. Override in a test package to mount yours."""
    return [HEALTH]


@pytest.fixture
def make_app(
    settings: Settings, database: MongoDatabase, redis_client: fakeredis.FakeRedis, app_routers: Sequence[RouterSpec]
) -> Callable[..., FastAPI]:
    def factory(app_settings: Settings | None = None, routers: Sequence[RouterSpec] | None = None) -> FastAPI:
        return create_app(
            app_settings or settings,
            database=database,
            redis=redis_client,
            routers=list(app_routers if routers is None else routers),
        )

    return factory


@pytest.fixture
def app(make_app: Callable[..., FastAPI]) -> FastAPI:
    return make_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


# -------------------------------------------------------------- factories
@pytest.fixture
def permission_factory(permissions_repo: Repository) -> Callable[..., dict[str, Any]]:
    counter = {"n": 0}

    def factory(**fields: Any) -> dict[str, Any]:
        counter["n"] += 1
        data = {"name": f"Permission {counter['n']}", "privileges": [], **fields}
        return permissions_repo.insert(data)

    return factory


@pytest.fixture
def user_factory(users_repo: Repository) -> Callable[..., dict[str, Any]]:
    counter = {"n": 0}

    def factory(
        *, password: str | None = TEST_PASSWORD, permission: dict[str, Any] | None = None, **fields: Any
    ) -> dict[str, Any]:
        counter["n"] += 1
        n = counter["n"]
        data: dict[str, Any] = {
            "username": f"user{n}",
            "fullname": f"User {n}",
            "email": f"user{n}@example.com",
            "status": "active",
            "email_verified": True,
            "password_hash": hash_password(password) if password else None,
            "permission_id": permission["id"] if permission else None,
            **fields,
        }
        return users_repo.insert(data)

    return factory


@pytest.fixture
def admin_permission(permission_factory: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    return permission_factory(name="Administrator", alias="admin", privileges=["*"])


@pytest.fixture
def user_permission(permission_factory: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    return permission_factory(name="User", alias="user", privileges=["profile:read"])


@pytest.fixture
def admin_user(user_factory: Callable[..., dict[str, Any]], admin_permission: dict[str, Any]) -> dict[str, Any]:
    return user_factory(username="admin", email="admin@example.com", permission=admin_permission)


@pytest.fixture
def regular_user(user_factory: Callable[..., dict[str, Any]], user_permission: dict[str, Any]) -> dict[str, Any]:
    return user_factory(username="alice", email="alice@example.com", permission=user_permission)


# ------------------------------------------------------------------- auth
@dataclass(frozen=True)
class AuthSession:
    pair: TokenPair
    headers: dict[str, str]  # Authorization: Bearer <access>
    cookies: dict[str, str]  # token / refresh_token


@pytest.fixture
def login(settings: Settings, redis_client: fakeredis.FakeRedis) -> Callable[[dict[str, Any]], AuthSession]:
    """Issue a token pair for ``user`` exactly like a successful login would."""

    def do_login(user: dict[str, Any]) -> AuthSession:
        pair = issue_token_pair(user["id"], settings)
        TokenStore(redis_client, settings).set_active_session(user["id"], pair.session_id)
        return AuthSession(
            pair=pair,
            headers={"Authorization": f"Bearer {pair.access.token}"},
            cookies={"token": pair.access.token, "refresh_token": pair.refresh.token},
        )

    return do_login


@pytest.fixture
def auth_headers(login: Callable[[dict[str, Any]], AuthSession]) -> Callable[[dict[str, Any]], dict[str, str]]:
    return lambda user: login(user).headers


@pytest.fixture
def admin_headers(
    auth_headers: Callable[[dict[str, Any]], dict[str, str]], admin_user: dict[str, Any]
) -> dict[str, str]:
    return auth_headers(admin_user)


@pytest.fixture
def user_headers(
    auth_headers: Callable[[dict[str, Any]], dict[str, str]], regular_user: dict[str, Any]
) -> dict[str, str]:
    return auth_headers(regular_user)


@pytest.fixture
def internal_headers(settings: Settings) -> dict[str, str]:
    assert settings.INTERNAL_TOKEN is not None
    return {INTERNAL_TOKEN_HEADER: settings.INTERNAL_TOKEN.get_secret_value()}
