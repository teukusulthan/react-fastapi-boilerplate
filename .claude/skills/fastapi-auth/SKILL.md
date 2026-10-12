---
name: auth
description: "Backend (apps/backend) authentication & authorization: BE_AUTH_PROVIDER=local (own HS256 JWT access/refresh with type/jti/sid claims, httpOnly token/refresh_token cookies, single-use refresh rotation, TokenStore revocation in Redis, single-session, lockout, OTP/2FA, register/forgot-password flows) or supabase (verify Supabase JWTs via JWKS/HS256, auto-provision users); X-Internal-Token system calls; RBAC deps CurrentUser, require_auth, require_admin, require_privilege, require_internal_token (core/deps.py). Use for login/registration/token work, protecting routes, roles/privileges, or ownership scoping."
---

# auth — Authentication & authorization

## Use this skill when

- Protecting an endpoint, adding a privilege check, or scoping data to the caller
- Changing login, refresh, logout, 2FA, registration, password or Google sign-in flows
- Switching between local auth and Supabase auth, or calling the API service-to-service

## Key files

| File | Contents |
|---|---|
| `apps/backend/core/deps.py` | `CurrentUser`, `get_current_user(_optional)`, `require_auth`, `require_admin`, `require_privilege`, `require_internal_token`, `require_user_or_internal`, aliases `PrincipalDep` `CurrentUserDep` `AdminUserDep` `InternalDep` `UserOrInternalDep` `OptionalUserDep`, `provision_supabase_user` |
| `apps/backend/core/security.py` | `hash_password`, `verify_password`, `validate_password_policy`, `create_token`, `issue_token_pair`, `decode_token`, `TokenStore`, `rotate_refresh_token`, `set_auth_cookies`, `clear_auth_cookies`, `verify_internal_token`, `generate_otp`/`hash_otp`/`verify_otp`, `encrypt_secret`, `SupabaseTokenVerifier` |
| `apps/backend/router/auth.py` | `router` (always), `local_router` (local provider), `google_router` (local + Google configured) |
| `apps/backend/service/auth/` | `tokens.py` (`SessionService`), `login.py` (`LoginService`, lockout), `two_factor.py`, `otp.py`, `registration.py`, `password.py`, `google.py`, `deps.py` (`LoginServiceDep` …) |
| `apps/backend/dto/auth.py` | request DTOs, `LoginResponse`, `TwoFactorChallengeResponse`, `LoginOutcome` |
| `apps/backend/dto/user_profile.py` + `service/user_profile.py` | `UserProfile` returned by `/auth/me` and login |
| `apps/backend/core/rate_limit.py` | `rate_limit(name, limit=, window=)` dependency |

## Principal resolution (`get_current_user_optional`)

1. `X-Internal-Token` header present → must equal `BE_INTERNAL_TOKEN` (constant-time) → `CurrentUser.internal()`
   (`is_internal=True`). An invalid header is a 401, never a fallback.
2. Else `Authorization: Bearer <token>`, else the `token` cookie.
3. **local**: `decode_token(token, settings, ACCESS)` (signature, issuer, expiry, **type**) → not revoked
   (`TokenStore.is_revoked`) → user `status == "active"` and not past `expired_at` → if `multi_login` is false
   the token's `sid` must be the active session → permission loaded → `CurrentUser`.
4. **supabase**: `SupabaseTokenVerifier.verify` (JWKS from `BE_SUPABASE_JWKS_URL`, else HS256 with
   `BE_SUPABASE_JWT_SECRET`; audience `BE_SUPABASE_JWT_AUDIENCE`) → find user by id / `external_id`, link a
   pre-created `auth_provider="supabase"` row by email, or auto-provision (default permission alias) → same active checks.

`CurrentUser` fields: `id, username, email, role` (permission alias), `privileges` (frozenset),
`permission_id, group_id, is_superuser` (alias ∈ `BE_SUPERUSER_ALIASES`, default `admin,owner`),
`is_internal, multi_login, auth_provider, session_id, token_jti, token_expires_at, record` (full row,
excluded from dumps) and `has_privilege(p)`.

## RBAC dependencies

| Dependency / alias | Allows |
|---|---|
| `get_current_user_optional` / `OptionalUserDep` | anyone (`None` without credentials; bad credentials still 401) |
| `get_current_user` / `PrincipalDep` | any authenticated principal (user **or** internal) |
| `require_auth` / `CurrentUserDep` | authenticated **user** (internal → 403) |
| `require_admin` / `AdminUserDep` | user with a superuser alias |
| `require_privilege("user:write", ..., any_of=False, allow_internal=False)` | superuser OR holds the privilege(s) |
| `require_internal_token` / `InternalDep` | only a valid `X-Internal-Token` |
| `require_user_or_internal` / `UserOrInternalDep` | user or internal |

```python
# router-wide: every route needs a signed-in user; admins for writes (router/group.py style)
router = APIRouter(prefix="/note", tags=["note"], dependencies=[Depends(require_auth)])

@router.post("/add", status_code=201, response_model=ApiResponse[NoteResponse])
def add(dto: NoteDTO, service: NoteServiceDep, user: CurrentUserDep): ...

@router.delete("/delete", response_model=ApiResponse[MessageData],
               dependencies=[Depends(require_privilege("note:delete"))])
def delete(id: IdParam, service: NoteServiceDep): ...
```

Privileges are strings stored on the permission (`permissions.privileges`, e.g. `["profile:read","upload:write"]`;
the seeded `admin` permission has `["*"]` and is a superuser by alias). Ownership: compare
`record["created_by"] == user.id` unless `user.is_superuser`, and answer **404** for other users' records
(`service/upload.py::_owned`).

## Local provider (`BE_AUTH_PROVIDER=local`, default)

- JWT HS256 with `BE_JWT_SECRET` (≥ 32 chars, placeholder rejected in production), claims `sub, exp, iat, jti,
  type (access|refresh), iss (BE_JWT_ISSUER), sid`. TTLs `BE_JWT_ACCESS_TTL` (900 s) / `BE_JWT_REFRESH_TTL` (7 d).
- Cookies (`set_auth_cookies`): `token` + `refresh_token`, httpOnly, `SameSite=BE_COOKIE_SAMESITE` (lax),
  `Secure=BE_COOKIE_SECURE` (must be true in production; false for plain-HTTP dev), refresh path
  `BE_COOKIE_REFRESH_PATH`. Tokens are **also** returned in the body (`auth.accessToken/refreshToken/expiresAt`)
  for bearer clients; the web app uses cookies only.
- Refresh (`POST /auth/refresh`, cookie or `Authorization: Bearer <refresh>`): `rotate_refresh_token` consumes the
  refresh jti once (`TokenStore.consume_refresh`); **reuse revokes the whole session family** (`sid`).
- Logout revokes access + refresh jti and the session; always 200. Password change/reset, admin block/expire/
  delete/reset-password call `TokenStore.revoke_all_for_user` (every token issued before now).
- Single session: users with `multi_login=false` keep one active `sid` (`set_active_session`/`is_session_current`).
- Login: generic `AuthenticationError("Invalid credentials")` for unknown user, wrong password and lockout
  (`ACCOUNT_LOCK_MAX_ATTEMPTS` per identifier+IP, `ACCOUNT_LOCK_SECONDS`); a pending account with the correct
  password gets 401 `errorCode=ACCOUNT_NOT_VERIFIED`. 2FA enabled → `{twoFactorRequired: true, sessionToken, method}` and no cookies.
- Passwords: bcrypt (`hash_password`; >72 bytes rejected, never truncated), policy `BE_PASSWORD_MIN_LENGTH`.
- OTPs: `secrets`-generated, stored hashed per (purpose, email) with TTL, attempt limit and resend cooldown
  (`service/auth/otp.py`). TOTP secrets encrypted at rest with `BE_DATA_ENCRYPTION_KEY`.
- Wrong *current* password on `/auth/change-password` and `/auth/2fa/disable` → **400** (so the web client does not try a refresh).

### Endpoints (`router/auth.py`)

| Mounted | Route | Body → result |
|---|---|---|
| always | `GET /auth/me` | `UserProfile` (local or Supabase JWT) |
| always | `POST /auth/logout` | `{message}`, clears cookies |
| local | `POST /auth/login` | `{identifier, password}` → `LoginResponse` + cookies, or 2FA challenge |
| local | `POST /auth/refresh` | → `LoginResponse` + rotated cookies |
| local | `POST /auth/2fa/verify` / `/2fa/resend` | `{sessionToken, otp}` / `{sessionToken}` |
| local (auth) | `POST /auth/2fa/setup` / `/2fa/enable` / `/2fa/disable` | `{method}` / `{otp}` / `{password}` |
| local | `POST /auth/register` (201) / `/register/verify` / `/register/resend` | `{username, fullname, email, phone?, password}` / `{email, otp}` / `{email}` |
| local | `POST /auth/forgot-password/request` / `/verify` / `/reset` | generic 200 / `{valid}` / `{email, otp, newPassword}` |
| local (auth) | `POST /auth/change-password` | `{currentPassword, newPassword}` → fresh `LoginResponse` |
| local | `POST /auth/verify-email/request` (auth) / `POST /auth/verify-email` | — / `{token}` |
| local + Google | `POST /auth/google/callback` | `{code, redirectUri, codeVerifier?}` → like login |

Public auth endpoints carry `rate_limit("auth:<name>")` (`BE_RATE_LIMIT_AUTH` per `BE_RATE_LIMIT_AUTH_WINDOW` per IP).

## Supabase provider (`BE_AUTH_PROVIDER=supabase`)

- Requires `BE_SUPABASE_JWKS_URL` or `BE_SUPABASE_JWT_SECRET` (validated at startup).
- Only `router` is mounted: `/auth/me`, `/auth/logout`. Login/refresh/register/2FA are **not mounted** (404) —
  the client signs in with Supabase and sends the Supabase access token as `Authorization: Bearer`.
- Admins may pre-create users without a password (`/user/add`); the first Supabase sign-in with that email links
  the row. A local-password row with the same email is never taken over (409).
- `python -m scripts.seed` promotes `BE_BOOTSTRAP_ADMIN_EMAIL` to admin when that user exists.

## Rules

### MUST
- Protect every non-public router with a dependency from `core/deps.py`; take `created_by`/owner from `CurrentUser`.
- Use `require_admin`/`require_privilege` for writes; reject internal principals where a human is required (`require_auth`).
- Hide existence of others' resources with 404; use generic messages for credential failures.
- Revoke tokens (`TokenStore.revoke_all_for_user`) whenever credentials or account status change.
- Keep secrets in settings (`SecretStr`), never in code or logs.

### MUST NOT
- Never decode JWTs yourself with `jwt.decode` in routes — use `decode_token` / the deps.
- Never trust role/permission/status/`created_by` from request bodies.
- Never log tokens, passwords, OTPs or full emails (use `censor_email`).
- Never return `password_hash`, `two_factor_secret` or OTP data (response models exclude them).
- Do not add a global "auth off" switch; public routes simply have no auth dependency.

## Checklist — protected endpoint

- [ ] Router-wide `dependencies=[Depends(require_auth)]` (or `get_current_user` if internal callers allowed)
- [ ] Per-route `AdminUserDep` / `require_privilege(...)` for privileged actions
- [ ] Ownership scoping (`extra_where=` / `_owned` → 404)
- [ ] RBAC test: anonymous 401, wrong role 403, internal token behaviour (see `tests/modules/test_rbac.py`)

## Common mistakes

| Mistake | Fix |
|---|---|
| Using `get_current_user` and assuming a human user | internal token passes it; use `require_auth` |
| Checking `user.role == "admin"` | `user.is_superuser` (honours `BE_SUPERUSER_ALIASES`) |
| Returning 401 for a wrong current password | 400 (`BadRequestError`) to avoid client refresh loops |
| Testing cookies over HTTP with `BE_COOKIE_SECURE=true` | browser drops them; set false for local HTTP only |
| Expecting `/auth/refresh` in supabase mode | not mounted; Supabase handles sessions |

Details: [references/auth-rules.md](references/auth-rules.md)
