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
