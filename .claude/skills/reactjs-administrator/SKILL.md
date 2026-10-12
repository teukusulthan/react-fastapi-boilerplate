---
name: reactjs-administrator
description: Build a CRUD list page under /administrator/* (e.g. Group, Role, Permission, Upload, or a new resource). Composite recipe on top of reactjs-architecture, reactjs-features, reactjs-menu-config, reactjs-service, reactjs-tanstack-query and reactjs-auth-guard, using the existing /administrator/user page as the canonical example. Read this before adding, removing, or changing any /administrator/* route, menu entry, or list page.
---

# Skill — Administrator CRUD List Page (Composite Recipe)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md` win over any markup here. This skill owns the `/administrator/*` route/menu/feature wiring and the list-page data flow (playbook recipe §5.3 is the visual target).

This is a **recipe skill**: it sequences the base skills for one recurring task — a paginated, searchable
list page at `/administrator/{resource}` backed by a backend CRUD module.

**Base skills (read as needed):**

1. `.claude/skills/reactjs-menu-config/SKILL.md` — menu entry shape, ID uniqueness
2. `.claude/skills/reactjs-architecture/SKILL.md` — file placement
3. `.claude/skills/reactjs-service/SKILL.md` — `createResourceService`, `API_ENDPOINTS`
4. `.claude/skills/reactjs-tanstack-query/SKILL.md` — list query hook, keys, invalidation
5. `.claude/skills/reactjs-features/SKILL.md` — feature folder scaffold
6. `.claude/skills/reactjs-auth-guard/SKILL.md` — `RoleGuard`
7. `.claude/skills/reactjs-ui-design/SKILL.md` — look & feel, component priority, `npm run ui:snapshot` review loop
8. `.claude/skills/reactjs-data-display/SKILL.md` — `DataTable` module (`src/modules/data-table/`)
9. `.claude/skills/reactjs-anti-slop/SKILL.md` — pre-emit critique before calling it done

## What already exists

Backend services for `user`, `group`, `permission`, `role`, `upload` already exist on the web side
(`src/services/{user,group,permission,role,upload}.service.ts`, types in `src/types/models.d.ts`). Only the
**user** page is built (search + pagination, an "Add user" dialog, and row actions: reset password,
block/activate, delete). Group/permission/role/upload pages are not
built yet — create them with this recipe.

**Canonical example (copy this shape):**

```
src/config/menu/administrator.menu.ts        ← parent 'qeuln' (section label) + one child per resource
src/routes/admin.routes.tsx                  ← path 'administrator', element <RoleGuard allowedRoles={ADMIN_ROLES} />, lazy children
src/services/user.service.ts                 ← createResourceService<UserDetail, IUserCreatePayload, IUserUpdatePayload>
src/features/administrator/user/
├── constants/user.constants.ts              ← USER_QUERY_KEYS, USER_STATUS_META (label + StatusBadge tone), filter options, page size, default sort, USER_SEARCH_FIELDS
├── schemas/user.schema.ts                   ← zod schemas for the create / reset-password forms
├── hooks/useUserListQuery.ts                ← search + status + sort + page/size state → memoized FindDTO (debounced search)
├── hooks/useUserList.ts                     ← useQuery(USER_QUERY_KEYS.list(query), () => userService.getAll(query))
├── hooks/useUserMutations.ts                ← useCreateUser / useDeleteUser / useUpdateUserStatus / useResetUserPassword
├── config/user-table.config.tsx             ← getUserColumns(currentUserId): ColumnDef<UserDetail, unknown>[] (JSX cells → .tsx)
├── components/UserListView.tsx              ← composition root: PageHeader + DataTable (toolbar/error/emptyState slots)
├── components/UserRowActions.tsx            ← DataTableRowActions + ConfirmDialog (block / delete) + ResetPasswordDialog
├── components/CreateUserDialog.tsx          ← Dialog form (react-hook-form + zod)
├── components/UserStatusBadge.tsx           ← thin mapping onto common StatusBadge tones
├── components/UserIdentityCell.tsx          ← avatar + name + email cell
└── index.ts                                 ← public exports
src/pages/administrator/user/UserPage.tsx    ← `return <UserListView />` only
```

> The user page is the reference implementation of this pattern (`DataTable` module, row actions with
> `ConfirmDialog`, create dialog). Copy it for new admin resources.

Shared building blocks to reuse (do not re-implement per resource):
- `src/modules/data-table/` — `DataTable` (renders `DataTablePagination` itself when you pass `pagination` +
  `onPageChange`), `DataTableToolbar`, `DataTableColumnHeader`, `DataTableRowActions` (built-in skeleton rows
  + empty state; see `reactjs-data-display`).
- `src/components/common/` — `PageHeader`, `StatusBadge`, `EmptyState`, `ConfirmDialog`, `SectionCard`,
  `LoadingState`, `ErrorFallback`.
- `src/components/ui/` — `card`, `input`, `button`, `badge`, `alert`, `dropdown-menu`, `dialog`, `sheet`,
  `select`, `tooltip`, `avatar` (install missing ones with `npx shadcn@latest add <name>` + the post-install
  checklist in `reactjs-ui-design` §3).
- `hooks/use-debounced-value.ts`, `utils/date-formatter.ts`, `getErrorMessage` from `services/api-error.ts`.

---

## Route & access contract

- One route group, one file: `src/routes/admin.routes.tsx` exports `adminRoutes` with a single entry
  `path: 'administrator'`, `element: <RoleGuard allowedRoles={ADMIN_ROLES} />`, index → `<Navigate to="user" replace />`,
  and one lazy child per resource.
- `adminRoutes` is spread **once** into the children of the `AuthGuard`-wrapped `/` route in
  `main.routes.tsx`, so admin pages render inside the normal `AppLayout` (header + sidebar). Never also add
  it to `routes/index.tsx`.
- Non-admins get the 403 page in place (RoleGuard). The backend enforces the same: `/user/*` is admin-only;
  `/group|permission|role` reads are any signed-in user, writes are admin.
- `AppSidebar` shows the `ADMINISTRATOR_MENU` section only when `hasAccess(user, { roles: ADMIN_ROLES })`;
  the parent entry (`qeuln`) renders as the section label "Administrator" and its children as items.

---

## Workflow — adding one admin resource (e.g. `group`)

1. **Service** — usually already present (`groupService`). For a new backend module add
   `API_ENDPOINTS.{RESOURCE}.BASE` and `src/services/{resource}.service.ts` via `createResourceService`, and
   the response type to `src/types/models.d.ts` (mirror the backend `…Response` DTO).
2. **Feature folder** `src/features/administrator/{resource}/`:
   - `constants/{resource}.constants.ts` — `{RESOURCE}_QUERY_KEYS = { all: ['{resource}s'] as const, list: (q: object) => ['{resource}s', 'list', q] as const }`,
     page size, `{RESOURCE}_SEARCH_FIELDS` (must be backend-searchable fields, see `apps/backend/db/schema.py`).
   - `hooks/use{Resource}ListQuery.ts` + `hooks/use{Resource}List.ts` — copy the user versions.
   - `config/{resource}-table.config.tsx` — `ColumnDef<{Entity}>[]` (identity column first, `StatusBadge`
     for status, relative dates with a full-date `Tooltip`, `DataTableRowActions` last).
   - `components/{Resource}ListView.tsx`, `index.ts`. No per-resource table component — use `DataTable`.
3. **Page** — `src/pages/administrator/{resource}/{Resource}Page.tsx`: `return <{Resource}ListView />`.
4. **Route** — lazy import + `{ path: '{resource}', element: <{Resource}Page /> }` in `admin.routes.tsx`.
5. **Menu** — child entry in `ADMINISTRATOR_MENU` with `idParent: 'qeuln'`, `path: '/administrator/{resource}'`,
   a unique id (rules in reactjs-menu-config), `group: 'system'`, `seo.title`.
6. **Mutations (optional)** — create/edit forms per `.claude/skills/reactjs-form/SKILL.md` in a `Dialog`
   (≤ 6 fields), a `Sheet` (more fields) or a dedicated page (complex); `useMutation` calling
   `{resource}Service.add/update/delete({ id })`, `onSuccess` → `queryClient.invalidateQueries({ queryKey: {RESOURCE}_QUERY_KEYS.all })`
   + `toast.success(...)` from `sonner`; show 409/422 via `ApiError` (`fieldErrors`, `applyApiFieldErrors`).
   Delete always goes through `ConfirmDialog` (never `confirm()`).
7. **Look at it** — `cd apps/web && npm run ui:snapshot -- --route /administrator/{resource}` (add a fixture
   for the new endpoint under `scripts/ui-snapshot/fixtures/`) and review the PNGs per `reactjs-ui-design` §8.

## List view composition (target pattern — playbook §5.3)

```tsx
export function GroupListView() {
  const { query, search, setSearch, sort, setSort, setPage, setPageSize, isFiltered, clearFilters } = useGroupListQuery()
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useGroupList(query)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Groups"
        description={data ? `${data.pagination.totalElements} groups in this workspace.` : 'Groups in this workspace.'}
        actions={<Button><i className="ph ph-plus" aria-hidden="true" />Add group</Button>}
      />

      <DataTable
        caption="Groups"
        columns={GROUP_COLUMNS}
        data={data?.items}
        getRowId={(row) => row.id}
        loading={isPending}
        fetching={isFetching && isPlaceholderData}
        pagination={data?.pagination}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        sort={sort}
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
        emptyState={
          isFiltered ? (
            <EmptyState
              icon="magnifying-glass"
              title="No matching groups"
              description="Try a different search term or clear the search."
              action={<Button variant="outline" onClick={clearFilters}>Clear filters</Button>}
            />
          ) : (
            <EmptyState icon="users-three" title="No groups yet" description="Create a group to organise users." />
          )
        }
      />
    </div>
  )
}
```

This mirrors the real `src/features/administrator/user/components/UserListView.tsx`; the full API is in
`src/modules/data-table/index.ts`.

- The `FindDTO` must be memoized (`useMemo` in the `use…ListQuery` hook) — it is part of the query key.
- Reset to page 1 whenever search/filters change.
- `DataTable` is the one card: it renders `toolbar` → table → pagination footer itself (do not wrap it in a
  `Card` or add a separate `DataTablePagination`). No cards inside cards, no extra outer padding (AppLayout owns it).
- Loading = skeleton rows (built into `DataTable`), not a page spinner. Empty = `EmptyState` with the primary
  action when nothing exists yet; filtered-empty says what to clear.
- Row actions: `DataTableRowActions` (a `DropdownMenu` on `ph-dots-three`, icon button with `aria-label`);
  destructive items open `ConfirmDialog`.
- Until a resource has a real create/edit form, either omit the Add/Edit buttons or wire them to an honest
  `toast.info('… coming soon')` — never a silent no-op button.
- Filters: faceted `Select`/`Popover` filters in the `DataTableToolbar`; sortable headers via
  `DataTableColumnHeader`. Send them as `FindDTO.filters` / `orderBy` with backend-whitelisted fields
  (`.claude/skills/reactjs-dynamic-filter/SKILL.md` for advanced filter panels).

## Visual tokens

Follow `reactjs-ui-design` §2: semantic classes only (`bg-card`, `text-muted-foreground`, `border-border`,
`bg-muted/50` header/hover rows), `rounded-md` controls, `rounded-xl` card. Status uses `StatusBadge` tones
(`success | warning | destructive | info | neutral`) — map resource statuses in `constants/`
(see `USER_STATUS_META`). Never raw hex/rgb, Tailwind palette colors or arbitrary values.

## Definition of done

- [ ] Service + `API_ENDPOINTS` entry + `models.d.ts` type exist and match the backend DTOs
- [ ] Feature folder under `features/administrator/{resource}/` with `index.ts`
- [ ] Page file is a one-line composition
- [ ] Route added inside the `administrator` RoleGuard group in `admin.routes.tsx` (not duplicated)
- [ ] Menu child added to `ADMINISTRATOR_MENU`, path matches the route
- [ ] `PageHeader` + one `DataTable` (with `toolbar`, `error`, `emptyState`, `pagination` + `onPageChange`)
- [ ] Loading (skeleton rows) / error (with retry) / empty (`EmptyState`) / data / pagination states all handled
- [ ] Search fields are backend-searchable; FindDTO memoized; page resets on search
- [ ] Destructive actions confirmed with `ConfirmDialog`, results toasted via `sonner`
- [ ] Reviewed `npm run ui:snapshot -- --route /administrator/{resource}` PNGs (light/dark, desktop/mobile)
- [ ] `npm run ci` (repo root) passes; ran the reactjs-anti-slop critique
