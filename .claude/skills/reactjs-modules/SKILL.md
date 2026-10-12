---
name: reactjs-modules
description: Recipe for a generic, domain-agnostic reusable system in apps/web/src/modules/{name}/ (own UI + hooks + optional client store, used by 2+ features) — e.g. the data-table module (src/modules/data-table/, the reference module used by every list), file preview, dynamic filter. Says when to create a module and how. Load before creating, using or extending anything in src/modules/.
---

# Modules (`src/modules/{name}/`)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns module boundaries, public API and data rules.

The reference module is **`src/modules/data-table/`** (TanStack Table + shadcn `Table`). Use it for
every list; copy its shape when you create a new module. Check `ls src/modules` — the code is the
source of truth for what exists and for exact props.

## What is a module

A **domain-agnostic system** with its own UI and logic, reused by 2+ features:

| Belongs in `src/modules/` (create on demand) | Belongs elsewhere |
|---|---|
| Generic data table/list system with paging, sorting, row actions (`data-table`) | Small presentational page pattern → `src/components/common/` (`PageHeader`, `StatCard`, `EmptyState`, `StatusBadge`, `StatusScreen`…) |
| File preview/viewer, dynamic filter builder, widget renderer | Third-party adapter (scroll, chart, map) → `src/components/wrappers/` |
| Anything that knows nothing about users/billing/etc. | Domain-aware logic → `src/features/{domain}/{feature}/` or `features/shared/` |

Create a module only when **all** hold:

- [ ] Used (or about to be used) by 2+ features
- [ ] Has behavior beyond markup (state, data orchestration, interaction logic)
- [ ] Contains no domain vocabulary — data and actions come in through props/generics

## Structure

```
src/modules/{name}/
├── {Name}.tsx              ← root component (if the module has UI)
├── parts/                  ← internal sub-components (not exported)
├── hooks/                  ← use{Name}.ts — logic/state hooks
├── store/                  ← use{Name}Store.ts — ONLY for client/UI state shared inside the module
├── types/                  ← {name}.types.ts
├── utils/                  ← pure helpers (+ tests)
└── index.ts                ← public API — the only import path for consumers
```

Naming: folder `kebab-case`; component `PascalCase.tsx`; hook `use{Name}.ts`; store
`use{Name}Store.ts`; types `{name}.types.ts`.

## Data rules

- **Server data is not fetched or cached by a Zustand store.** A module either:
  - receives data from the caller (preferred: the feature runs `useQuery` with its own
    service + query keys and passes `{ items, pagination }`, `isPending`, `error` in), or
  - takes a fetcher + query key as props and calls `useQuery` itself.
- Errors are `ApiError` (`@/services/api-error`); show them with `getErrorMessage(error)`.
- Notifications via `toast` from `sonner`.
- Lists follow the backend contract: request `FindDTO` (`page`, `size`, `search`, `searchBy`,
  `orderBy`, `order`, `filters: FilterItem[]` — `@/types/api`), response
  `ApiList<T> = { items, pagination: { page, size, totalElements, totalPages } }`.
- Bounded scroll regions use `PerfectScrollArea`. Tables never get rebuilt per module or feature —
  compose `@/modules/data-table`.
- UI inside a module is built from `src/components/ui/*` primitives and `src/components/common/*`
  patterns, with semantic token classes only (`bg-card`, `text-muted-foreground`, `border-border`,
  `rounded-md` controls / `rounded-xl` surfaces). Every async surface ships loading (skeleton),
  empty (`EmptyState`) and error (`Alert variant="destructive"` + Retry) states.

## Reference module — `src/modules/data-table/`

```
src/modules/data-table/
├── components/
│   ├── DataTable.tsx              ← root: toolbar → shadcn Table → pagination inside one rounded-xl card; skeleton rows (`loading`), dimmed rows (`fetching`), `emptyState`, `error` slots; server sort/pagination
│   ├── DataTableToolbar.tsx       ← search InputGroup (ph-magnifying-glass + clear, sm:max-w-xs) + `filters` slot + `actions` slot
│   ├── DataTableColumnHeader.tsx  ← sortable header button (asc → desc → default, arrow icons); DataTable sets aria-sort
│   ├── DataTablePagination.tsx    ← "Showing 1–10 of 42" · rows-per-page Select · page x of y · first/prev/next/last
│   └── DataTableRowActions.tsx    ← ph-dots-three DropdownMenu built from `DataTableRowAction[]`
├── types.ts                       ← DataTablePaginationState, DataTableSort, DataTableRowAction
├── utils.ts                       ← toSortingState / fromSortingState / getPageRange
└── index.ts                       ← public API
```

Consumer — the feature owns the query, columns and actions; the module only renders:

```tsx
// src/features/administrator/role/config/role-table.config.tsx
export const ROLE_COLUMNS: ColumnDef<Role, unknown>[] = [
  // sortable: column id = backend sortable field (camelCase) → becomes FindDTO `orderBy`
  { id: 'name', accessorKey: 'name', enableSorting: true, header: ({ column }) => <DataTableColumnHeader column={column} title="Name" /> },
  { id: 'status', accessorKey: 'status', header: 'Status', cell: ({ row }) => <StatusBadge tone="success">{row.original.status}</StatusBadge> },
  { id: 'actions', header: () => <span className="sr-only">Actions</span>, cell: ({ row }) => <RoleRowActions role={row.original} />, meta: { className: 'w-12 text-right' } }, // wraps DataTableRowActions
]

// src/features/administrator/role/components/RoleListView.tsx
import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { DataTable, DataTableToolbar } from '@/modules/data-table'
import { getErrorMessage } from '@/services/api-error'

const { query, search, setSearch, sort, setSort, setPage, setPageSize } = useRoleListQuery()
const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useRoleList(query) // useQuery + roleService.getAll

return (
  <div className="flex flex-col gap-6">
    <PageHeader title="Roles" description="Catalogue of roles." actions={<Button><i className="ph ph-plus" aria-hidden="true" />Add role</Button>} />
    <DataTable
      caption="Roles"
      columns={ROLE_COLUMNS}
      data={data?.items}
      getRowId={(row) => row.id}
      loading={isPending}
      fetching={isFetching && isPlaceholderData}
      pagination={data?.pagination}
      onPageChange={setPage}
      onPageSizeChange={setPageSize}
      sort={sort}
      onSortChange={setSort}
      toolbar={<DataTableToolbar searchValue={search} onSearchChange={setSearch} searchPlaceholder="Search roles…" />}
      error={
        isError ? (
          <Alert variant="destructive">
            <i className="ph ph-warning-circle" aria-hidden="true" />
            <AlertTitle>Couldn&apos;t load roles</AlertTitle>
            <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
              <span>{getErrorMessage(error)}</span>
              <Button variant="outline" size="sm" onClick={() => void refetch()}>Try again</Button>
            </AlertDescription>
          </Alert>
        ) : undefined
      }
      emptyState={<EmptyState icon="shield" title="No roles yet" description="Create the first role." />}
    />
  </div>
)
```

The full API is in `src/modules/data-table/index.ts`; the working reference consumer is
`src/features/administrator/user/` (`UserListView.tsx`, `config/user-table.config.tsx`, `UserRowActions.tsx`).
Visual details (header row `bg-muted/50`, row height, hover, pagination footer) follow
`reactjs-ui-design` §5.3; `.claude/skills/reactjs-data-display/SKILL.md` covers list UX
(search, filters, URL state). `.claude/skills/reactjs-dynamic-filter/SKILL.md` describes the
filter module recipe.

## Rules

- MUST import a module only through its barrel: `@/modules/{name}`.
- MUST keep modules domain-agnostic (no `userService`, no `/administrator` paths inside).
- MUST NOT duplicate server state in a module store; MUST NOT make the store a singleton that
  breaks when two instances render on one page (prefer props/hook-local state).
- MUST NOT import from `src/features/**` or `src/pages/**` inside a module.
- When a module is added, mention it in `apps/web/AI_GUIDE.md` (owner: docs) so agents find it.

## Checklist

- [ ] The three "create a module" conditions hold
- [ ] `src/modules/{name}/index.ts` exports the public API only
- [ ] Data/actions come from props or a passed fetcher; errors handled as `ApiError`
- [ ] Generic types (`<T>`), no domain names
- [ ] Built from shadcn primitives + `components/common` patterns; loading/empty/error states; light + dark
- [ ] Rendered on the `/ui-kit` page and reviewed with `npm run ui:snapshot` (see `reactjs-ui-design` §8)
- [ ] Unit tests for `utils/` and a render test for the root component (`src/test/render.tsx`)
- [ ] `npm run typecheck && npm run lint && npm run test:ci` (apps/web) pass
