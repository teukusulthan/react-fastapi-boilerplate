"""Router registry, health probes and lifespan wiring."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from core.app_factory import create_app
from router import HEALTH, ROUTERS, RouterSpec, select_routers


def _names(specs) -> list[tuple[str, str]]:
    return [(s.name, s.attr) for s in specs]


def test_all_routers_by_default(settings) -> None:
    selected = _names(select_routers(settings))
    assert ("health", "router") in selected
    assert ("auth", "local_router") in selected
    assert ("auth", "google_router") not in selected  # google not configured
    assert {n for n, _ in selected} == {"health", "auth", "user", "group", "permission", "role", "upload"}


def test_exact_name_toggle_no_substring_match(make_settings) -> None:
    selected = _names(select_routers(make_settings(ENABLED_ROUTERS="user")))
    assert selected == [("health", "router"), ("user", "router")]


def test_unknown_router_name_is_an_error(make_settings) -> None:
    with pytest.raises(ValueError, match="use"):
        select_routers(make_settings(ENABLED_ROUTERS="use"))


def test_auth_routes_depend_on_provider(make_settings) -> None:
    supabase = make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET="x" * 40)
    assert _names(select_routers(supabase, [s for s in ROUTERS if s.name == "auth"])) == [("auth", "router")]
    google = make_settings(GOOGLE_CLIENT_ID="id", GOOGLE_CLIENT_SECRET="secret")
    assert ("auth", "google_router") in _names(select_routers(google))


def test_registry_is_strict(settings, database, redis_client) -> None:
    with pytest.raises(ModuleNotFoundError):
        create_app(
            settings, database=database, redis=redis_client, routers=[HEALTH, RouterSpec("x", "router.does_not_exist")]
        )
    with pytest.raises(ImportError, match="not an APIRouter"):
        create_app(
            settings, database=database, redis=redis_client, routers=[RouterSpec("x", "router.health", attr="nope")]
        )


def test_health_live_and_ready(client: TestClient) -> None:
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["data"] == {"status": "ok"}
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["data"] == {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}


def test_ready_reports_failures(app, monkeypatch: pytest.MonkeyPatch) -> None:
    with TestClient(app) as c:

        def broken_ping() -> None:
            raise RedisConnectionError("down")

        monkeypatch.setattr(app.state.redis, "ping", broken_ping)
        resp = c.get("/health/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["metaData"]["errorCode"] == "SERVICE_UNAVAILABLE"
    assert body["data"] == {"database": "ok", "redis": "unavailable"}


def test_lifespan_keeps_injected_clients(app) -> None:
    with TestClient(app):
        db, redis = app.state.database, app.state.redis
        assert app.state.schema_ready is True
    assert app.state.database is db and app.state.redis is redis  # not closed/owned


def test_docs_can_be_disabled(make_settings, make_app) -> None:
    with TestClient(make_app(make_settings(DOCS_ENABLED=False))) as c:
        assert c.get("/docs").status_code == 404
        assert c.get("/openapi.json").status_code == 404


def test_infrastructure_errors_map_to_503(settings, database, redis_client) -> None:
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/down")
    def down() -> None:
        raise RedisConnectionError("connection refused to secret-host")

    import types

    module = types.ModuleType("tests_tmp_down_router")
    module.router = router  # type: ignore[attr-defined]
    import sys

    sys.modules["tests_tmp_down_router"] = module
    try:
        app = create_app(
            settings, database=database, redis=redis_client, routers=[RouterSpec("d", "tests_tmp_down_router")]
        )
        with TestClient(app) as c:
            resp = c.get("/down")
    finally:
        del sys.modules["tests_tmp_down_router"]
    assert resp.status_code == 503
    assert resp.json()["metaData"]["errorCode"] == "SERVICE_UNAVAILABLE"
    assert "secret-host" not in resp.text
