# API — Auth (`/auth`)

Code: `apps/backend/router/auth.py`, `service/auth/`, `dto/auth.py`. The envelope, error codes and auth
mechanisms are described in [`../api-spec.md`](../api-spec.md).

**Mounting:**
- `GET /auth/me` and `POST /auth/logout` are always mounted.
- Everything else is mounted only when `BE_AUTH_PROVIDER=local`.
- `POST /auth/google/callback` additionally needs `BE_GOOGLE_CLIENT_ID` and `BE_GOOGLE_CLIENT_SECRET`.

**Rate limit:** every public endpoint here allows `BE_RATE_LIMIT_AUTH` requests per client IP per
`BE_RATE_LIMIT_AUTH_WINDOW` (`/auth/refresh`: 6×). Over the limit you get 429 `RATE_LIMITED` with a
`Retry-After` header.

**Successful authentication** (login, 2FA verify, refresh, change-password, Google) always returns
`LoginResponse` and sets two cookies:

```json
{
  "twoFactorRequired": false,
  "user": { "id": "…", "username": "admin", "role": "admin", "...": "UserProfile, see api-spec.md" },
  "auth": { "accessToken": "<jwt>", "refreshToken": "<jwt>", "expiresAt": "2026-10-12T05:39:08Z" }
}
```

```
Set-Cookie: token=<access>; HttpOnly; Max-Age=900; Path=/; SameSite=lax[; Secure]
Set-Cookie: refresh_token=<refresh>; HttpOnly; Max-Age=604800; Path=<BE_COOKIE_REFRESH_PATH>; SameSite=lax[; Secure]
```

Browsers should rely on the cookies. Mobile and server clients can use the body tokens with
`Authorization: Bearer`.

---

## Session

### `GET /auth/me` — user

Returns the current `UserProfile`. It works with local JWTs (cookie or Bearer) and with Supabase JWTs.
In Supabase mode, the first call auto-provisions a `users` row (`authProvider: "supabase"`, default
permission). A row an admin created earlier with the same email (`authProvider: "supabase"`, no
`externalId`) is linked instead.

Errors: 401 when credentials are missing, invalid, expired or revoked, or when the account is not
`active` or has passed `expiredAt`.

### `POST /auth/logout` — public

Revokes the presented access and refresh tokens (local mode) and clears both cookies. It always
returns 200 `{message: "Logged out"}`, even when you are already logged out.

### `POST /auth/refresh`

The refresh token comes from the `refresh_token` cookie or `Authorization: Bearer <refreshToken>`.
Refresh tokens are **single-use**: each call returns a new pair and new cookies with the same session
id. Reusing an old refresh token revokes the whole session (401). An access token used here is rejected
(401, wrong `type`).

## Login

### `POST /auth/login`

```json
{ "identifier": "admin@example.com", "password": "…" }
```

`identifier` is an email or a username.

| Outcome | Response |
|---|---|
| Success, no 2FA | 200 `LoginResponse` + cookies |
| 2FA enabled | 200 `{ "twoFactorRequired": true, "sessionToken": "…", "method": "email" \| "totp" }`. No cookies; the email method sends a code. |
| Unknown user, wrong password, or locked account | 401 `AUTHENTICATION_ERROR` "Invalid credentials" (always the same message) |
| Correct password but account `pending` | 401 `ACCOUNT_NOT_VERIFIED` |
| Blocked, deleted or expired account | 401 |

Lockout: after `BE_ACCOUNT_LOCK_MAX_ATTEMPTS` failures for an account from one IP, logins from that IP
fail for `BE_ACCOUNT_LOCK_SECONDS`, still with the generic message.

### `POST /auth/2fa/verify`

`{ "sessionToken": "…", "otp": "123456" }` → 200 `LoginResponse` + cookies. A wrong or expired code or
session returns 401. The challenge lasts `BE_TWO_FACTOR_SESSION_TTL` seconds.

### `POST /auth/2fa/resend`

`{ "sessionToken": "…" }` → 200 `{message}`. Email method only (400 for TOTP). There is a resend cooldown
of `BE_OTP_RESEND_COOLDOWN`; calling too soon returns 429 with `Retry-After`.

## Two-factor management (user)

| Endpoint | Body | Result |
|---|---|---|
| `POST /auth/2fa/setup` | `{ "method": "email" \| "totp" }` | 200 `{method, message, otpauthUri, qrImageBase64, secret}`. The TOTP fields are null for email, which emails a code instead. The setup stays pending until it is enabled. 409 if already enabled. 503 when email is unavailable. |
| `POST /auth/2fa/enable` | `{ "otp": "123456" }` | 200 `UserProfile` (`twoFactorEnabled: true`). 400 for a bad code. |
| `POST /auth/2fa/disable` | `{ "password": "…" }` | 200 `UserProfile`. **400** (not 401) for a wrong password. |

TOTP secrets are encrypted at rest when `BE_DATA_ENCRYPTION_KEY` is set.

## Registration (self-service)

### `POST /auth/register`

```json
{ "username": "jane", "fullname": "Jane Doe", "email": "jane@example.com", "phone": "+6281234567890", "password": "…" }
```

| Field | Rules |
|---|---|
| `username` | 3–32 chars, matching `^[A-Za-z0-9][A-Za-z0-9._-]{2,31}$` |
| `fullname` | 1–100 chars |
| `email` | Valid email; stored lowercased |
| `phone` | Optional. Separators are stripped, then it must be `+` and 6–15 digits. |
| `password` | Min length `BE_PASSWORD_MIN_LENGTH`, max 72 bytes |

The response is **201** `{message}` with the same generic message for new and existing emails (no
enumeration). The user is stored with `status: "pending"` and the password hashed. An OTP is emailed;
if the email already belongs to an active account, an "account exists" notice is emailed instead.

Errors:
- 409 `CONFLICT` when the username or phone is taken by another account. A pending account older than
  `BE_REGISTRATION_PENDING_TTL` is replaced instead.
- 403 when `BE_REGISTRATION_ENABLED=false`.
- 503 `CONFIGURATION_ERROR` when email cannot be sent.
- 422 for the password policy.

### `POST /auth/register/verify`

`{ "email", "otp" }` → 200 `{message}`. The account becomes `active` with `emailVerified: true`. A bad
or expired code returns 400 "Invalid or expired code". After `BE_OTP_MAX_ATTEMPTS` failures the code is
invalidated.

### `POST /auth/register/resend`

`{ "email" }` → 200 with a generic `{message}`, subject to the resend cooldown.

## Passwords

| Endpoint | Body | Result |
|---|---|---|
| `POST /auth/forgot-password/request` | `{ "email" }` | Always 200 "If an account exists for this email, a password reset code has been sent". 503 if email is unavailable (checked before any lookup). |
| `POST /auth/forgot-password/verify` | `{ "email", "otp" }` | 200 `{ "valid": true }`; 400 otherwise. Does not consume the code. |
| `POST /auth/forgot-password/reset` | `{ "email", "otp", "newPassword" }` | 200 `{message}`. Consumes the code, sets the password, **revokes every session** and emails a notice. 400 for a bad code; 422 for policy. |
| `POST /auth/change-password` (user) | `{ "currentPassword", "newPassword" }` | 200 `LoginResponse` + **new cookies**. Other sessions are revoked. 400 for a wrong current password; 422 when the new password equals the old one or fails policy. |

## Email verification (link)

| Endpoint | Body | Result |
|---|---|---|
| `POST /auth/verify-email/request` (user) | — | Emails `BE_PUBLIC_WEB_URL + BE_EMAIL_VERIFY_PATH + ?token=…` (default web route `/auth/verify-email`). 200 `{message}`; 429 during cooldown. |
| `POST /auth/verify-email` | `{ "token" }` | 200 "Your email address is verified"; 400 "Invalid or expired link". |

## Google sign-in

### `POST /auth/google/callback`

`{ "code", "redirectUri", "codeVerifier"? }`. The backend exchanges the authorization code with Google,
verifies the ID token, and responds exactly like `/auth/login`.

- Without `BE_GOOGLE_AUTO_REGISTER=true`, only existing accounts can sign in (401 otherwise).
- `BE_GOOGLE_ALLOWED_DOMAINS` restricts email domains (403 for others).
- An unverified Google email returns 401. If Google is unreachable, the response is 503.

## Development tips

- With `BE_EMAIL_BACKEND=auto` and no SMTP, every OTP and link is printed in the backend log
  (`[email:console] …`).
- Clients must **not** attempt a refresh after a 401 from login, refresh, logout, 2FA verify/resend,
  register (and its verify/resend), the forgot-password endpoints, verify-email or the Google callback.
  The web app keeps this list in `NO_REFRESH_ENDPOINTS` (`apps/web/src/services/api-client.ts`).
