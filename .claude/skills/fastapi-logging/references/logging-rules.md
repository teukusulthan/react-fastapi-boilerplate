# Logging rules (detailed)

Companion to [../SKILL.md](../SKILL.md). Verified against `apps/backend/core/logging.py` and
`apps/backend/core/middleware.py`.

## Real examples in the codebase

```python
# service/upload.py
logger.info("Upload {} stored ({} bytes, {}) by {}", upload_id, size, mime, actor.id)
logger.error("S3 upload of {} failed: {}", key, exc)              # then: raise ServiceUnavailableError(...)

# core/deps.py
logger.info("Provisioned local user for Supabase identity {}", censor_email(email))

# service/auth/login.py
logger.warning("Login locked for identifier hash {} from {}", digest(identifier.lower())[:12], ip)

# core/app_factory.py (lifespan)
logger.info("{} {} started (env={}, db={}, auth={})", settings.APP_NAME, settings.APP_VERSION, ...)
```

## What to log

| Event | Level |
|---|---|
| Startup/shutdown, provider in use | info |
| Record created/deleted by an actor (ids only) | info |
| Security-relevant: lockout, revoked-token reuse, internal token misconfigured | warning |
| Best-effort side effect failed (Kafka publish, email send) | error, no raise if best-effort |
| External dependency failed and request aborted | error + raise `ServiceUnavailableError` / `ConfigurationError` |
| Branches useful when debugging | debug |

## Never log

Passwords, password hashes, JWTs/refresh tokens, `X-Internal-Token`, OTP codes, TOTP secrets, cookies,
`BE_*` secret values, full request/response bodies, full email addresses or phone numbers.
Exception: `BE_EMAIL_BACKEND=console` intentionally prints dev emails (incl. OTPs) — it is refused in production.

## Third-party loggers

stdlib logging (uvicorn, pymongo, psycopg, botocore, httpx, kafka…) is routed into loguru by
`InterceptHandler`; chatty ones are capped at WARNING in `_NOISY_LOGGERS`. To quiet another library, add it
to that tuple rather than configuring logging elsewhere.

## Tests

Tests set `BE_LOG_LEVEL=WARNING` and `BE_ACCESS_LOG=false` (`apps/backend/tests/conftest.py`). To assert on a
log line, add a temporary loguru sink in the test (`handler_id = logger.add(list.append)` … `logger.remove(handler_id)`).

## Forbidden patterns

| Forbidden | Instead |
|---|---|
| `print(...)` / `traceback.print_exc()` | `logger.debug(...)` / `logger.opt(exception=exc).error(...)` |
| `import logging; logging.info(...)` in app code | `from loguru import logger` |
| f-string log messages | `{}` placeholders with arguments |
| `str(exc)` in an API message | fixed safe message; exception only in the log |
