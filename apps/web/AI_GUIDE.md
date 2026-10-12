# AI Guide — Web (React + Vite)

The canonical guide for working in `apps/web`. Read it before you change web code.
Repository-wide rules are in [`../../AGENTS.md`](../../AGENTS.md) and
[`../../.claude/rules/architecture.md`](../../.claude/rules/architecture.md). For setup, scripts and
env vars, see [`README.md`](README.md). The backend contract is in
[`../../docs/api-spec.md`](../../docs/api-spec.md).

> Skills live in `.claude/skills/reactjs-*` (repo root). If a skill disagrees with the code or with
> this guide, the **code wins**, then this guide. Some skills describe modules that do not exist yet
> (chart and map wrappers). Create them per the skill when a task needs them.
>
> **Building or restyling UI?** Read [`.claude/rules/web/ui-design.md`](../../.claude/rules/web/ui-design.md)
> and load the [`reactjs-ui-design`](../../.claude/skills/reactjs-ui-design/SKILL.md) skill first (see §4 UI).

## 1. Mental model

- **Stack (installed):** React 18.3, TypeScript 5.9 (strict), Vite 7, React Router 7
  (`createBrowserRouter`), TanStack Query 5, Zustand 5, axios, React Hook Form 7 + Zod 4, Tailwind CSS v4
  (`@tailwindcss/vite`), shadcn/ui on Radix, sonner (toasts), Phosphor icons (`@phosphor-icons/web`,
  bundled), `react-perfect-scrollbar`, date-fns. Tests use Vitest 4, jsdom and Testing Library.
  `@tanstack/react-table` powers `src/modules/data-table/`. Available but not yet wired: `echarts`,
  `mapbox-gl` and `styled-components`.
- **Backend access:** every request goes to `env.api.baseUrl` (default `/api/v1/apps`). In dev, Vite
  proxies `/api/v1/apps/*` to `DEV_PROXY_TARGET` (default `http://localhost:8020`) and strips the
  prefix. In Docker, nginx does the same. The browser therefore sees one origin, and the httpOnly auth
  cookies just work.
- **Auth:** the httpOnly cookies `token` and `refresh_token` are the source of truth. JS never sees a
  token. `useAuthStore` (Zustand, **not persisted**) mirrors the session, and guards bootstrap it with
  `GET /auth/me`. On a 401, `api-client.ts` makes a single-flight `POST /auth/refresh` and retries once.
  If the refresh fails, the session is cleared and the user goes to `/auth/login?redirect=…`.
- **Envelope:** the backend returns `{metaData, data}`. `apiRequests.*` unwraps `data` (lists become
  `{items, pagination}`). Every failure is rejected as `ApiError {status, code, message, details,
  requestId}`, where `code` is the backend `errorCode` or a client code such as `NETWORK_ERROR`.

### Data flow

```
Page (src/pages, thin) ─► Feature component (src/features/<domain>/<feature>/components)
   ─► hook (TanStack Query useQuery/useMutation, in the feature's hooks/)
      ─► service (src/services/<module>.service.ts: createResourceService / apiRequests)
         ─► api-client.ts (axios, withCredentials, refresh-on-401, ApiError) ─► /api/v1/apps/… ─► backend
UI/client state ─► Zustand (src/stores or the feature's store/) — never server data
```

## 2. Layout

```
apps/web/
├── env/.env.example          VITE_* keys (copy to env/.env); DEV_PROXY_TARGET for the dev proxy
├── index.html                %VITE_APP_NAME% / %VITE_APP_DESCRIPTION% placeholders (vite.config.ts fills them)
├── vite.config.ts            port 3000, /api/v1/apps proxy, alias @ → src, build → build/, vitest config
├── eslint.config.js          ESLint 9 flat config (typescript-eslint, react-hooks, jsx-a11y); --max-warnings=0
├── components.json           shadcn CLI config (ui → @/components/ui, css → src/styles/tailwind.css)
├── Dockerfile, nginx.conf    production image: nginx-unprivileged on :8080, SPA fallback, /api/v1/apps proxy
└── src/
    ├── main.tsx              StrictMode + AppProviders + RouteIndex; Phosphor icon CSS imports
    ├── index.css             imports tailwind, styles/variable.css, styles/tailwind.css, styles/components.css
    ├── components/
    │   ├── ui/               shadcn primitives (new-york, React 18 forwardRef, Phosphor, `radix-ui`): alert, alert-dialog,
    │   │                     avatar, badge, breadcrumb, button, button-group, calendar, card, checkbox, collapsible,
    │   │                     command, dialog, dropdown-menu, empty, field, form, hover-card, input, input-group, kbd,
    │   │                     label, pagination, popover, progress, radio-group, select, separator, sheet, sidebar,
    │   │                     skeleton, sonner, spinner, switch, table, tabs, textarea, toggle, toggle-group, tooltip
    │   ├── layouts/          AppLayout, AppHeader, AppSidebar, SidebarNavItem, AuthLayout
    │   ├── wrappers/         AppProviders (ErrorBoundary, QueryClient, Tooltip, Toaster), PerfectScrollArea
    │   └── common/           generic page patterns: PageHeader, StatCard, EmptyState, SectionCard, StatusBadge,
    │                         ConfirmDialog, RelativeTime, plus ErrorFallback, RouteErrorFallback, LoadingState, StatusScreen,
    │                         FullScreenLoader, ThemeToggle
    ├── config/
    │   ├── env.ts            the ONLY reader of import.meta.env (zod-validated) → `env.api.baseUrl`, `env.app.*`, `env.map.*`
    │   ├── constants.ts      SUPERUSER_ROLES, ADMIN_ROLES, LOGIN_PATH, REDIRECT_PARAM, page sizes
    │   ├── theme-config.ts
    │   └── menu/             app.menu.ts (APP_MENU), administrator.menu.ts (ADMINISTRATOR_MENU), index.ts (ALL_MENUS)
    ├── modules/
    │   └── data-table/       DataTable (TanStack Table + shadcn Table; loading/fetching/emptyState/error/toolbar slots,
    │                         server pagination + sort), DataTableToolbar, DataTableColumnHeader, DataTablePagination,
    │                         DataTableRowActions
    ├── features/
    │   ├── administrator/user/   components, config (table columns), constants (query keys), hooks
    │   ├── dashboard/overview/   components, constants
    │   └── shared/auth/          LoginForm/LoginView/TwoFactorForm/UserMenu/VerifyEmailView, hooks (useSession,
    │                             useLoginFlow, useLogout, useVerifyEmail), schemas (zod), utils (access, redirect…)
    ├── pages/                one thin file per route: auth/, dashboard/, administrator/user/, errors/
    ├── routes/               index.tsx (createBrowserRouter), auth.routes.tsx, main.routes.tsx, admin.routes.tsx,
    │                         guards/ (AuthGuard, GuestGuard, RoleGuard, ServerUnavailable)
    ├── services/             api-client.ts, api-error.ts, api-endpoints.ts, api-factory.service.ts (apiRequests),
    │                         api-factory-crud.service.ts (createResourceService), auth/user/group/permission/role/upload services
    ├── stores/               useAuthStore (session mirror), useThemeStore (persisted theme preference)
    ├── lib/query-client.ts   QueryClient (retry policy: no retry on 4xx)
    ├── hooks/                use-debounced-value, use-mobile, use-page-title, use-resolved-theme, use-theme-sync
    ├── types/                *.d.ts only: api.d.ts (envelope, ApiErrorCode, FindDTO), models.d.ts (UserProfile, UserDetail,
    │                         Permission, Group, Role, Upload…), menu.d.ts, icon.d.ts
    ├── utils/                cn, date-formatter, form-errors (applyApiFieldErrors), icon-renderer (renderIcon), menu
    ├── styles/               variable.css (tokens), tailwind.css (@theme), components.css (incl. .ps__* scrollbar theming)
    ├── schemas/              (empty) global zod schemas; feature schemas live in the feature
    └── test/                 setup.ts, render.tsx (renderWithProviders), axios-mock.ts (createMockAdapter, ok(), fail(), pathOf())
```

Routes today:

| Path | Guard | Page |
|---|---|---|
| `/auth/login` | `GuestGuard` | `pages/auth/LoginPage.tsx` |
| `/auth/verify-email?token=` | none (works signed in or out) | `pages/auth/VerifyEmailPage.tsx` |
| `/` | `AuthGuard` + `AppLayout` | `pages/dashboard/DashboardPage.tsx` |
| `/administrator/user` | `AuthGuard` + `RoleGuard allowedRoles={ADMIN_ROLES}` | `pages/administrator/user/UserPage.tsx` |
| `*` | none | `pages/errors/NotFoundPage.tsx` (a 403 renders `ForbiddenPage` in place) |

## 3. Golden rules

1. **No API calls in components.** Use component → hook (TanStack Query) → service → `apiRequests`.
   Never `fetch` or `axios` in components, and never create a second axios instance.
2. **Server data lives in TanStack Query.** Zustand is for client/UI state only. `useState` is for local
   component state only. Use XState only for real multi-step workflows (read `reactjs-xstate` before
   adding the dependency).
3. **Endpoints come from `src/services/api-endpoints.ts`.** Paths are relative to the base URL (for
   example `/user`), never `/api/v1/apps/...`.
4. **Env only via `src/config/env.ts`.** Never read `import.meta.env` elsewhere. New keys are `VITE_*`
   and go in `env/.env.example` **and** the zod schema in `env.ts`.
5. **Routes and menus go together.** Every user-facing page gets a route in `src/routes/*.routes.tsx`
   **and** a menu entry in `src/config/menu/*`, unless the task explicitly says the route is hidden,
   redirect-only or modal-only. Never hardcode nav arrays in layout components.
6. **File placement** (see `.claude/rules/architecture.md` and `reactjs-architecture`):
   - pages hold one thin file each;
   - domain code goes in `src/features/<domain>/<feature>/{components,hooks,constants,config,types,utils,store,schemas,mocks}`;
   - generic cross-feature code goes in `src/modules/<name>/` (create it per `reactjs-modules`);
   - shadcn primitives go in `src/components/ui/`, shell components in `src/components/layouts/`, and
     third-party adapters in `src/components/wrappers/`.
   - `.tsx` files hold no inline types, constants, config objects, helpers or mock arrays. Extract them.
7. **Imports** use the `@/` alias across folders. Relative imports are fine only inside the same
   feature (for example `../constants/...`).
8. **UI:** follow `.claude/rules/web/ui-design.md` and the `reactjs-ui-design` playbook (§4 UI below):
   shadcn primitives first, `components/common` patterns, `DataTable` for lists, shadcn semantic token
   classes only (no inline styles, raw colors or arbitrary values), modern-minimal and slightly rounded.
   Support light and dark (the `.dark` class on `<html>`). Header, sidebar and main must not overlap.
   Bounded scroll regions use `PerfectScrollArea`. Look at the result with `npm run ui:snapshot`.
9. **Every async state is handled:** loading, error (`getErrorMessage(error)`) and empty.
10. **Forms** use React Hook Form + Zod. Map backend 422 field errors with
    `applyApiFieldErrors(error, setError, fields)`.
11. **Icons** use Phosphor via `renderIcon({ icon: 'users' })` or `<i className="ph ph-users" />`; the
    CSS is imported in `main.tsx`.
12. **Tests and checks:** add or adjust Vitest tests for logic, hooks, services and guards. Run
    `npm run typecheck && npm run lint && npm run test:ci && npm run build`. ESLint fails on any warning.
13. Do not add npm packages without checking `package.json` first. Prefer what is installed.

Extend through these patterns. Changing existing code is allowed when the task needs it, as long as you
update its tests.

## 4. Building blocks

### UI — look, components and review

- **Rules (always on):** [`.claude/rules/web/ui-design.md`](../../.claude/rules/web/ui-design.md) —
  modern, minimal, calm; neutral surfaces with one accent; `rounded-md` controls, `rounded-xl` surfaces;
  1px quiet borders, `shadow-xs` at rest; Inter `text-sm` body; designed loading/empty/error states.
- **Playbook:** [`reactjs-ui-design`](../../.claude/skills/reactjs-ui-design/SKILL.md) — tokens, page
  recipes (dashboard, list/CRUD, form, detail, auth) with code, lucide → Phosphor map, review checklist.
  Where another `reactjs-*` skill shows markup, the playbook's visual rules win.
- **Component priority:**
  1. `src/components/ui/` — shadcn primitives, themed to the semantic tokens.
  2. Missing but available in shadcn → install it, never hand-roll it (below).
  3. Compose from `src/components/common/` (`PageHeader`, `StatCard`, `EmptyState`, `SectionCard`,
     `StatusBadge`, `ConfirmDialog`, `LoadingState`, `ErrorFallback`, `StatusScreen`) and
     `src/modules/data-table/` (`DataTable`, `DataTableToolbar`, `DataTableColumnHeader`,
     `DataTablePagination`, `DataTableRowActions`).
  4. Hand-written markup only for static, behavior-less surfaces.
- **Tokens:** shadcn semantic classes (`bg-background`, `bg-card`, `bg-muted`, `text-foreground`,
  `text-muted-foreground`, `border-border`, `ring-ring`, `bg-primary`, `success`/`warning`/`info`/
  `destructive`, `chart-1…5`) from `src/styles/variable.css` → `tailwind.css`. Re-brand by changing the
  semantic variables only. Legacy aliases (`bg-background-primary`, `text-font-*`,
  `border-border-primary`) are for old code only.
- **See what exists:** the `/ui-kit` page (dev builds only) renders every primitive and pattern in both
  themes. Add new generic patterns there.
- **Review loop (mandatory before "done"):**
  ```bash
  npm run ui:snapshot -- --route /administrator/user            # light + dark, desktop + mobile
  npm run ui:snapshot -- --route / --route /ui-kit --theme dark # several routes / one theme
  ```
  It serves the app with a mocked API (fixtures in `scripts/ui-snapshot/fixtures/`; add one for a new
  endpoint) and writes PNGs to `.ui-snapshots/`. Open every PNG and check it against the playbook §8
  checklist, fix, re-run.

### Services

```ts
// src/services/note.service.ts
import type { Note } from '@/types/models'
import { API_ENDPOINTS } from './api-endpoints'
import { createResourceService } from './api-factory-crud.service'

export interface INoteCreatePayload { title: string; body?: string | null; tags?: string[] }
export interface INoteUpdatePayload extends Partial<INoteCreatePayload> { id: string }

// add (POST /add, 201) · update (PUT /update) · delete({id}) · getOne({id}) · getAll(FindDTO) → { items, pagination }
export const noteService = createResourceService<Note, INoteCreatePayload, INoteUpdatePayload>(API_ENDPOINTS.NOTE.BASE)
```

For non-CRUD calls, use `apiRequests.get/post/put/patch/delete/list/upload` from
`api-factory.service.ts`. Use `apiRequests.envelope(config)` when you need `metaData`. Endpoints where a
401 means "bad credentials" (login, 2FA, register, password reset…) are listed in `NO_REFRESH_ENDPOINTS`
in `api-client.ts`. Add new public auth endpoints there.

### Query hooks

```ts
// src/features/<domain>/note/constants/note.constants.ts
export const NOTE_QUERY_KEYS = { all: ['notes'] as const, list: (q: object) => ['notes', 'list', q] as const }

// src/features/<domain>/note/hooks/useNoteList.ts
export function useNoteList(query: FindDTO) {
  return useQuery({ queryKey: NOTE_QUERY_KEYS.list(query), queryFn: () => noteService.getAll(query), placeholderData: keepPreviousData })
}

// mutation: invalidate the list, toast via sonner
const qc = useQueryClient()
useMutation({ mutationFn: noteService.add, onSuccess: () => { qc.invalidateQueries({ queryKey: NOTE_QUERY_KEYS.all }); toast.success('Note created') } })
```

Use `import { toast } from 'sonner'` for toasts. The `<Toaster>` is already mounted in `AppProviders`.

### Errors

`ApiError` (from `@/services/api-error`) has `status`, `code` (`'VALIDATION_ERROR' | 'CONFLICT' | … |
'NETWORK_ERROR'`), `message`, `details` (422 → `[{field, message}]`) and `requestId`. Use
`isApiError(e)` and `getErrorMessage(e, fallback)`. `ACCOUNT_NOT_VERIFIED` is only returned by login.

### Guards and roles

- `AuthGuard` resolves the session (`/auth/me`), shows a loader, redirects anonymous users to
  `/auth/login?redirect=…`, and shows `ServerUnavailable` with a retry when the API is down.
- `GuestGuard` redirects signed-in users away from guest-only pages to a safe `redirect`.
- `RoleGuard allowedRoles={[...]} requiredPrivileges={[...]}` sits inside AuthGuard. Superusers
  (`SUPERUSER_ROLES` = `admin`, `owner`, which mirrors `BE_SUPERUSER_ALIASES`) always pass. Denied users
  see the 403 page in place. `user.role` is the backend permission alias, and `user.permission.privileges`
  holds the privilege strings. The backend remains the authority.

### Menus

`IMenu` entries live in `src/config/menu/app.menu.ts` (`APP_MENU`, for every signed-in user) and
`administrator.menu.ts` (`ADMINISTRATOR_MENU`, rendered only for admins). `path` must match a route.
IDs must be unique across `ALL_MENUS()`; see `.claude/skills/reactjs-menu-config/SKILL.md` for the ID
table. `icon` is a Phosphor name (`'squares-four'`, `'users'`).

## 5. Recipes

### 5.1 Add a page (route + menu)

1. Build the UI in a feature: `src/features/<domain>/<feature>/components/<Name>View.tsx`, and export
   it from the feature's `index.ts`. Start from the matching `reactjs-ui-design` page recipe:
   `PageHeader` → toolbar/tabs → content surfaces (`StatCard`, `SectionCard`, `DataTable`).
2. Create a thin page at `src/pages/<area>/<Name>Page.tsx` (default export) that renders the view.
3. Register a lazy route:
   - signed-in pages go in the `children` of `src/routes/main.routes.tsx`;
   - admin pages go in `src/routes/admin.routes.tsx` (already wrapped in `RoleGuard`);
   - public auth pages go in `src/routes/auth.routes.tsx`.
4. Add the menu entry to `APP_MENU` or `ADMINISTRATOR_MENU`, with a unique `id`, a `path` equal to the
   route, an icon, and `seo.title` (used for the page title).
5. Handle loading (skeletons), error (destructive `Alert` + retry) and empty (`EmptyState`) states.
   Review with `npm run ui:snapshot -- --route <path>` (light/dark, desktop/mobile) and fix what you see.
6. Add a test for any non-trivial logic, then run typecheck, lint, test:ci and build.

### 5.2 Call a new backend endpoint

1. Read the contract in `docs/api-spec.md` / `docs/api/<module>.md`.
2. Add the TS types to `src/types/models.d.ts` (response) and to the service file (payloads). Mirror the
   backend DTO field by field (camelCase, nullable where the backend allows `null`).
3. Add the path to `API_ENDPOINTS` (a `BASE` for CRUD modules).
4. Add or extend `src/services/<module>.service.ts` (`createResourceService` or `apiRequests`).
5. Wrap it in a TanStack Query hook inside the feature that uses it. Never call it from a component
   directly.
6. Test the service with the axios mock adapter (`src/test/axios-mock.ts`; see
   `services/module-services.test.ts`).

### 5.3 Add a feature module

Create `src/features/<domain>/<feature>/` with only the subfolders you need (`components/`, `hooks/`,
`constants/`, `config/`, `types/`, `utils/`, `store/`, `schemas/`, `mocks/`) plus an `index.ts`
exporting the public surface. `<domain>` is the business area (`administrator`, `dashboard`…). Use
`shared` for cross-domain features such as `auth`. Follow `.claude/skills/reactjs-features/SKILL.md`.

### 5.4 Add a form

Put the zod schema in `features/<…>/schemas/<name>.schema.ts`. Use `useForm({ resolver:
zodResolver(schema) })` with the shadcn `Form` components from `@/components/ui/form`. In `onError` of
the mutation, call `applyApiFieldErrors(error, form.setError, ['email', 'username'])` and show the
remaining message with `getErrorMessage`. See `features/shared/auth/components/LoginForm.tsx`.

### 5.5 Add an env variable

Add `VITE_X=` to `env/.env.example` (and your local `env/.env`), add it to `envSchema` plus `AppEnv` and
the return value in `src/config/env.ts`, and read it as `env.<group>.<key>`. Values are baked in at build
time. Docker builds take them as `--build-arg` (see `Dockerfile`). Follow
`.claude/skills/reactjs-manage-env/SKILL.md`.

### 5.6 Add a shadcn primitive

Check `src/components/ui/` first. If shadcn has the component, install it **from `apps/web`**:

```bash
npx shadcn@latest add <name> [<name> ...]     # never with -y / --overwrite
```

The CLI output is not final. Post-install checklist (details in `reactjs-ui-design` §3):

- [ ] **No blind overwrites:** don't pass `-y`/`--overwrite`; answer "no" when it offers to overwrite an
      existing primitive (they are themed and React 18). If a file changed, diff it and restore the themed parts.
- [ ] **Location:** files must land in `src/components/ui/` (the CLI resolves `@/` via `paths` in
      `apps/web/tsconfig.json`). A literal `apps/web/@/` folder means the alias broke — move the files and
      delete it.
- [ ] **`cn`:** the CLI may write `from "cn"` and install a junk `cn` package → use `@/utils/cn` and
      `npm uninstall cn` (ESLint blocks `from 'cn'`).
- [ ] **Radix:** import from the unified `radix-ui` package (`import { Dialog as DialogPrimitive } from 'radix-ui'`);
      `@radix-ui/*` imports are lint-blocked.

- [ ] **Icons:** replace every `lucide-react` import with a Phosphor `<i className="ph ph-…" aria-hidden="true" />`
      (lucide → Phosphor map in the playbook); `lucide-react` must not end up in `package.json`.
- [ ] **React 18 refs:** components that render a DOM element and may be used with `asChild` or as a
      trigger use `React.forwardRef` (mirror `button.tsx`); shadcn's current output assumes React 19.
- [ ] **Tokens:** semantic classes only; radius/shadow per `ui-design.md`; drop `dark:` overrides the
      tokens already handle.
- [ ] Keep Radix behavior (`asChild`, refs, `aria-*`, focus, portals) intact.
- [ ] `npm run typecheck && npm run lint`, add it to `/ui-kit`, and look at it with `npm run ui:snapshot`.

## 6. Mock data (POC scope only)

Use this only when the project scope is POC (`.claude/rules/project-scope.md`) or when the task
explicitly asks for mock data. Otherwise call the real backend.

- Source datasets live in the repo-root `data/` folder (today `data/mock/mock-sentiment-layanan-publik.json`).
  Copy what you need into `apps/web/public/data/` so Vite serves it statically.
- Every JSON mock uses the envelope `{ "metaData": { "status": true, ... }, "data": [...] }`.
- Mirror the real API layer with three files, created once: `src/services/mock-client.ts` (a `fetch`
  wrapper for `/data/*`), `src/services/mock-endpoints.ts` (`MOCK_ENDPOINTS` path constants) and
  `src/services/mock.service.ts` (`mockRequest<T>(path)`). Domain services call
  `mockRequest(MOCK_ENDPOINTS.X)`, never a raw `fetch('/data/…')`. Hooks and components stay the same as
  with the real API, so you can switch later by swapping the service implementation.
- Register datasets in `docs/mock-data.md`.

None of these mock files exist yet; this boilerplate talks to the real backend.

## 7. Commands

From `apps/web`:

```bash
npm run dev            # Vite on http://localhost:3000 (proxy /api/v1/apps → DEV_PROXY_TARGET)
npm run typecheck      # tsc for app + node configs
npm run lint           # eslint, 0 warnings allowed   (npm run lint:fix to autofix)
npm run format:check   # prettier                     (npm run format to write)
npm run test           # vitest in watch mode
npm run test:ci        # vitest run (what CI and the root `npm run ci` use)
npm run build          # production build → build/   (build:staging uses env/.env.staging)
npm run preview        # serve build/ on :4173 with the same API proxy
npm run ui:snapshot -- --route <path>   # screenshots (light/dark, desktop/mobile, mocked API) → .ui-snapshots/
```

UI kit: open `/ui-kit` on the dev server to see every primitive and pattern.

From the repo root: `npm run dev:web`, `npx nx run web:test`, `npm run ci`.

## 8. Testing

- Vitest with jsdom; setup is in `src/test/setup.ts`, and tests match `src/**/*.test.{ts,tsx}`.
- `renderWithProviders(ui, { route, routes, path, queryClient })` (`src/test/render.tsx`) wraps
  QueryClient (no retries), Tooltip and MemoryRouter.
- `createMockAdapter(handler)` (`src/test/axios-mock.ts`) answers axios requests without a network. Pair
  it with `ok(data, { pagination })` and `fail(status, message, errorCode)` to return backend-shaped
  envelopes.
- Examples: `services/api-client.test.ts` (refresh/401 behaviour), `routes/guards/guards.test.tsx`,
  `features/shared/auth/components/LoginView.test.tsx`, `config/env.test.ts`.
- **E2E smoke suite (Playwright)** in `apps/web/e2e/` (config `apps/web/playwright.config.ts`, details in
  [`e2e/README.md`](e2e/README.md)): sign-in, the app shell, the admin users page and sign-out against
  the **real** backend. From the repo root, `npm run test:e2e -- --docker` (throwaway Mongo/Redis, seed,
  backend, Playwright, teardown) or `E2E_MONGO_URI=… E2E_REDIS_URL=… npm run test:e2e` (your own
  disposable instances). From `apps/web`, `npm run test:e2e` runs only Playwright against an already
  running backend. It is **not** part of the root `npm run ci`; GitLab runs it in the `web:e2e` job.

## 9. Pitfalls

- `npm run test` is watch mode and never exits in scripts. Use `npm run test:ci`.
- Login looks fine but every call returns 401 over plain HTTP (a LAN IP, or Docker on :8080): the backend
  sets Secure cookies, so set `BE_COOKIE_SECURE=false` for HTTP setups.
- Do not put `/api/v1/apps` in endpoint constants. It is the base URL, and the proxy strips it.
- In `BE_AUTH_PROVIDER=supabase` mode, the web app has no Supabase client and `/auth/refresh` does not
  exist. Treat that mode as API-only until a Supabase JS login is added.
- Register, forgot-password, change-password and 2FA-settings **pages do not exist yet**. The service
  functions do (`auth.service.ts`). The user admin page (`/administrator/user`) lists and searches
  users, has an "Add user" dialog, and row actions (reset password, block/activate, delete).
- `index.html` placeholders are `%VITE_*%`, filled by `vite.config.ts`; the defaults are in
  `HTML_ENV_DEFAULTS`.

## 10. Documentation map

| Need | Read |
|---|---|
| Folder layout, naming, placement | `.claude/skills/reactjs-architecture/SKILL.md` |
| Feature folders | `.claude/skills/reactjs-features/SKILL.md` |
| Reusable modules | `.claude/skills/reactjs-modules/SKILL.md` |
| Services, endpoints, payload types | `.claude/skills/reactjs-service/SKILL.md`, `.claude/skills/reactjs-api-design/SKILL.md` |
| TanStack Query | `.claude/skills/reactjs-tanstack-query/SKILL.md` |
| State choice (Query / Zustand / XState / RHF) | `.claude/skills/reactjs-state-management/SKILL.md` |
| Errors | `.claude/skills/reactjs-error-handling/SKILL.md` |
| Forms | `.claude/skills/reactjs-form/SKILL.md` |
| Guards / roles | `.claude/skills/reactjs-auth-guard/SKILL.md` |
| Admin CRUD pages | `.claude/skills/reactjs-administrator/SKILL.md` |
| Shell, sidebar, menus | `.claude/skills/reactjs-app-layout/SKILL.md`, `.claude/skills/reactjs-sidebar/SKILL.md`, `.claude/skills/reactjs-menu-config/SKILL.md` |
| Tables, lists, pagination (`src/modules/data-table/`) | `.claude/skills/reactjs-data-display/SKILL.md` |
| **Any UI: look, components, page recipes, review loop** | **`.claude/rules/web/ui-design.md` + `.claude/skills/reactjs-ui-design/SKILL.md` (load first)** |
| Figma/mockup → React, tokens/re-brand, theme switch, quality gate | `.claude/skills/reactjs-slicing-ui/SKILL.md`, `.claude/skills/reactjs-design-system/SKILL.md`, `.claude/skills/reactjs-switch-theme/SKILL.md`, `.claude/skills/reactjs-anti-slop/SKILL.md` |
| Responsive, scroll regions | `.claude/skills/reactjs-responsive/SKILL.md` |
| Icons | `.claude/skills/reactjs-icon/SKILL.md` |
| Charts / maps | `.claude/skills/reactjs-chart/SKILL.md`, `.claude/skills/reactjs-map/SKILL.md` (tactical override archived in `.claude/skills-library/reactjs-tactical-map/SKILL.md`) |
| Filters / dashboard widgets | `.claude/skills/reactjs-dynamic-filter/SKILL.md`, `.claude/skills/reactjs-dynamic-widget/SKILL.md` |
| Env vars | `.claude/skills/reactjs-manage-env/SKILL.md` |
| index.html meta / SEO | `.claude/skills/reactjs-seo-html/SKILL.md` |
| Workflows (XState) | `.claude/skills/reactjs-xstate/SKILL.md` |
| Backend contract | [`docs/api-spec.md`](../../docs/api-spec.md) |

## 11. Definition of done (web)

- [ ] No API calls in components; services use `API_ENDPOINTS` and `apiRequests`/`createResourceService`.
- [ ] Server data is in TanStack Query with feature-scoped query keys; mutations invalidate them.
- [ ] Types mirror the backend DTOs (`src/types/models.d.ts`), with no `any`.
- [ ] Route and menu entry were added together (or the route is explicitly hidden).
- [ ] UI follows `.claude/rules/web/ui-design.md`: shadcn primitives, `components/common` patterns, `DataTable`
      for lists, semantic tokens, designed loading/error/empty states, no layout overlap.
- [ ] Looked at it: `npm run ui:snapshot -- --route <path>` PNGs (light/dark, desktop/mobile) reviewed against
      the `reactjs-ui-design` §8 checklist and issues fixed.
- [ ] No inline types, constants or config in `.tsx` files; `@/` imports are used across folders.
- [ ] `npm run typecheck`, `npm run lint`, `npm run format:check`, `npm run test:ci` and `npm run build` pass.
- [ ] `changelog/web.md` is updated.
