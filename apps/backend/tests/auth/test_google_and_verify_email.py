"""Google sign-in (code exchange + id_token verification) and email-link verification."""

from __future__ import annotations

import json
import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from service.auth.deps import get_google_client
from service.auth.google import GOOGLE_TOKEN_URL, GoogleOAuthClient
from tests.auth.helpers import assert_no_secrets

CLIENT_ID = "client-id.apps.googleusercontent.com"
GOOGLE = {"GOOGLE_CLIENT_ID": CLIENT_ID, "GOOGLE_CLIENT_SECRET": "google-secret"}
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class FakeJwks:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token):
        return SimpleNamespace(key=self.key)


def id_token(**claims):
    now = int(time.time())
    payload = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "google-sub-1",
        "email": "gina@example.com",
        "email_verified": True,
        "name": "Gina G",
        "iat": now,
        "exp": now + 300,
        **claims,
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")


@pytest.fixture
def google_env(build_app, make_settings):
    """Returns (client factory, captured token requests)."""
    from fastapi.testclient import TestClient

    requests: list[dict] = []
    state = {"token": id_token(), "status": 200}
    clients = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == GOOGLE_TOKEN_URL
        requests.append({k: v[0] for k, v in parse_qs(request.content.decode()).items()})
        if state["status"] != 200:
            return httpx.Response(state["status"], json={"error": "invalid_grant"})
        return httpx.Response(200, json={"access_token": "at", "id_token": state["token"]})

    def factory(**overrides):
        settings = make_settings(**GOOGLE, **overrides)
        app = build_app(settings)
        oauth = GoogleOAuthClient(
            settings, transport=httpx.MockTransport(handler), jwks_client=FakeJwks(PRIVATE_KEY.public_key())
        )
        app.dependency_overrides[get_google_client] = lambda: oauth
        client = TestClient(app)
        client.__enter__()
        clients.append(client)
        return client

    yield factory, requests, state
    for client in clients:
        client.__exit__(None, None, None)


def _callback(client, **extra):
    return client.post(
        "/auth/google/callback", json={"code": "abc", "redirectUri": "http://localhost:3000/cb", **extra}
    )


def test_google_router_only_mounted_when_configured(client):
    assert _callback(client).status_code == 404


def test_google_links_existing_account(google_env, user_factory, users_repo):
    factory, requests, _ = google_env
    user = user_factory(email="gina@example.com")
    client = factory()
    resp = _callback(client, codeVerifier="v" * 43)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["twoFactorRequired"] is False and data["user"]["id"] == user["id"]
    assert any(c.startswith("token=") for c in resp.headers.get_list("set-cookie"))
    assert_no_secrets(resp.text)
    assert requests[0]["code"] == "abc" and requests[0]["redirect_uri"] == "http://localhost:3000/cb"
    assert requests[0]["code_verifier"] == "v" * 43 and requests[0]["client_secret"] == "google-secret"
    assert users_repo.get_by_id(user["id"])["external_id"] == "google-sub-1"


def test_google_unknown_account_without_auto_register(google_env, users_repo):
    factory, _, _ = google_env
    resp = _callback(factory())
    assert resp.status_code == 401
    assert users_repo.count() == 0


def test_google_auto_register_and_domain_restriction(google_env, users_repo, user_permission):
    factory, _, _ = google_env
    resp = _callback(factory(GOOGLE_AUTO_REGISTER=True))
    assert resp.status_code == 200, resp.text
    created = users_repo.find_one({"email": "gina@example.com"})
    assert created["auth_provider"] == "google" and created["password_hash"] is None
    assert created["status"] == "active" and created["permission_id"] == user_permission["id"]
    # second sign-in finds it by sub
    assert _callback(factory(GOOGLE_AUTO_REGISTER=True)).json()["data"]["user"]["id"] == created["id"]

    restricted = factory(GOOGLE_AUTO_REGISTER=True, GOOGLE_ALLOWED_DOMAINS="corp.example")
    assert _callback(restricted).status_code == 403


def test_google_rejects_bad_tokens(google_env, user_factory):
    factory, _, state = google_env
    user_factory(email="gina@example.com")
    client = factory()
    state["token"] = id_token(email_verified=False)
    assert _callback(client).status_code == 401
    state["token"] = id_token(aud="someone-else")
    assert _callback(client).status_code == 401
    state["token"] = id_token(iss="https://evil.example")
    assert _callback(client).status_code == 401
    state["token"] = id_token(exp=int(time.time()) - 3600)
    assert _callback(client).status_code == 401
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    state["token"] = jwt.encode(json.loads(json.dumps({"sub": "x", "aud": CLIENT_ID})), other_key, algorithm="RS256")
    assert _callback(client).status_code == 401
    state["token"] = id_token()
    state["status"] = 400
    assert _callback(client).status_code == 401


def test_google_takes_over_pending_signup(google_env, user_factory, users_repo):
    factory, _, _ = google_env
    pending = user_factory(email="gina@example.com", status="pending", email_verified=False)
    resp = _callback(factory())
    assert resp.status_code == 200
    stored = users_repo.get_by_id(pending["id"])
    assert stored["status"] == "active" and stored["password_hash"] is None  # squatter's password dropped


def test_google_respects_2fa(google_env, user_factory):
    factory, _, _ = google_env
    user_factory(email="gina@example.com", two_factor_enabled=True, two_factor_method="email")
    resp = _callback(factory())
    assert resp.status_code == 200
    assert resp.json()["data"]["twoFactorRequired"] is True
    assert "set-cookie" not in resp.headers


# ------------------------------------------------------------- verify email
def test_verify_email_link_flow(client, user_factory, auth_headers, users_repo, outbox):
    user = user_factory(email="vera@example.com", email_verified=False)
    headers = auth_headers(user)
    resp = client.post("/auth/verify-email/request", headers=headers)
    assert resp.status_code == 200
    message = outbox.last("vera@example.com", "verify_email_link")
    link = next(line.strip() for line in message.text.splitlines() if "token=" in line)
    parsed = urlparse(link)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "http://localhost:3000/auth/verify-email"
    token = parse_qs(parsed.query)["token"][0]

    # cooldown on repeated requests
    assert client.post("/auth/verify-email/request", headers=headers).status_code == 429

    assert client.post("/auth/verify-email", json={"token": "x" * 43}).status_code == 400
    ok = client.post("/auth/verify-email", json={"token": token})
    assert ok.status_code == 200
    assert users_repo.get_by_id(user["id"])["email_verified"] is True
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 400  # single use
    already = client.post("/auth/verify-email/request", headers=headers)
    assert already.status_code == 200 and "already" in already.json()["data"]["message"]


def test_verify_email_link_invalid_after_email_change(client, user_factory, auth_headers, users_repo, outbox):
    user = user_factory(email="vic@example.com", email_verified=False)
    client.post("/auth/verify-email/request", headers=auth_headers(user))
    link = next(line.strip() for line in outbox.last("vic@example.com").text.splitlines() if "token=" in line)
    users_repo.update(user["id"], {"email": "vic2@example.com"})
    token = parse_qs(urlparse(link).query)["token"][0]
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 400
    assert users_repo.get_by_id(user["id"])["email_verified"] is False
