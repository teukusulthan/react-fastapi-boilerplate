---
name: reactjs-app-layout
description: The authenticated app shell of apps/web (AppLayout + AppHeader + AppSidebar + SidebarNavItem, AuthLayout for /auth/*), how routes nest under it with <Outlet/>, the non-overlap region contract, and how to add a page/route/menu entry. Load before changing the shell, adding a layout, or adding any user-facing page.
---

# App Layout (React / TypeScript)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md` win over any markup here. This skill owns the shell structure (regions, nesting, non-overlap contract, page/route/menu wiring).

The shell **already exists** in the boilerplate — extend it, don't rebuild it.

| File | Role |
|---|---|
| `src/components/layouts/AppLayout.tsx` | Authenticated shell: `SidebarProvider` root, header, sidebar, `SidebarInset` (the `<main>`, an inset rounded panel) with `PerfectScrollArea` + `<Suspense>` + `<Outlet/>`; calls `usePageTitle()` |
| `src/components/layouts/AppHeader.tsx` | Full-width `h-12` bar on the `bg-sidebar` canvas: skip link, brand (`AppBrand`, aligned with the sidebar column), `SidebarTrigger`, `AppBreadcrumb`, `ThemeToggle`, `UserMenu` |
| `src/components/layouts/AppSidebar.tsx` | Config-driven nav: `buildMenuSections(APP_MENU [+ ADMINISTRATOR_MENU], MENU_GROUP_LABEL)` — admin entries only when `hasAccess(user, { roles: ADMIN_ROLES })`; `<Sidebar variant="inset" collapsible="icon">` |
| `src/components/layouts/SidebarNavItem.tsx` | One menu entry: `NavLink` + `renderIcon`, active state via `isMenuPathActive` |
| `src/components/layouts/AuthLayout.tsx` | Centered layout for `/auth/*` (login, verify-email); sets title per route |
| `src/components/ui/sidebar.tsx` | shadcn Sidebar primitive (`SIDEBAR_WIDTH = '15rem'` = 240px, `SIDEBAR_WIDTH_ICON = '3.25rem'`, icon-collapse, mobile sheet, `SidebarInset`) |
| `src/components/wrappers/PerfectScrollArea.tsx` | Mandatory scroll wrapper for bounded regions |
| `src/routes/main.routes.tsx` | `/` → `<AuthGuard><AppLayout/></AuthGuard>` with page children |
| `src/routes/auth.routes.tsx` | `/auth` → `<AuthLayout/>` with `login` (wrapped in `GuestGuard`) and `verify-email` |
| `src/routes/admin.routes.tsx` | `administrator` → `<RoleGuard allowedRoles={ADMIN_ROLES}/>` children; spread into the AppLayout children |
| `src/routes/index.tsx` | `createBrowserRouter` root with `RouteErrorFallback` + `*` → `NotFoundPage` |

## Design tokens

Tokens live in `src/styles/variable.css` (light `:root` + `.dark`) and are mapped to Tailwind in
`src/styles/tailwind.css`. Use the **shadcn semantic classes** from `reactjs-ui-design` §2:
`bg-background`, `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`,
`border-border`, `bg-sidebar…`, `bg-primary text-primary-foreground`. Legacy aliases
(`bg-background-primary`, `text-font-*`, `border-border-primary`) still resolve but are not used in
new code — replace them when you touch a shell file. A project `design/` theme, if one is selected,
only changes the variable values, not the class names.

## Region contract — no header/sidebar overlap

```tsx
// src/components/layouts/AppLayout.tsx
<SidebarProvider className="h-svh flex-col overflow-hidden bg-sidebar text-foreground">
  <AppHeader />                                         {/* h-12 shrink-0, full width, bg-sidebar (shell canvas) */}
  <div className="flex min-h-0 flex-1 overflow-hidden">
    <AppSidebar />                                      {/* <Sidebar variant="inset" collapsible="icon" className="top-12 h-[calc(100svh-3rem)]"> */}
    <SidebarInset id="main-content" tabIndex={-1} className="min-h-0 outline-none">
      <PerfectScrollArea className="h-full" contentClassName="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <Suspense fallback={<LoadingState />}>
          <Outlet />
        </Suspense>
      </PerfectScrollArea>
    </SidebarInset>
  </div>
</SidebarProvider>
```

| Region | Contract |
|---|---|
| Root | `SidebarProvider` with `h-svh flex-col overflow-hidden bg-sidebar` (the sidebar color is the canvas around the inset panel) |
| Header | `h-12 shrink-0`, full width, above the body |
| Body | `flex min-h-0 flex-1 overflow-hidden` |
| Sidebar | shadcn `Sidebar` (`variant="inset"`, `collapsible="icon"`) is `fixed` on desktop → offset `top-12 h-[calc(100svh-3rem)]`; width `--sidebar-width` = 15rem (240px), 3.25rem collapsed; its in-flow gap element reserves that width |
| Main | `SidebarInset` (`<main>`, `min-w-0 flex-1`): on `md+` an inset rounded panel (`rounded-xl border shadow-xs bg-background`, `mr-2 mb-2`); scrolls through `PerfectScrollArea` (not raw `overflow-auto`); owns the page padding (`px-4 py-6 sm:px-6 lg:px-8 lg:py-8`) and `max-w-7xl` — pages don't add their own outer padding |

Forbidden:

```tsx
// ❌ header inside the content column while the fixed sidebar starts at inset-y-0 → overlap
<div className="flex h-screen"><AppSidebar /><div><AppHeader /><main /></div></div>
// ❌ fixed sidebar without the header offset
<Sidebar className="fixed inset-y-0" />
// ❌ raw scroll on main / sidebar body
<main className="flex-1 overflow-auto">…</main>
```

## Adding a user-facing page (the common task)

1. **Feature** — build the UI in `src/features/{domain}/{feature}/` and export it from the
   feature's `index.ts` (see `.claude/skills/reactjs-features/SKILL.md`).
   The view starts with `PageHeader` (title, one-line description, primary action) and stacks
   sections with `gap-6` (playbook §5.1); every async surface has loading/empty/error states.
2. **Page** — `src/pages/{area}/{Name}Page.tsx`, default export, composition only:
   ```tsx
   import { ReportListView } from '@/features/reports/list'   // your feature barrel

   export default function ReportPage() {
     return <ReportListView />
   }
   ```
3. **Route** — lazy child of the AppLayout route in `src/routes/main.routes.tsx`:
   ```tsx
   const ReportPage = lazy(() => import('@/pages/reports/ReportPage'))
   // children: [{ index: true, element: <DashboardPage /> }, { path: 'reports', element: <ReportPage /> }, ...adminRoutes]
   ```
   Role-restricted? wrap in `<RoleGuard allowedRoles={…} requiredPrivileges={…} />`
   (`src/routes/guards/RoleGuard.tsx`, renders the 403 page in place).
4. **Menu** — add an `IMenu` entry to `src/config/menu/app.menu.ts` with a unique id and a
   `path` equal to the route (see `.claude/skills/reactjs-menu-config/SKILL.md`). The sidebar
   and the page title (`seo.title`) pick it up automatically.

Skip step 4 only when the task explicitly says the route is hidden, callback-only,
redirect-only, modal-only, or a public auth entry point (like `/auth/*`).

## Adding an admin page

Use `.claude/skills/reactjs-administrator/SKILL.md`. Short version: entry in
`administrator.menu.ts` (child of the `qeuln` section) → service → feature under
`features/administrator/{resource}/` → page under `pages/administrator/{resource}/` →
lazy child in `admin.routes.tsx`. `admin.routes.tsx` is spread **once**, into the
AppLayout children of `main.routes.tsx`; it is already wrapped in
`RoleGuard allowedRoles={ADMIN_ROLES}` — don't add a second guard.

## Adding a public (non-shell) page

Public auth-style pages go under the `auth` route of `src/routes/auth.routes.tsx` and render
inside `AuthLayout`. Wrap guest-only pages (login, register) in `GuestGuard`; pages that
must work signed in or out (verify-email) are not wrapped. Add a title to
`AUTH_PAGE_TITLES` in `AuthLayout.tsx`.

## Rules

- MUST render page content only through `<Outlet/>`; never hardcode page content in layouts.
- MUST nest every authenticated page under the AppLayout route (single shared shell).
- MUST keep navigation config-driven: sidebar reads `src/config/menu/*`; no local
  `const menuItems = [...]` in layout files.
- MUST keep sidebar open/collapsed state in shadcn `SidebarProvider` (persisted by the
  primitive) — no duplicate store.
- MUST call `usePageTitle()` once per layout, never in pages.
- MUST use Phosphor classes (`<i className="ph ph-…">` or `renderIcon`) for shell icons —
  no React icon packages (see `.claude/skills/reactjs-icon/SKILL.md`).
- MUST NOT fetch page data in layouts; only session/user state (`useAuthStore`) is allowed.
- MUST NOT import `ADMINISTRATOR_MENU` anywhere except the sidebar/admin code paths.
- MUST use semantic token classes in shell files (header `border-b border-border bg-background`,
  sidebar `bg-sidebar`, main `bg-muted/40` or `bg-background`); no raw colors, no square brand tiles —
  the logo mark uses `rounded-md`.

## Checklist

- [ ] Header, sidebar, main are separate regions; sidebar offset `top-12 h-[calc(100svh-3rem)]`
- [ ] Main/sidebar scroll via `PerfectScrollArea`; ancestors keep `min-h-0`
- [ ] New page: feature + page + lazy route + menu entry in one change
- [ ] Route `path` matches the menu `path` exactly (title + active state depend on it)
- [ ] No hardcoded nav arrays, no icon packages, no hex colors / legacy aliases in shell files
- [ ] Reviewed `npm run ui:snapshot -- --route <path>` (light/dark, desktop + 390px mobile)
- [ ] `npm run typecheck && npm run lint && npm run test:ci` (apps/web) pass

## Common mistakes

- Spreading `adminRoutes` into `routes/index.tsx` as well as `main.routes.tsx` (duplicate routes).
- Adding a route but no menu entry → page unreachable and `document.title` falls back to the app name.
- Putting `overflow-auto` on `<main>` instead of using `PerfectScrollArea`.
- Lazy-loading a page that uses a named export — pages must `export default`.
