---
name: reactjs-service
description: Use when calling the backend API from apps/web — fetching data, submitting forms, creating CRUD services, uploads. Covers API_ENDPOINTS constants, the createResourceService factory, apiRequests helpers (get/post/put/delete/list/upload/envelope), custom service objects and the ApiError contract.
---

# Skill: Calling Backend Services

The API layer lives in `apps/web/src/services/` (flat). Components and hooks only ever see **unwrapped
data** (`T`, or `ApiList<T> = { items, pagination }` for lists) and **`ApiError`** on failure.

## When to use

Adding a backend module to the web app, calling a new endpoint, or wiring a page/hook to data.
For hook patterns (query keys, invalidation) also read `.claude/skills/reactjs-tanstack-query/SKILL.md`;
for envelope/DTO types read `.claude/skills/reactjs-api-design/SKILL.md`.

---

## The layer (real files)

```
src/services/
├── api-client.ts                ← the ONLY axios instance + interceptors (do not edit per feature)
├── api-error.ts                 ← ApiError, toApiError, getErrorMessage, isApiError
├── api-endpoints.ts             ← API_ENDPOINTS: every backend path
├── api-factory.service.ts       ← apiRequests helpers + toApiList + requestEnvelope
├── api-factory-crud.service.ts  ← createResourceService / IResourceService / IIdParams
├── auth.service.ts              ← custom (non-CRUD) service: /auth/*
├── user.service.ts              ← CRUD factory + extra endpoints (reference example)
├── group.service.ts / role.service.ts        ← pure CRUD factory
├── permission.service.ts        ← CRUD factory + updatePrivileges (/permission/update-partial)
└── upload.service.ts            ← multipart upload + list/get/delete
```

`apiClient` behaviour (`api-client.ts`):

- `baseURL` = `env.api.baseUrl` from `src/config/env.ts` (`VITE_API_BASE_URL`, default `/api/v1/apps`;
  the Vite dev proxy / nginx strip that prefix and forward to the backend on :8020).
- `withCredentials: true`; auth is httpOnly cookies (`token`, `refresh_token`) — no Authorization header,
  never store tokens in JS.
- Success interceptor resolves with the **envelope** `{ metaData, data }`; a 200 that is not an envelope,
  or `metaData.status === false`, is rejected as `ApiError`.
- 401 → single-flight `POST /auth/refresh` then one retry; never for public auth endpoints
  (`NO_REFRESH_ENDPOINTS`) or requests sent with `{ skipAuthRefresh: true }`. Refresh rejected →
  `endClientSession()` (store anonymous + `queryClient.clear()`) → guards redirect to `/auth/login?redirect=…`.
  Network/5xx refresh failures keep the session.

---

## Decision tree

```
Does the backend module follow the house CRUD contract?
  POST {base}/add · PUT {base}/update · DELETE {base}/delete?id= · GET {base}/get-one?id= · POST {base}/get-all
  YES → createResourceService (one line), spread it and add extra endpoints if needed (see user.service.ts)
  NO  → custom service object whose methods call apiRequests.* (see auth.service.ts)
File upload?           → apiRequests.upload (see upload.service.ts)
Need metaData itself?  → apiRequests.envelope / requestEnvelope (rare; e.g. a message or pagination on non-list)
```

There is no `api.service.ts` / `request()` helper — always go through `apiRequests` and a service file.

---

## Step 1 — Add the endpoint constant

`src/services/api-endpoints.ts` (paths are relative to the base URL and mirror the backend routers exactly):

```ts
export const API_ENDPOINTS = {
  // …existing AUTH, USER, GROUP, PERMISSION, ROLE, UPLOAD, HEALTH
  PRODUCT: {
    BASE: '/product',                       // backend: APIRouter(prefix="/product")
    PUBLISH: '/product/publish',            // non-CRUD extra action
  },
} as const
```

## Step 2a — CRUD module (factory)

Create `src/services/product.service.ts`:

```ts
import type { Product } from '@/types/models'   // response type: add it to src/types/models.d.ts

import { API_ENDPOINTS } from './api-endpoints'
import { createResourceService } from './api-factory-crud.service'
import { apiRequests } from './api-factory.service'

/** `POST /product/add` — must match the backend DTO (extra="forbid" → unknown keys = 422). */
export interface IProductCreatePayload {
  name: string
  price: number
  description?: string | null
}

/** `PUT /product/update` — PATCH semantics: only sent fields change, null clears. */
export interface IProductUpdatePayload extends Partial<IProductCreatePayload> {
  id: string
}

const crud = createResourceService<Product, IProductCreatePayload, IProductUpdatePayload>(API_ENDPOINTS.PRODUCT.BASE)

export const productService = {
  ...crud,
  publish: ({ id }: { id: string }) => apiRequests.post<Product, { id: string }>(API_ENDPOINTS.PRODUCT.PUBLISH, { id }),
}
```

Consumer API (`IResourceService` in `api-factory-crud.service.ts`):

```ts
await productService.add({ name, price })                      // → Product (201)
await productService.update({ id, name })                      // → Product
await productService.delete({ id })                            // → void   (DELETE ?id=)
await productService.getOne({ id })                            // → Product (GET ?id=)
const { items, pagination } = await productService.getAll({    // → ApiList<Product>
  page: 1, size: 20, search: 'foo', searchBy: ['name'], orderBy: 'createdAt', order: 'desc',
})
```

`getOne` / `delete` take an object `{ id }`, never a bare string, and never a path segment (`/product/123` does not exist).

## Step 2b — Custom (non-CRUD) module

Follow `auth.service.ts`: one object, each method calls a typed `apiRequests` helper.

```ts
// src/services/report.service.ts
import { API_ENDPOINTS } from './api-endpoints'
import { apiRequests } from './api-factory.service'

export interface IReportRunPayload { reportId: string; from: string; to: string }
export interface IReportRunResult { rows: number; url: string }

export const reportService = {
  run: (data: IReportRunPayload) => apiRequests.post<IReportRunResult, IReportRunPayload>(API_ENDPOINTS.REPORT.RUN, data),
  status: (jobId: string) => apiRequests.get<{ state: string }>(API_ENDPOINTS.REPORT.STATUS, { jobId }),
}
```

`apiRequests` (`api-factory.service.ts`) — all resolve with unwrapped `data`, reject with `ApiError`:

| helper | call |
|---|---|
| `get<T>(url, params?, options?)` | GET with query params |
| `post<T, P>(url, data?, options?)` | POST JSON |
| `put<T, P>(url, data?, options?)` | PUT JSON |
| `patch<T, P>(url, data?, options?)` | PATCH JSON (the house API rarely uses PATCH) |
| `delete<T>(url, params?, options?)` | DELETE with query params |
| `list<T>(url, query?: FindDTO, options?)` | POST a FindDTO to a `get-all` → `ApiList<T>` |
| `upload<T>(url, formData, onProgress?, options?)` | multipart POST with % progress |
| `envelope<T>(config)` | raw `ApiEnvelope<T>` when you need `metaData` |

`options` is an axios config minus url/method/data/params — e.g. `{ signal }` (TanStack Query passes one)
or `{ skipAuthRefresh: true }`.

## Step 2c — File upload

Use (or mirror) `upload.service.ts`. The backend expects multipart with the file part named **`file`** and
camelCase text fields (`folder`, `filename`, `tags` as CSV, `widgetId`, …; booleans as strings):

```ts
import { uploadService } from '@/services/upload.service'

const upload = await uploadService.uploadFile(file, { folder: 'reports', tags: ['q1'] }, setProgress)
const { items } = await uploadService.getAll({ page: 1, size: 20 })
const { downloadUrl } = await uploadService.getOne({ id: upload.id })   // short-lived presigned URL
```

Errors to expect: 413 `PAYLOAD_TOO_LARGE`, 415 `UNSUPPORTED_MEDIA_TYPE`, 503 `CONFIGURATION_ERROR` (S3 not configured).

## Step 3 — Use it from a hook

Services are called from TanStack Query hooks inside the feature (`features/<domain>/<feature>/hooks/`),
never directly from page components. Reference: `features/administrator/user/hooks/useUserList.ts`:

```ts
export function useUserList(query: FindDTO) {
  return useQuery({
    queryKey: USER_QUERY_KEYS.list(query),
    queryFn: () => userService.getAll(query),
    placeholderData: keepPreviousData,
  })
}
```

---

## ✅ Do

- ✅ Use `createResourceService` whenever the 5-endpoint contract matches; spread + extend for extra endpoints.
- ✅ Reference every path through `API_ENDPOINTS.*`.
- ✅ Keep payload interfaces (`I…Payload`) in the service file; shared response entities in `src/types/models.d.ts`.
- ✅ Match payloads to the backend DTO field-for-field (camelCase). Unknown keys → 422.
- ✅ Let errors bubble as `ApiError`; handle them in the hook/component (`getErrorMessage`, `error.fieldErrors`).

## ❌ Don't

- ❌ Don't `import axios` or call `fetch()` outside `api-client.ts`; don't import `apiClient` in features.
- ❌ Don't read `import.meta.env` for the base URL — `apiClient` already uses `env.api.baseUrl`.
- ❌ Don't `try/catch` inside services or swallow errors.
- ❌ Don't create `src/services/modules/` or an `api.service.ts` "request()" helper.
- ❌ Don't send tokens/Authorization headers or store tokens (cookies are httpOnly).
- ❌ Don't build REST-style URLs (`/product/{id}`); the backend uses `?id=` query params.

## Common mistakes

- Reading `response.data.data` — services already return the unwrapped `data`.
- Expecting `getAll` to return an array — it returns `{ items, pagination }` (`pagination.totalElements`, `totalPages`).
- `getOne(id)` instead of `getOne({ id })`.
- Adding a public auth endpoint without adding it to `NO_REFRESH_ENDPOINTS` (causes refresh loops on bad credentials).

## Verification checklist

- [ ] Endpoint added to `api-endpoints.ts` (`BASE` for CRUD modules, named keys for extra actions)
- [ ] Service at `src/services/{module}.service.ts` (flat)
- [ ] Factory for CRUD; custom object over `apiRequests` otherwise; uploads via `apiRequests.upload`
- [ ] Response type in `src/types/models.d.ts` mirrors the backend response DTO
- [ ] No `try/catch`, no direct axios, no inline URL strings
- [ ] `npm run typecheck` / `npm run lint` / `npm run test` (or `npm run ci` from the repo root) pass
