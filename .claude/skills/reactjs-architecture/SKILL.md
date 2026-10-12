---
name: reactjs-architecture
description: Folder structure, file placement and naming conventions for apps/web (React 18 + Vite + TS). Use before creating, moving or naming any web file — components, pages, routes, features, hooks, services, stores, types, schemas, utils, config, styles, tests. Single source of truth for where every file goes, matched to the real src/ tree.
---

# Web Architecture — Folder Structure & Naming

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns folder placement, naming and import boundaries.

Before creating or moving any file under `apps/web/`, find its row below. The tree reflects
the **current** boilerplate; folders marked *(create on demand)* do not exist yet — create
them only when the first file that belongs there is written.

## The real `src/` tree

```
apps/web/src/
├── main.tsx                 ← entry: icon fonts, index.css, <AppProviders><RouteIndex/>
├── index.css                ← Tailwind v4 entry: imports styles/*.css + perfect-scrollbar CSS
├── vite-env.d.ts
├── components/
│   ├── ui/                  ← shadcn/Radix primitives bound to design tokens (button, card, form, input, sidebar, sonner, table, …)
│   ├── common/              ← domain-agnostic page patterns + composites (PageHeader, StatCard, EmptyState, SectionCard, StatusBadge, ConfirmDialog, LoadingState, StatusScreen, ErrorFallback, RouteErrorFallback, ThemeToggle, FullScreenLoader, RelativeTime)
│   ├── layouts/             ← app shell (AppLayout, AppHeader, AppSidebar, SidebarNavItem, AuthLayout)
│   └── wrappers/            ← providers + 3rd-party adapters (AppProviders, PerfectScrollArea)
├── config/
│   ├── env.ts               ← zod-validated env (`import env from '@/config/env'`)
│   ├── constants.ts         ← global constants (SUPERUSER_ROLES, ADMIN_ROLES, LOGIN_PATH, DEFAULT_PAGE_SIZE…)
│   ├── theme-config.ts      ← theme labels/icons for the theme toggle
│   └── menu/                ← APP_MENU, ADMINISTRATOR_MENU, ALL_MENUS (navigation source of truth)
├── features/
│   ├── administrator/user/  ← components/ config/ constants/ hooks/ index.ts
│   ├── dashboard/overview/  ← components/ constants/ index.ts
│   └── shared/auth/         ← components/ constants/ hooks/ schemas/ utils/ index.ts
├── hooks/                   ← cross-domain hooks (use-page-title, use-mobile, use-debounced-value, use-theme-sync, use-resolved-theme)
├── lib/
│   └── query-client.ts      ← TanStack Query client singleton
├── pages/                   ← thin route entries: administrator/user/UserPage.tsx, auth/{Login,VerifyEmail}Page.tsx, dashboard/DashboardPage.tsx, errors/{NotFound,Forbidden}Page.tsx
├── routes/                  ← index.tsx, auth/main/admin .routes.tsx, guards/{AuthGuard,GuestGuard,RoleGuard,ServerUnavailable}.tsx
├── services/                ← api-client, api-error, api-endpoints, api-factory*, <resource>.service.ts
├── stores/                  ← global Zustand stores (useAuthStore, useThemeStore)
├── styles/                  ← variable.css (tokens), tailwind.css (@theme mapping), components.css (overrides, .ps__* scrollbar theme)
├── test/                    ← vitest setup.ts, render.tsx (providers), axios-mock.ts
├── types/                   ← global ambient types: api.d.ts, models.d.ts, menu.d.ts, icon.d.ts (types only — no runtime code)
└── utils/                   ← pure helpers (cn, date-formatter, form-errors, icon-renderer, menu, browser)
```

`src/modules/{name}/` holds generic multi-feature systems; the reference module is
`src/modules/data-table/` (`DataTable`, `DataTableToolbar`, `DataTableColumnHeader`,
`DataTablePagination`, `DataTableRowActions`) — see `.claude/skills/reactjs-modules/SKILL.md`.
Other folders to create on demand: `src/schemas/` (schemas shared by 2+ domains), `src/assets/`
(images/SVGs imported from TS). Check `ls src/components/common src/modules` — the code is the
source of truth for what exists.

## Step 1 — Where does this file go?

| File type | Location |
|---|---|
| shadcn/Radix primitive or design-system binding | `src/components/ui/` (`npx shadcn@latest add <name>` + the post-install checklist in `reactjs-ui-design` §3) |
| App shell piece (layout, header, sidebar, footer) | `src/components/layouts/` |
| Provider or 3rd-party adapter (scroll, chart, map wrapper) | `src/components/wrappers/` |
| Domain-agnostic page pattern or composite (`PageHeader`, `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`, `ConfirmDialog`, loading/error states) | `src/components/common/` |
| Any list/table (sorting, paging, toolbar, row actions) | use `src/modules/data-table/` — don't build a table per feature |
| Generic system with its own state/fetching reused by 2+ features | `src/modules/{name}/` |
| Domain component, hook, constants, config, schema, utils | `src/features/{domain}/{feature}/{components,hooks,constants,config,schemas,utils,types,store}/` |
| Domain piece shared by 2+ features of the same domain | `src/features/{domain}/components/` (domain root) |
| Route entry | `src/pages/{area}/{PageName}Page.tsx` — composition only |
| Route definitions / guards | `src/routes/*.routes.tsx`, `src/routes/guards/` |
| Navigable page entry in the menu | `src/config/menu/*.menu.ts` (see `.claude/skills/reactjs-menu-config/SKILL.md`) |
| HTTP call to the backend | `src/services/{resource}.service.ts` (see `.claude/skills/reactjs-service/SKILL.md`) |
| Global client state | `src/stores/use{Name}Store.ts`; domain state → `features/{domain}/{feature}/store/` |
| Global type used across domains | `src/types/{name}.d.ts` (types only); domain types → `features/…/types/` |
| Env variable | `src/config/env.ts` schema + `apps/web/env/.env.example` (see `.claude/skills/reactjs-manage-env/SKILL.md`) |
| Pure helper used by 2+ domains | `src/utils/{name}.ts` |
| Library singleton (query client, i18n…) | `src/lib/` |
| Test helper / setup | `src/test/`; specs sit next to the code as `*.test.ts(x)` |
| CSS tokens / theme mapping / overrides | `src/styles/variable.css`, `src/styles/tailwind.css`, `src/styles/components.css` |
| Static file served as-is (favicon, manifest, robots) | `apps/web/public/` |

Where the API error type lives: `ApiError` is a class in `src/services/api-error.ts` (not in
`types/`). `src/types/api.d.ts` only declares the envelope/DTO types (`ApiEnvelope`,
`ApiPagination`, `ApiList`, `FindDTO`, `FilterItem`, …).

## Domain code never goes in `src/components/`

`src/components/` is domain-agnostic. Panel content, data widgets, status badges for a
business domain, list views… belong in `src/features/{domain}/{feature}/components/`
(real example: `features/administrator/user/components/UserListView.tsx`,
`UserStatusBadge.tsx`). Before creating a domain component, read
`.claude/skills/reactjs-features/SKILL.md` to pick the domain bucket.

> `.claude/rules/architecture.md` also allows `src/pages/{page}/parts/` for a purely
> presentational piece used by exactly one page. The boilerplate itself never uses it —
> prefer the feature folder; only use `parts/` when there is truly no domain owner.

## Pages are composition-only

```tsx
// src/pages/administrator/user/UserPage.tsx  (real file)
import { UserListView } from '@/features/administrator/user'

export default function UserPage() {
  return <UserListView />
}
```

- File name: `PascalCase` + `Page` suffix, default export (routes lazy-load it:
  `lazy(() => import('@/pages/administrator/user/UserPage'))`).
- Folder: `kebab-case`, mirrors the URL (`/administrator/user` → `pages/administrator/user/`).
- No hooks/helpers/sub-components declared in the page file; no `hooks/` folder under `pages/`.
- Pages never import other pages.

## Features

```
src/features/{domain}/{feature}/
├── components/   ← PascalCase.tsx, one component per file
├── hooks/        ← useXxx.ts (TanStack Query hooks, view state)
├── constants/    ← {feature}.constants.ts (query keys, labels, page size)
├── config/       ← {feature}-table.config.tsx, chart options, filter maps
├── schemas/      ← {name}.schema.ts (zod) + inferred form types
├── utils/        ← pure helpers for this feature
├── types/        ← {feature}.types.ts when types are feature-local
├── store/        ← Zustand slice when the feature needs shared client state
└── index.ts      ← public API (barrel) — the only entry other folders import
```

Other code imports a feature **only through its barrel** (`@/features/administrator/user`).
Inside a feature, files use short relative imports (`../hooks/useUserList`); across folders
always use the `@/` alias.

## Naming (as used in the codebase)

| Type | Convention | Real example |
|---|---|---|
| Component file | `PascalCase.tsx` | `UserListView.tsx`, `AppSidebar.tsx` |
| shadcn primitive file | `kebab-case.tsx` (shadcn CLI default) | `components/ui/button-group.tsx` |
| Page | `PascalCase` + `Page.tsx` | `DashboardPage.tsx` |
| Hook (global) | `use-kebab-case.ts`, export `useCamelCase` | `hooks/use-page-title.ts` → `usePageTitle` |
| Hook (feature) | `useCamelCase.ts` | `features/administrator/user/hooks/useUserList.ts` |
| Service | `{resource}.service.ts`, export `{resource}Service` | `user.service.ts` → `userService` |
| Store | `use{Name}Store.ts` | `stores/useAuthStore.ts` |
| Routes | `{area}.routes.tsx` | `admin.routes.tsx` |
| Schema | `{name}.schema.ts`, `{name}Schema` + `T{Name}FormValues` | `login.schema.ts` → `loginSchema`, `TLoginFormValues` |
| Constants file | `{feature}.constants.ts`; values `UPPER_SNAKE_CASE` | `USER_QUERY_KEYS`, `DEFAULT_PAGE_SIZE` |
| Config file | `kebab-case.ts` / `{feature}-table.config.tsx` | `theme-config.ts`, `user-table.config.tsx` |
| Menu file | `{area}.menu.ts` | `administrator.menu.ts` |
| Domain model / API types | `PascalCase` (no prefix) | `UserProfile`, `ApiEnvelope<T>`, `FindDTO` |
| Request payload interfaces | `I` + `PascalCase` | `IUserCreatePayload`, `ILoginPayload` |
| CSS file | `kebab-case.css` | `components.css` |
| Test | `*.test.ts(x)` next to the code | `services/api-client.test.ts` |

## Component file cleanliness

A `.tsx` component file contains JSX, event handlers and component-local `useState`/`useRef`.
Extract before writing the component:

| Need | Put it in |
|---|---|
| Formatter / mapper | `src/utils/` (global) or `features/…/utils/` |
| Label map, enum, query keys | `features/…/constants/` or `src/config/constants.ts` |
| Table columns / chart options | `features/…/config/` |
| zod schema | `features/…/schemas/` |
| Fetching / mutations | service in `src/services/` + TanStack Query hook in `features/…/hooks/` |
| Derived/computed state | hook in `features/…/hooks/` or `src/hooks/` |

```tsx
// ✅ features/administrator/user/components/UserListView.tsx (shape — imports patterns, owns no helpers)
import { PageHeader } from '@/components/common/PageHeader'
import { DataTable } from '@/modules/data-table'

import { USER_COLUMNS } from '../config/user-table.config'

import { useUserList } from '../hooks/useUserList'
import { useUserListQuery } from '../hooks/useUserListQuery'

export function UserListView() {
  const { query, search, setSearch, setPage } = useUserListQuery()
  const { data, isPending, isError, error } = useUserList(query)
  // …JSX only
}
```

## Styling rules

- Tailwind v4 utility classes bound to the design tokens in `src/styles/variable.css` /
  `tailwind.css`, using the shadcn semantic classes (`bg-background`, `bg-card`, `text-foreground`,
  `text-muted-foreground`, `border-border`, `bg-primary`…). Legacy aliases (`bg-background-primary`,
  `text-font-*`, `border-border-primary`) still resolve but are not used in new code. Radius, shadow,
  spacing and typography follow `reactjs-ui-design` §2.
- No hex/rgb literals in `className` (`bg-[#1B1E26]`) or `style={{}}`; add a token to
  `variable.css` (light `:root` **and** `.dark`) and map it in `tailwind.css`.
- `style={{}}` only for runtime-computed values (sizes from props, CSS custom properties).
- Dark mode is class-based (`.dark` on `<html>`, managed by `stores/useThemeStore.ts`).

## Absolute rules

- ✅ `@/` alias for cross-folder imports (configured in `tsconfig.app.json` + `vite.config.ts`).
- ✅ One component per file; extract helpers/types/constants/config first.
- ✅ Route guards only in `src/routes/guards/`.
- ✅ Every navigable page is wired in `src/routes/` **and** `src/config/menu/` in the same change.
- ✅ Bounded scroll regions use `PerfectScrollArea` (`src/components/wrappers/PerfectScrollArea.tsx`).
- ❌ No `any` (ESLint `@typescript-eslint/no-explicit-any: error`); use `unknown` + narrowing.
- ❌ No `import.meta.env` outside `src/config/env.ts`.
- ❌ No runtime code in `src/types/*.d.ts`.
- ❌ No files directly in `src/` besides `main.tsx`, `index.css`, `vite-env.d.ts`.
- ❌ No new top-level `src/` folder beyond the on-demand ones listed above without agreement.
- ❌ No hand-rolled dropdown/select/dialog/tabs/tooltip/checkbox etc. — install the shadcn primitive.

## Verify

```bash
npm run ci          # from repo root: lint, format-check, typecheck, test, build (web + backend)
# web only (from apps/web): npm run typecheck && npm run lint && npm run test:ci
```

Detailed allow/deny tables and the PR checklist: [references/architecture-rules.md](references/architecture-rules.md)
