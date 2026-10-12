# API — Role (`/role`)

Code: `apps/backend/router/role.py`, `service/role.py`, `dto/role.py`. This is the **reference CRUD
module**: copy it when you add a resource (see `apps/backend/AI_GUIDE.md` §5.1).
The envelope, `FindDTO` and error codes are described in [`../api-spec.md`](../api-spec.md).

Roles are a hierarchical catalogue (positions, workspace or organization references). They are **not**
used for authorization; that is `permission`.

**Access:**
- Reads accept any authenticated principal: a user or `X-Internal-Token`.
- Writes are **admin-only**.

## Response — `RoleResponse`

```json
{
  "id": "ae41780c-…", "name": "Editor", "alias": "editor", "description": null, "rolePosition": null,
  "type": null, "parentId": null, "workspaceId": null, "organizationId": null,
  "createdBy": "7b139221-…", "createdAt": "2026-10-12T05:24:09Z", "updatedAt": "2026-10-12T05:24:09Z"
}
```

## Endpoints

| Endpoint | Body / query | Notes |
|---|---|---|
| `POST /role/add` → 201 | `{ name, alias?, description?, rolePosition?, type?, parentId?, workspaceId?, organizationId? }` | `name` 1–100 chars; `alias` ≤ 50 (not unique); `rolePosition` 0–1,000,000; `parentId` must exist (422) |
| `PUT /role/update` | `{ id, ...fields }` | PATCH semantics; `name` cannot be null; parent cycles return 422 |
| `DELETE /role/delete?id=` | — | Children are detached (`parentId` → null) |
| `GET /role/get-one?id=` | — | 404 if unknown |
| `POST /role/get-all` | `FindDTO` | See whitelists below |

Whitelists:

| | Fields |
|---|---|
| search | `name`, `alias`, `description` |
| filter | `id`, `name`, `alias`, `rolePosition`, `type`, `parentId`, `workspaceId`, `organizationId`, `createdBy`, `createdAt`, `updatedAt` |
| sort | `name`, `alias`, `rolePosition`, `createdAt`, `updatedAt` |
