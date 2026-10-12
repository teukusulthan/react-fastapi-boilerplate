"""BE_AUTH_PROVIDER=supabase: only /auth/me and /auth/logout are mounted."""

from __future__ import annotations

import time

import jwt
import pytest

SUPA_SECRET = "supabase-jwt-secret-0123456789abcdef0123"


@pytest.fixture
def supa(make_client, make_settings):
    return make_client(make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET=SUPA_SECRET))


def _token(**claims):
    now = int(time.time())
    payload = {
        "sub": "6f1c1f2e-8a3b-4b8e-9c1d-2a1b3c4d5e6f",
        "email": "supa@example.com",
        "aud": "authenticated",
        "iat": now,
        "exp": now + 600,
        **claims,
    }
    return jwt.encode(payload, SUPA_SECRET, algorithm="HS256")


def test_me_with_supabase_jwt(supa, user_permission, users_repo):
    resp = supa.get("/auth/me", headers={"Authorization": f"Bearer {_token()}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["email"] == "supa@example.com" and data["role"] == "user"
    assert users_repo.get_by_id(data["id"])["auth_provider"] == "supabase"


def test_supabase_rejects_bad_tokens(supa, regular_user, login):
    assert supa.get("/auth/me", headers={"Authorization": f"Bearer {_token(aud='anon')}"}).status_code == 401
    assert supa.get("/auth/me", headers=login(regular_user).headers).status_code == 401  # local JWT


def test_local_endpoints_not_mounted(supa):
    for path in ("/auth/login", "/auth/register", "/auth/refresh", "/auth/forgot-password/request", "/auth/2fa/verify"):
        assert supa.post(path, json={}).status_code == 404, path
    resp = supa.post("/auth/logout")
    assert resp.status_code == 200
    assert any(c.startswith("token=") for c in resp.headers.get_list("set-cookie"))
