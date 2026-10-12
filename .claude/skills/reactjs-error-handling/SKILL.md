---
name: reactjs-error-handling
description: Error handling standards for apps/web across 8 layers (exception, validation, state, UI, business rule, security, concurrency, cleanup), built on the real stack — ApiError from services/api-error.ts, TanStack Query error state, react-error-boundary (ErrorFallback / RouteErrorFallback), sonner toasts, applyApiFieldErrors for 422s. Use before writing API calls, mutations, forms, useEffect hooks, or any code that can fail.
---

# Error Handling Skill

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here (states recipe: §5.7). This skill owns error normalization, where each error
> is surfaced, retries and cleanup.

## What the boilerplate already does (don't re-implement)

| Concern | Where | Behaviour |
|---|---|---|
| Error normalization | `src/services/api-error.ts` | Every rejection from `apiClient` / `apiRequests` / services is an **`ApiError`** `{ status, code, message, details, requestId }` + `fieldErrors`. Helpers: `toApiError(e)`, `isApiError(e)`, `getErrorMessage(e, fallback?)`. Messages are user-safe (backend never leaks internals; network/timeout get friendly copy). |
| Envelope check | `src/services/api-client.ts` | A 2xx that isn't `{ metaData, data }` or has `metaData.status === false` becomes `ApiError` (`INVALID_RESPONSE` / backend code). |
| 401 / session | `api-client.ts` | One single-flight `POST /auth/refresh`, then retry. Refresh rejected → `endClientSession()`; guards redirect to `/auth/login?redirect=…`. Network/5xx during refresh keep the session. |
| 403 | `RoleGuard` + backend | Route-level: `ForbiddenPage` rendered in place. API-level 403 is an `ApiError` (`PERMISSION_ERROR`) you show inline. |
| Query retries | `src/lib/query-client.ts` | `shouldRetryQuery`: 1 retry for network / 429 / 5xx only; never 4xx. Mutations never retry. |
| Render crashes | `src/components/wrappers/AppProviders.tsx` | `<ErrorBoundary FallbackComponent={ErrorFallback}>` (react-error-boundary) around the app. |
| Route/lazy-chunk errors | `src/routes/index.tsx` | `errorElement: <RouteErrorFallback />` (404 → not-found screen; otherwise reload prompt; logs only in dev). |
| Unknown URL | `routes/index.tsx` | `{ path: '*', element: <NotFoundPage /> }` |
| Toasts | `src/components/ui/sonner.tsx` | `<Toaster>` mounted in `AppProviders`; call `toast.*` from `sonner`. There is no `use-toast` hook. |
| 422 → form fields | `src/utils/form-errors.ts` | `applyApiFieldErrors(error, form.setError, FIELDS)` |
| Session API down | `src/routes/guards/ServerUnavailable.tsx` | AuthGuard shows it with Retry when `/auth/me` fails transiently. |

## The 8 layers

### 1. Exception handling

Services don't catch. TanStack Query captures the rejection; components read `error`.

```ts
// ✅ service: no try/catch — ApiError bubbles
export const groupService = createResourceService<Group, IGroupCreatePayload, IGroupUpdatePayload>(API_ENDPOINTS.GROUP.BASE)

// ✅ imperative code outside React Query: catch, narrow, handle — never swallow
try {
  await uploadService.uploadFile(file, { folder: 'reports' })
  toast.success('File uploaded')
} catch (error) {
  const apiError = toApiError(error)
  if (apiError.code === 'UNSUPPORTED_MEDIA_TYPE') toast.error('This file type is not allowed.')
  else toast.error(apiError.message)
}
```

- ✅ `catch (error)` is `unknown` → `toApiError` / `isApiError` / `instanceof` before use. Never `any`.
- ✅ Branch on `error.code` / `error.status`, not on message text.
- ❌ No empty `catch`, no `console.log(error)` as handling. `console.error` only behind `env.app.isDev`.
- ❌ No custom `handleApiError` / `AppError` normalizer — `ApiError` is the one error type.
- Monitoring (Sentry etc.) is not wired in the boilerplate; if a project adds it, hook it into
  `ErrorFallback`/`RouteErrorFallback` and a `QueryCache({ onError })` in `lib/query-client.ts`, not per call site.

### 2. Validation

- ✅ Forms: zod 4 schema + `zodResolver` (`@hookform/resolvers/zod`) — see `features/shared/auth/schemas/login.schema.ts`
  and `.claude/skills/reactjs-form/SKILL.md`.
- ✅ Server-side 422: `error.fieldErrors` (`[{ field, message }]`, camelCase field names) → `applyApiFieldErrors`.
- ✅ External/untrusted JSON (localStorage, URL params, third-party APIs) → validate with zod before use.
  Backend responses are already typed against the DTOs; runtime-validate only where a wrong shape is plausible.
- ✅ Env is validated once in `src/config/env.ts` (throws a readable error at startup).
- ❌ No `dangerouslySetInnerHTML` with user/API content (only trusted `svg-code` icons).

### 3. State

Server state lives in TanStack Query — use its states instead of hand-rolled `idle/loading/error` flags:
`isPending` (no data yet), `isError` + `error` (an `ApiError`), `data`, `isFetching`, `isPlaceholderData`.
Client UI state → `useState` / zustand. Optimistic updates need `onMutate` snapshot + `onError` rollback
(see `.claude/skills/reactjs-tanstack-query/SKILL.md`).

### 4. UI

Handle every state. Lists get the slots from `@/modules/data-table`: `DataTable` renders skeleton rows
(`loading`), dimmed rows (`fetching`), your `emptyState` node (or a default "No results") and your `error`
node (pass the `Alert` + Retry below as `error={isError ? <Alert …/> : undefined}`). Write it by hand only for
non-table sections:

```tsx
{isPending && <Skeleton className="h-32 rounded-xl" />}                 {/* skeleton shaped like the content */}
{isError && (
  <Alert variant="destructive">
    <i className="ph ph-warning-circle size-4" aria-hidden="true" />
    <AlertTitle>Couldn't load activity</AlertTitle>
    <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
      <span>{getErrorMessage(error)}</span>
      <Button variant="outline" size="sm" onClick={() => void refetch()}>Retry</Button>
    </AlertDescription>
  </Alert>
)}
{data && data.items.length === 0 && (
  <EmptyState icon="users" title="No users yet" description="Invite your first teammate." action={<Button>Invite user</Button>} />
)}
```

`EmptyState` (`src/components/common/EmptyState.tsx`): `icon`, `title`, `description`, `action`, `eyebrow`,
`variant` (`plain` inside a card / `dashed` on its own), `size` (`default` / `compact` / `full`), `titleAs`. Filtered-empty says what to
clear ("No users match "ana" — clear the search"). `StatusScreen` is for route-level / full-screen
states only (404, 403, server unavailable), not for an empty table section.

| Error type | Where | Component |
|---|---|---|
| Query / section failure | inline in the section, with Retry | `Alert variant="destructive"` + `getErrorMessage` + Retry `Button` |
| Empty list / section | in place | `EmptyState` (icon tile + title + hint + primary action) |
| Destructive action confirmation | dialog | `ConfirmDialog` (AlertDialog) — never `confirm()` |
| Form submit failure (non-field) | top of the form | `Alert` (see `LoginForm.tsx`) |
| Field validation | under the field | `<FormMessage />` (react-hook-form + `components/ui/form.tsx`) |
| Mutation result feedback | toast | `toast.success(...)` / `toast.error(getErrorMessage(e))` from `sonner` |
| Render crash | full screen | `ErrorFallback` (global boundary) — wrap risky widgets in their own `<ErrorBoundary>` |
| Route / chunk load failure | full screen | `RouteErrorFallback` / `StatusScreen` |
| No access | in place | `ForbiddenPage` via `RoleGuard`; disable/hide actions with `hasAccess` |

- ❌ Never show raw technical text (`AxiosError: Network Error`, stack traces).
- ❌ Don't use toasts for errors the user must act on — keep them inline until resolved.
- ❌ Never leave a blank area on empty/error, never a bare "No data" line or plain red text.
- ❌ Never `alert()` / `confirm()`; use `toast` (sonner) and `ConfirmDialog`.

Domain-specific copy: map codes in a feature util, like `features/shared/auth/utils/login-errors.ts`
(`ACCOUNT_NOT_VERIFIED` → clear message).

### 5. Business rules

- ✅ Guard clauses; disable/hide forbidden actions up front (`hasAccess(user, { roles, privileges })`).
- ✅ Expect the backend's rule errors and show them meaningfully: 409 `CONFLICT` (duplicate / still referenced —
  `details` names the field), 422 (invalid reference, parent cycle), 400 (`BAD_REQUEST`).
- ❌ Don't duplicate complex server rules client-side as the only enforcement — the backend is authoritative.

### 6. Security

- ✅ Auth is httpOnly cookies — never store, log or read tokens in JS; never add Authorization headers.
- ✅ 401 handling is central (api-client); don't add per-component 401 redirects or `window.location` hacks.
- ✅ Logout / expiry → `useLogout()` / `endClientSession()` (clears store + query cache).
- ✅ Public auth endpoints must be listed in `NO_REFRESH_ENDPOINTS`.
- ❌ Don't log PII/passwords; don't show `requestId`-less raw errors to users (the `requestId` is fine to show for support).

### 7. Concurrency

- ✅ TanStack Query passes an `AbortSignal` to `queryFn` (`({ signal }) => apiRequests.get(url, params, { signal })`);
  cancelled requests reject with code `REQUEST_CANCELLED` — ignore those, don't toast them.
- ✅ Debounce search inputs with `useDebouncedValue` (`src/hooks/use-debounced-value.ts`, 300 ms).
- ✅ Disable submit buttons while `mutation.isPending`; keep previous page with `placeholderData: keepPreviousData`.
- ❌ Don't fire a request per keystroke or rely on response ordering.

### 8. Cleanup

Every `useEffect` that registers something returns a cleanup (listeners, timers, observers, sockets, map
instances). Session-sensitive data goes away via `endClientSession()` — don't keep user data in module
variables or localStorage.

## Quick decision guide

```
Calling the API?                 → service + useQuery/useMutation; let ApiError bubble     [1]
Form submit failed with 422?     → applyApiFieldErrors(error, form.setError, FIELDS)       [2]
Rendering server data?           → isPending / isError(+Retry) / empty / data              [3][4]
Mutation done?                   → toast.success / toast.error(getErrorMessage(error))     [4]
Action not allowed?              → hide/disable via hasAccess; expect 403/409 anyway        [5]
Auth / 401 / logout?             → already central (api-client, guards, useLogout)          [6]
Typing / rapid input?            → useDebouncedValue; disable while pending                 [7]
useEffect registers something?   → return cleanup                                           [8]
```

## Common mistakes

- Never import `useToast` / `@/hooks/use-toast` (not part of this app) — use `import { toast } from 'sonner'`.
- Wrapping service calls in try/catch that returns `{ data: null, error }` — breaks Query error state.
- Checking `error.response?.status` — errors are `ApiError`; use `error.status` / `error.code`.
- Toasting `REQUEST_CANCELLED` errors on unmount/navigation.

> Full rule tables and the pre-submission checklist: `references/error-handling-rules.md`
