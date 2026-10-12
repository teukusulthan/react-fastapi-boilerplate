---
name: reactjs-api-design
description: API contract reference for apps/web (React/TypeScript) against the FastAPI backend. Covers the house endpoint shape, API_ENDPOINTS constants, the ApiEnvelope/ApiMetaData/ApiPagination response envelope, ApiError and error codes, the FindDTO/FilterItem list-query contract (searchBy, operators, whitelists) and request payload typing. Load when writing service files, defining API_ENDPOINTS, or typing request/response payloads.
---

# API Design (React / TypeScript)

## Source of truth

1. **The backend itself.** Run it (`npm run dev` or `npm run dev:backend` from the repo root) and open
   `http://localhost:8020/docs` (Swagger) or `/openapi.json`. Request/response models there are generated
   from `apps/backend/dto/*.py` and are authoritative for field names and required/optional.
2. **The typed client layer already in the repo:** `apps/web/src/types/api.d.ts` (envelope, errors,
   FindDTO), `apps/web/src/types/models.d.ts` (entities), `apps/web/src/services/api-endpoints.ts`.

There is no checked-in OpenAPI JSON file — never invent paths or fields; read the DTO or `/docs`.

---

## 1. Endpoint shape (house style)

| Action        | Method   | Path               | Params / body                       | Success |
| ------------- | -------- | ------------------ | ----------------------------------- | ------- |
| Create        | `POST`   | `/<module>/add`    | JSON body                           | 201 + entity |
| Update        | `PUT`    | `/<module>/update` | JSON body incl. `id` (PATCH semantics: only sent fields change; `null` clears) | 200 + entity |
| Delete        | `DELETE` | `/<module>/delete` | query `?id=`                        | 200 `{ message }` |
| Get one       | `GET`    | `/<module>/get-one`| query `?id=`                        | 200 + entity |
| List / filter | `POST`   | `/<module>/get-all`| FindDTO body                        | 200 + array + pagination |

Extra actions are explicit sub-paths (`/user/reset-password`, `/user/check-email?email=`,
`/permission/update-partial`, `/upload/upload-file`). There are no REST-style `/<module>/{id}` routes.

Paths are relative to `env.api.baseUrl` (`VITE_API_BASE_URL`, default `/api/v1/apps`) — never include
that prefix in `API_ENDPOINTS`.

## 2. Endpoint constants (`src/services/api-endpoints.ts`)

```ts
export const API_ENDPOINTS = {
  USER: {
    BASE: '/user',                              // CRUD factory appends /add, /update, /delete, /get-one, /get-all
    GET_BY_USERNAME: '/user/get-by-username',
    RESET_PASSWORD: '/user/reset-password',
    CHECK_EMAIL: '/user/check-email',
    UPDATE_PROFILE: '/user/settings/update-profile',
  },
  PERMISSION: { BASE: '/permission', UPDATE_PARTIAL: '/permission/update-partial' },
  // …AUTH, GROUP, ROLE, UPLOAD, HEALTH
} as const
```

- Group and key names: `UPPER_SNAKE_CASE`; values: the backend path verbatim.
- CRUD modules expose `BASE`; extra actions get their own key.
- New public (unauthenticated) auth endpoint? Also add it to `NO_REFRESH_ENDPOINTS` in `api-client.ts`.

## 3. Response envelope (`src/types/api.d.ts`)

Every response — success or error — is `{ metaData, data }`:

```ts
export interface ApiPagination { page: number; size: number; totalElements: number; totalPages: number }

export interface ApiMetaData {
  status: boolean               // false on errors
  responseCode: number          // mirrors the HTTP status
  message: string
  executionTime: number         // ms
  requestId?: string | null     // also in the X-Request-ID header
  pagination?: ApiPagination | null   // only on get-all
  errorCode?: ApiErrorCode | (string & Record<never, never>) | null  // only on errors
}

export interface ApiEnvelope<T> { metaData: ApiMetaData; data: T }
export interface ApiList<T> { items: T[]; pagination: ApiPagination }   // what services return for get-all
export interface ApiFieldError { field: string; message: string }       // 422 details
```

Services unwrap the envelope (`apiRequests` in `api-factory.service.ts`): components get `T` or
`ApiList<T>`. Use `apiRequests.envelope<T>(config)` only when you need `metaData` itself.

## 4. Errors

All failures reach the app as `ApiError` (`src/services/api-error.ts`):
`{ status, code, message, details, requestId }` + `fieldErrors` getter (422 → `[{ field, message }]`).

| HTTP | `code` (`metaData.errorCode`) | notes |
|---|---|---|
| 400 | `BAD_REQUEST` | also wrong *current* password on change-password / 2FA disable (not 401) |
| 401 | `AUTHENTICATION_ERROR`, `ACCOUNT_NOT_VERIFIED` (login only) | triggers one refresh attempt except on public auth endpoints |
| 403 | `PERMISSION_ERROR` | |
| 404 | `RESOURCE_NOT_FOUND` | |
| 405 | `METHOD_NOT_ALLOWED` | |
| 409 | `CONFLICT` | unique field taken / referenced record; `details` names the field |
| 413 / 415 | `PAYLOAD_TOO_LARGE` / `UNSUPPORTED_MEDIA_TYPE` | uploads |
| 422 | `VALIDATION_ERROR` | `details = [{ field, message }]`, field is camelCase (`email`, `filters[0].field`) |
| 429 | `RATE_LIMITED` | `Retry-After` header |
| 503 | `CONFIGURATION_ERROR`, `SERVICE_UNAVAILABLE` | feature not configured / backing service down |
| 500 | `INTERNAL_ERROR` | message is always generic |
| 0 | `NETWORK_ERROR`, `TIMEOUT`, `REQUEST_CANCELLED` | client-side codes (`ClientErrorCode`) |
| any | `INVALID_RESPONSE` | 2xx that was not an envelope |

See `.claude/skills/reactjs-error-handling/SKILL.md` for how to surface them.

## 5. List query — `FindDTO` (body of every `get-all`)

```ts
import type { FindDTO, FilterItem } from '@/types/api'

const query: FindDTO = {
  page: 1,                        // >= 1 (default 1)
  size: 20,                       // 1..BE_MAX_PAGE_SIZE (default 10, max 100) — bigger → 422
  search: 'jane',                 // literal, case-insensitive "contains"
  searchBy: ['username', 'email'],// optional; must be searchable fields; omitted = all searchable fields
  orderBy: 'createdAt',           // sortable field (default createdAt)
  order: 'desc',                  // 'asc' | 'desc' (default desc)
  filters: [
    { field: 'status', operator: 'is', value: { is: 'active' } },
    { field: 'createdAt', operator: 'is between', value: { gte: '2025-01-01T00:00:00Z', lte: '2025-12-31T23:59:59Z' } },
  ],
}
```

`FilterItem = { field, operator, value?: { is?, isOneOf?, gte?, lte? }, operatorType?: 'and' | 'or' }`.
Values are scalars or lists of scalars only (objects → 422). Filters flagged `operatorType: 'or'` are OR-ed
together as one group; everything else is AND-ed.

| `operator` | value key | backend meaning |
|---|---|---|
| `is` / `is not` | `is` | equals / not equals (on list fields: contains element) |
| `is one of` / `is not one of` | `isOneOf` | in / not in |
| `greater than equals` / `less than equals` | `gte` / `lte` | ≥ / ≤ (numbers, dates, text) |
| `is between` / `is not between` | `gte` + `lte` | inclusive range / outside range |
| `is exist` / `is not exist` | — | not null / null |
| `is contains` / `is not contains` | `is` | case-insensitive literal substring (text fields only) |
| `all` | `isOneOf` | list field contains all values |

**Whitelists:** every resource declares filterable / searchable / sortable fields in
`apps/backend/db/schema.py` (camelCase in the API). Anything else — including sensitive fields — returns
422 with one `{ field: 'filters[i].field' | 'searchBy[i]' | 'orderBy', message }` per problem. Examples:
users search `username, fullname, email, phone`; filter also `status, permissionId, groupId, emailVerified,
createdAt…`; sort `username, fullname, email, status, lastLoginAt, createdAt…`. Datetime values accept ISO
strings or epoch ms; booleans accept `true/false`.

Legacy `search_by` is still accepted by the backend; new code sends `searchBy`.

## 6. Request payloads

- Define `I<Entity>CreatePayload` / `I<Entity>UpdatePayload extends Partial<…> { id: string }` **in the
  service file** (see `user.service.ts`, `group.service.ts`).
- Mirror the backend DTO exactly: camelCase keys, same optionality, `T | null` where the DTO allows null.
  The backend DTOs use `extra="forbid"` → **unknown keys are 422**, and server-owned fields
  (`id` on create, `createdBy`, `createdAt`, `updatedAt`, `role`) must never be sent.
- Upload is multipart: file part `file`, camelCase text fields, tags as CSV, booleans as strings
  (`buildUploadForm` in `upload.service.ts`).

## 7. Response entity types (`src/types/models.d.ts`)

Mirror the backend response DTO field-by-field (camelCase, timestamps as ISO-8601 UTC strings, nullable
where the DTO is optional). Existing: `UserProfile` (`/auth/me`, login), `UserDetail` (`/user/*`),
`AvailabilityCheck`, `Permission`, `Group`, `Role`, `Upload`. Add new shared entities here; types used by
a single feature may live in that feature's `types/` folder.

---

## Forbidden patterns

| Pattern | Use instead |
|---|---|
| `apiClient.delete('/feature/delete/' + id)` | `apiRequests.delete(API_ENDPOINTS.X.DELETE, { id })` or the CRUD factory |
| `GET …/get-all` | `POST` with a FindDTO body (`apiRequests.list` / `service.getAll`) |
| Hard-coded URL strings in services/hooks | `API_ENDPOINTS.*` |
| `import axios` / `fetch()` in features | services → `apiRequests` |
| Service functions returning `{ loading, data, error }` wrappers or catching errors | return `Promise<T>`, let `ApiError` bubble; TanStack Query owns loading/error state |
| Reading `metaData.pagination.totalPage` / `totalData` | `pagination.totalPages` / `totalElements` |
| Sending `workspaceId`, `organizationId`, arbitrary keys in FindDTO | only the FindDTO fields above; scope server-side |
| `any` on DTO fields | explicit types or `unknown` / `JsonObject` |

## Checklist

- [ ] Path verified against `/docs` or the backend router; constant added to `API_ENDPOINTS`
- [ ] Payload interfaces match the backend DTO (camelCase, no server-owned fields)
- [ ] Response type in `models.d.ts` matches the response DTO
- [ ] Lists consume `ApiList<T>` (`items`, `pagination.totalElements/totalPages`)
- [ ] Filter/search/sort fields are in the backend whitelist
