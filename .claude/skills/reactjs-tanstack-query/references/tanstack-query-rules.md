# TanStack Query — Rules & Constraints

## Allowed

### Query Setup

| # | Rule |
|---|------|
| ✅ | Use the existing singleton `queryClient` (`src/lib/query-client.ts`), provided in `AppProviders` — never create another one in app code |
| ✅ | Override `staleTime` / `retry` per query only with a reason (globals: 60 s stale, 5 min gc, `shouldRetryQuery`) |
| ✅ | Outside React, import `queryClient` from `@/lib/query-client` |
| ✅ | Wrap each resource's query logic in a dedicated hook calling a service (e.g. `useUserList` → `userService.getAll`) |
| ✅ | Place query hooks under `src/features/{domain}/{feature}/hooks/`; key factories in the feature's `constants/` |

### QueryKey

| # | Rule |
|---|------|
| ✅ | Always use array queryKeys — single string keys are forbidden |
| ✅ | Include every variable the `queryFn` depends on inside the key |
| ✅ | Use an object literal `{}` for filter/param groups so TanStack can deep-compare |
| ✅ | Include the memoized FindDTO (or, once the dynamic-filter module exists, `useResolvedFilterParams(widgetId)`) in the queryKey |

### Mutations

| # | Rule |
|---|------|
| ✅ | Use `useMutation` for all create / update / delete operations |
| ✅ | Invalidate queries in `onSuccess` — not in component event handlers |
| ✅ | Use `onError` to show `toast.error(getErrorMessage(error))` (sonner) and roll back optimistic updates |
| ✅ | Use `onMutate` + `onSettled` for optimistic updates — always cancel in-flight queries first |

### Cache Invalidation

| # | Rule |
|---|------|
| ✅ | Invalidate by the narrowest queryKey prefix possible |
| ✅ | After creating/deleting an item, invalidate the resource prefix (e.g. `USER_QUERY_KEYS.all`) |
| ✅ | After updating an item, invalidate the resource prefix (covers list + detail) |

---

## Forbidden

| # | Rule |
|---|------|
| ❌ | Do not store API response data in Zustand — use TanStack Query cache |
| ❌ | Do not manage `isLoading` / `isError` with `useState` alongside `useQuery` |
| ❌ | Do not call `queryClient.invalidateQueries({})` (no key) — it flushes the entire cache |
| ❌ | Do not put mutation side effects (invalidation, toast) inside the component — use callbacks |
| ❌ | Do not skip the queryKey variable when the `queryFn` depends on a param |
| ❌ | Do not retry or toast 4xx / `REQUEST_CANCELLED` errors |
| ❌ | Do not import a `use-toast` hook (not part of this app) — use `sonner` |
| ❌ | Do not fetch data in `useEffect` + `useState` when `useQuery` covers the same use case |
| ❌ | Do not use `enabled: false` to block a query permanently — gate on a meaningful condition |

---

## Verification

Code is considered complete when **all** of the following are true:

### useQuery

- [ ] QueryKey is an array and includes all variables the queryFn uses
- [ ] `isPending`, `isError` (with Retry) and empty states are handled in the component
- [ ] No `useState` duplicates the loading/error/data state
- [ ] The FindDTO / filter params are memoized and included in the queryKey

### useMutation

- [ ] `onSuccess` calls `queryClient.invalidateQueries` with the correct key prefix
- [ ] `onError` shows user-facing feedback (toast or inline message)
- [ ] `isPending` is used to disable the submit button
- [ ] Side effects are in mutation callbacks, not in component handlers

### useInfiniteQuery

- [ ] `initialPageParam` is set
- [ ] `getNextPageParam` uses `pagination.page < pagination.totalPages` and returns `undefined` at the end
- [ ] Results are flattened with `pages.flatMap(p => p.items)`

### General

- [ ] No new `QueryClient` created in app code
- [ ] No API response data is stored in Zustand
