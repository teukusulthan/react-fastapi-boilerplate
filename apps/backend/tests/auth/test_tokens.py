"""Refresh rotation, reuse detection, token-type confusion, logout, single session."""

from __future__ import annotations

from core.security import create_token
from tests.auth.helpers import PASSWORD


def _tokens(resp):
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["auth"]


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_refresh_with_cookie_rotates(client, do_login, regular_user):
    first = _tokens(do_login("alice"))
    resp = client.post("/auth/refresh")  # refresh_token cookie
    second = _tokens(resp)
    assert second["refreshToken"] != first["refreshToken"]
    assert second["accessToken"] != first["accessToken"]
    assert resp.json()["data"]["user"]["id"] == regular_user["id"]
    assert any(c.startswith("refresh_token=") for c in resp.headers.get_list("set-cookie"))
    client.cookies.clear()
    assert client.get("/auth/me", headers=_bearer(second["accessToken"])).status_code == 200


def test_refresh_reuse_revokes_session_family(client, do_login, regular_user):
    first = _tokens(do_login("alice"))
    client.cookies.clear()
    second = _tokens(client.post("/auth/refresh", headers=_bearer(first["refreshToken"])))
    reuse = client.post("/auth/refresh", headers=_bearer(first["refreshToken"]))
    assert reuse.status_code == 401
    # the whole family is now dead: the rotated refresh token AND its access token
    assert client.post("/auth/refresh", headers=_bearer(second["refreshToken"])).status_code == 401
    assert client.get("/auth/me", headers=_bearer(second["accessToken"])).status_code == 401


def test_token_type_confusion_rejected(client, do_login, regular_user):
    tokens = _tokens(do_login("alice"))
    client.cookies.clear()
    assert client.post("/auth/refresh", headers=_bearer(tokens["accessToken"])).status_code == 401
    assert client.get("/auth/me", headers=_bearer(tokens["refreshToken"])).status_code == 401


def test_forged_and_foreign_tokens_rejected(client, regular_user, make_settings):
    other = make_settings(JWT_SECRET="another-secret-0123456789abcdef0123456789")
    forged = create_token(regular_user["id"], "refresh", other).token
    assert client.post("/auth/refresh", headers=_bearer(forged)).status_code == 401
    custom = create_token(regular_user["id"], "2fa", make_settings(), ttl=60).token
    assert client.post("/auth/refresh", headers=_bearer(custom)).status_code == 401
    assert client.post("/auth/refresh").status_code == 401


def test_refresh_rejected_for_blocked_user(client, do_login, regular_user, users_repo):
    _tokens(do_login("alice"))
    users_repo.update(regular_user["id"], {"status": "blocked"})
    assert client.post("/auth/refresh").status_code == 401


def test_logout_revokes_access_and_refresh(client, do_login, regular_user):
    tokens = _tokens(do_login("alice"))
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
    cleared = resp.headers.get_list("set-cookie")
    assert any(c.startswith("token=") and "max-age=0" in c.lower() for c in cleared)
    assert any(c.startswith("refresh_token=") and "max-age=0" in c.lower() for c in cleared)
    client.cookies.clear()
    assert client.get("/auth/me", headers=_bearer(tokens["accessToken"])).status_code == 401
    assert client.post("/auth/refresh", headers=_bearer(tokens["refreshToken"])).status_code == 401
    # idempotent, also without any credentials
    assert client.post("/auth/logout").status_code == 200
    assert client.post("/auth/logout", headers=_bearer("garbage")).status_code == 200


def test_logout_with_bearer_tokens_only(client, do_login, regular_user):
    tokens = _tokens(do_login("alice"))
    client.cookies.clear()
    assert client.post("/auth/logout", headers=_bearer(tokens["accessToken"])).status_code == 200
    # session revoked -> its refresh token is dead as well
    assert client.post("/auth/refresh", headers=_bearer(tokens["refreshToken"])).status_code == 401


def test_logout_only_affects_own_session(client, do_login, regular_user):
    one = _tokens(do_login("alice"))
    two = _tokens(do_login("alice"))
    client.cookies.clear()
    client.post("/auth/logout", headers=_bearer(one["accessToken"]))
    assert client.get("/auth/me", headers=_bearer(two["accessToken"])).status_code == 200


def test_single_session_login_kicks_previous(client, user_factory):
    user_factory(email="solo@example.com", multi_login=False)
    body = {"identifier": "solo@example.com", "password": PASSWORD}
    first = _tokens(client.post("/auth/login", json=body))
    second = _tokens(client.post("/auth/login", json=body))
    client.cookies.clear()
    assert client.get("/auth/me", headers=_bearer(first["accessToken"])).status_code == 401
    assert client.post("/auth/refresh", headers=_bearer(first["refreshToken"])).status_code == 401
    assert client.get("/auth/me", headers=_bearer(second["accessToken"])).status_code == 200
    third = _tokens(client.post("/auth/refresh", headers=_bearer(second["refreshToken"])))
    assert client.get("/auth/me", headers=_bearer(third["accessToken"])).status_code == 200
