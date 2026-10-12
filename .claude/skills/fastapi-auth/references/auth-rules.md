# Auth & Security Rules (detailed)

Companion to [../SKILL.md](../SKILL.md). Verified against `apps/backend/core/{deps,security,rate_limit}.py`,
`apps/backend/router/auth.py` and `apps/backend/service/auth/`.

## Settings that matter

| Setting (`BE_*`) | Default | Notes |
|---|---|---|
| `AUTH_PROVIDER` | `local` | `local` \| `supabase` |
| `JWT_SECRET` | — (required) | ≥ 32 chars; `change-me…` placeholder refused in production |
| `JWT_ALGORITHM` / `JWT_ISSUER` / `JWT_LEEWAY` | `HS256` / `app` / `10` | |
| `JWT_ACCESS_TTL` / `JWT_REFRESH_TTL` | `900` / `604800` | seconds |
| `COOKIE_SECURE` / `COOKIE_SAMESITE` / `COOKIE_DOMAIN` / `COOKIE_REFRESH_PATH` | `true` / `lax` / — / `/` | `none` requires secure |
| `INTERNAL_TOKEN` | empty (disabled) | ≥ 32 chars when set; header `X-Internal-Token` |
| `SUPERUSER_ALIASES` / `DEFAULT_PERMISSION_ALIAS` | `admin,owner` / `user` | |
| `PASSWORD_MIN_LENGTH`, `ACCOUNT_LOCK_MAX_ATTEMPTS`, `ACCOUNT_LOCK_SECONDS` | `8`, `5`, `900` | |
| `OTP_LENGTH`, `OTP_TTL`, `OTP_MAX_ATTEMPTS`, `OTP_RESEND_COOLDOWN`, `TWO_FACTOR_SESSION_TTL` | `6`, `600`, `5`, `60`, `300` | |
| `DATA_ENCRYPTION_KEY` | empty | Fernet key; encrypts TOTP secrets at rest |
| `SUPABASE_JWKS_URL` / `SUPABASE_JWT_SECRET` / `SUPABASE_JWT_AUDIENCE` / `SUPABASE_JWT_ISSUER` | — / — / `authenticated` / — | one of the first two required in supabase mode |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | empty | both set → `google_router` mounted (local mode) |
| `RATE_LIMIT_AUTH` / `RATE_LIMIT_AUTH_WINDOW` | `10` / `60` | per client IP; `TRUST_PROXY_HEADERS` for X-Forwarded-For |
| `EMAIL_BACKEND` | `auto` | `auto`/`smtp`/`console`/`disabled`; email flows → 503 `CONFIGURATION_ERROR` when disabled |

## Token mechanics (`core/security.py`)

```python
pair = issue_token_pair(user_id, settings)            # TokenPair(.access, .refresh, .session_id)
claims = decode_token(token, settings, ACCESS)       # 401 on bad sig/issuer/expiry/missing claim/WRONG TYPE
store = TokenStore(redis, settings)
store.revoke(claims); store.revoke_session(sid); store.revoke_all_for_user(uid)
store.consume_refresh(claims)                        # one-time; False => reuse => family revoked
new_pair = rotate_refresh_token(claims, store, settings)
set_auth_cookies(response, pair, settings); clear_auth_cookies(response, settings)
```

In routes, get the store via `TokenStoreDep`; services in `service/auth/` receive it through constructors
(`service/auth/deps.py`). Session-level orchestration lives in `service/auth/tokens.py::SessionService`
(`start`, `refresh`, `logout`, `revoke_all`).

## Response shapes

- Success (login, 2FA verify, refresh, change-password, Google): `LoginResponse =
  {twoFactorRequired: false, user: UserProfile, auth: {accessToken, refreshToken, expiresAt}}` + cookies.
- 2FA gate: `TwoFactorChallengeResponse = {twoFactorRequired: true, sessionToken, method: "email"|"totp"}`.
- `UserProfile` (`dto/user_profile.py`): `id, username, fullname, email, phone, status, emailVerified,
  twoFactorEnabled, role, permissionId, permission{id,name,alias,privileges}|null, groupId, group{id,name}|null,
  lastLoginAt, createdAt, updatedAt`.

## Rate limiting

```python
from core.rate_limit import rate_limit
@local_router.post("/login", dependencies=[Depends(rate_limit("auth:login"))])
rate_limit("auth:otp", limit=lambda s: 5, window=lambda s: 300)
```
Fixed window in Redis, fails open on Redis errors (logged), disabled by `BE_RATE_LIMIT_ENABLED=false`.
Exceeding → 429 `RATE_LIMITED` with `Retry-After`.

## Testing auth

Fixtures in `apps/backend/tests/conftest.py`: `admin_user`, `regular_user`, `login(user)`, `auth_headers(user)`,
`admin_headers`, `user_headers`, `internal_headers`. Auth-flow tests mount the auth routers and capture emails
with `MemoryEmailSender` (`apps/backend/tests/auth/conftest.py`, fixture `outbox`). Supabase mode:
`apps/backend/tests/auth/test_supabase_mode.py`. RBAC matrix: `apps/backend/tests/modules/test_rbac.py`.

## Forbidden patterns

| Forbidden | Instead |
|---|---|
| Hard-coded bypass tokens / "debug" auth switches | none — public routes just omit the dependency |
| `jwt.decode(..., options={"verify_signature": False})` | `decode_token` |
| Accepting an access token at `/auth/refresh` (or vice versa) | `decode_token(..., expected_type)` always checks `type` |
| Plain-text passwords/OTPs in DB or Redis | `hash_password`, `hash_otp` |
| Different error messages for "no such user" vs "wrong password" | one generic `Invalid credentials` |
| `==` comparison of secrets | `verify_internal_token` (constant-time) |
| `async def` route doing bcrypt/Redis/DB | sync `def` route |
