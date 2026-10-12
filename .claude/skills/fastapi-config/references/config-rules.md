# Settings reference (`apps/backend/core/config.py`)

Companion to [../SKILL.md](../SKILL.md). Env names are `BE_<FIELD>`; the authoritative, commented list is
`apps/backend/.env.example`. Dependencies/venv rules live in the `fastapi-dependency-constraints` and
`fastapi-virtual-environment` skills.

| Group | Fields (defaults) |
|---|---|
| App | `APP_NAME` (App), `APP_VERSION`, `ENVIRONMENT` (development\|test\|staging\|production), `HOST` (0.0.0.0), `PORT` (8020), `WORKERS` (1), `RELOAD` (false), `ROOT_PATH` (""), `DOCS_ENABLED` (true), `THREADPOOL_SIZE` (40), `ENABLED_ROUTERS` ([] = all), `PUBLIC_WEB_URL` (http://localhost:3000) |
| Logging | `LOG_LEVEL` (INFO), `LOG_JSON` (false), `ACCESS_LOG` (true) |
| Database | `DB_PROVIDER` (mongo\|supabase), `MONGO_URI`, `MONGO_DB` (app), `MONGO_TIMEOUT_MS`, `SUPABASE_URL`, `SUPABASE_DB_URL`, `SUPABASE_DB_SCHEMA` (public), `SUPABASE_DB_POOL_MIN/MAX`, `SUPABASE_DB_TIMEOUT`, `TABLE_USERS/PERMISSIONS/GROUPS/ROLES/UPLOADS` |
| Redis | `REDIS_URL` (wins), `REDIS_HOST/PORT/PASSWORD/DB/SSL`, `REDIS_KEY_PREFIX` (app) |
| Auth | `AUTH_PROVIDER`, `JWT_*`, `COOKIE_*`, `INTERNAL_TOKEN`, `SUPERUSER_ALIASES`, `DEFAULT_PERMISSION_ALIAS`, `PASSWORD_MIN_LENGTH`, `ACCOUNT_LOCK_*`, `OTP_*`, `TWO_FACTOR_SESSION_TTL`, `TOTP_ISSUER`, `GOOGLE_*`, `SUPABASE_JWT_SECRET/JWKS_URL/JWT_AUDIENCE/JWT_ISSUER`, `BOOTSTRAP_ADMIN_*` |
| HTTP | `CORS_ORIGINS` (http://localhost:3000; no `*`), `TRUST_PROXY_HEADERS` (false), `PROXY_TRUSTED_HOPS` (1) |
| Rate limit | `RATE_LIMIT_ENABLED`, `RATE_LIMIT_GLOBAL` (0 = off), `RATE_LIMIT_WINDOW`, `RATE_LIMIT_AUTH`, `RATE_LIMIT_AUTH_WINDOW`, `MAX_PAGE_SIZE` (100) |
| Encryption | `DATA_ENCRYPTION_KEY` (Fernet), `ENC_ACTIVE` (false), `ENC_SECRET` (base64 32 bytes) |
| Upload | `UPLOAD_MAX_SIZE_MB` (25), `UPLOAD_ALLOWED_TYPES`, `UPLOAD_IMAGE_MAX_DIMENSION`, `UPLOAD_KEY_PREFIX` |
| S3 | `S3_ENDPOINT_URL`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET`, `S3_FORCE_PATH_STYLE`, `S3_PRESIGN_TTL` |
| Kafka | `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_CLIENT_ID`, `KAFKA_TOPIC_FILE_EXTRACTION` |
| SMTP / email | `SMTP_*`, `EMAIL_BACKEND` (auto\|smtp\|console\|disabled), `EMAIL_TEMPLATES_DIR` |
| Auth flows | `REGISTRATION_ENABLED`, `REGISTRATION_PENDING_TTL`, `EMAIL_VERIFY_TTL`, `EMAIL_VERIFY_PATH` (/auth/verify-email), `WEB_LOGIN_PATH` (/auth/login), `GOOGLE_AUTO_REGISTER`, `GOOGLE_ALLOWED_DOMAINS`, `GOOGLE_HTTP_TIMEOUT` |

Helper properties: `is_production`, `redis_url`, `google_configured`, `smtp_configured`, `s3_configured`,
`kafka_configured`, `internal_token_configured`, `upload_max_bytes`, `totp_issuer`, `smtp_from_name`,
`table_name(setting_key)`.

## Startup validation (fails fast with a readable message)

- `JWT_SECRET` ≥ 32 chars; `INTERNAL_TOKEN` ≥ 32 chars when set.
- `ENC_ACTIVE` requires a valid `ENC_SECRET`; `DATA_ENCRYPTION_KEY` must be a valid Fernet key.
- `DB_PROVIDER=supabase` requires `SUPABASE_DB_URL`; `AUTH_PROVIDER=supabase` requires JWKS URL or JWT secret.
- `COOKIE_SAMESITE=none` requires `COOKIE_SECURE=true`; `EMAIL_BACKEND=smtp` requires SMTP host + from.
- Production: no placeholder JWT secret, `COOKIE_SECURE=true`, `RELOAD=false`, `EMAIL_BACKEND` ≠ console.

## Running behind the reverse proxy

The web dev server / nginx proxies `/api/v1/apps/*` → backend with the prefix stripped. Behind nginx set
`BE_TRUST_PROXY_HEADERS=true` (+ `BE_PROXY_TRUSTED_HOPS`) so rate limits see the real client IP
(`docker-compose.yml` already does). `BE_ROOT_PATH=/api/v1/apps` only if Swagger must work through the proxy.

## Forbidden patterns

| Forbidden | Instead |
|---|---|
| `os.getenv("MONGO_URI")` | `settings.MONGO_URI.get_secret_value()` |
| Settings singleton built at import | `get_settings()` / `SettingsDep` |
| CLI flags to select routers | `BE_ENABLED_ROUTERS` |
| Required setting for an optional integration | `None` default + `*_configured` + `ConfigurationError` |
| `BaseHTTPMiddleware` reading `request.body()` | pure ASGI middleware |
