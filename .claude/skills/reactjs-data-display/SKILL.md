---
name: reactjs-data-display
description: Use when rendering server data as lists, tables, card grids or infinite feeds in apps/web. Explains the list data flow (feature hook + useQuery + FindDTO → ApiList) and how to render it with the shared DataTable module at src/modules/data-table/ (DataTable, DataTableToolbar, DataTableColumnHeader, DataTablePagination, DataTableRowActions — TanStack Table + shadcn Table with skeleton rows and empty state), plus card grids and infinite feeds. Trigger: list, table, grid, cards, scroll, pagination.
---

# Skill: Rendering Server Data (lists, tables, feeds)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md` win over any markup here. This skill owns the list data flow (FindDTO, query keys, pagination, infinite loading) and how to use `src/modules/data-table/`.

## Building blocks

| Piece | Where | Role |
|---|---|---|
| `DataTable` | `src/modules/data-table/` | TanStack Table (`@tanstack/react-table`) rendered with shadcn `Table` inside one `rounded-xl` card. Props: `columns`, `data`, `loading` (skeleton rows), `fetching` (dimmed rows), `emptyState`, `toolbar`, `error` (ReactNodes), `pagination` + `onPageChange` (+ `onPageSizeChange`, `pageSizeOptions`) — renders `DataTablePagination` itself, `sort` + `onSortChange` (server sort), `getRowId`, `skeletonRows`, `caption`, `className` |
| `DataTableToolbar` | `src/modules/data-table/` | Search `InputGroup` (`ph-magnifying-glass` + clear button, `sm:max-w-xs`). Props: `searchValue`, `onSearchChange`, `searchPlaceholder`, `filters` (slot), `actions` (right slot), `className` |
| `DataTableColumnHeader` | `src/modules/data-table/` | Sortable header button (`column`, `title`, `className`); cycles asc → desc → default; maps to `FindDTO.orderBy` / `order` via `DataTable` `sort`/`onSortChange` |
| `DataTablePagination` | `src/modules/data-table/` | Footer driven by `ApiList.pagination`: "Showing 1–10 of 42" · rows-per-page `Select` · page x of y · first/prev/next/last. Props: `pagination`, `onPageChange`, `onPageSizeChange`, `pageSizeOptions`, `disabled`, `className`. Use it standalone only outside `DataTable` (card grids, feeds) |
| `DataTableRowActions` | `src/modules/data-table/` | `DropdownMenu` on a `ph-dots-three` icon button. Props: `actions: DataTableRowAction[]` (`{ label, icon?, onSelect, variant?: 'default' \| 'destructive', disabled?, separatorBefore? }`), `label` (trigger `aria-label`) |
| `StatusBadge`, `EmptyState`, `ConfirmDialog` | `src/components/common/` | Status cells, empty states, delete confirmation |
| `PerfectScrollArea` | `src/components/wrappers/` | Bounded scroll regions (feeds, side lists) |

The module's `index.ts` is its public API — import only from `@/modules/data-table`. The working reference is
`src/features/administrator/user/` (`UserListView.tsx`, `config/user-table.config.tsx`, `UserRowActions.tsx`).

---

## Pattern A — server-paginated table (default)

```
features/<domain>/<feature>/
├── constants/<feature>.constants.ts   ← QUERY_KEYS, page size, SEARCH_FIELDS, status → StatusBadge tone map
├── hooks/use<Feature>ListQuery.ts     ← useState page/size/search/filters/sort → useMemo<FindDTO>
├── hooks/use<Feature>List.ts          ← useQuery({ queryKey: KEYS.list(query), queryFn: () => service.getAll(query), placeholderData: keepPreviousData })
├── config/<feature>-table.config.tsx  ← ColumnDef<Entity>[] (JSX cells → .tsx)
└── components/<Feature>ListView.tsx   ← PageHeader + DataTable (toolbar / error / emptyState slots; pagination footer built in)
```

Copy the query hooks from `src/features/administrator/user/` (`useUserListQuery`, `useUserList`).

```tsx
// components/<Feature>ListView.tsx
const { query, search, setSearch, sort, setSort, setPage, setPageSize } = useGroupListQuery()
const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useGroupList(query)

<DataTable
  caption="Groups"
  columns={GROUP_COLUMNS}
  data={data?.items}
  getRowId={(row) => row.id}
  loading={isPending}                                // first load → skeleton rows
  fetching={isFetching && isPlaceholderData}         // page/search change → dimmed rows, aria-busy
  pagination={data?.pagination}                      // footer shows when pagination + onPageChange are set
  onPageChange={setPage}
  onPageSizeChange={setPageSize}
  sort={sort}                                        // { orderBy, order } | null
  onSortChange={setSort}
  toolbar={<DataTableToolbar searchValue={search} onSearchChange={setSearch} searchPlaceholder="Search groups…" />}
  error={
    isError ? (
      <Alert variant="destructive">
        <i className="ph ph-warning-circle" aria-hidden="true" />
        <AlertTitle>Couldn&apos;t load groups</AlertTitle>
        <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
          <span>{getErrorMessage(error)}</span>
          <Button variant="outline" size="sm" onClick={() => void refetch()}>Try again</Button>
        </AlertDescription>
      </Alert>
    ) : undefined
  }
  emptyState={<EmptyState icon="users-three" title="No groups yet" description="Create a group to organise users." />}
/>
```

`error` and `emptyState` are ReactNodes rendered inside the table card (there is no `onRetry` prop — put the
Retry button in the `Alert`). Never leave a blank area or plain red text.

### Columns (`config/<feature>-table.config.tsx`)

```tsx
export const GROUP_COLUMNS: ColumnDef<Group, unknown>[] = [
  {
    id: 'name',                 // sortable column id = backend sortable field (camelCase) → FindDTO.orderBy
    accessorKey: 'name',
    enableSorting: true,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
    cell: ({ row }) => (
      <div className="flex flex-col">
        <span className="font-medium text-foreground">{row.original.name}</span>
        <span className="text-xs text-muted-foreground">{row.original.description ?? '—'}</span>
      </div>
    ),
  },
  { accessorKey: 'status', header: 'Status', cell: ({ row }) => <StatusBadge tone={GROUP_STATUS_TONE[row.original.status]}>{row.original.status}</StatusBadge> },
  { accessorKey: 'memberCount', header: 'Members', cell: ({ row }) => <span className="tabular-nums">{row.original.memberCount}</span> },
  { accessorKey: 'updatedAt', header: 'Updated', cell: ({ row }) => <RelativeTime value={row.original.updatedAt} /> },
  {
    id: 'actions',
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => <GroupRowActions group={row.original} />,
    meta: { className: 'w-12 text-right', skeletonClassName: 'ml-auto size-6' } satisfies DataTableColumnMeta,
  },
]
```

Table conventions (playbook §5.3): first column is the identity (avatar/name + muted secondary line);
status is a `StatusBadge`; numbers `tabular-nums`; dates relative with the full date in a `Tooltip`
(`utils/date-formatter`); last column is the row-actions menu. Header row `bg-muted/50 text-xs font-medium
text-muted-foreground`, rows `h-12 hover:bg-muted/50` — these come from the module, don't restyle per page.

### Row actions + delete

```tsx
// components/GroupRowActions.tsx
const [confirmOpen, setConfirmOpen] = useState(false)
const remove = useDeleteGroup() // useMutation → groupService.delete({ id }), invalidate GROUP_QUERY_KEYS.all

const actions: DataTableRowAction[] = [
  { label: 'Edit', icon: 'pencil-simple', onSelect: () => onEdit(group) },
  { label: 'Delete', icon: 'trash', variant: 'destructive', separatorBefore: true, onSelect: () => setConfirmOpen(true) },
]

<DataTableRowActions actions={actions} label={`Actions for ${group.name}`} />
<ConfirmDialog
  open={confirmOpen}
  onOpenChange={setConfirmOpen}
  icon="trash"
  variant="destructive"
  title={`Delete ${group.name}?`}
  description="This can't be undone."
  confirmLabel="Delete group"
  // returning a promise keeps the dialog open with a spinner; it closes on resolve, stays open on reject
  onConfirm={() =>
    remove
      .mutateAsync(group.id)
      .then(() => toast.success(`${group.name} was deleted`))
      .catch((error: unknown) => {
        toast.error('Could not delete the group', { description: getErrorMessage(error) })
        throw error
      })
  }
/>
```

### Sorting & filters

- Sorting: keep `sort: DataTableSort | null` (`{ orderBy, order }`) in the `use…ListQuery` state and pass
  `sort` / `onSortChange` to `DataTable`; columns opt in with `enableSorting: true` and a
  `DataTableColumnHeader` (manual sorting — the server sorts). The column `id` must be a backend-whitelisted
  sort field.
- Filters: `Select` / faceted filter popovers in the toolbar write `FindDTO.filters`; reset page to 1.
  For config-driven filter panels use `reactjs-dynamic-filter`.

---

## Pattern B — card grid

Use when items are visual (projects, files, integrations). Same hooks; render
`grid gap-4 sm:grid-cols-2 xl:grid-cols-3` of `Card`s (`rounded-xl`, `p-4`/`p-6`, `hover:bg-muted/50`
with a real link inside), skeleton cards while loading, `EmptyState` when empty, `DataTablePagination` below.

## Pattern C — infinite feed (activity, notifications, logs)

- `useInfiniteQuery({ initialPageParam: 1, queryFn: ({ pageParam }) => service.getAll({ ...query, page: pageParam, size }), getNextPageParam: (last) => last.pagination.page < last.pagination.totalPages ? last.pagination.page + 1 : undefined })`;
  rows = `data.pages.flatMap((p) => p.items)`.
- The list lives in `PerfectScrollArea` inside a bounded flex parent (`flex-1 min-h-0`); trigger
  `fetchNextPage()` from its `onYReachEnd` prop (guard with `hasNextPage && !isFetchingNextPage`).
  No raw `overflow-auto`, no viewport `IntersectionObserver`.
- Rows: `flex items-start gap-3 py-3` with `Separator` or `divide-y divide-border`; avatar/icon tile, text,
  muted relative time. Loading more → 2–3 skeleton rows at the end.

---

## ✅ Do

- ✅ Fetch through TanStack Query + a service `getAll` (POST `/x/get-all` with a FindDTO). Never `useEffect(fetch)`.
- ✅ Render tables with `@/modules/data-table`; one card holds toolbar + table + pagination.
- ✅ Memoize the FindDTO / `query` object; reset to page 1 when search/filters/sort change.
- ✅ Use backend pagination (`ApiPagination.totalElements / totalPages`); page size ≤ 100.
- ✅ Search/filter/sort only on backend-whitelisted fields (`apps/backend/db/schema.py`).
- ✅ Render all states: skeleton loading, error + retry, empty (`EmptyState`), filtered-empty, data, refetching (dim), pagination.
- ✅ Bounded scroll regions use `PerfectScrollArea`; wide tables scroll horizontally inside their card on mobile.

## ❌ Don't

- ❌ Don't hand-build a `<table>` per feature or re-implement pagination/row menus — extend the module.
- ❌ Don't fetch everything and paginate client-side.
- ❌ Don't pass an inline object literal as the query (new key every render → refetch loop).
- ❌ Don't build a module-level singleton store for list data (TanStack Query already caches).
- ❌ Don't combine infinite and paginated mode in one list.
- ❌ Don't use native `<select>` / `<input type="checkbox">`, `confirm()` or "No data" plain text.
- ❌ Don't hard-code `h-[calc(100vh-…)]` or put `overflow: hidden` on `body`/`html`.

## Checklist

- [ ] Single fetch path: `useQuery`/`useInfiniteQuery` → service `getAll`
- [ ] FindDTO memoized and part of the query key; page resets on search/filter/sort change
- [ ] Table via `DataTable` (`toolbar={<DataTableToolbar … />}`, built-in pagination footer); columns in the feature's `config/`
- [ ] Status via `StatusBadge`, row actions via `DataTableRowActions`, delete via `ConfirmDialog` + toast
- [ ] All states rendered; errors via `getErrorMessage`
- [ ] Scroll containers use `PerfectScrollArea` inside `flex-1 min-h-0`
- [ ] Reviewed with `npm run ui:snapshot -- --route <path>` (light/dark, desktop/mobile)
- [ ] If the module lacks something generic (e.g. column visibility), add it to `src/modules/data-table/` with tests — not a one-off copy in the feature
