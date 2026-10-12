---
name: reactjs-features
description: Scaffold or extend a business feature under apps/web/src/features/{domain}/{feature}/ (components, hooks with TanStack Query, constants/query keys, config, schemas, utils, optional Zustand store, index.ts barrel). Covers choosing the domain bucket (domain vs shared vs src/modules, which you create on demand), the real reference features (administrator/user, dashboard/overview, shared/auth), and wiring the page/route/menu. Load before creating any domain component, hook or feature folder.
---

# Scaffolding a Feature

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns feature folders, buckets, data flow and barrels.

A feature is a self-contained business unit. Real ones in the boilerplate:

```
src/features/
├── administrator/user/      ← admin user list (TanStack Query + table config)
│   ├── components/  UserListView.tsx, UserTable.tsx, UserStatusBadge.tsx
│   ├── config/      user-table.config.tsx      (ColumnDef<UserDetail>[])
│   ├── constants/   user.constants.ts          (USER_QUERY_KEYS, page size, search fields, badge map)
│   ├── hooks/       useUserList.ts (useQuery), useUserListQuery.ts (search/page → FindDTO)
│   └── index.ts
├── dashboard/overview/      ← dashboard cards
│   ├── components/  DashboardOverview.tsx, AccountSummaryCard.tsx, GettingStartedCard.tsx
│   ├── constants/   overview.constants.ts
│   └── index.ts
└── shared/auth/             ← login, 2FA, verify-email, session, access helpers (used by routes, layouts, pages)
    ├── components/ constants/ hooks/ schemas/ utils/
    └── index.ts
```

Copy the `administrator/user` shape for list-style features and `shared/auth` for form flows.

## Step 1 — Pick the bucket

| Condition | Where |
|---|---|
| Belongs to one business domain (one or more pages of that domain) | `features/{domain}/{feature}/` |
| Domain-aware but used by 2+ unrelated domains (auth, notifications) | `features/shared/{feature}/` |
| Shared by 2+ features of the same domain | `features/{domain}/components/` (domain root) |
| Generic, domain-agnostic system (data table system, file preview) | `src/modules/{name}/` — see `.claude/skills/reactjs-modules/SKILL.md` |
| Domain-agnostic page pattern (`PageHeader`, `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`, `ConfirmDialog`) | `src/components/common/` — reuse, don't re-create inside a feature |
| Any list/table | compose `@/modules/data-table` with feature-owned columns in `config/` |

Always nest under a domain or `shared/` — never `src/features/{feature}/` flat. Page folders
contain only the `{Name}Page.tsx` file; everything else lives in the feature.

## Step 2 — Scaffold (only folders you need)

```
src/features/{domain}/{feature}/
├── components/   ← PascalCase.tsx, one component each, presentational + hook calls
├── hooks/        ← useXxx.ts: TanStack Query hooks, view-state hooks
├── constants/    ← {feature}.constants.ts: query-key factory, labels, page size
├── config/       ← {feature}-table.config.tsx, chart/filter config
├── schemas/      ← {name}.schema.ts (zod 4) + z.infer form types
├── utils/        ← pure helpers for this feature (+ *.test.ts)
├── types/        ← {feature}.types.ts if types are feature-local
├── store/        ← use{Name}Store.ts only if several components share client state
└── index.ts      ← public API
```

Server data does **not** go in a Zustand store — TanStack Query owns it (see
`.claude/skills/reactjs-tanstack-query/SKILL.md`). Stores are for client/UI state only.

## Step 3 — Implement (real pattern)

### Service (in `src/services/`, not in the feature)

Most resources already have one: `userService`, `permissionService`, `groupService`,
`roleService`, `uploadService`, `authService`. New backend resource → create
`src/services/{resource}.service.ts` with `createResourceService<T, TCreate, TUpdate>(API_ENDPOINTS.X.BASE)`
(see `.claude/skills/reactjs-service/SKILL.md`). Services return unwrapped data
(`T` or `{ items, pagination }`) and reject with `ApiError`.

### Constants (query keys)

```ts
// features/administrator/user/constants/user.constants.ts (real)
export const USER_QUERY_KEYS = {
  all: ['users'] as const,
  list: (query: object) => ['users', 'list', query] as const,
}
export const USER_LIST_PAGE_SIZE = 10
export const USER_SEARCH_FIELDS = ['username', 'fullname', 'email'] as const
```

### Query hook

```ts
// features/administrator/user/hooks/useUserList.ts (real)
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { userService } from '@/services/user.service'
import type { FindDTO } from '@/types/api'

import { USER_QUERY_KEYS } from '../constants/user.constants'

export function useUserList(query: FindDTO) {
  return useQuery({
    queryKey: USER_QUERY_KEYS.list(query),
    queryFn: () => userService.getAll(query),
    placeholderData: keepPreviousData,
  })
}
```

### Mutation hook (example: upload a file)

```ts
// features/{domain}/{feature}/hooks/useUploadFile.ts  — example; create in your feature
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { toast } from 'sonner'

import { getErrorMessage } from '@/services/api-error'
import { uploadService, type IUploadOptions } from '@/services/upload.service'

export function useUploadFile() {
  const queryClient = useQueryClient()
  const [progress, setProgress] = useState(0)
  const mutation = useMutation({
    mutationFn: ({ file, options }: { file: File; options?: IUploadOptions }) =>
      uploadService.uploadFile(file, options, setProgress),
    onSuccess: (upload) => {
      toast.success(`${upload.filename} uploaded`)
      void queryClient.invalidateQueries({ queryKey: ['uploads'] })
    },
    onError: (error) => toast.error(getErrorMessage(error)),
    onSettled: () => setProgress(0),
  })
  return { ...mutation, progress }
}
```

### Component

Feature components compose shadcn primitives (`src/components/ui`), page patterns
(`src/components/common`) and `@/modules/data-table`; they do not hand-roll tables, dropdowns,
dialogs or empty states.

```tsx
// features/administrator/user/components/UserListView.tsx (trimmed from the real file)
export function UserListView() {
  const { query, search, setSearch, sort, setSort, setPage, setPageSize } = useUserListQuery()
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useUserList(query)
  const columns = useMemo(() => getUserColumns(currentUserId), [currentUserId])
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Users" description="Manage who can sign in and what they can access." actions={<CreateUserDialog />} />
      <DataTable
        caption="Users"
        columns={columns}
        data={data?.items}
        loading={isPending}
        fetching={isFetching && isPlaceholderData}
        pagination={data?.pagination}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        sort={sort}
        onSortChange={setSort}
        toolbar={<DataTableToolbar searchValue={search} onSearchChange={setSearch} searchPlaceholder="Search name, username or email…" />}
        error={isError ? <Alert variant="destructive">…{getErrorMessage(error)} + Try again (refetch)…</Alert> : undefined}
        emptyState={<EmptyState icon="users" title="No users yet" description="Create the first account to give someone access." />}
      />
    </div>
  )
}
```

States: skeleton rows while `loading`, the `emptyState` node when there are no rows, the `error` node
(`Alert variant="destructive"` + Retry) in place of the rows (see `reactjs-ui-design` §5.7). The full
file is `src/features/administrator/user/components/UserListView.tsx`; the API is
`src/modules/data-table/index.ts`.

### Barrel

```ts
// features/administrator/user/index.ts (real)
export { UserListView } from './components/UserListView'
export { USER_QUERY_KEYS } from './constants/user.constants'
export { useUserList } from './hooks/useUserList'
```

Export only what other folders need. Pages, routes and layouts import
`@/features/{domain}/{feature}` — never internal paths.

## Step 4 — Page, route, menu

If the feature is a screen:

1. `src/pages/{area}/{Name}Page.tsx` renders the feature's view (default export).
2. Lazy route in `src/routes/main.routes.tsx` (or `admin.routes.tsx` for `/administrator/*`).
3. Menu entry in `src/config/menu/*.menu.ts` unless the task says the route is hidden.

See `.claude/skills/reactjs-app-layout/SKILL.md`; for admin CRUD screens follow
`.claude/skills/reactjs-administrator/SKILL.md`.

## Rules

- ✅ Decide the bucket first; nest under `{domain}/` or `shared/`.
- ✅ Fetching only through services + TanStack Query hooks in `hooks/`; components never call axios/services directly.
- ✅ Errors: `getErrorMessage(error)` / `toApiError(error)` from `@/services/api-error`; toasts via `sonner`.
- ✅ Forms: zod schema in `schemas/`, react-hook-form + `components/ui/form.tsx`, 422 mapping with `applyApiFieldErrors` (see `.claude/skills/reactjs-form/SKILL.md`).
- ✅ Bounded scroll regions inside feature UI use `PerfectScrollArea`.
- ✅ Co-locate tests (`*.test.ts(x)`) and use helpers in `src/test/` (`render.tsx`, `axios-mock.ts`).
- ❌ No helpers/types/constants/config declared inside `.tsx` component files.
- ❌ No cross-imports between domain features (`features/billing/…` → `features/dashboard/…`); share via `features/shared/`, `src/stores/`, or a module.
- ❌ No server data copied into Zustand stores.
- ❌ No feature code in `src/components/` or `src/pages/{page}/` subfolders.

## Checklist

- [ ] Bucket chosen; folder `kebab-case` under `features/{domain}/` or `features/shared/`
- [ ] `index.ts` barrel lists the public API; consumers import only the barrel
- [ ] Query keys in `constants/`, query/mutation hooks in `hooks/`
- [ ] Types from `@/types/models` / `@/types/api` reused; feature-only types in `types/`
- [ ] Route + menu wired if the feature is a screen
- [ ] UI built from shadcn primitives + `components/common` + `modules/data-table`; reviewed with `npm run ui:snapshot` (`reactjs-ui-design` §8)
- [ ] `npm run typecheck && npm run lint && npm run test:ci` (apps/web) pass
