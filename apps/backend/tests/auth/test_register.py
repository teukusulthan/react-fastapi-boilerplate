"""Registration (S8: no plaintext password anywhere), verification, enumeration resistance."""

from __future__ import annotations

from datetime import timedelta

from core.security import verify_password
from tests.auth.helpers import assert_no_secrets
from util.helper import utc_now

NEW_PASSWORD = "Fresh-Passw0rd!"


def _payload(**overrides):
    return {
        "username": "newbie",
        "fullname": "New  Bie",
        "email": "New.Bie@Example.com",
        "phone": "+62 812-3456-789",
        "password": NEW_PASSWORD,
        **overrides,
    }


def test_register_verify_login(client, users_repo, redis_client, outbox, last_code, user_permission):
    resp = client.post("/auth/register", json=_payload())
    assert resp.status_code == 201, resp.text
    assert resp.json()["metaData"]["responseCode"] == 201
    user = users_repo.find_one({"email": "new.bie@example.com"})
    assert user["status"] == "pending" and user["email_verified"] is False
    assert user["fullname"] == "New Bie" and user["phone"] == "+628123456789"
    assert user["permission_id"] == user_permission["id"]
    assert verify_password(NEW_PASSWORD, user["password_hash"])
    # the plaintext password is stored nowhere (DB record or Redis)
    assert NEW_PASSWORD not in str(user)
    for key in redis_client.keys("*"):
        dump = str(redis_client.hgetall(key) if redis_client.type(key) == "hash" else redis_client.get(key))
        assert NEW_PASSWORD not in dump

    login = client.post("/auth/login", json={"identifier": "newbie", "password": NEW_PASSWORD})
    assert login.status_code == 401 and login.json()["metaData"]["errorCode"] == "ACCOUNT_NOT_VERIFIED"

    message = outbox.last("new.bie@example.com", "register_otp")
    assert "newbie" in message.text and message.html and "App" in message.subject
    code = last_code("new.bie@example.com", "register_otp")
    verified = client.post("/auth/register/verify", json={"email": "new.bie@example.com", "otp": code})
    assert verified.status_code == 200, verified.text
    stored = users_repo.get_by_id(user["id"])
    assert stored["status"] == "active" and stored["email_verified"] is True

    login = client.post("/auth/login", json={"identifier": "newbie", "password": NEW_PASSWORD})
    assert login.status_code == 200
    assert_no_secrets(login.text)
    # code consumed
    again = client.post("/auth/register/verify", json={"email": "new.bie@example.com", "otp": code})
    assert again.status_code == 400


def test_reregister_pending_resends_and_updates(make_client, make_settings, users_repo, outbox, last_code):
    client = make_client(make_settings(OTP_RESEND_COOLDOWN=0))
    assert client.post("/auth/register", json=_payload()).status_code == 201
    first = last_code("new.bie@example.com", "register_otp")
    resp = client.post("/auth/register", json=_payload(username="newbie2", password="Other-Passw0rd"))
    assert resp.status_code == 201
    assert len(outbox.to("new.bie@example.com")) == 2
    second = last_code("new.bie@example.com", "register_otp")
    users = users_repo.find_all({"email": "new.bie@example.com"})
    assert len(users) == 1 and users[0]["username"] == "newbie2"
    assert verify_password("Other-Passw0rd", users[0]["password_hash"])
    if first != second:  # only the latest code is valid
        assert (
            client.post("/auth/register/verify", json={"email": "new.bie@example.com", "otp": first}).status_code == 400
        )
    assert client.post("/auth/register/verify", json={"email": "new.bie@example.com", "otp": second}).status_code == 200


def test_resend_cooldown_is_silent(client, outbox):
    assert client.post("/auth/register", json=_payload()).status_code == 201
    assert client.post("/auth/register/resend", json={"email": "new.bie@example.com"}).status_code == 200
    assert client.post("/auth/register/resend", json={"email": "ghost@example.com"}).status_code == 200
    assert len(outbox.outbox) == 1  # cooldown (60 s default) + unknown email: nothing more sent


def test_existing_email_gets_generic_response(client, regular_user, users_repo, outbox):
    resp = client.post("/auth/register", json=_payload(email="alice@example.com"))
    assert resp.status_code == 201
    fresh = client.post("/auth/register", json=_payload(email="brand-new@example.com", username="brandnew"))
    assert resp.json()["data"] == fresh.json()["data"]  # identical answer: no enumeration
    assert users_repo.count({"email": "alice@example.com"}) == 1
    assert users_repo.get_by_id(regular_user["id"])["username"] == "alice"  # untouched
    assert outbox.last("alice@example.com").template == "account_exists"


def test_username_and_phone_conflicts(client, user_factory):
    user_factory(username="taken", phone="+620000000")
    resp = client.post("/auth/register", json=_payload(username="taken"))
    assert resp.status_code == 409
    assert resp.json()["data"][0]["field"] == "username"
    resp = client.post("/auth/register", json=_payload(phone="+620000000"))
    assert resp.status_code == 409 and resp.json()["data"][0]["field"] == "phone"


def test_stale_pending_account_releases_username(client, user_factory, users_repo):
    stale = user_factory(username="newbie", email="old@example.com", status="pending", email_verified=False)
    old = utc_now() - timedelta(days=3)
    # simulate age (repositories always refresh updated_at, so patch the mongomock collection directly)
    collection = users_repo.collection  # type: ignore[attr-defined]
    collection.update_one({"_id": stale["id"]}, {"$set": {"updated_at": old, "created_at": old}})
    resp = client.post("/auth/register", json=_payload())
    assert resp.status_code == 201, resp.text
    assert users_repo.get_by_id(stale["id"]) is None


def test_fresh_pending_account_keeps_username(client, user_factory):
    user_factory(username="newbie", email="other@example.com", status="pending", email_verified=False)
    assert client.post("/auth/register", json=_payload()).status_code == 409


def test_otp_bound_to_email_and_attempt_limit(make_client, make_settings, last_code):
    client = make_client(make_settings(OTP_MAX_ATTEMPTS=2, OTP_RESEND_COOLDOWN=0))
    client.post("/auth/register", json=_payload())
    client.post("/auth/register", json=_payload(email="b@example.com", username="bee", phone=None))
    code_a = last_code("new.bie@example.com", "register_otp")
    code_b = last_code("b@example.com", "register_otp")
    if code_a != code_b:
        assert client.post("/auth/register/verify", json={"email": "b@example.com", "otp": code_a}).status_code == 400
    wrong = "000000" if code_b != "000000" else "111111"
    assert client.post("/auth/register/verify", json={"email": "b@example.com", "otp": wrong}).status_code == 400
    # 2 attempts used -> the code is burnt
    assert client.post("/auth/register/verify", json={"email": "b@example.com", "otp": code_b}).status_code == 400
    # unknown email -> same error
    unknown = client.post("/auth/register/verify", json={"email": "zzz@example.com", "otp": "123456"})
    assert unknown.status_code == 400 and unknown.json()["metaData"]["message"] == "Invalid or expired code"


def test_password_policy_and_validation(client, make_client, make_settings):
    short = client.post("/auth/register", json=_payload(password="short"))
    assert short.status_code == 422 and short.json()["data"][0]["field"] == "password"
    bad = client.post("/auth/register", json=_payload(email="not-an-email", username="x y"))
    assert bad.status_code == 422
    assert {item["field"] for item in bad.json()["data"]} == {"email", "username"}
    too_long = client.post("/auth/register", json=_payload(password="é" * 40))  # 80 bytes > bcrypt limit
    assert too_long.status_code == 422


def test_registration_disabled(make_client, make_settings):
    client = make_client(make_settings(REGISTRATION_ENABLED=False))
    resp = client.post("/auth/register", json=_payload())
    assert resp.status_code == 403


def test_email_not_configured_returns_503(make_settings, make_app):
    from fastapi.testclient import TestClient

    settings = make_settings(EMAIL_BACKEND="disabled")
    with TestClient(make_app(settings)) as client:  # real sender resolution (no override)
        resp = client.post("/auth/register", json=_payload())
        assert resp.status_code == 503
        assert resp.json()["metaData"]["errorCode"] == "CONFIGURATION_ERROR"
        forgot = client.post("/auth/forgot-password/request", json={"email": "ghost@example.com"})
        assert forgot.status_code == 503
