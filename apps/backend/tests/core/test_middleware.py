from __future__ import annotations

import json

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from dto.common import BaseSchema
from router import HEALTH, RouterSpec
from util.crypto import aesgcm_decrypt, aesgcm_encrypt, decode_aes_key, generate_aes_key

router = APIRouter(prefix="/m")


class Echo(BaseSchema):
    full_name: str


@router.post("/echo")
def echo(dto: Echo) -> dict:
    return {"metaData": {"status": True}, "data": {"fullName": dto.full_name}}


@router.get("/text")
def text() -> str:
    return "plain"


@pytest.fixture
def app_routers():
    return [HEALTH, RouterSpec("m", __name__)]


# ------------------------------------------------------------ request id
def test_request_id_generated(client: TestClient) -> None:
    resp = client.get("/health/live")
    rid = resp.headers["X-Request-ID"]
    assert len(rid) == 32
    assert resp.json()["metaData"]["requestId"] == rid


def test_request_id_propagated_and_sanitised(client: TestClient) -> None:
    assert client.get("/health/live", headers={"X-Request-ID": "abc-123"}).headers["X-Request-ID"] == "abc-123"
    bad = client.get("/health/live", headers={"X-Request-ID": "bad id\nwith newline"}).headers["X-Request-ID"]
    assert bad != "bad id\nwith newline" and len(bad) == 32


# ------------------------------------------------------------------ CORS
def test_cors_allows_configured_origin_with_credentials(client: TestClient) -> None:
    resp = client.options(
        "/m/echo",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert resp.headers["access-control-allow-credentials"] == "true"
    other = client.get("/health/live", headers={"Origin": "http://evil.test"})
    assert "access-control-allow-origin" not in other.headers


# ------------------------------------------------------------ encryption
@pytest.fixture
def enc_key() -> str:
    return generate_aes_key()


@pytest.fixture
def enc_client(make_settings, make_app, enc_key) -> TestClient:
    s = make_settings(ENC_ACTIVE=True, ENC_SECRET=enc_key)
    with TestClient(make_app(s)) as c:
        yield c


def test_encrypted_roundtrip(enc_client: TestClient, enc_key: str) -> None:
    key = decode_aes_key(enc_key)
    payload = aesgcm_encrypt(key, json.dumps({"fullName": "Ann"}).encode())
    resp = enc_client.post("/m/echo", json={"payload": payload})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"payload"}
    assert json.loads(aesgcm_decrypt(key, body["payload"]))["data"] == {"fullName": "Ann"}
    assert int(resp.headers["content-length"]) == len(resp.content)


def test_encrypted_errors_are_encrypted_too(enc_client: TestClient, enc_key: str) -> None:
    key = decode_aes_key(enc_key)
    resp = enc_client.post("/m/echo", json={"payload": aesgcm_encrypt(key, b"{}")})
    assert resp.status_code == 422
    assert json.loads(aesgcm_decrypt(key, resp.json()["payload"]))["metaData"]["errorCode"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "body", [{"payload": "not-base64!!"}, {"nope": 1}, {"payload": "QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUE="}]
)
def test_invalid_encrypted_payload(enc_client: TestClient, body: dict) -> None:
    resp = enc_client.post("/m/echo", json=body)
    assert resp.status_code == 400
    assert resp.json()["metaData"]["errorCode"] == "BAD_REQUEST"


def test_health_and_non_json_not_encrypted(enc_client: TestClient) -> None:
    assert enc_client.get("/health/live").json()["data"] == {"status": "ok"}
    assert enc_client.get("/openapi.json").json()["openapi"]
