# Error Handling — Rules & Constraints (apps/web)

Companion to `../SKILL.md`. Every rule assumes the real API layer: services reject with `ApiError`
(`src/services/api-error.ts`), server state is TanStack Query, toasts are `sonner`, crashes are caught by
react-error-boundary.

## 1. Exception handling

| ✅ Allowed | ❌ Not allowed |
|---|---|
| Let services reject; read `error` from `useQuery` / `useMutation` | `try/catch` inside services, or returning `{ data: null, error }` wrappers |
| `catch (error)` → `toApiError(error)` / `isApiError(error)` before property access | `catch (error: any)`, reading `error.response?.data` (axios shape is gone after the interceptor) |
| Branch on `error.code` (`CONFLICT`, `VALIDATION_ERROR`, `ACCOUNT_NOT_VERIFIED`…) or `error.status` | Branching on message strings |
| Local `<ErrorBoundary FallbackComponent={…}>` (react-error-boundary) around risky widgets (charts, maps) | A second global boundary or custom class boundary per page |
| `console.error` guarded by `env.app.isDev` | Empty catch blocks; `console.log(error)` in production paths |

## 2. Validation

| ✅ | ❌ |
|---|---|
| zod 4 schemas + `zodResolver` for every form | Hand-written `if (!email.includes('@'))` checks in handlers |
| Backend 422 → `applyApiFieldErrors(error, form.setError, FIELDS)` + generic `Alert` for the rest | Ignoring `error.fieldErrors` and showing only "Validation error" |
| zod-validate untrusted input (URL params, localStorage, third-party JSON) | `as T` casts on untrusted data |
| Env vars only via `src/config/env.ts` (validated) | `import.meta.env.X` in components |

## 3. State

| ✅ | ❌ |
|---|---|
| TanStack Query flags: `isPending`, `isError`, `isFetching`, `isPlaceholderData` | Parallel `useState` loading/error flags for server data |
| Optimistic updates with `onMutate` snapshot + `onError` rollback + `onSettled` invalidate | Optimistic updates without rollback |
| `keepPreviousData` for paginated lists | Flashing an empty table between pages |

## 4. UI

| ✅ | ❌ |
|---|---|
| Inline `Alert variant="destructive"` with `getErrorMessage(error)` + Retry for failed sections | Raw technical messages, stack traces |
| `EmptyState` (from `components/common`) for empty lists/sections, different copy when filtered/searched; `StatusScreen` only for route-level screens | Blank areas, bare "No data" text |
| `toast.success/error` (sonner) for mutation feedback | Toasts for errors the user must act on |
| `Skeleton` shaped like the content while `isPending` (`LoadingState` for route-level loads) | Page spinners for section loads; spinners that never resolve on error |
| `FormMessage` under fields for field errors | Field errors only in a toast |

## 5. Business rules

| ✅ | ❌ |
|---|---|
| Guard clauses; hide/disable actions with `hasAccess(user, { roles, privileges })` | Letting users click into a guaranteed 403 |
| Show 409 `CONFLICT` details (which field / what references it) | Treating 409 as a generic failure |
| Backend is the authority; client checks are UX | Client-only enforcement of permissions |

## 6. Security

| ✅ | ❌ |
|---|---|
| httpOnly cookie session; `withCredentials` already set | Storing tokens in localStorage/zustand; adding Authorization headers |
| Central 401 refresh/redirect in `api-client.ts`; logout via `useLogout()` | Per-component 401 redirects, `window.location.href = '/auth/login'` |
| Public auth endpoints in `NO_REFRESH_ENDPOINTS` | Refresh loops on bad credentials |
| `getSafeRedirect` / `buildLoginPath` for redirects | Redirecting to an unvalidated `?redirect=` value |
| `svg-code` icons only from trusted constants | `dangerouslySetInnerHTML` with API/user content |

## 7. Concurrency

| ✅ | ❌ |
|---|---|
| Pass the Query `signal` through `apiRequests` options; ignore `REQUEST_CANCELLED` | Toasting cancelled requests |
| `useDebouncedValue` (300 ms) for search inputs | A request per keystroke |
| Disable submit while `isPending` | Double submissions |

## 8. Cleanup

Every effect that registers a listener/timer/observer/socket/map instance returns a cleanup. Session data is
cleared by `endClientSession()` (store + `queryClient.clear()`).

## Pre-submission checklist

- [ ] No try/catch or error swallowing in services; components use Query error state
- [ ] Errors narrowed via `toApiError` / `isApiError`; branching on `code`/`status`
- [ ] Every data view: loading, error + Retry, empty, data
- [ ] Forms: zod schema + `applyApiFieldErrors` for 422
- [ ] Mutations: sonner toast on success/failure; buttons disabled while pending
- [ ] Risky widgets wrapped in a local `ErrorBoundary`
- [ ] No token handling, no per-component 401 logic, no raw technical messages
- [ ] Effects clean up everything they register
