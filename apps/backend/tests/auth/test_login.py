from __future__ import annotations

from datetime import datetime, timedelta, timezone

from tests.auth.helpers import PASSWORD, assert_no_secrets


def test_login_success_shape_cookies_and_me(client, do_login, regular_user, user_permission):
    resp = do_login("alice@example.com")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["metaData"]["status"] is True
    data = body["data"]
    assert data["twoFactorRequired"] is False
    assert set(data["auth"]) == {"accessToken", "refreshToken", "expiresAt"}
    expires = datetime.fromisoformat(data["auth"]["expiresAt"].replace("Z", "+00:00"))
    assert expires.tzinfo is not None
    assert timedelta(seconds=800) < expires - datetime.now(timezone.utc) <= timedelta(seconds=901)
    user = data["user"]
    assert user["id"] == regular_user["id"]
    assert user["role"] == "user"
    assert user["permission"]["alias"] == "user"
    assert user["lastLoginAt"] is not None
    assert_no_secrets(resp.text)

    set_cookie = resp.headers.get_list("set-cookie")
    token_cookie = next(c for c in set_cookie if c.startswith("token="))
    refresh_cookie = next(c for c in set_cookie if c.startswith("refresh_token="))
    for cookie in (token_cookie, refresh_cookie):
        lowered = cookie.lower()
        assert "httponly" in lowered and "path=/" in lowered and "samesite=lax" in lowered
        assert "secure" not in lowered  # BE_COOKIE_SECURE=false in tests

    me = client.get("/auth/me")  # cookie auth
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "alice@example.com"
    assert_no_secrets(me.text)
    client.cookies.clear()
    assert client.get("/auth/me").status_code == 401
    bearer = client.get("/auth/me", headers={"Authorization": f"Bearer {data['auth']['accessToken']}"})
    assert bearer.status_code == 200


def test_secure_cookie_flag(make_client, make_settings, regular_user):
    client = make_client(make_settings(COOKIE_SECURE=True), base_url="https://testserver")
    resp = client.post("/auth/login", json={"identifier": "alice", "password": PASSWORD})
    assert resp.status_code == 200
    assert all("secure" in c.lower() for c in resp.headers.get_list("set-cookie"))


def test_login_by_username_and_case_insensitive_email(do_login, regular_user):
    assert do_login("alice").status_code == 200
    assert do_login("  ALICE@Example.com ").status_code == 200


def test_generic_error_for_unknown_user_and_wrong_password(do_login, regular_user):
    wrong = do_login("alice", "wrong-password")
    unknown = do_login("nobody@example.com")
    for resp in (wrong, unknown):
        assert resp.status_code == 401
        assert resp.json()["metaData"]["message"] == "Invalid credentials"
        assert resp.json()["metaData"]["errorCode"] == "AUTHENTICATION_ERROR"
        assert "set-cookie" not in resp.headers


def test_lockout_per_identifier_and_ip(make_client, make_settings, regular_user):
    client = make_client(make_settings(ACCOUNT_LOCK_MAX_ATTEMPTS=3, TRUST_PROXY_HEADERS=True, RATE_LIMIT_AUTH=100))
    attacker = {"X-Forwarded-For": "203.0.113.9"}
    victim = {"X-Forwarded-For": "198.51.100.7"}

    def attempt(password, headers):
        return client.post("/auth/login", json={"identifier": "alice", "password": password}, headers=headers)

    for _ in range(3):
        assert attempt("bad", attacker).status_code == 401
    locked = attempt(PASSWORD, attacker)  # correct password, but locked from this IP
    assert locked.status_code == 401
    assert locked.json()["metaData"]["message"] == "Invalid credentials"
    # The real user from another IP is not locked out (no lockout DoS)
    assert attempt(PASSWORD, victim).status_code == 200


def test_success_resets_failure_counter(make_client, make_settings, regular_user):
    client = make_client(make_settings(ACCOUNT_LOCK_MAX_ATTEMPTS=3, RATE_LIMIT_AUTH=100))
    body = {"identifier": "alice", "password": "bad"}
    for _ in range(2):
        client.post("/auth/login", json=body)
    assert client.post("/auth/login", json={**body, "password": PASSWORD}).status_code == 200
    for _ in range(2):
        client.post("/auth/login", json=body)
    assert client.post("/auth/login", json={**body, "password": PASSWORD}).status_code == 200


def test_pending_user_cannot_login(do_login, user_factory):
    user_factory(email="pending@example.com", status="pending", email_verified=False)
    wrong = do_login("pending@example.com", "nope-nope")
    assert wrong.json()["metaData"]["message"] == "Invalid credentials"  # no state leak without password
    resp = do_login("pending@example.com")
    assert resp.status_code == 401
    assert resp.json()["metaData"]["errorCode"] == "ACCOUNT_NOT_VERIFIED"


def test_blocked_and_expired_users(do_login, user_factory):
    user_factory(email="blocked@example.com", status="blocked")
    user_factory(email="old@example.com", expired_at=datetime.now(timezone.utc) - timedelta(days=1))
    blocked = do_login("blocked@example.com")
    assert blocked.status_code == 401 and blocked.json()["metaData"]["message"] == "Account is not active"
    expired = do_login("old@example.com")
    assert expired.status_code == 401 and expired.json()["metaData"]["message"] == "Account has expired"


def test_sso_only_user_cannot_password_login(do_login, user_factory):
    user_factory(email="g@example.com", password=None, auth_provider="google")
    resp = do_login("g@example.com")
    assert resp.status_code == 401 and resp.json()["metaData"]["message"] == "Invalid credentials"


def test_login_rate_limited(make_client, make_settings, regular_user):
    client = make_client(make_settings(RATE_LIMIT_AUTH=3, ACCOUNT_LOCK_MAX_ATTEMPTS=50))
    codes = [client.post("/auth/login", json={"identifier": "alice", "password": "x"}).status_code for _ in range(4)]
    assert codes == [401, 401, 401, 429]
    last = client.post("/auth/login", json={"identifier": "alice", "password": "x"})
    assert last.json()["metaData"]["errorCode"] == "RATE_LIMITED"
    assert "retry-after" in last.headers


def test_validation_errors_are_camel_case(client):
    resp = client.post("/auth/login", json={"identifier": "", "password": ""})
    assert resp.status_code == 422
    fields = {item["field"] for item in resp.json()["data"]}
    assert fields == {"identifier", "password"}


def test_me_requires_user(client, internal_headers):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers=internal_headers).status_code == 403
