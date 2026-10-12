"""Liveness / readiness probes (public, never rate-limited or encrypted)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from loguru import logger

from core.errors import ServiceUnavailableError
from core.responses import ApiResponse, ok
from dto.common import BaseSchema

router = APIRouter(prefix="/health", tags=["health"])


class LiveData(BaseSchema):
    status: Literal["ok"] = "ok"


class ReadyData(BaseSchema):
    status: Literal["ready"] = "ready"
    checks: dict[str, str]


@router.get("/live", response_model=ApiResponse[LiveData])
def live() -> ApiResponse:
    return ok(LiveData())


@router.get("/ready", response_model=ApiResponse[ReadyData])
def ready(request: Request) -> ApiResponse:
    state = request.app.state
    checks: dict[str, str] = {}

    database = getattr(state, "database", None)
    try:
        if database is None:
            raise RuntimeError("not initialised")
        database.ping()
        if not getattr(state, "schema_ready", False):
            database.ensure_schema()
            state.schema_ready = True
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001  # probe must report, not raise
        logger.warning("Readiness: database check failed: {}", exc)
        checks["database"] = "unavailable"

    redis = getattr(state, "redis", None)
    try:
        if redis is None:
            raise RuntimeError("not initialised")
        redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001  # probe must report, not raise
        logger.warning("Readiness: redis check failed: {}", exc)
        checks["redis"] = "unavailable"

    if any(value != "ok" for value in checks.values()):
        raise ServiceUnavailableError("Service is not ready", details=checks)
    return ok(ReadyData(checks=checks))
