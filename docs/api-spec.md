# API Specification

The contract between `apps/backend` (FastAPI) and its clients (`apps/web`, mobile, other services).
This file is the **endpoint registry**. Per-module request and response details are in
[`docs/api/`](api/). The live OpenAPI schema is at `/docs` (Swagger) and `/openapi.json` when
`BE_DOCS_ENABLED=true`.

> Keep this file in sync with the code. When you add, remove or change an endpoint, update this
> registry, the module file in `docs/api/`, and `changelog/backend.md` in the same change. To list the
> mounted routes, see "Checking this registry" at the end.

## Base URL

| Context | Base URL |
|---|---|
| Backend directly (dev) | `http://localhost:8020` |
| Through the web dev server or Docker nginx (what the web app uses) | `http://localhost:3000/api/v1/apps` (dev) · `http://localhost:8080/api/v1/apps` (Docker) |

The proxy strips `/api/v1/apps`, so `/api/v1/apps/auth/me` reaches the backend as `/auth/me`. Paths
below are backend paths.

## Conventions

- **Style:** RPC-ish CRUD per module:
  - `POST /x/add` → 201
  - `PUT /x/update` (body has `id`; PATCH semantics: only the fields you send change, and an explicit
    `null` clears a nullable field)
  - `DELETE /x/delete?id=`
  - `GET /x/get-one?id=`
  - `POST /x/get-all` (body: `FindDTO`)
- **JSON is camelCase.** Storage is snake_case. Unknown request fields return **422** (mass assignment
  is blocked).
- **IDs** are UUID v4 strings. **Timestamps** are ISO-8601 UTC (`2026-10-12T05:24:08.947000Z`).
- Every response carries an `X-Request-ID` header (echoed in `metaData.requestId`). Send your own
  `X-Request-ID` to correlate logs.

## Envelope

Success:

```json
{
  "metaData": { "status": true, "responseCode": 200, "message": "Success", "executionTime": 5,
                "requestId": "d50aa49f196e42eeb52f3c31b9af6664", "pagination": null },
  "data": { }
}
```

List (`POST /x/get-all`): `data` is an array, and `pagination` is
`{"page": 1, "size": 10, "totalElements": 42, "totalPages": 5}`.

Error (every error: 4xx, 5xx, validation, 404 for unknown routes, 405). It sits at the top level, with
no `detail` wrapper:

```json
{
  "metaData": { "status": false, "responseCode": 404, "message": "User not found",
                "errorCode": "RESOURCE_NOT_FOUND", "executionTime": 3, "requestId": "…" },
  "data": null
}
```

- **422** puts field errors in `data`: `[{"field": "email", "message": "value is not a valid email address"}]`.
  Field names are camelCase and nested ones are dotted or indexed (`filters[0].field`).
- **409** usually names the field: `data: [{"field": "alias", "message": "already exists"}]`.
- **500** always says `"Internal server error"`. Details go only to the server log, under the
  `requestId`.
- **401** includes `WWW-Authenticate: Bearer`. **429** includes `Retry-After` (seconds).

### Error codes (`metaData.errorCode`)

| errorCode | HTTP | When |
|---|---|---|
| `BAD_REQUEST` | 400 | Invalid operation: wrong OTP or reset code, wrong current password on change-password or 2FA disable, password reset in Supabase mode |
| `AUTHENTICATION_ERROR` | 401 | Missing, invalid, expired or revoked credentials; generic "Invalid credentials" on login |
| `ACCOUNT_NOT_VERIFIED` | 401 | Login only: correct password, but the account is still `pending` |
| `PERMISSION_ERROR` | 403 | Authenticated but not allowed (role or privilege, internal token on a user-only route, registration disabled) |
| `RESOURCE_NOT_FOUND` | 404 | Unknown id or route, or another user's upload |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP method |
| `CONFLICT` | 409 | Unique value taken, record still referenced, or self-lockout / last-admin guard |
| `PAYLOAD_TOO_LARGE` | 413 | Upload exceeds `BE_UPLOAD_MAX_SIZE_MB` |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Upload type not in `BE_UPLOAD_ALLOWED_TYPES` (detected from content) |
| `VALIDATION_ERROR` | 422 | Body, query or filter validation, password policy, or missing references |
| `RATE_LIMITED` | 429 | Too many requests (auth endpoints: `BE_RATE_LIMIT_AUTH` per IP per window) |
| `INTERNAL_ERROR` | 500 | Unhandled error |
| `CONFIGURATION_ERROR` | 503 | Feature not configured (SMTP or email disabled, S3, Kafka) |
| `SERVICE_UNAVAILABLE` | 503 | Database or Redis unreachable; `/health/ready` not ready |

## List query — `FindDTO` (body of every `get-all`)

```json
{
  "page": 1,
  "size": 10,
  "search": "jane",
  "searchBy": ["username", "email"],
  "orderBy": "createdAt",
  "order": "desc",
  "filters": [
    { "field": "status", "operator": "is", "value": { "is": "active" } },
    { "field": "createdAt", "operator": "is between", "value": { "gte": "2026-01-01T00:00:00Z", "lte": "2026-12-31T23:59:59Z" } },
    { "field": "permissionId", "operator": "is one of", "value": { "isOneOf": ["<uuid>", "<uuid>"] }, "operatorType": "or" }
  ]
}
```

| Key | Rules |
|---|---|
| `page` | ≥ 1, default 1 |
| `size` | 1…`BE_MAX_PAGE_SIZE` (default 100), default 10 |
| `search` | ≤ 200 chars; literal, case-insensitive "contains" (regex characters are escaped) |
| `searchBy` (or `search_by`) | Searchable fields; empty = every searchable field of the resource |
| `orderBy` / `order` | A sortable field (default `createdAt`); `asc` or `desc` (default `desc`) |
| `filters[]` | ≤ 50. `field` must be filterable. `operator` is one of `is`, `is not`, `is one of`, `is not one of`, `greater than equals`, `less than equals`, `is between`, `is not between`, `is exist`, `is not exist`, `is contains`, `is not contains`, `all`. `value` = `{is?, isOneOf?, gte?, lte?}` with scalars or lists of scalars only (objects → 422). `operatorType: "or"` groups the flagged filters with OR (default `and`). |

Any field outside the resource whitelist, and any secret field (`passwordHash`, `twoFactorSecret`),
returns **422** with every bad field listed. The whitelists are in the module docs and in
`apps/backend/db/schema.py`.

## Authentication

| Mechanism | How | Used by |
|---|---|---|
| Access cookie | httpOnly cookie `token` (path `/`), set by login, 2FA verify, refresh, change-password and Google | Web app (default) |
| Refresh cookie | httpOnly cookie `refresh_token` (path `BE_COOKIE_REFRESH_PATH`, default `/`) | Web app → `POST /auth/refresh` |
| Bearer | `Authorization: Bearer <accessToken>` (the tokens are also in the login response body) | Mobile, scripts, other services |
| Internal token | `X-Internal-Token: <BE_INTERNAL_TOKEN>` (≥ 32 chars; constant-time compare). If present, it must be valid; there is no fallback. | System-to-system calls |
| Supabase JWT | `Authorization: Bearer <supabase access token>` when `BE_AUTH_PROVIDER=supabase` | Apps using Supabase Auth |

Credentials are checked in this order: `X-Internal-Token` → Bearer → `token` cookie. Local JWTs are
HS256 (`BE_JWT_SECRET`) with the claims `sub` (user id), `exp`, `iat`, `jti`, `type` (`access` or
`refresh`, always checked), `iss` (`BE_JWT_ISSUER`) and `sid` (session id). Access TTL is
`BE_JWT_ACCESS_TTL` (900 s); refresh TTL is `BE_JWT_REFRESH_TTL` (7 days). Refresh tokens are single-use:
reusing one revokes the whole session. Logout revokes both tokens. Users with `multiLogin=false` keep
only their latest session.

### Authorization model

User → `permissionId` → permission `{name, alias, privileges[]}`. The user's `role` is the permission
**alias**. Aliases in `BE_SUPERUSER_ALIASES` (default `admin,owner`) are superusers. The seed creates
`admin` (`["*"]`) and `user` (`profile:read`, `profile:write`, `upload:read`, `upload:write`). The
`roles` resource is a plain catalogue and plays no part in authorization.

Values in the **Auth** column below:

| Value | Meaning |
|---|---|
| `public` | No credentials needed |
| `user` | Signed-in user; an internal token gets 403 |
| `principal` | Signed-in user **or** a valid `X-Internal-Token` |
| `admin` | Superuser |

## Endpoint registry

Status codes list the success code first, then the notable errors. Every endpoint can also return 422
(invalid input), 429 (where rate limited) and 500/503. Endpoints marked ⏱ are rate limited per IP
(`BE_RATE_LIMIT_AUTH` per `BE_RATE_LIMIT_AUTH_WINDOW`; refresh allows 6×).

### Health — [`api/health.md`](api/health.md)

| Method | Path | Auth | Request | Response `data` | Status |
|---|---|---|---|---|---|
| GET | `/health/live` | public | — | `{status: "ok"}` | 200 |
| GET | `/health/ready` | public | — | `{status: "ready", checks: {database, redis}}` | 200 · 503 (`data` = checks) |

### Auth — [`api/auth.md`](api/auth.md)

Mounted when `BE_AUTH_PROVIDER=local`, except `/auth/me` and `/auth/logout`, which are mounted in both
modes. `/auth/google/callback` is mounted only when Google is configured.

| Method | Path | Auth | Request | Response `data` | Status |
|---|---|---|---|---|---|
| GET | `/auth/me` | user | — | `UserProfile` | 200 · 401 |
| POST | `/auth/logout` | public | — (cookies or Bearer) | `{message}` + clears cookies | 200 (idempotent) |
| POST | `/auth/login` ⏱ | public | `{identifier, password}` | `LoginResponse` + cookies, **or** `{twoFactorRequired: true, sessionToken, method}` | 200 · 401 · 401 `ACCOUNT_NOT_VERIFIED` |
| POST | `/auth/refresh` ⏱ | refresh cookie or `Bearer <refresh>` | — | `LoginResponse` + new cookies | 200 · 401 |
| POST | `/auth/2fa/verify` ⏱ | public | `{sessionToken, otp}` | `LoginResponse` + cookies | 200 · 401 |
| POST | `/auth/2fa/resend` ⏱ | public | `{sessionToken}` | `{message}` | 200 · 400 (TOTP) · 401 · 429 · 503 |
| POST | `/auth/2fa/setup` ⏱ | user | `{method: "email" \| "totp"}` | `{method, message, otpauthUri?, qrImageBase64?, secret?}` | 200 · 409 · 503 |
| POST | `/auth/2fa/enable` ⏱ | user | `{otp}` | `UserProfile` | 200 · 400 · 409 |
| POST | `/auth/2fa/disable` ⏱ | user | `{password}` | `UserProfile` | 200 · 400 |
| POST | `/auth/register` ⏱ | public | `{username, fullname, email, phone?, password}` | `{message}` | 201 · 403 (disabled) · 409 · 422 · 503 |
| POST | `/auth/register/verify` ⏱ | public | `{email, otp}` | `{message}` | 200 · 400 |
| POST | `/auth/register/resend` ⏱ | public | `{email}` | `{message}` | 200 · 503 |
| POST | `/auth/forgot-password/request` ⏱ | public | `{email}` | `{message}` (always generic) | 200 · 503 |
| POST | `/auth/forgot-password/verify` ⏱ | public | `{email, otp}` | `{valid: true}` | 200 · 400 |
| POST | `/auth/forgot-password/reset` ⏱ | public | `{email, otp, newPassword}` | `{message}` | 200 · 400 · 422 |
| POST | `/auth/change-password` ⏱ | user | `{currentPassword, newPassword}` | `LoginResponse` + new cookies | 200 · 400 · 422 |
| POST | `/auth/verify-email/request` ⏱ | user | — | `{message}` | 200 · 429 · 503 |
| POST | `/auth/verify-email` ⏱ | public | `{token}` | `{message}` | 200 · 400 |
| POST | `/auth/google/callback` ⏱ | public | `{code, redirectUri, codeVerifier?}` | like `/auth/login` | 200 · 401 · 403 (domain) · 503 |

### User — [`api/user.md`](api/user.md)

| Method | Path | Auth | Request | Response `data` | Status |
|---|---|---|---|---|---|
| POST | `/user/add` | admin | `CreateUserDTO` | `UserResponse` | 201 · 409 · 422 |
| PUT | `/user/update` | admin | `UpdateUserDTO` (`id` + fields) | `UserResponse` | 200 · 404 · 409 · 422 |
| DELETE | `/user/delete?id=` | admin | — | `{message}` | 200 · 404 · 409 (self) |
| GET | `/user/get-one?id=` | admin | — | `UserResponse` | 200 · 404 |
| GET | `/user/get-by-username?username=` | admin | — | `UserResponse` | 200 · 404 |
| POST | `/user/get-all` | admin | `FindDTO` | `UserResponse[]` + pagination | 200 · 422 |
| POST | `/user/reset-password` | admin | `{id, newPassword}` | `{message}` | 200 · 400 (Supabase mode) · 404 · 422 |
| GET | `/user/check-email?email=` | admin | — | `{field, exists, available}` | 200 |
| GET | `/user/check-username?username=` | admin | — | `{field, exists, available}` | 200 |
| GET | `/user/check-phone?phone=` | admin | — | `{field, exists, available}` | 200 |
| PUT | `/user/settings/update-profile` | user | `{fullname?, phone?, about?, image?, settings?, personalization?}` | `UserResponse` | 200 · 409 · 422 |

### Group — [`api/group.md`](api/group.md)

| Method | Path | Auth | Request | Response `data` | Status |
|---|---|---|---|---|---|
| POST | `/group/add` | admin | `GroupDTO` | `GroupResponse` | 201 · 422 |
| PUT | `/group/update` | admin | `UpdateGroupDTO` | `GroupResponse` | 200 · 404 · 422 |
| DELETE | `/group/delete?id=` | admin | — | `{message}` | 200 · 404 · 409 (has members) |
| GET | `/group/get-one?id=` | principal | — | `GroupResponse` | 200 · 404 |
| POST | `/group/get-all` | principal | `FindDTO` | `GroupResponse[]` + pagination | 200 · 422 |

### Permission — [`api/permission.md`](api/permission.md)

| Method | Path | Auth | Request | Response `data` | Status |
|---|---|---|---|---|---|
| POST | `/permission/add` | admin | `PermissionDTO` | `PermissionResponse` | 201 · 409 · 422 |
| PUT | `/permission/update` | admin | `UpdatePermissionDTO` | `PermissionResponse` | 200 · 404 · 409 · 422 |
| PUT | `/permission/update-partial` | admin | `{id, addPrivileges?, removePrivileges?}` | `PermissionResponse` | 200 · 404 · 422 |
| DELETE | `/permission/delete?id=` | admin | — | `{message}` | 200 · 404 · 409 (assigned) |
| GET | `/permission/get-one?id=` | principal | — | `PermissionResponse` | 200 · 404 |
| POST | `/permission/get-all` | principal | `FindDTO` | `PermissionResponse[]` + pagination | 200 · 422 |

### Role — [`api/role.md`](api/role.md)

| Method | Path | Auth | Request | Response `data` | Status |
|---|---|---|---|---|---|
| POST | `/role/add` | admin | `RoleDTO` | `RoleResponse` | 201 · 422 |
| PUT | `/role/update` | admin | `UpdateRoleDTO` | `RoleResponse` | 200 · 404 · 422 |
| DELETE | `/role/delete?id=` | admin | — | `{message}` | 200 · 404 |
| GET | `/role/get-one?id=` | principal | — | `RoleResponse` | 200 · 404 |
| POST | `/role/get-all` | principal | `FindDTO` | `RoleResponse[]` + pagination | 200 · 422 |

### Upload — [`api/upload.md`](api/upload.md)

| Method | Path | Auth | Request | Response `data` | Status |
|---|---|---|---|---|---|
| POST | `/upload/upload-file` | user | `multipart/form-data`: `file` + metadata fields | `UploadResponse` (with `downloadUrl`) | 201 · 413 · 415 · 422 · 503 |
| POST | `/upload/get-all` | user | `FindDTO` | `UploadResponse[]` + pagination (own files; admin sees all) | 200 · 422 |
| GET | `/upload/get-one?id=` | user | — | `UploadResponse` (with `downloadUrl`) | 200 · 404 |
| DELETE | `/upload/delete?id=` | user (owner or admin) | — | `{message}` | 200 · 404 · 503 |

## Shared response models

`UserProfile` (`/auth/me`, login):

```json
{
  "id": "uuid", "username": "admin", "fullname": "Administrator", "email": "admin@example.com",
  "phone": null, "status": "active", "emailVerified": true, "twoFactorEnabled": false,
  "role": "admin", "permissionId": "uuid",
  "permission": { "id": "uuid", "name": "Administrator", "alias": "admin", "privileges": ["*"] },
  "groupId": null, "group": null,
  "lastLoginAt": "2026-10-12T05:24:08.947000Z", "createdAt": "…", "updatedAt": "…"
}
```

`UserResponse` (admin views) is `UserProfile` plus `about, image, multiLogin, expiredAt,
twoFactorMethod, authProvider, settings, personalization, additional, createdBy`.

`LoginResponse` is `{ "twoFactorRequired": false, "user": UserProfile, "auth": { "accessToken",
"refreshToken", "expiresAt" } }`, where `expiresAt` is the access-token expiry in ISO-8601 UTC.

No response ever contains `passwordHash`, `twoFactorSecret` or OTP data.

## Checking this registry

```bash
cd apps/backend
BE_JWT_SECRET=$(openssl rand -hex 32) .venv/bin/python -c "
from core.app_factory import create_app
import json; print('\n'.join(sorted(f'{m} {p}' for p, ops in create_app().openapi()['paths'].items() for m in ops)))"
```

Set `BE_GOOGLE_CLIENT_ID` and `BE_GOOGLE_CLIENT_SECRET` to include `/auth/google/callback`.
