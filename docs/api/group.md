# API — Group (`/group`)

Code: `apps/backend/router/group.py`, `service/group.py`, `dto/group.py`.
The envelope, `FindDTO` and error codes are described in [`../api-spec.md`](../api-spec.md).

Groups are an organisational grouping of users (`users.groupId`) and can be nested through `parentId`.

**Access:**
- Reads (`get-one`, `get-all`) accept any authenticated principal: a user or `X-Internal-Token`.
- Writes are **admin-only**.

## Response — `GroupResponse`

```json
{
  "id": "uuid", "name": "Engineering", "description": null, "parentId": null,
  "settings": null, "filters": null, "image": null, "personalization": null,
  "createdBy": "uuid", "createdAt": "2026-10-12T05:24:09Z", "updatedAt": "2026-10-12T05:24:09Z"
}
```

## Endpoints

| Endpoint | Body / query | Notes |
|---|---|---|
| `POST /group/add` → 201 | `{ name, description?, parentId?, settings?, filters?, image?, personalization? }` | `name` 1–100 chars; `description` ≤ 500; `filters` is a list of JSON objects (≤ 100). `parentId` must exist (422). |
| `PUT /group/update` | `{ id, ...fields }` | PATCH semantics; `name` cannot be null. A parent that is the group itself or one of its descendants returns 422 (cycle). |
| `DELETE /group/delete?id=` | — | **409** while users still belong to the group. Child groups are detached (`parentId` → null). |
| `GET /group/get-one?id=` | — | 404 if unknown |
| `POST /group/get-all` | `FindDTO` | See whitelists below |

Whitelists:

| | Fields |
|---|---|
| search | `name`, `description` |
| filter | `id`, `name`, `parentId`, `createdBy`, `createdAt`, `updatedAt` |
| sort | `name`, `createdAt`, `updatedAt` |

Unknown body fields return 422.
