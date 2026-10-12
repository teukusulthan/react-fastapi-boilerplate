"""Application factory.

``create_app(settings=None, *, database=None, redis=None, routers=None)``:

* ``settings`` — defaults to ``core.config.get_settings()``.
* ``database`` / ``redis`` — inject pre-built clients (tests: mongomock + fakeredis);
  otherwise they are created in the lifespan from settings and closed on shutdown.
* ``routers`` — a subset of ``router.ROUTERS`` (default: the full registry).

Middleware (outermost first): CORS -> request context (X-Request-ID, access log,
last-resort 500) -> optional global rate limit -> optional payload encryption -> app.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import anyio.to_thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.config import Settings, get_settings
from core.errors import ErrorCode, error_response, register_exception_handlers
from core.logging import setup_logging
from core.middleware import REQUEST_ID_HEADER, PayloadEncryptionMiddleware, RequestContextMiddleware
from core.rate_limit import GlobalRateLimitMiddleware
from core.redis import create_redis
from core.security import SupabaseTokenVerifier
from db.factory import create_database
from router import RouterSpec, include_routers
from util.crypto import decode_aes_key
from util.kafka import close_kafka_producer

if TYPE_CHECKING:
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from redis import Redis

    from db.base import Database


def _ensure_schema(app: FastAPI) -> None:
    try:
        app.state.database.ensure_schema()
        app.state.schema_ready = True
    except Exception as exc:  # noqa: BLE001  # reported via /health/ready, retried there
        app.state.schema_ready = False
        logger.error("Database schema check failed (readiness will retry): {}", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    anyio.to_thread.current_default_thread_limiter().total_tokens = settings.THREADPOOL_SIZE
    if app.state.database is None:
        app.state.database = create_database(settings)
    if app.state.redis is None:
        app.state.redis = create_redis(settings)
    await anyio.to_thread.run_sync(app.state.database.open)
    await anyio.to_thread.run_sync(_ensure_schema, app)
    logger.info(
        "{} {} started (env={}, db={}, auth={})",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
        settings.DB_PROVIDER,
        settings.AUTH_PROVIDER,
    )
    try:
        yield
    finally:
        await anyio.to_thread.run_sync(close_kafka_producer)
        if app.state.owns_database and app.state.database is not None:
            await anyio.to_thread.run_sync(app.state.database.close)
            app.state.database = None
        if app.state.owns_redis and app.state.redis is not None:
            app.state.redis.close()
            app.state.redis = None
        logger.info("{} stopped", settings.APP_NAME)


def _register_infrastructure_errors(app: FastAPI) -> None:
    """Driver-level outages -> 503 SERVICE_UNAVAILABLE instead of an opaque 500."""
    from psycopg import OperationalError as PgOperationalError
    from psycopg_pool import PoolTimeout
    from pymongo.errors import ConnectionFailure as MongoConnectionFailure
    from redis.exceptions import ConnectionError as RedisConnectionError
    from redis.exceptions import TimeoutError as RedisTimeoutError

    async def handler(_: Request, exc: Exception) -> JSONResponse:
        logger.error("Backing service unavailable: {}: {}", type(exc).__name__, exc)
        return error_response(503, "Service temporarily unavailable", ErrorCode.SERVICE_UNAVAILABLE)

    for exc_type in (MongoConnectionFailure, PgOperationalError, PoolTimeout, RedisConnectionError, RedisTimeoutError):
        app.add_exception_handler(exc_type, handler)


def create_app(
    settings: Settings | None = None,
    *,
    database: Database | None = None,
    redis: Redis | None = None,
    routers: Sequence[RouterSpec] | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings)

    docs = settings.DOCS_ENABLED
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        root_path=settings.ROOT_PATH,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings
    app.state.database = database
    app.state.redis = redis
    app.state.owns_database = database is None
    app.state.owns_redis = redis is None
    app.state.schema_ready = False
    app.state.supabase_verifier = SupabaseTokenVerifier(settings) if settings.AUTH_PROVIDER == "supabase" else None

    register_exception_handlers(app)
    _register_infrastructure_errors(app)
    include_routers(app, settings, routers)

    # add_middleware() prepends: the LAST one added is the OUTERMOST.
    if settings.ENC_ACTIVE and settings.ENC_SECRET is not None:  # secret presence enforced by Settings
        app.add_middleware(PayloadEncryptionMiddleware, key=decode_aes_key(settings.ENC_SECRET.get_secret_value()))
    if settings.RATE_LIMIT_ENABLED and settings.RATE_LIMIT_GLOBAL > 0:
        app.add_middleware(GlobalRateLimitMiddleware, settings=settings, redis_getter=lambda: app.state.redis)
    app.add_middleware(RequestContextMiddleware, access_log=settings.ACCESS_LOG, max_page_size=settings.MAX_PAGE_SIZE)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER, "Retry-After"],
        max_age=600,
    )
    return app
