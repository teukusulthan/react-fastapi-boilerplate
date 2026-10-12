# Backend Changelog

Tracks all backend changes across sprints — API routes added, DB migrations applied, services built, auth changes.

Append-only. Newest entries at the top. Updated whenever a backend task is created or completed.

---

<!-- ENTRY FORMAT:
### YYYY-MM-DD · [Sprint NN — slug](../sprint/active/NN-slug/sprint.md) · Task: [task title](../sprint/.../backend/NN-task.md) · STATUS

**Event:** Task created | Task completed | Files modified
**Files:** `path/to/route.py`, `path/to/migration.sql`
> One-line summary of what changed or was delivered.
-->

### 2026-10-12 · Boilerplate refactor (no sprint) · Task: backend foundation, auth and modules rewrite · ✅ Done

**Event:** Files modified
**Files:** `apps/backend/**` (new `core/`, `db/`, `migrations/supabase/`, `scripts/`, `templates/email/`, `tests/`; rewritten `api.py`, `dto/`, `service/`, `router/`, `util/`; removed `auth/`, `config/`, `models/`, `exceptions/`, `middleware/`)
> The backend was rebuilt on a layered foundation (router → service → repository). It supports MongoDB **or** Supabase Postgres (`BE_DB_PROVIDER`) and local **or** Supabase JWT auth (`BE_AUTH_PROVIDER`). It adds enforced RBAC, global error handling, one response envelope, rate limiting, health probes, a seed script, and about 340 tests (about 440 with Postgres).

**BREAKING CHANGES**
- **Envelope:**
  - Success is `{metaData: {status, responseCode, message, executionTime, requestId, pagination}, data}`.
  - Errors use the same top-level shape with `metaData.errorCode` and `data` (details), and no
    `detail` wrapper. Error codes: `BAD_REQUEST`, `AUTHENTICATION_ERROR`, `ACCOUNT_NOT_VERIFIED`,
    `PERMISSION_ERROR`, `RESOURCE_NOT_FOUND`, `METHOD_NOT_ALLOWED`, `CONFLICT`, `PAYLOAD_TOO_LARGE`,
    `UNSUPPORTED_MEDIA_TYPE`, `VALIDATION_ERROR`, `RATE_LIMITED`, `INTERNAL_ERROR`,
    `CONFIGURATION_ERROR`, `SERVICE_UNAVAILABLE`.
  - 422 returns `data: [{field, message}]`. 500s never include exception text.
  - The `copyright` and `execution_time` fields are gone, and every response has an `X-Request-ID`
    header.
- **Status codes:** `/add` and `/auth/register` return 201. Duplicates return 409, unknown ids 404,
  RBAC denials 403, and validation errors 422 (previously most failures were 400).
- **Pagination:** `{page, size, totalElements, totalPages}`. `size` is capped by `BE_MAX_PAGE_SIZE`
  (100), and `size=0` is rejected.
- **List queries:** `filters`, `search`, `searchBy` and `orderBy` accept only whitelisted fields
  (`db/schema.py`); anything else returns 422. Search is literal (no regex). Filter values must be
  scalars or lists.
- **Auth endpoints:**
  - `POST /auth/login` takes `{identifier, password}`. With 2FA enabled it returns
    `{twoFactorRequired: true, sessionToken, method}`, and tokens come only after `POST /auth/2fa/verify`.
  - `/auth/logout` is now `POST` (was `DELETE`), and `/auth/refresh` is now `POST` (was `GET`).
  - **Removed:** `GET /auth/validate` (use `GET /auth/me`), `POST /auth/verification` (use
    `/auth/register/verify`), `POST /auth/forgot-password/change` (use `/auth/forgot-password/reset`),
    `POST /auth/2fa/generate` (use `/auth/2fa/setup` + `/auth/2fa/enable`), `GET /auth/verify-email`
    (use `POST /auth/verify-email {token}`), `GET /auth/google`, `/auth/google/token_exchange` and
    `/auth/google/register` (use `POST /auth/google/callback`).
  - **New:** `/auth/register/resend`, `/auth/2fa/{setup,enable,disable}`, `/auth/change-password`,
    `/auth/verify-email/request`.
  - In `BE_AUTH_PROVIDER=supabase` mode, only `/auth/me` and `/auth/logout` are mounted.
- **Cookies / JWT:**
  - The cookies `token` and `refresh_token` are httpOnly, `SameSite=lax`, and `Secure` per
    `BE_COOKIE_SECURE` (default `true`).
  - JWTs use the standard claims `sub`, `exp`, `iat`, `jti`, `type` (`access`/`refresh`, always
    checked), `iss` (`BE_JWT_ISSUER`) and `sid`, replacing the custom `expire` and `user_id`. Old tokens
    are invalid.
  - Refresh tokens are single-use, and reuse revokes the session. Logout revokes both tokens.
  - The `JWT_ACTIVE` global switch and the hardcoded bypass token are gone.
- **Users and RBAC:**
  - User admin endpoints, including `check-*` and `reset-password`, are now **admin-only**.
  - Permission, group and role writes are admin-only.
  - `PUT /user/update` and `/user/settings/update-profile` reject unknown or privileged fields (422).
  - `POST /user/reset-password` takes `{id, newPassword}`.
  - `GET /user/{username}` was removed (use `GET /user/get-by-username?username=`).
  - The `check-*` endpoints return `{field, exists, available}`.
  - `PUT /permission/update-partial` takes `{id, addPrivileges, removePrivileges}`.
- **Uploads:**
  - Uploads require a signed-in user; `createdBy` comes from the token, and users only see their own
    files.
  - The MIME type is sniffed from content, so HTML, SVG and octet-stream are rejected by default (415).
    Oversized files get 413.
- **Removed:** `GET /monitoring/threadpool`.
- **Data:**
  - IDs are app-generated UUID v4 strings (previously md5/content-derived). Storage field names are
    snake_case in both providers (the API stays camelCase). Timestamps are timezone-aware UTC.
  - Unique indexes and constraints are enforced (409 on duplicates). The legacy `v_*` Mongo views are
    no longer used.
  - Existing Mongo data from the old schema needs a migration.
- **Settings (all `BE_*`; see `apps/backend/.env.example`):**
  - `MONGO_COLLECTION_*` → `BE_TABLE_{USERS,PERMISSIONS,GROUPS,ROLES,UPLOADS}`.
  - `JWT_ALGORITH` → `BE_JWT_ALGORITHM`.
  - `JWT_EXPIRED` → `BE_JWT_ACCESS_TTL`, and `JWT_REFRESH` → `BE_JWT_REFRESH_TTL`.
  - `ACCOUNT_FAIL_LIMIT` / `ACCOUNT_LOCK_TIME` → `BE_ACCOUNT_LOCK_MAX_ATTEMPTS` / `BE_ACCOUNT_LOCK_SECONDS`.
  - `RATE_LIMIT` → `BE_RATE_LIMIT_GLOBAL` (+ `BE_RATE_LIMIT_AUTH`).
  - `SMTP_EMAIL` / `SMTP_SENDER` / `SMTP_USE_TLS` / `SMTP_TYPE` → `BE_SMTP_USERNAME`, `BE_SMTP_FROM_EMAIL`,
    `BE_SMTP_FROM_NAME`, `BE_SMTP_STARTTLS`, `BE_SMTP_SSL` (+ `BE_EMAIL_BACKEND`).
  - `S3FS_*` → `BE_S3_*`.
  - `KAFKA_SERVER` → `BE_KAFKA_BOOTSTRAP_SERVERS`.
  - `MAX_THREADS_WORKERS` → `BE_THREADPOOL_SIZE`.
  - `ENABLED_ROUTERS` now takes exact names only; `ACTIVE_ROUTERS` and the `--routers` CLI were removed.
  - **Removed:** `JWT_ACTIVE`, `BASE_RESPONSE_CASE`, `COPYRIGHT`, `PROOFY_*`, `ENC_SECRET_PERMISSION`,
    `EXCLUDE_UPLOAD_EXTENSIONS`, `KAFKA_MAX_REQUEST`, `MONGO_COLLECTION_CONNECTION`.
  - **New:** `BE_DB_PROVIDER`, `BE_AUTH_PROVIDER`, `BE_SUPABASE_*`, `BE_INTERNAL_TOKEN`, `BE_COOKIE_*`,
    `BE_CORS_ORIGINS`, `BE_DATA_ENCRYPTION_KEY`, `BE_BOOTSTRAP_ADMIN_*`, `BE_ROOT_PATH`, and others.
  - `BE_JWT_SECRET` must be at least 32 characters.
  - `BE_ENC_SECRET` is now a base64 32-byte key (AES-256-GCM instead of AES-ECB).
- **Run:**
  - `python api.py` reads host, port, workers and reload from settings (no argv parsing);
    `uvicorn api:app` also works.
  - The entry point is `api.py`. The old docs referred to a `main.py`, which does not exist.
  - Dependencies are in `requirements.txt` + `requirements-dev.txt`; config is in `pyproject.toml`.
