# Web Changelog

Tracks all frontend changes across sprints — screens added, components built, bugs fixed, design tokens applied.

Append-only. Newest entries at the top. Updated whenever a frontend task is created or completed.

---

<!-- ENTRY FORMAT:
### YYYY-MM-DD · [Sprint NN — slug](../sprint/active/NN-slug/sprint.md) · Task: [task title](../sprint/.../frontend/NN-task.md) · STATUS

**Event:** Task created | Task completed | Files modified
**Files:** `path/to/file.tsx`, `path/to/style.css`
> One-line summary of what changed or was delivered.
-->

### 2026-10-12 · Boilerplate (no sprint) · Task: Docs consistency check + archived domain skills · ✅ Done

**Event:** Files modified
**Files:** `scripts/docs-check/**`, `package.json`, `.gitlab-ci.yml`, `.pre-commit-config.yaml`, `.claude/skills-library/**`, `AGENTS.md`, `README.md`, `.claude/**`, `apps/web/AI_GUIDE.md`
> New `npm run docs:check` (also the last step of `npm run ci`, GitLab job `docs:check`, pre-commit hook)
> fails on doc drift: broken links/paths, unknown npm scripts, env vars, code-block imports, and
> `docs/api-spec.md` vs the live FastAPI routes. Domain recipes from other projects moved from
> `.claude/skills/` to `.claude/skills-library/` (not auto-loaded; enable on demand).

### 2026-10-12 · Boilerplate (no sprint) · Task: Playwright e2e smoke suite against the real backend · ✅ Done

**Event:** Files modified
**Files:** `apps/web/{playwright.config.ts,tsconfig.e2e.json,tsconfig.json,package.json,package-lock.json,eslint.config.js,.gitignore,.prettierignore,.dockerignore}`, `apps/web/e2e/**`, `apps/web/src/components/layouts/AppSidebar.tsx`, `scripts/e2e.mjs`, `package.json`, `.gitlab-ci.yml`
> Added a Playwright smoke suite (`apps/web/e2e/`, `@playwright/test` 1.63.0): admin sign-in → dashboard
> → users table shows the admin → sign out, plus the anonymous redirect and the wrong-credentials error.
> `npm run test:e2e` (apps/web) runs Playwright against a running backend; the root `npm run test:e2e`
> (`scripts/e2e.mjs`) seeds, starts an isolated backend, runs the suite and tears everything down
> (`--docker` for throwaway Mongo/Redis). New GitLab job `web:e2e`. The sidebar's links now sit in a
> `<nav aria-label="Main navigation">` landmark. `npm run typecheck` also checks `e2e/` (`tsconfig.e2e.json`).

### 2026-10-12 · Boilerplate refactor (no sprint) · Task: web app rebuild against the new backend contract · ✅ Done

**Event:** Files modified
**Files:** `apps/web/**` (`package.json`, `vite.config.ts`, `eslint.config.js`, `index.html`, `env/.env.example`, `src/{components,config,features,pages,routes,services,stores,types,lib,test}/**`)
> The web app now reaches the backend (`/api/v1/apps` via the Vite or nginx proxy) using httpOnly cookie
> auth. It has a typed envelope and `ApiError`, single-flight refresh, guards bootstrapped from
> `/auth/me`, a real app shell with a config-driven sidebar, login with 2FA, a verify-email page, an
> admin user list, and TanStack Query. Typecheck, ESLint (0 warnings), Prettier, about 70 Vitest tests
> and the build all pass.

**BREAKING CHANGES**
- **Scripts:**
  - Added `typecheck`, `lint`, `lint:fix`, `format`, `format:check`, `test` (watch) and `test:ci`.
  - `build` outputs to `build/`.
  - Removed `start`, `start:prod` (`server.js`), `build:prod`, `build:analyze` and `find-deadcode`.
  - The dev server is pinned to port 3000 (`strictPort`).
- **Env:**
  - `VITE_API_BASE_URL` now defaults to `/api/v1/apps`. It is read only via `src/config/env.ts` (zod),
    and `process.env.*` no longer works.
  - New `VITE_APP_NAME`, `VITE_APP_DESCRIPTION` and `DEV_PROXY_TARGET` (dev proxy target, default
    `http://localhost:8020`).
  - `index.html` uses `%VITE_*%` placeholders (formerly `{{…}}`).
- **API layer:**
  - Services resolve to unwrapped `data` (lists become `{items, pagination}` with
    `totalElements`/`totalPages`) and reject with `ApiError {status, code, message, details, requestId}`.
  - The old `ApiResponse {success, message}` types are gone.
  - CRUD services take `{id}` for `delete` and `getOne`.
- **Auth state:**
  - `useAuthStore` is no longer persisted to localStorage and holds no token; the cookies are the
    source of truth.
  - Guards are status-based (`unknown`/`authenticated`/`anonymous`).
  - `RoleGuard` renders 403 in place.
- **Routes:**
  - The auth and admin routes are now actually mounted: `/auth/login` and the new
    `/auth/verify-email?token=`.
  - `/` is the authenticated dashboard (the marketing landing page was removed).
  - `/administrator/user` is admin-only.
- **Dependencies:**
  - **Removed:** moment, dayjs, recharts, react-table v7, lodash, immer, next-themes, sass,
    crypto-js, @babel/standalone, web-vitals, the PWA/service worker, and others.
  - **Added:** TanStack Query, Vitest, ESLint 9 flat config, Prettier, `@tailwindcss/vite`, and
    `@phosphor-icons/web` (icons are bundled; there is no `/cdn-assets` proxy).
  - One toast system (sonner).
