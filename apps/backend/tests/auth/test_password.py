"""Forgot-password (no enumeration, attempt limits, session revocation) and change-password."""

from __future__ import annotations

from core.security import verify_password
from tests.auth.helpers import PASSWORD, assert_no_secrets

NEW = "Brand-New-Passw0rd"


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_forgot_password_full_flow(client, regular_user, users_repo, outbox, last_code, login):
    old_session = login(regular_user)
    resp = client.post("/auth/forgot-password/request", json={"email": "ALICE@example.com"})
    assert resp.status_code == 200
    code = last_code("alice@example.com", "password_reset_otp")

    check = client.post("/auth/forgot-password/verify", json={"email": "alice@example.com", "otp": code})
    assert check.status_code == 200 and check.json()["data"] == {"valid": True}

    short = client.post(
        "/auth/forgot-password/reset", json={"email": "alice@example.com", "otp": code, "newPassword": "x"}
    )
    assert short.status_code == 422 and short.json()["data"][0]["field"] == "newPassword"

    reset = client.post(
        "/auth/forgot-password/reset", json={"email": "alice@example.com", "otp": code, "newPassword": NEW}
    )
    assert reset.status_code == 200, reset.text
    assert verify_password(NEW, users_repo.get_by_id(regular_user["id"])["password_hash"])
    assert outbox.last("alice@example.com").template == "password_changed"
    # every pre-existing session is revoked
    assert client.get("/auth/me", headers=old_session.headers).status_code == 401
    assert client.post("/auth/refresh", headers=_bearer(old_session.pair.refresh.token)).status_code == 401
    # the code is single use
    replay = client.post(
        "/auth/forgot-password/reset", json={"email": "alice@example.com", "otp": code, "newPassword": NEW + "x"}
    )
    assert replay.status_code == 400
    login_resp = client.post("/auth/login", json={"identifier": "alice", "password": NEW})
    assert login_resp.status_code == 200


def test_forgot_password_no_enumeration(client, regular_user, user_factory, outbox):
    user_factory(email="blocked@example.com", status="blocked")
    answers = [
        client.post("/auth/forgot-password/request", json={"email": email})
        for email in ("alice@example.com", "nobody@example.com", "blocked@example.com")
    ]
    assert {r.status_code for r in answers} == {200}
    assert len({r.json()["data"]["message"] for r in answers}) == 1
    assert [m.to for m in outbox.outbox] == ["alice@example.com"]
    # cooldown: a second request within BE_OTP_RESEND_COOLDOWN is answered identically, nothing sent
    again = client.post("/auth/forgot-password/request", json={"email": "alice@example.com"})
    assert again.status_code == 200 and len(outbox.outbox) == 1


def test_forgot_password_attempt_limit(make_client, make_settings, regular_user, last_code):
    client = make_client(make_settings(OTP_MAX_ATTEMPTS=3, RATE_LIMIT_AUTH=100))
    client.post("/auth/forgot-password/request", json={"email": "alice@example.com"})
    code = last_code("alice@example.com", "password_reset_otp")
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(3):
        bad = client.post("/auth/forgot-password/verify", json={"email": "alice@example.com", "otp": wrong})
        assert bad.status_code == 400
    burnt = client.post(
        "/auth/forgot-password/reset", json={"email": "alice@example.com", "otp": code, "newPassword": NEW}
    )
    assert burnt.status_code == 400


def test_forgot_password_code_bound_to_email(client, regular_user, user_factory, last_code):
    user_factory(email="bob@example.com")
    client.post("/auth/forgot-password/request", json={"email": "alice@example.com"})
    code = last_code("alice@example.com", "password_reset_otp")
    stolen = client.post(
        "/auth/forgot-password/reset", json={"email": "bob@example.com", "otp": code, "newPassword": NEW}
    )
    assert stolen.status_code == 400


def test_forgot_password_rate_limited(make_client, make_settings, regular_user):
    client = make_client(make_settings(RATE_LIMIT_AUTH=2))
    codes = [
        client.post("/auth/forgot-password/request", json={"email": "alice@example.com"}).status_code for _ in range(3)
    ]
    assert codes == [200, 200, 429]


def test_change_password(client, regular_user, login, users_repo, outbox):
    current = login(regular_user)
    other = login(regular_user)
    wrong = client.post(
        "/auth/change-password",
        json={"currentPassword": "nope-nope", "newPassword": NEW},
        headers=current.headers,
    )
    assert wrong.status_code == 400 and wrong.json()["data"][0]["field"] == "currentPassword"
    same = client.post(
        "/auth/change-password", json={"currentPassword": PASSWORD, "newPassword": PASSWORD}, headers=current.headers
    )
    assert same.status_code == 422

    resp = client.post(
        "/auth/change-password", json={"currentPassword": PASSWORD, "newPassword": NEW}, headers=current.headers
    )
    assert resp.status_code == 200, resp.text
    assert_no_secrets(resp.text)
    fresh = resp.json()["data"]["auth"]
    assert verify_password(NEW, users_repo.get_by_id(regular_user["id"])["password_hash"])
    client.cookies.clear()
    # all previous sessions (including the caller's old tokens) are revoked ...
    assert client.get("/auth/me", headers=other.headers).status_code == 401
    assert client.get("/auth/me", headers=current.headers).status_code == 401
    # ... and the caller continues with the freshly issued pair
    assert client.get("/auth/me", headers=_bearer(fresh["accessToken"])).status_code == 200
    assert client.post("/auth/refresh", headers=_bearer(fresh["refreshToken"])).status_code == 200
    assert outbox.last("alice@example.com").template == "password_changed"


def test_change_password_requires_auth(client):
    resp = client.post("/auth/change-password", json={"currentPassword": "a", "newPassword": NEW})
    assert resp.status_code == 401
