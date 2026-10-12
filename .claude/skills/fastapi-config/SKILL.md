---
name: config
description: "Backend (apps/backend) configuration & startup: pydantic-settings Settings in core/config.py (BE_* env vars, .env / BE_ENV_FILE, get_settings(), SettingsDep, startup validation), app factory create_app() + lifespan in core/app_factory.py, api.py entrypoint (port 8020), router registry RouterSpec/ROUTERS + BE_ENABLED_ROUTERS in router/__init__.py, pure-ASGI middleware stack (CORS, RequestContext/X-Request-ID, global rate limit, PayloadEncryptionMiddleware/BE_ENC_ACTIVE), optional integrations (S3, Kafka, SMTP, Google, Supabase). Use when adding env vars, changing startup, enabling/disabling routers, or adding middleware."
---

# config — Settings, startup, routers & middleware

## Use this skill when

- Adding/changing an environment variable or a default
- Changing app startup/shutdown, CORS, proxies, docs, workers/reload
- Enabling/disabling routers per deployment, or registering a new router
- Adding middleware

## Key files

| File | Contents |
|---|---|
| `apps/backend/core/config.py` | `Settings` (env prefix `BE_`), validators, helper properties, `get_settings()`, `load_settings()` |
| `apps/backend/.env.example` | every key, documented; `npm run setup:backend` copies it to `apps/backend/.env` and fills secrets |
| `apps/backend/api.py` | `app = create_app()`; `python api.py` runs uvicorn with `BE_HOST/PORT/WORKERS/RELOAD` |
| `apps/backend/core/app_factory.py` | `create_app(settings=None, *, database=None, redis=None, routers=None)`, `lifespan` |
| `apps/backend/router/__init__.py` | `RouterSpec`, `HEALTH`, `ROUTERS`, `select_routers`, `include_routers` |
| `apps/backend/core/middleware.py` | `RequestContextMiddleware`, `PayloadEncryptionMiddleware` (pure ASGI) |
| `apps/backend/core/rate_limit.py` | `GlobalRateLimitMiddleware`, `rate_limit()` dependency |
| `apps/backend/core/logging.py` | `setup_logging(settings)` (called by `create_app`) |

## Settings rules

### MUST
- Declare every setting as a typed field on `Settings` in `core/config.py` (name **without** prefix) and document
  it in `apps/backend/.env.example` **with** the `BE_` prefix: `UPLOAD_MAX_SIZE_MB` ↔ `BE_UPLOAD_MAX_SIZE_MB`.
- Secrets are `SecretStr` (read with `.get_secret_value()`); optional values default to `None` and blank strings
  are normalised to `None` (add the field to the `_blank_to_none` / `_blank_secret_to_none` validator lists).
- Lists are `CsvList` (comma-separated or JSON array) and listed in the `_parse_csv` validator.
- Cross-field rules go in `_cross_field_checks` (they fail startup with a clear message).
- Optional integrations expose a `*_configured` property (`s3_configured`, `kafka_configured`, `smtp_configured`,
  `google_configured`, `internal_token_configured`); code that needs an unconfigured feature raises
  `ConfigurationError` (503) instead of failing at startup.
- In routes/deps read settings via `SettingsDep` (the instance the app was built with); in plain code
  `core.config.get_settings()` (cached; `get_settings.cache_clear()` in tests).

### MUST NOT
- Never `os.getenv` / `os.environ[...]` in app code, never `python-dotenv`, never parse `sys.argv` at import time.
- Never instantiate `Settings()` at module import (nothing happens at import time).
- No hard-coded hosts, ports, secrets, origins or table names.
- No `"*"` in `BE_CORS_ORIGINS` (rejected: cookies are used).

```python
# core/config.py (excerpt)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BE_", env_file=None, extra="ignore", ...)
    APP_NAME: str = "App"
    PORT: int = Field(default=8020, ge=1, le=65535)
    ENABLED_ROUTERS: CsvList = Field(default_factory=list)
    DB_PROVIDER: Literal["mongo", "supabase"] = "mongo"
    JWT_SECRET: SecretStr
    S3_BUCKET: str | None = None

    @property
    def s3_configured(self) -> bool: ...
```

Env file: `BE_ENV_FILE` (default `.env`), looked up in the cwd then `apps/backend/`; real environment variables win.

## Startup (`create_app`)

1. `setup_logging(settings)`; FastAPI app with `root_path=BE_ROOT_PATH`, docs at `/docs` unless `BE_DOCS_ENABLED=false`.
2. `app.state`: `settings`, `database`, `redis`, `schema_ready`, `supabase_verifier`.
3. `register_exception_handlers(app)` + driver-outage → 503 handlers.
4. `include_routers(app, settings, routers)` (strict: unknown name / import failure aborts startup).
5. Middleware (added inner → outer): `PayloadEncryptionMiddleware` (if `BE_ENC_ACTIVE`) →
   `GlobalRateLimitMiddleware` (if `BE_RATE_LIMIT_GLOBAL > 0`) → `RequestContextMiddleware` → `CORSMiddleware` (outermost).
6. Lifespan: thread limiter = `BE_THREADPOOL_SIZE`; create DB (`db.factory.create_database`) and Redis
   unless injected; `ensure_schema()` (Mongo indexes / Postgres table check — failures are logged and retried by
   `/health/ready`); on shutdown close Kafka producer, DB and Redis.

Run: `npm run dev:backend` (root; reload on) · `npm run dev` (backend 8020 + web 3000) ·
`cd apps/backend && .venv/bin/python api.py` · `uvicorn api:app --port 8020`.

## Router registry

```python
# router/__init__.py
ROUTERS = (
    HEALTH,
    RouterSpec("auth", "router.auth"),
    RouterSpec("auth", "router.auth", attr="local_router", enabled=_local_auth),
    RouterSpec("auth", "router.auth", attr="google_router", enabled=_google_auth),
    RouterSpec("user", "router.user"),
    ...
)
```
- Add one `RouterSpec("<name>", "router.<module>")` per new router (optionally `attr=`, `enabled=` predicate on settings).
- `BE_ENABLED_ROUTERS=user,auth` mounts exactly those + `health`; empty = all. Names are exact and lower-cased.
- Tests/tools pass `create_app(settings, routers=[HEALTH, RouterSpec("note", "router.note")])`.

## Middleware rules

- Write pure ASGI middleware (`__call__(scope, receive, send)`) like `core/middleware.py`; **no** `BaseHTTPMiddleware`
  body hacks. Remember `add_middleware` prepends: the last added is the outermost.
- Errors produced in middleware use `core.errors.error_response(status, message, ErrorCode.X)` so the envelope stays consistent.
- Exempt `/health`, `/docs`, `/redoc`, `/openapi.json` where it makes sense (`is_exempt_path`).
- Prefer a dependency (`Depends(...)`) over middleware for per-route concerns (auth, rate limits).

## Checklist — new setting

- [ ] Field on `Settings` (type, default, `Field(ge=..)` bounds, `SecretStr` for secrets)
- [ ] Blank-to-None / CSV validator lists updated if applicable
- [ ] Cross-field check if it depends on another setting
- [ ] `apps/backend/.env.example` entry with comment
- [ ] `*_configured` property + `ConfigurationError` path if the feature is optional
- [ ] Test in `apps/backend/tests/core/test_config.py` (`make_settings(...)` fixture)
- [ ] Docker/compose env (`docker-compose.yml`) if needed in containers

## Common mistakes

| Mistake | Fix |
|---|---|
| `.env` key without `BE_` prefix | silently ignored — always `BE_` |
| `get_settings()` inside a route | `SettingsDep` (tests build apps with custom settings) |
| Feature crashes startup when its service is absent | make it optional + `ConfigurationError` on use |
| `BE_RELOAD=true` with `BE_ENVIRONMENT=production` | refused at startup by design |
| Cookies missing over plain HTTP | `BE_COOKIE_SECURE=false` locally only |
| Swagger broken behind the proxy | `BE_ROOT_PATH=/api/v1/apps` (then direct `:8020/docs` cannot load the schema) |

Full settings reference: [references/config-rules.md](references/config-rules.md)
