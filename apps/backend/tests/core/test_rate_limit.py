from __future__ import annotations

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from core.rate_limit import RateLimiter, client_ip_from_scope, rate_limit
from router import HEALTH, RouterSpec

router = APIRouter(prefix="/r")


@router.post("/login", dependencies=[Depends(rate_limit("login", limit=lambda s: 3, window=lambda s: 60))])
def login() -> dict:
    return {"ok": True}


@pytest.fixture
def app_routers():
    return [HEALTH, RouterSpec("r", __name__)]


def test_limiter_counts_and_resets(settings, redis_client) -> None:
    limiter = RateLimiter(redis_client, settings)
    results = [limiter.hit("k", limit=2, window=30) for _ in range(3)]
    assert [r.allowed for r in results] == [True, True, False]
    assert results[0].remaining == 1
    assert 0 < results[-1].reset_after <= 30
    limiter.reset("k")
    assert limiter.hit("k", limit=2, window=30).allowed


def test_limiter_fails_open(settings) -> None:
    class Broken:
        def pipeline(self, **_):
            raise RedisConnectionError("down")

    assert RateLimiter(Broken(), settings).hit("k", limit=1, window=1).allowed  # type: ignore[arg-type]


def test_dependency_returns_429(client: TestClient) -> None:
    codes = [client.post("/r/login").status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    resp = client.post("/r/login")
    assert resp.json()["metaData"]["errorCode"] == "RATE_LIMITED"
    assert int(resp.headers["Retry-After"]) >= 1


def test_dependency_can_be_disabled(make_settings, make_app) -> None:
    with TestClient(make_app(make_settings(RATE_LIMIT_ENABLED=False))) as c:
        assert all(c.post("/r/login").status_code == 200 for _ in range(5))


def test_global_limit(make_settings, make_app) -> None:
    with TestClient(make_app(make_settings(RATE_LIMIT_GLOBAL=2))) as c:
        assert [c.post("/r/login").status_code for _ in range(3)] == [200, 200, 429]
        assert c.get("/health/live").status_code == 200  # exempt


def test_client_ip_respects_trust_setting(make_settings) -> None:
    scope = {"client": ("10.0.0.5", 1234), "headers": [(b"x-forwarded-for", b"6.6.6.6, 1.2.3.4")]}
    assert client_ip_from_scope(scope, make_settings()) == "10.0.0.5"
    assert client_ip_from_scope(scope, make_settings(TRUST_PROXY_HEADERS=True)) == "1.2.3.4"
    assert client_ip_from_scope(scope, make_settings(TRUST_PROXY_HEADERS=True, PROXY_TRUSTED_HOPS=2)) == "6.6.6.6"
