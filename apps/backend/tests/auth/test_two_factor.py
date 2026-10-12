"""2FA really gates login (S5), email + TOTP, setup/enable/disable, attempt limits."""

from __future__ import annotations

import time

import pyotp
import pytest

from core.security import hash_password
from tests.auth.helpers import PASSWORD, assert_no_secrets
from util.crypto import generate_fernet_key


def _setup_email_2fa(client, headers, last_code, email):
    resp = client.post("/auth/2fa/setup", json={"method": "email"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["method"] == "email"
    code = last_code(email, "two_factor_setup_otp")
    enabled = client.post("/auth/2fa/enable", json={"otp": code}, headers=headers)
    assert enabled.status_code == 200, enabled.text
    assert enabled.json()["data"]["twoFactorEnabled"] is True


def _login(client, identifier="alice@example.com", password=PASSWORD):
    return client.post("/auth/login", json={"identifier": identifier, "password": password})


def test_email_2fa_gates_login(client, regular_user, auth_headers, last_code, users_repo, outbox):
    _setup_email_2fa(client, auth_headers(regular_user), last_code, "alice@example.com")
    stored = users_repo.get_by_id(regular_user["id"])
    assert stored["two_factor_enabled"] is True and stored["two_factor_method"] == "email"

    resp = _login(client)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data == {"twoFactorRequired": True, "sessionToken": data["sessionToken"], "method": "email"}
    assert "set-cookie" not in resp.headers  # no tokens before the second factor
    code = last_code("alice@example.com", "two_factor_login_otp")

    verified = client.post("/auth/2fa/verify", json={"sessionToken": data["sessionToken"], "otp": code})
    assert verified.status_code == 200, verified.text
    body = verified.json()["data"]
    assert body["twoFactorRequired"] is False
    assert set(body) == {"twoFactorRequired", "user", "auth"}  # same shape as /auth/login
    assert set(body["auth"]) == {"accessToken", "refreshToken", "expiresAt"}
    assert any(c.startswith("token=") for c in verified.headers.get_list("set-cookie"))
    assert_no_secrets(verified.text)

    # the challenge is single use
    again = client.post("/auth/2fa/verify", json={"sessionToken": data["sessionToken"], "otp": code})
    assert again.status_code == 401


def test_2fa_wrong_codes_burn_challenge(make_client, make_settings, user_factory, last_code, login):
    client = make_client(make_settings(OTP_MAX_ATTEMPTS=3, RATE_LIMIT_AUTH=100))
    user = user_factory(email="bob@example.com")
    _setup_email_2fa(client, login(user).headers, last_code, "bob@example.com")
    token = _login(client, "bob@example.com").json()["data"]["sessionToken"]
    code = last_code("bob@example.com", "two_factor_login_otp")
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(3):
        resp = client.post("/auth/2fa/verify", json={"sessionToken": token, "otp": wrong})
        assert resp.status_code == 401
        assert resp.json()["metaData"]["message"] == "Invalid or expired code"
    # budget exhausted: even the right code no longer works
    assert client.post("/auth/2fa/verify", json={"sessionToken": token, "otp": code}).status_code == 401


def test_2fa_resend_cooldown_and_new_code(make_client, make_settings, user_factory, last_code, login, outbox):
    client = make_client(make_settings(OTP_RESEND_COOLDOWN=60))
    user = user_factory(email="carol@example.com")
    _setup_email_2fa(client, login(user).headers, last_code, "carol@example.com")
    token = _login(client, "carol@example.com").json()["data"]["sessionToken"]
    first_code = last_code("carol@example.com", "two_factor_login_otp")
    resend = client.post("/auth/2fa/resend", json={"sessionToken": token})
    assert resend.status_code == 429 and "retry-after" in resend.headers

    client2 = make_client(make_settings(OTP_RESEND_COOLDOWN=0))
    token = _login(client2, "carol@example.com").json()["data"]["sessionToken"]
    first_code = last_code("carol@example.com", "two_factor_login_otp")
    assert client2.post("/auth/2fa/resend", json={"sessionToken": token}).status_code == 200
    new_code = last_code("carol@example.com", "two_factor_login_otp")
    if new_code != first_code:
        assert client2.post("/auth/2fa/verify", json={"sessionToken": token, "otp": first_code}).status_code == 401
    assert client2.post("/auth/2fa/verify", json={"sessionToken": token, "otp": new_code}).status_code == 200


def test_2fa_unknown_session_token(client):
    resp = client.post("/auth/2fa/verify", json={"sessionToken": "x" * 43, "otp": "123456"})
    assert resp.status_code == 401
    assert client.post("/auth/2fa/resend", json={"sessionToken": "x" * 43}).status_code == 401


def _setup_totp(client, headers):
    resp = client.post("/auth/2fa/setup", json={"method": "totp"}, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["otpauthUri"].startswith("otpauth://totp/")
    assert data["qrImageBase64"]
    return data["secret"]


def test_totp_flow_and_replay_protection(client, regular_user, auth_headers, users_repo):
    headers = auth_headers(regular_user)
    secret = _setup_totp(client, headers)
    totp = pyotp.TOTP(secret)
    # not enabled until confirmed
    assert users_repo.get_by_id(regular_user["id"])["two_factor_enabled"] is False
    assert client.post("/auth/2fa/enable", json={"otp": "000000"}, headers=headers).status_code in (400,)
    enable_code = totp.now()
    assert client.post("/auth/2fa/enable", json={"otp": enable_code}, headers=headers).status_code == 200

    token = _login(client).json()["data"]["sessionToken"]
    # the code used for enabling cannot be replayed
    replay = client.post("/auth/2fa/verify", json={"sessionToken": token, "otp": enable_code})
    assert replay.status_code == 401
    next_code = totp.at(time.time() + 30)
    ok = client.post("/auth/2fa/verify", json={"sessionToken": token, "otp": next_code})
    assert ok.status_code == 200, ok.text
    assert ok.json()["data"]["user"]["twoFactorEnabled"] is True


def test_totp_secret_encrypted_at_rest(make_client, make_settings, user_factory, login, users_repo):
    key = generate_fernet_key()
    client = make_client(make_settings(DATA_ENCRYPTION_KEY=key))
    user = user_factory(email="dave@example.com")
    headers = login(user).headers
    secret = _setup_totp(client, headers)
    assert client.post("/auth/2fa/enable", json={"otp": pyotp.TOTP(secret).now()}, headers=headers).status_code == 200
    stored = users_repo.get_by_id(user["id"])["two_factor_secret"]
    assert stored and secret not in stored


def test_setup_conflict_and_disable(client, regular_user, auth_headers, last_code, users_repo):
    headers = auth_headers(regular_user)
    _setup_email_2fa(client, headers, last_code, "alice@example.com")
    again = client.post("/auth/2fa/setup", json={"method": "totp"}, headers=headers)
    assert again.status_code == 409
    bad = client.post("/auth/2fa/disable", json={"password": "wrong-password"}, headers=headers)
    assert bad.status_code == 400  # not 401: the caller is authenticated
    good = client.post("/auth/2fa/disable", json={"password": PASSWORD}, headers=headers)
    assert good.status_code == 200 and good.json()["data"]["twoFactorEnabled"] is False
    stored = users_repo.get_by_id(regular_user["id"])
    assert stored["two_factor_secret"] is None and stored["two_factor_method"] is None
    assert _login(client).json()["data"]["twoFactorRequired"] is False


def test_2fa_endpoints_require_auth(client):
    assert client.post("/auth/2fa/setup", json={"method": "totp"}).status_code == 401
    assert client.post("/auth/2fa/enable", json={"otp": "123456"}).status_code == 401
    assert client.post("/auth/2fa/disable", json={"password": "x"}).status_code == 401


@pytest.mark.parametrize("method", ["sms", ""])
def test_setup_rejects_unknown_method(client, user_headers, method):
    assert client.post("/auth/2fa/setup", json={"method": method}, headers=user_headers).status_code == 422


def test_prepared_totp_user_login(client, users_repo, user_factory):
    """A user enabled out-of-band (e.g. seed) with a plaintext secret still works."""
    secret = pyotp.random_base32()
    user_factory(
        email="eve@example.com",
        two_factor_enabled=True,
        two_factor_method="totp",
        two_factor_secret=secret,
        password_hash=hash_password(PASSWORD),
    )
    challenge = _login(client, "eve@example.com").json()["data"]
    assert challenge["method"] == "totp"
    resp = client.post(
        "/auth/2fa/verify", json={"sessionToken": challenge["sessionToken"], "otp": pyotp.TOTP(secret).now()}
    )
    assert resp.status_code == 200
