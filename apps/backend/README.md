# Backend — FastAPI

A FastAPI service with JWT auth (local or Supabase), RBAC, and CRUD modules (user, group, permission,
role, upload). It runs on MongoDB **or** Supabase Postgres through a provider-agnostic repository layer.
The default port is **8020**.

- Conventions and recipes for contributors and AI agents: [`AI_GUIDE.md`](AI_GUIDE.md)
- Endpoint contract: [`../../docs/api-spec.md`](../../docs/api-spec.md)
- Data model: [`../../docs/database-schema.md`](../../docs/database-schema.md)

## Requirements

- Python ≥ 3.10 (3.12 recommended; Docker and CI use 3.12). [uv](https://docs.astral.sh/uv/) is
  recommended; plain `venv` + `pip` also works.
- Redis (sessions, token revocation, OTPs, rate limits). The app boots without it, but `/health/ready`
  reports it, and auth flows fail with 503 until it is reachable.
- MongoDB (default provider) **or** a Postgres/Supabase database with `migrations/supabase/*.sql` applied.
- `libmagic` (upload MIME detection): `apt install libmagic1` on Debian/Ubuntu, `brew install libmagic`
  on macOS.

Start Mongo and Redis quickly with Docker from the repo root: `npm run docker:infra`.

## Setup

From the repository root (recommended):

```bash
npm run setup:backend        # creates apps/backend/.venv, installs requirements-dev.txt,
                             # creates apps/backend/.env from .env.example with random secrets
npm run seed                 # default permissions (admin, user) + bootstrap admin
npm run dev:backend          # http://localhost:8020  (Swagger: /docs)
```

`setup:backend` fills in `BE_JWT_SECRET`, `BE_INTERNAL_TOKEN`, `BE_DATA_ENCRYPTION_KEY` and a random
`BE_BOOTSTRAP_ADMIN_PASSWORD`, and prints the admin login once. Options:
`npm run setup:backend -- --recreate | --python 3.12 | --no-uv | --dry-run`.

Manual setup, if you prefer it:

```bash
cd apps/backend
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt   # runtime only: requirements.txt
cp .env.example .env            # then set BE_JWT_SECRET (openssl rand -hex 32)
.venv/bin/python -m scripts.seed
.venv/bin/python api.py         # or: .venv/bin/uvicorn api:app --port 8020 --no-access-log --no-proxy-headers
```

`api.py` reads host, port, workers and reload from settings (`BE_HOST`, `BE_PORT`, `BE_WORKERS`,
`BE_RELOAD`). It has no CLI flags. `npm run dev` / `dev:backend` set `BE_RELOAD=true` unless you
override it.

## Commands

| Task | From the repo root | From `apps/backend` |
|---|---|---|
| Run (dev) | `npm run dev:backend` | `.venv/bin/python api.py` |
| Tests | `npx nx run backend:test` | `.venv/bin/python -m pytest` |
| Postgres integration tests | — | `TEST_POSTGRES_DSN=postgresql://… .venv/bin/python -m pytest -m integration` |
| Lint | `npx nx run backend:lint` | `.venv/bin/python -m ruff check .` |
| Format check / apply | `npx nx run backend:format-check` / `backend:format` | `.venv/bin/python -m ruff format --check .` / `ruff format .` |
| Seed | `npm run seed` | `.venv/bin/python -m scripts.seed` |
| Whole repo quality gate | `npm run ci` | — |

Tests need no running services: they use mongomock and fakeredis. When `TEST_POSTGRES_DSN` is set, the
module tests also run against real Postgres and apply the migrations themselves.

## Database providers

| `BE_DB_PROVIDER` | What you need | Schema |
|---|---|---|
| `mongo` (default) | `BE_MONGO_URI`, `BE_MONGO_DB` | Unique and lookup indexes are created on startup (`db/mongo/indexes.py`) |
| `supabase` | `BE_SUPABASE_DB_URL` (direct :5432 or pooler :6543) | Apply `migrations/supabase/*.sql` yourself; see [`migrations/supabase/README.md`](migrations/supabase/README.md). The app only checks that the tables exist. |

Local Postgres without a full Supabase stack:
`DB_PROVIDER=supabase docker compose --profile postgres up -d --build` (from the repo root). This applies
a small compatibility layer plus the migrations.

## Auth providers

| `BE_AUTH_PROVIDER` | Behaviour |
|---|---|
| `local` (default) | Own HS256 JWTs (`BE_JWT_*`), httpOnly cookies `token` / `refresh_token` plus tokens in the body, login/register/OTP/2FA/forgot-password, refresh rotation with reuse detection, Redis-backed revocation. Google sign-in is mounted only when `BE_GOOGLE_CLIENT_ID` and `BE_GOOGLE_CLIENT_SECRET` are set. |
| `supabase` | Verifies Supabase-issued JWTs (`BE_SUPABASE_JWKS_URL`, or HS256 with `BE_SUPABASE_JWT_SECRET`; audience `BE_SUPABASE_JWT_AUDIENCE`). The first request auto-provisions a `users` row (permission `BE_DEFAULT_PERMISSION_ALIAS`). Only `/auth/me` and `/auth/logout` are mounted. Run the seed after the admin's first sign-in to promote `BE_BOOTSTRAP_ADMIN_EMAIL`. |

In both modes, system-to-system calls may send `X-Internal-Token: <BE_INTERNAL_TOKEN>`.

## Environment

Every setting has the `BE_` prefix and lives in `apps/backend/.env`. Use `BE_ENV_FILE=.env.staging` to
pick another file. Real environment variables override the file. Lists accept CSV or JSON arrays. The
source of truth is [`core/config.py`](core/config.py), and [`.env.example`](.env.example) documents
every key. Values below are the `.env.example` values; where the code default differs, it is noted.

| Variable | Example | Notes |
|---|---|---|
| **App** | | |
| `BE_APP_NAME` / `BE_APP_VERSION` | `App` / `1.0.0` | Used in the OpenAPI title, logs and email branding |
| `BE_ENVIRONMENT` | `development` | `development`, `test`, `staging` or `production`. Production enforces secure cookies, a real JWT secret and no reload. |
| `BE_HOST` / `BE_PORT` / `BE_WORKERS` / `BE_RELOAD` | `0.0.0.0` / `8020` / `1` / `false` | Read by `python api.py` |
| `BE_ROOT_PATH` | _(empty)_ | Set only to browse Swagger through the `/api/v1/apps` proxy (see Troubleshooting) |
| `BE_DOCS_ENABLED` | `true` | `/docs`, `/redoc`, `/openapi.json` |
| `BE_THREADPOOL_SIZE` | `40` | Maximum concurrent sync routes and dependencies |
| `BE_ENABLED_ROUTERS` | _(empty)_ | Exact names, comma-separated; empty = all (`health`, `auth`, `user`, `group`, `permission`, `role`, `upload`). Unknown names fail startup. `health` is always mounted. |
| `BE_PUBLIC_WEB_URL` | `http://localhost:3000` | Base URL of the web app, for links in emails |
| **Logging** | | |
| `BE_LOG_LEVEL` / `BE_LOG_JSON` / `BE_ACCESS_LOG` | `INFO` / `false` / `true` | |
| **Database** | | |
| `BE_DB_PROVIDER` | `mongo` | `mongo` or `supabase` |
| `BE_MONGO_URI` / `BE_MONGO_DB` / `BE_MONGO_TIMEOUT_MS` | `mongodb://localhost:27017` / `app` / `5000` | |
| `BE_SUPABASE_URL` | _(empty)_ | Informational |
| `BE_SUPABASE_DB_URL` | _(empty)_ | Required when `BE_DB_PROVIDER=supabase` |
| `BE_SUPABASE_DB_SCHEMA` / `_POOL_MIN` / `_POOL_MAX` / `_TIMEOUT` | `public` / `1` / `10` / `10` | |
| `BE_TABLE_USERS` … `BE_TABLE_UPLOADS` | `users`, `permissions`, `groups`, `roles`, `uploads` | Collection/table names. The SQL migrations assume the defaults. |
| **Redis** | | |
| `BE_REDIS_URL` | _(empty)_ | Wins over host/port/password/db (`rediss://` for TLS) |
| `BE_REDIS_HOST` / `_PORT` / `_PASSWORD` / `_DB` / `_SSL` | `localhost` / `6379` / _(empty)_ / `0` / `false` | |
| `BE_REDIS_KEY_PREFIX` | `app` | Namespace for every key |
| **Auth** | | |
| `BE_AUTH_PROVIDER` | `local` | `local` or `supabase` |
| `BE_JWT_SECRET` | placeholder | **Required**, ≥ 32 chars (`openssl rand -hex 32`); the placeholder is rejected in production |
| `BE_JWT_ALGORITHM` / `BE_JWT_ISSUER` | `HS256` / `app` | |
| `BE_JWT_ACCESS_TTL` / `BE_JWT_REFRESH_TTL` / `BE_JWT_LEEWAY` | `900` / `604800` / `10` | Seconds |
| `BE_COOKIE_SECURE` | `false` | Code default `true`. Must be `true` in production (HTTPS). |
| `BE_COOKIE_SAMESITE` / `BE_COOKIE_DOMAIN` / `BE_COOKIE_REFRESH_PATH` | `lax` / _(empty)_ / `/` | `none` requires secure cookies |
| `BE_INTERNAL_TOKEN` | _(empty)_ | `X-Internal-Token` value (≥ 32 chars); empty disables internal calls |
| `BE_SUPERUSER_ALIASES` | `admin,owner` | Permission aliases that act as superuser |
| `BE_DEFAULT_PERMISSION_ALIAS` | `user` | Given to self-registered, auto-provisioned and admin-created users without `permissionId` |
| `BE_PASSWORD_MIN_LENGTH` | `8` | |
| `BE_ACCOUNT_LOCK_MAX_ATTEMPTS` / `BE_ACCOUNT_LOCK_SECONDS` | `5` / `900` | Per account + IP |
| `BE_OTP_LENGTH` / `_TTL` / `_MAX_ATTEMPTS` / `_RESEND_COOLDOWN` | `6` / `600` / `5` / `60` | |
| `BE_TWO_FACTOR_SESSION_TTL` / `BE_TOTP_ISSUER` | `300` / _(empty = app name)_ | |
| `BE_GOOGLE_CLIENT_ID` / `BE_GOOGLE_CLIENT_SECRET` | _(empty)_ | Both set → `POST /auth/google/callback` is mounted |
| `BE_SUPABASE_JWKS_URL` / `BE_SUPABASE_JWT_SECRET` | _(empty)_ | One is required when `BE_AUTH_PROVIDER=supabase` |
| `BE_SUPABASE_JWT_AUDIENCE` / `BE_SUPABASE_JWT_ISSUER` | `authenticated` / _(empty)_ | |
| `BE_BOOTSTRAP_ADMIN_EMAIL` / `_PASSWORD` / `_USERNAME` / `_FULLNAME` | `admin@example.com` / placeholder / `admin` / `Administrator` | Used by the seed. `npm run setup` randomizes the password. |
| **HTTP / CORS** | | |
| `BE_CORS_ORIGINS` | `http://localhost:3000` | Explicit origins only (`*` is rejected because cookies are used) |
| `BE_TRUST_PROXY_HEADERS` / `BE_PROXY_TRUSTED_HOPS` | `false` / `1` | Honour `X-Forwarded-For` only behind your own proxy (Compose sets `true`) |
| **Rate limit** | | |
| `BE_RATE_LIMIT_ENABLED` | `true` | |
| `BE_RATE_LIMIT_GLOBAL` / `BE_RATE_LIMIT_WINDOW` | `0` / `60` | Global per-client budget; `0` = off |
| `BE_RATE_LIMIT_AUTH` / `BE_RATE_LIMIT_AUTH_WINDOW` | `10` / `60` | Login, OTP, register and password endpoints, per IP |
| `BE_MAX_PAGE_SIZE` | `100` | Maximum `size` in `get-all` |
| **Encryption** | | |
| `BE_DATA_ENCRYPTION_KEY` | _(empty)_ | Fernet key; encrypts TOTP secrets at rest (setup generates one) |
| `BE_ENC_ACTIVE` / `BE_ENC_SECRET` | `false` / _(empty)_ | Optional AES-256-GCM payload encryption (`{"payload": "<b64>"}`); the secret is base64 of 32 bytes |
| **Upload** | | |
| `BE_UPLOAD_MAX_SIZE_MB` | `25` | |
| `BE_UPLOAD_ALLOWED_TYPES` | images, pdf, text, csv, json, zip | The code default also allows Office formats. HTML/SVG/XML/JS are blocked unless listed here. |
| `BE_UPLOAD_IMAGE_MAX_DIMENSION` / `BE_UPLOAD_KEY_PREFIX` | `2048` / `uploads` | |
| **S3 (AWS / MinIO / Supabase Storage)** | | |
| `BE_S3_ENDPOINT_URL` / `BE_S3_REGION` / `BE_S3_BUCKET` | _(empty)_ / `us-east-1` / _(empty)_ | Upload endpoints return 503 `CONFIGURATION_ERROR` until the bucket and keys are set |
| `BE_S3_ACCESS_KEY_ID` / `BE_S3_SECRET_ACCESS_KEY` | _(empty)_ | |
| `BE_S3_FORCE_PATH_STYLE` / `BE_S3_PRESIGN_TTL` | `true` / `900` | |
| **Kafka (optional)** | | |
| `BE_KAFKA_BOOTSTRAP_SERVERS` / `BE_KAFKA_CLIENT_ID` / `BE_KAFKA_TOPIC_FILE_EXTRACTION` | _(empty)_ | Used only by `extractFile=true` uploads |
| **SMTP / email** | | |
| `BE_SMTP_HOST` / `_PORT` / `_USERNAME` / `_PASSWORD` | _(empty)_ / `587` / … | |
| `BE_SMTP_STARTTLS` / `BE_SMTP_SSL` / `BE_SMTP_TIMEOUT` | `true` / `false` / `10` | Port 465 → `BE_SMTP_SSL=true` |
| `BE_SMTP_FROM_EMAIL` / `BE_SMTP_FROM_NAME` | _(empty)_ | |
| `BE_EMAIL_BACKEND` | `auto` | `auto` = SMTP if configured, else the console log (non-production) or disabled (production). `smtp`, `console` and `disabled` force a backend. |
| `BE_EMAIL_TEMPLATES_DIR` | _(empty)_ | Override `templates/email` (for example, to localize) |
| **Auth flows (local)** | | |
| `BE_REGISTRATION_ENABLED` / `BE_REGISTRATION_PENDING_TTL` | `true` / `86400` | |
| `BE_EMAIL_VERIFY_TTL` / `BE_EMAIL_VERIFY_PATH` | `86400` / `/auth/verify-email` | The link is `BE_PUBLIC_WEB_URL + path + ?token=` |
| `BE_WEB_LOGIN_PATH` | `/auth/login` | Used in emails |
| `BE_GOOGLE_AUTO_REGISTER` / `BE_GOOGLE_ALLOWED_DOMAINS` / `BE_GOOGLE_HTTP_TIMEOUT` | `false` / _(empty)_ / `10` | |

## Docker

`Dockerfile` builds a slim, non-root image (`python:3.12-slim`, uv, `libmagic1`) that serves on
**8020** and has a healthcheck on `/health/live`:

```bash
docker build -t app-backend apps/backend
docker run --rm -p 8020:8020 --env-file apps/backend/.env app-backend
```

For the full stack (Mongo + Redis + backend + nginx web on **:8080**), run `npm run docker:up` from the
repo root. See `docker-compose.yml` for the knobs.

## Health

- `GET /health/live` → 200 `{status: "ok"}` (process is up).
- `GET /health/ready` → 200 `{status: "ready", checks: {database, redis}}`, or 503
  `SERVICE_UNAVAILABLE` with the failing checks in `data`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `JWT_SECRET … Field required` or `must be at least 32 characters` at startup | Set `BE_JWT_SECRET` in `.env` (`npm run setup:backend` does this) |
| Login succeeds but the next call is 401 (browser) | Secure cookies over plain HTTP. Set `BE_COOKIE_SECURE=false` for HTTP dev or LAN, or use HTTPS. |
| `/health/ready` 503, `database: unavailable` with `BE_DB_PROVIDER=supabase` | Tables missing: apply `migrations/supabase/*.sql` |
| 429 on login during manual testing | `BE_RATE_LIMIT_AUTH` per IP per window; raise it in dev or wait |
| OTP / verification email never arrives in dev | `BE_EMAIL_BACKEND=auto` without SMTP prints emails to the backend log (`[email:console]`) |
| Upload returns 503 `CONFIGURATION_ERROR` | S3 is not configured (`BE_S3_BUCKET`, `BE_S3_ACCESS_KEY_ID`, `BE_S3_SECRET_ACCESS_KEY`), or libmagic is missing |
| Swagger through `http://localhost:3000/api/v1/apps/docs` cannot load `openapi.json` | Set `BE_ROOT_PATH=/api/v1/apps` (then direct `:8020/docs` breaks; this is the trade-off) |
| `Unknown router(s) in BE_ENABLED_ROUTERS` | Use exact names from `router/__init__.py` |
