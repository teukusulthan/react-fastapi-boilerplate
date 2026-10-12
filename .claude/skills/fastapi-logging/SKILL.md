---
name: logging
description: "Backend (apps/backend) logging & observability: loguru configured once by core/logging.py setup_logging() ({}-style formatting, stdlib/uvicorn intercepted, BE_LOG_LEVEL / BE_LOG_JSON / BE_ACCESS_LOG), request ids (X-Request-ID, logger.contextualize) and access log from RequestContextMiddleware, censor_email for PII, health probes /health/live and /health/ready. Use when adding logs, debugging, or instrumenting services."
---

# Logging & observability (backend)

## Use this skill when

- Adding log lines to services, deps, scripts or middleware
- Debugging a request (find it by `requestId` / `X-Request-ID`)
- Changing log format/level, JSON logs for shippers, access logging, or health checks

## Key files

| File | Contents |
|---|---|
| `apps/backend/core/logging.py` | `setup_logging(settings)`: loguru sink (text or JSON), stdlib `InterceptHandler`, noisy loggers capped at WARNING |
| `apps/backend/core/middleware.py` | `RequestContextMiddleware`: `X-Request-ID` in/out, `logger.contextualize(request_id=...)`, one access-log line per request, last-resort 500 |
| `apps/backend/core/context.py` | `get_request_id()`, `get_execution_time_ms()` (used by the response envelope) |
| `apps/backend/router/health.py` | `GET /health/live`, `GET /health/ready` (DB + Redis checks) |
| `apps/backend/util/helper.py` | `censor_email()` |

## Rules

### MUST
- `from loguru import logger` and `{}` placeholders: `logger.info("Upload {} stored ({} bytes) by {}", upload_id, size, actor.id)`.
- Log **ids**, counts, durations and outcomes; mask emails with `censor_email(email)`.
- Use levels deliberately: `debug` (flow detail), `info` (state changes: created/deleted/started), `warning`
  (recoverable/suspicious: lockouts, readiness failures), `error` (failed external call, data not saved).
- Log exceptions where they are handled, with context: `logger.opt(exception=exc).error(...)` or
  `logger.error("S3 upload of {} failed: {}", key, exc)` — then raise a safe `AppError`.
- Let the middleware log unhandled exceptions and access lines; every line automatically carries `request_id`.

### MUST NOT
- No `print()` (ruff `T20` fails the lint), no `traceback.print_exc()`, no `logging.getLogger(__name__)` in app code.
- No f-strings or `%` in log calls (`logger.info(f"...")`) — formatting must stay lazy and structured.
- Never log passwords, tokens (JWT, refresh, internal), OTPs, secrets, full request bodies, cookies or full emails.
- Don't call `setup_logging` or `logger.add` from modules — only `create_app` configures logging.
- Don't put exception text into API responses (it goes to logs only).

## Configuration

| Setting | Effect |
|---|---|
| `BE_LOG_LEVEL` (INFO) | TRACE…CRITICAL |
| `BE_LOG_JSON` (false) | one JSON object per line (`serialize=True`) for log shippers |
| `BE_ACCESS_LOG` (true) | middleware access line `ip "METHOD path" status 12.3ms` (health at DEBUG) |
| `BE_ENVIRONMENT=production` | disables loguru `diagnose` (no variable values in tracebacks) |

Text format: `time | LEVEL | request_id | module:line - message`. uvicorn's own access log is silenced
(`api.py` runs uvicorn with `access_log=False`, `log_config=None`).

## Health & tracing

- `/health/live` → 200 always; `/health/ready` → 200 with `{"database":"ok","redis":"ok"}` or 503
  `SERVICE_UNAVAILABLE` with the checks in `data` (also retries Mongo index / Postgres table checks).
- Clients may send `X-Request-ID` (validated `[A-Za-z0-9._:-]{1,128}`); otherwise one is generated. It is echoed
  in the response header and in `metaData.requestId`, so a user-reported error maps to log lines.

## Checklist

- [ ] `logger` from loguru, `{}` placeholders, no secrets/PII
- [ ] Level matches impact; failure paths log once (not at every layer)
- [ ] `npm run lint` passes (ruff `T20` catches `print`)

## Common mistakes

| Mistake | Fix |
|---|---|
| `logger.info(f"user {email} logged in")` | `logger.info("user {} logged in", censor_email(email))` |
| Logging then re-raising at every layer | log where handled; let `AppError` propagate |
| `except Exception: pass` | log with context, or let the global handler log it |
| `print(debug)` left in code | `logger.debug(...)` |

Details: [references/logging-rules.md](references/logging-rules.md)
