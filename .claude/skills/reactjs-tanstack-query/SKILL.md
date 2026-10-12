---
name: reactjs-tanstack-query
description: Fetch and cache backend data in apps/web with TanStack Query v5 — the shared queryClient (src/lib/query-client.ts), query-key factories, useQuery over service calls (FindDTO → ApiList), useMutation with invalidation and sonner toasts, keepPreviousData pagination, useInfiniteQuery from ApiPagination, optimistic updates, and dynamic-filter integration.
---

# TanStack Query (server state)

TanStack Query owns **all** backend data: loading, error (`ApiError`), caching, refetch, invalidation.
Never copy API data into Zustand or `useState`.

| Need | Use |
|------|-----|
| Read | `useQuery` |
| Create / update / delete | `useMutation` |
| Paged list, keep old page while loading | `useQuery` + `placeholderData: keepPreviousData` |
| Infinite feed | `useInfiniteQuery` |
| Refresh after a write | `queryClient.invalidateQueries({ queryKey })` |
| Outside React | `import { queryClient } from '@/lib/query-client'` |

## Setup (already done — don't duplicate)

- `src/lib/query-client.ts` exports the singleton `queryClient`: `staleTime` 60 s, `gcTime` 5 min,
  `refetchOnWindowFocus: false`, `retry: shouldRetryQuery` (1 retry, only for network / 429 / 5xx — never 4xx),
  mutations `retry: false`.
- `QueryClientProvider` is mounted in `src/components/wrappers/AppProviders.tsx`.
- `endClientSession()` (logout / failed refresh) calls `queryClient.clear()` so no user data survives a session.

Do not create another `QueryClient` (tests use their own via `src/test/render.tsx`).

## Query keys — factories per feature

Keys live in the feature's constants file (real: `features/administrator/user/constants/user.constants.ts`,
`features/shared/auth/constants/auth.constants.ts`):

```ts
export const USER_QUERY_KEYS = {
  all: ['users'] as const,
  list: (query: object) => ['users', 'list', query] as const,
}
// add as needed: detail: (id: string) => ['users', 'detail', id] as const
```

- Include every variable the `queryFn` uses (the whole FindDTO for lists).
- The FindDTO object must be memoized (`useMemo`) — see `useUserListQuery.ts`.
- Invalidate by prefix: `USER_QUERY_KEYS.all` refreshes lists and details of that resource.

## queryFn — call a service

Hooks call the service layer (`src/services/*.service.ts`, see `.claude/skills/reactjs-service/SKILL.md`),
which returns unwrapped data and rejects with `ApiError`.

```ts
// features/administrator/user/hooks/useUserList.ts (real)
export function useUserList(query: FindDTO) {
  return useQuery({
    queryKey: USER_QUERY_KEYS.list(query),
    queryFn: () => userService.getAll(query),     // → ApiList<UserDetail> = { items, pagination }
    placeholderData: keepPreviousData,
  })
}

// detail
export function useGroup(id: string | undefined) {
  return useQuery({
    queryKey: ['groups', 'detail', id],
    queryFn: () => groupService.getOne({ id: id! }),
    enabled: !!id,
  })
}
```

For one-off endpoints without a service method, `apiRequests.get/post/list` with an `API_ENDPOINTS` constant is
fine. To forward cancellation: `queryFn: ({ signal }) => apiRequests.get<T>(url, params, { signal })`.

## Consuming in a component

```tsx
const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useUserList(query)

// Tables: hand the query state to DataTable (@/modules/data-table) — it renders skeleton / error / empty / pagination.
return (
  <DataTable
    columns={columns}
    data={data?.items}
    loading={isPending}
    fetching={isFetching && isPlaceholderData}
    pagination={data?.pagination}
    onPageChange={setPage}
    error={isError ? <Alert variant="destructive">{getErrorMessage(error)} <Button variant="outline" size="sm" onClick={() => void refetch()}>Try again</Button></Alert> : undefined}
    emptyState={<EmptyState icon="users" title="No users yet" />}
  />
)

// Non-table surfaces branch on the query state themselves:
if (isPending) return <LoadingState label="Loading users…" />
if (isError) return <Alert variant="destructive">{getErrorMessage(error)} <Button variant="outline" size="sm" onClick={() => void refetch()}>Try again</Button></Alert>
if (data.items.length === 0) return <EmptyState icon="users" title="No users yet" variant="dashed" />
```

Full table example: `src/features/administrator/user/components/UserListView.tsx`.

`isPending` = no data yet (v5 naming; `isLoading` = pending **and** fetching). `error` is an `ApiError`.

## Mutations

```ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { getErrorMessage } from '@/services/api-error'
import { groupService, type IGroupCreatePayload } from '@/services/group.service'

export function useCreateGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: IGroupCreatePayload) => groupService.add(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['groups'] })
      toast.success('Group created')
    },
    onError: (error) => toast.error(getErrorMessage(error)),
  })
}

export function useDeleteGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => groupService.delete({ id }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['groups'] }),
    onError: (error) => toast.error(getErrorMessage(error)),   // e.g. 409 "Group is assigned to 3 user(s)"
  })
}
```

Forms: when a mutation backs a form, map 422 field errors with `applyApiFieldErrors(error, form.setError, FIELDS)`
in the submit handler's `onError` (see `LoginForm.tsx`) and show the rest in an `Alert`; disable submit with
`mutation.isPending`. Updates use `service.update({ id, ...changedFields })` (PATCH semantics).

## Infinite lists (from `ApiPagination`)

```ts
export function useInfiniteUploads(query: Omit<FindDTO, 'page'>) {
  return useInfiniteQuery({
    queryKey: ['uploads', 'infinite', query],
    initialPageParam: 1,
    queryFn: ({ pageParam }) => uploadService.getAll({ ...query, page: pageParam, size: 20 }),
    getNextPageParam: (last) => (last.pagination.page < last.pagination.totalPages ? last.pagination.page + 1 : undefined),
  })
}
// rows: data?.pages.flatMap((p) => p.items) ?? []
```

Trigger `fetchNextPage()` from a "Load more" button or `PerfectScrollArea`'s `onYReachEnd`
(guard `hasNextPage && !isFetchingNextPage`).

## Optimistic update

```ts
useMutation({
  mutationFn: (changes: IGroupUpdatePayload) => groupService.update(changes),
  onMutate: async (changes) => {
    const key = ['groups', 'detail', changes.id]
    await queryClient.cancelQueries({ queryKey: key })
    const previous = queryClient.getQueryData<Group>(key)
    queryClient.setQueryData<Group>(key, (old) => (old ? { ...old, ...changes } : old))
    return { previous, key }
  },
  onError: (error, _vars, ctx) => {
    if (ctx) queryClient.setQueryData(ctx.key, ctx.previous)
    toast.error(getErrorMessage(error))
  },
  onSettled: () => void queryClient.invalidateQueries({ queryKey: ['groups'] }),
})
```

## Dynamic filter integration

Only once `src/modules/dynamic-filter/` exists (not present in the boilerplate yet — see
`.claude/skills/reactjs-dynamic-filter/SKILL.md`): put `useResolvedFilterParams(widgetId)` (or the FindDTO built from
it) in the query key so filter changes refetch automatically.

## File placement

```
src/features/<domain>/<feature>/
├── constants/<feature>.constants.ts   ← <FEATURE>_QUERY_KEYS
└── hooks/
    ├── use<Resource>List.ts           ← useQuery (list)
    ├── use<Resource>.ts               ← useQuery (detail)
    └── useCreate<Resource>.ts / useUpdate… / useDelete…   ← useMutation
```

## Quick rules

| Rule | Value |
|------|-------|
| Loading / error state | from the query — never duplicated in `useState` |
| API data storage | Query cache — never Zustand |
| Keys | array factories per feature; include every queryFn input |
| Invalidation | narrowest prefix; never `invalidateQueries()` without a key |
| Toasts | `toast` from `sonner` in mutation callbacks |
| Errors | `ApiError` → `getErrorMessage(error)`; 4xx are not retried |
| Pagination | `keepPreviousData`; read `pagination.totalElements / totalPages` |

> Rules & checklist: `references/tanstack-query-rules.md`
