# API — User (`/user`)

Code: `apps/backend/router/user.py`, `service/user.py`, `dto/user.py`, `dto/user_profile.py`.
The envelope, `FindDTO` and error codes are described in [`../api-spec.md`](../api-spec.md).

**Access:** every route needs a signed-in **user** (an `X-Internal-Token` gets 403). Everything is
**admin-only** except `PUT /user/settings/update-profile`, which is self-service.

## Response — `UserResponse`

```json
{
  "id": "9b914099-…", "username": "admin", "fullname": "Administrator", "email": "admin@example.com",
  "phone": null, "status": "active", "emailVerified": true, "twoFactorEnabled": false,
  "role": "admin", "permissionId": "6550ca1a-…",
  "permission": { "id": "6550ca1a-…", "name": "Administrator", "alias": "admin", "privileges": ["*"] },
  "groupId": null, "group": null,
  "lastLoginAt": "2026-10-12T05:24:18.960000Z", "createdAt": "…", "updatedAt": "…",
  "about": null, "image": null, "multiLogin": true, "expiredAt": null, "twoFactorMethod": null,
  "authProvider": "local", "settings": null, "personalization": null, "additional": null, "createdBy": null
}
```

`status` is one of `pending`, `active`, `blocked` or `deleted`. `role` is the permission alias. The
password hash and 2FA secret are never returned.

## Endpoints

### `POST /user/add` — admin → 201

| Field | Type | Notes |
|---|---|---|
| `username` | string, required | 3–50 chars, `[A-Za-z0-9._-]` |
| `fullname` | string, required | 1–100 chars |
| `email` | email, required | Lowercased |
| `phone` | string \| null | `^\+?[0-9]{6,20}$` |
| `password` | string \| null | **Required** with local auth; **rejected** (422) with `BE_AUTH_PROVIDER=supabase` |
| `permissionId` | uuid \| null | **Omitted** → `BE_DEFAULT_PERMISSION_ALIAS` permission; an explicit `null` means no permission |
| `groupId` | uuid \| null | Must exist (422 otherwise) |
| `status` | enum | Default `active` |
| `emailVerified`, `multiLogin` | bool | Defaults `false`, `true` |
| `expiredAt` | datetime \| null | After this, the account cannot authenticate |
| `about`, `image` | string \| null | |
| `settings`, `personalization`, `additional` | object \| null | Free-form JSON |

Unknown fields (for example `role`) return 422. A duplicate username, email or phone returns 409, with
the field in `data`.

### `PUT /user/update` — admin

`{ "id": "…", ...any of the fields above except password }`. PATCH semantics: only the fields you send
change. `null` clears nullable fields; for `username`, `email`, `status`, `emailVerified` and
`multiLogin`, it returns 422.

- Blocking, expiring, or removing/demoting a user **revokes all of that user's sessions**.
- 409 when admins would demote or block themselves, or when the change would remove the last active
  superuser.

### `DELETE /user/delete?id=` — admin

200 `{message: "User deleted"}`. Revokes the user's sessions. 409 when deleting yourself or the last
active superuser. 404 for an unknown id.

### `GET /user/get-one?id=` · `GET /user/get-by-username?username=` — admin

200 `UserResponse`, or 404.

### `POST /user/get-all` — admin

Body: `FindDTO`. Whitelists (camelCase API names):

| | Fields |
|---|---|
| search | `username`, `fullname`, `email`, `phone` |
| filter | `id`, `username`, `fullname`, `email`, `phone`, `status`, `permissionId`, `groupId`, `emailVerified`, `multiLogin`, `twoFactorEnabled`, `authProvider`, `expiredAt`, `lastLoginAt`, `createdBy`, `createdAt`, `updatedAt` |
| sort | `username`, `fullname`, `email`, `status`, `expiredAt`, `lastLoginAt`, `createdAt`, `updatedAt` |

```json
{ "page": 1, "size": 10, "search": "jane", "searchBy": ["username", "email"],
  "filters": [{ "field": "status", "operator": "is", "value": { "is": "active" } }] }
```

Returns 200 with `data: UserResponse[]` and `metaData.pagination`. A field outside the whitelist (for
example `passwordHash`) returns 422 with `field: "filters[0].field"`.

### `POST /user/reset-password` — admin

`{ "id": "…", "newPassword": "…" }` → 200 `{message}`. Sets the password (policy applies, 422) and
revokes all of the user's sessions. Returns 400 in Supabase auth mode (Supabase manages passwords) and
404 for an unknown id.

### `GET /user/check-email?email=` · `GET /user/check-username?username=` · `GET /user/check-phone?phone=` — admin

200 `{ "field": "email", "exists": true, "available": false }`.

### `PUT /user/settings/update-profile` — the signed-in user

Body: any of `fullname`, `phone`, `about`, `image`, `settings`, `personalization`. Every other field
(`permissionId`, `status`, `email`, `username`, `role`…) returns **422**. The response is 200
`UserResponse`; a phone taken by another user returns 409.
