# API — Permission (`/permission`)

Code: `apps/backend/router/permission.py`, `service/permission.py`, `dto/permission.py`.
The envelope, `FindDTO` and error codes are described in [`../api-spec.md`](../api-spec.md).

Permissions are the RBAC unit. Each user has one `permissionId`. The permission's `alias` becomes the
user's `role`, and its `privileges` are the strings checked by
`require_privilege("x:y")` (`apps/backend/core/deps.py`). Aliases listed in `BE_SUPERUSER_ALIASES`
(default `admin,owner`) make the user a superuser.

The seed (`npm run seed`) creates `admin` (privileges `["*"]`) and `user` (`profile:read`,
`profile:write`, `upload:read`, `upload:write`).

**Access:**
- Reads accept any authenticated principal: a user or `X-Internal-Token`.
- Writes are **admin-only**.

## Response — `PermissionResponse`

```json
{
  "id": "uuid", "name": "Administrator", "alias": "admin", "description": null, "type": null,
  "privileges": ["*"], "parentId": null, "image": null,
  "createdBy": "seed", "createdAt": "…", "updatedAt": "…"
}
```

## Endpoints

| Endpoint | Body / query | Notes |
|---|---|---|
| `POST /permission/add` → 201 | `{ name, alias?, description?, type?, privileges?, parentId?, image? }` | `alias` is lowercased and must match `^[a-z0-9_-]+$` (≤ 50). It is unique: a duplicate returns **409**. `privileges` is a list of non-blank strings without spaces (≤ 200), deduplicated. |
| `PUT /permission/update` | `{ id, ...fields }` | PATCH semantics. **409** if the change would drop your own superuser alias, or leave no active superuser. |
| `PUT /permission/update-partial` | `{ id, addPrivileges?: [], removePrivileges?: [] }` | Adds and removes individual privileges in one request |
| `DELETE /permission/delete?id=` | — | **409** while users hold it. Children are detached. |
| `GET /permission/get-one?id=` | — | 404 if unknown |
| `POST /permission/get-all` | `FindDTO` | See whitelists below |

Whitelists:

| | Fields |
|---|---|
| search | `name`, `alias`, `description` |
| filter | `id`, `name`, `alias`, `type`, `privileges` (list: `is` = contains, `is one of` = contains any, `all` = contains all), `parentId`, `createdBy`, `createdAt`, `updatedAt` |
| sort | `name`, `alias`, `createdAt`, `updatedAt` |
