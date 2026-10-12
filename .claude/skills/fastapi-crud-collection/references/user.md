# Reference — `user` (rich admin module)

Not a template for simple resources (start from `role`), but the reference for: custom
response building, uniqueness, admin lockout guards, token revocation and a self-service route.

## Files

- `apps/backend/dto/user.py` — `CreateUserDTO`, `UpdateUserDTO`, `ResetPasswordDTO`, `FindUserDTO`,
  `CheckAvailabilityResponse`, `UpdateProfileDTO`; responses from `apps/backend/dto/user_profile.py`
  (`UserProfile`, `UserResponse` — never contain `password_hash` / `two_factor_secret`)
- `apps/backend/service/user.py` — `UserService(CrudService)` + helpers `superuser_permission_ids`,
  `count_active_superusers`, `is_active_superuser`
- `apps/backend/service/user_profile.py` — `load_user_profile`, `load_user_profiles` (batched
  permission/group joins)
- `apps/backend/router/user.py`
- Tests: `apps/backend/tests/modules/test_users.py`
- Web: `apps/web/src/services/user.service.ts`, list page in `apps/web/src/features/administrator/user/`

## Endpoints and RBAC

Router-level `Depends(require_auth)` (users only; `X-Internal-Token` → 403).

| Method | Path | Body / query | Who |
|---|---|---|---|
| POST | `/user/add` | `CreateUserDTO` → 201 | superuser |
| PUT | `/user/update` | `UpdateUserDTO` (PATCH) | superuser |
| DELETE | `/user/delete?id=` | — | superuser |
| GET | `/user/get-one?id=` | — | superuser |
| GET | `/user/get-by-username?username=` | — | superuser |
| POST | `/user/get-all` | `FindUserDTO` | superuser |
| POST | `/user/reset-password` | `{id, newPassword}` → `{message}` | superuser |
| GET | `/user/check-email?email=` / `check-username?username=` / `check-phone?phone=` | → `{field, exists, available}` | superuser |
| PUT | `/user/settings/update-profile` | `UpdateProfileDTO` (fullname, phone, about, image, settings, personalization) | the caller (self) |

There is deliberately no `/user/{username}` catch-all.

## Whitelists (`USERS`)

search: `username, fullname, email, phone`; filter: those + `status, permissionId, groupId,
emailVerified, multiLogin, twoFactorEnabled, authProvider, expiredAt, lastLoginAt, id, createdBy,
createdAt, updatedAt`; sort: `username, fullname, email, status, expiredAt, lastLoginAt, createdAt,
updatedAt`. `passwordHash` / `twoFactorSecret` are sensitive → 422 if used.

## Domain rules

- Response models built through `load_user_profile(s)(…, model=UserResponse)` (adds `role`,
  `permission{…}`, `group{…}`).
- `/user/add` without `permissionId` gets `BE_DEFAULT_PERMISSION_ALIAS`; explicit `null` = none.
- `permissionId` / `groupId` must exist (422); `username` / `email` / `phone` unique (409, pre-check +
  constraint). Emails are lowercased.
- Passwords: `validate_password_policy` + `hash_password` (`core.security`). In
  `BE_AUTH_PROVIDER=supabase` mode `/user/add` rejects a password (422) and `reset-password` → 400.
- Lockout guards (409): cannot delete yourself, cannot remove your own admin access, cannot
  delete/block/expire/demote the last active superuser.
- Blocking, expiring, resetting the password or deleting a user calls
  `TokenStore.revoke_all_for_user` (live sessions get 401).
