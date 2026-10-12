"""Principal resolution + RBAC dependencies, through a throwaway router."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from core.deps import (
    AdminUserDep,
    CurrentUser,
    CurrentUserDep,
    InternalDep,
    OptionalUserDep,
    UserOrInternalDep,
    require_privilege,
)
from core.security import TokenStore, decode_token
from router import HEALTH, RouterSpec

router = APIRouter(prefix="/p")


def _view(user: CurrentUser | None) -> dict:
    if user is None:
        return {"anonymous": True}
    return {"id": user.id, "role": user.role, "superuser": user.is_superuser, "internal": user.is_internal}


@router.get("/me")
def me(user: CurrentUserDep) -> dict:
    return _view(user)


@router.get("/admin")
def admin(user: AdminUserDep) -> dict:
    return _view(user)


@router.get("/priv")
def priv(user: CurrentUser = Depends(require_privilege("profile:read"))) -> dict:
    return _view(user)


@router.get("/priv-any")
def priv_any(user: CurrentUser = Depends(require_privilege("x:y", "profile:read", any_of=True))) -> dict:
    return _view(user)


@router.get("/priv-internal")
def priv_internal(user: CurrentUser = Depends(require_privilege("x:y", allow_internal=True))) -> dict:
    return _view(user)


@router.get("/internal")
def internal(user: InternalDep) -> dict:
    return _view(user)


@router.get("/either")
def either(user: UserOrInternalDep) -> dict:
    return _view(user)


@router.get("/optional")
def optional(user: OptionalUserDep) -> dict:
    return _view(user)


@pytest.fixture
def app_routers():
    return [HEALTH, RouterSpec("p", __name__)]


def code(resp) -> str:
    return resp.json()["metaData"]["errorCode"]


def test_requires_credentials(client: TestClient) -> None:
    resp = client.get("/p/me")
    assert resp.status_code == 401
    assert code(resp) == "AUTHENTICATION_ERROR"
    assert client.get("/p/optional").json() == {"anonymous": True}


def test_bearer_and_cookie(client: TestClient, regular_user, login) -> None:
    session = login(regular_user)
    by_header = client.get("/p/me", headers=session.headers)
    assert by_header.status_code == 200
    assert by_header.json() == {"id": regular_user["id"], "role": "user", "superuser": False, "internal": False}
    client.cookies.set("token", session.pair.access.token)
    assert client.get("/p/me").status_code == 200


def test_refresh_token_not_accepted_as_access(client: TestClient, regular_user, login) -> None:
    session = login(regular_user)
    resp = client.get("/p/me", headers={"Authorization": f"Bearer {session.pair.refresh.token}"})
    assert resp.status_code == 401


def test_revoked_token(client: TestClient, regular_user, login, settings, redis_client) -> None:
    session = login(regular_user)
    TokenStore(redis_client, settings).revoke(decode_token(session.pair.access.token, settings, "access"))
    assert client.get("/p/me", headers=session.headers).status_code == 401


@pytest.mark.parametrize(
    "changes",
    [{"status": "blocked"}, {"status": "pending"}, {"expired_at": datetime.now(timezone.utc) - timedelta(days=1)}],
)
def test_inactive_or_expired_user(client: TestClient, regular_user, login, users_repo, changes) -> None:
    session = login(regular_user)
    users_repo.update(regular_user["id"], changes)
    assert client.get("/p/me", headers=session.headers).status_code == 401


def test_deleted_user(client: TestClient, regular_user, login, users_repo) -> None:
    session = login(regular_user)
    users_repo.delete(regular_user["id"])
    assert client.get("/p/me", headers=session.headers).status_code == 401


def test_single_session_enforced(client: TestClient, user_factory, user_permission, login) -> None:
    user = user_factory(permission=user_permission, multi_login=False)
    first = login(user)
    second = login(user)  # newer login replaces the active session
    assert client.get("/p/me", headers=second.headers).status_code == 200
    assert client.get("/p/me", headers=first.headers).status_code == 401


def test_admin_rbac(client: TestClient, admin_headers, user_headers) -> None:
    assert client.get("/p/admin", headers=admin_headers).json()["superuser"] is True
    resp = client.get("/p/admin", headers=user_headers)
    assert resp.status_code == 403
    assert code(resp) == "PERMISSION_ERROR"


def test_owner_alias_is_superuser(client: TestClient, user_factory, permission_factory, auth_headers) -> None:
    owner = user_factory(permission=permission_factory(alias="owner"))
    assert client.get("/p/admin", headers=auth_headers(owner)).status_code == 200


def test_user_without_permission(client: TestClient, user_factory, auth_headers) -> None:
    headers = auth_headers(user_factory())
    body = client.get("/p/me", headers=headers).json()
    assert body["role"] is None
    assert client.get("/p/priv", headers=headers).status_code == 403


def test_privileges(client: TestClient, admin_headers, user_headers) -> None:
    assert client.get("/p/priv", headers=user_headers).status_code == 200
    assert client.get("/p/priv-any", headers=user_headers).status_code == 200
    assert client.get("/p/priv-internal", headers=user_headers).status_code == 403
    assert client.get("/p/priv-internal", headers=admin_headers).status_code == 200


def test_internal_token(client: TestClient, internal_headers, user_headers) -> None:
    assert client.get("/p/internal", headers=internal_headers).json()["internal"] is True
    assert client.get("/p/internal", headers=user_headers).status_code == 401
    assert client.get("/p/internal", headers={"X-Internal-Token": "wrong"}).status_code == 401
    assert client.get("/p/either", headers=internal_headers).status_code == 200
    assert client.get("/p/either", headers=user_headers).status_code == 200
    # internal principal is not a user / not an admin
    assert client.get("/p/me", headers=internal_headers).status_code == 403
    assert client.get("/p/admin", headers=internal_headers).status_code == 403
    assert client.get("/p/priv-internal", headers=internal_headers).status_code == 200
    # a present-but-invalid internal token never falls back to the bearer token
    resp = client.get("/p/me", headers={**user_headers, "X-Internal-Token": "wrong"})
    assert resp.status_code == 401


# ---------------------------------------------------------- supabase mode
SUPA_SECRET = "supabase-jwt-secret-0123456789abcdef0123"


@pytest.fixture
def supabase_client(make_settings, make_app) -> TestClient:
    s = make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET=SUPA_SECRET)
    with TestClient(make_app(s)) as c:
        yield c


def _supa_token(sub: str, email: str | None = "new.person@example.com", **extra) -> dict[str, str]:
    claims = {"sub": sub, "aud": "authenticated", "exp": int(time.time()) + 300, **extra}
    if email:
        claims["email"] = email
    return {"Authorization": f"Bearer {jwt.encode(claims, SUPA_SECRET, algorithm='HS256')}"}


def test_supabase_auto_provisions_user(supabase_client, users_repo, user_permission) -> None:
    sub = "8d0f6c1e-4f0a-4c8e-9a51-2f7f1d3c9b10"
    headers = _supa_token(sub, user_metadata={"full_name": "New Person"})
    resp = supabase_client.get("/p/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == sub
    assert resp.json()["role"] == "user"
    stored = users_repo.get_by_id(sub)
    assert stored["auth_provider"] == "supabase"
    assert stored["external_id"] == sub
    assert stored["fullname"] == "New Person"
    assert stored["status"] == "active"
    # second request reuses the row
    assert supabase_client.get("/p/me", headers=headers).status_code == 200
    assert users_repo.count({"external_id": sub}) == 1


def test_supabase_rejects_local_tokens_and_email_conflicts(supabase_client, regular_user, login) -> None:
    assert supabase_client.get("/p/me", headers=login(regular_user).headers).status_code == 401
    clash = _supa_token("0b9f7f8e-0000-4000-8000-000000000001", email=regular_user["email"])
    resp = supabase_client.get("/p/me", headers=clash)
    assert resp.status_code == 409
    assert (
        supabase_client.get(
            "/p/me", headers=_supa_token("0b9f7f8e-0000-4000-8000-000000000002", email=None)
        ).status_code
        == 401
    )


def test_supabase_links_preprovisioned_user_by_email(
    supabase_client, users_repo, user_factory, admin_permission
) -> None:
    # An admin created the row ahead of time (/user/add in supabase mode): no external_id yet.
    pre = user_factory(
        email="invited@example.com", auth_provider="supabase", password_hash=None, permission=admin_permission
    )
    sub = "1c7e0d2a-5b8f-4c3d-9e6a-0f1b2c3d4e5f"
    resp = supabase_client.get("/p/me", headers=_supa_token(sub, email="Invited@Example.com"))
    assert resp.status_code == 200
    assert resp.json()["id"] == pre["id"]
    assert resp.json()["role"] == "admin"
    assert users_repo.get_by_id(pre["id"])["external_id"] == sub
    assert users_repo.count({"email": "invited@example.com"}) == 1
    # subsequent requests resolve through external_id
    assert supabase_client.get("/p/me", headers=_supa_token(sub, email="invited@example.com")).json()["id"] == pre["id"]
    # an already-linked row is never re-linked to a different identity
    other = _supa_token("2c7e0d2a-5b8f-4c3d-9e6a-0f1b2c3d4e5f", email="invited@example.com")
    assert supabase_client.get("/p/me", headers=other).status_code == 409
