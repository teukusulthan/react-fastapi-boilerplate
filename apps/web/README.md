# Web — React + Vite

The single-page app for the boilerplate. It provides a login flow (with 2FA and email verification), an
authenticated app shell (header, config-driven sidebar, main area), a dashboard placeholder, and an admin
user list. It talks to the FastAPI backend through `/api/v1/apps`. The dev port is **3000**.

- Conventions and recipes for contributors and AI agents: [`AI_GUIDE.md`](AI_GUIDE.md)
- Backend contract: [`../../docs/api-spec.md`](../../docs/api-spec.md)

## Stack

React 18 · TypeScript 5.9 (strict) · Vite 7 · React Router 7 · TanStack Query 5 · Zustand 5 · axios ·
React Hook Form 7 + Zod 4 · Tailwind CSS v4 · shadcn/ui (Radix) · sonner · Phosphor icons ·
react-perfect-scrollbar · date-fns · Vitest 4 + Testing Library · ESLint 9 (flat) · Prettier.

## Getting started

Node ≥ 20.19 (`.nvmrc`: 24).

```bash
# from the repo root (recommended): installs deps and creates env/.env from env/.env.example
npm run setup:web
npm run dev:web            # http://localhost:3000  (or `npm run dev` for backend + web together)

# or inside apps/web
npm ci
cp env/.env.example env/.env
npm run dev
```

The backend must be running on `DEV_PROXY_TARGET` (default `http://localhost:8020`). Sign in with the
bootstrap admin created by `npm run seed`.

## Scripts

| Script | What it does |
|---|---|
| `npm run dev` | Vite dev server on :3000, proxying `/api/v1/apps/*` → `DEV_PROXY_TARGET` (prefix stripped) |
| `npm run build` / `build:staging` | Production build into `build/` (`--mode staging` reads `env/.env.staging`) |
| `npm run preview` | Serve `build/` on :4173 with the same proxy |
| `npm run typecheck` | `tsc` for `tsconfig.app.json` and `tsconfig.node.json` |
| `npm run lint` / `lint:fix` | ESLint, zero warnings allowed |
| `npm run format` / `format:check` | Prettier |
| `npm run test` / `test:ci` | Vitest watch mode / single run (CI) |
| `npm run ui:snapshot -- --route <path>` | Screenshots of routes (light/dark, desktop/mobile) with a mocked API → `.ui-snapshots/` |

## Environment

Env files live in `env/` (not the app root). Only `VITE_*` keys reach the browser, and they are read
**only** through `src/config/env.ts` (validated with zod). Values are baked in at build time.

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1/apps` | API base: a relative path (proxied) or an absolute `http(s)` URL |
| `VITE_APP_NAME` | `App` | App name (UI and `index.html` `%VITE_APP_NAME%`) |
| `VITE_APP_DESCRIPTION` | `''` in `env.ts` (`Internal web application` in `index.html`) | Meta description |
| `VITE_MAPBOX_TOKEN` | _(empty)_ | Only for future Mapbox features |
| `DEV_PROXY_TARGET` | `http://localhost:8020` | Dev/preview proxy target; read by `vite.config.ts` only, never exposed |

## How it talks to the backend

- Every request goes to `VITE_API_BASE_URL` + an endpoint from `src/services/api-endpoints.ts`.
- Auth uses httpOnly cookies (`token`, `refresh_token`) set by the backend. axios sends them with
  `withCredentials`. On a 401, the client calls `POST /auth/refresh` once (single-flight) and retries.
  If that fails, it signs out and redirects to `/auth/login?redirect=…`.
- Responses are the backend envelope `{metaData, data}`. Services resolve to `data` (or
  `{items, pagination}` for lists) and reject with `ApiError`.

## Project structure

See [`AI_GUIDE.md` §2](AI_GUIDE.md#2-layout) for the annotated tree. In short: `pages/` (thin route
files) → `features/<domain>/<feature>/` (components, hooks, constants…) → `services/` (API) →
`stores/` (client state only). The shell lives in `components/layouts/`, primitives in
`components/ui/`, menus in `config/menu/`, and routes and guards in `routes/`.

## UI

The UI is modern, minimal and slightly rounded, built **shadcn-first**.

- Rules: [`.claude/rules/web/ui-design.md`](../../.claude/rules/web/ui-design.md) · playbook:
  [`reactjs-ui-design`](../../.claude/skills/reactjs-ui-design/SKILL.md) · summary in
  [`AI_GUIDE.md` §4](AI_GUIDE.md#4-building-blocks).
- Component priority: `src/components/ui/` (shadcn primitives) → install a missing shadcn component →
  compose from `src/components/common/` (`PageHeader`, `StatCard`, `EmptyState`, `SectionCard`,
  `StatusBadge`, `ConfirmDialog`, `RelativeTime`) and `src/modules/data-table/` (`DataTable`) → hand-written markup only
  for static surfaces.
- Tokens: shadcn semantic classes from `src/styles/variable.css` (light + `.dark`) mapped in
  `src/styles/tailwind.css`. Re-brand by changing the semantic variables (`--primary`, `--ring`,
  `--radius`, chart colors).
- UI kit: `/ui-kit` on the dev server (dev builds only) shows every primitive and pattern.
- Review: `npm run ui:snapshot -- --route <path>` and look at the PNGs before calling UI work done.

Adding a shadcn component:

```bash
npx shadcn@latest add <name>      # from apps/web (components.json → src/components/ui); never -y / --overwrite
```

Then: decline overwrites of existing (themed) primitives, swap `lucide-react` icons for Phosphor
(`<i className="ph ph-…" />`), use `React.forwardRef` where the component may be an `asChild` trigger
(React 18), import Radix from `radix-ui` (not `@radix-ui/*`), keep only semantic token classes, import `cn`
from `@/utils/cn` (not `"cn"`; `npm uninstall cn` if the CLI added it), run `npm run typecheck && npm run lint`, and add it to `/ui-kit`. Full checklist:
[`AI_GUIDE.md` §5.6](AI_GUIDE.md#56-add-a-shadcn-primitive).

## Docker

`Dockerfile` builds the SPA and serves it with `nginxinc/nginx-unprivileged` on **:8080**. nginx proxies
`/api/v1/apps/` to `BACKEND_URL` (default `http://backend:8020`) and falls back to `index.html` for
client routes. `VITE_*` values can be passed as build args:

```bash
docker build --build-arg VITE_APP_NAME="My App" -t app-web apps/web
```

For the full stack (web on http://localhost:8080), run `npm run docker:up` from the repo root.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Invalid environment configuration (check env/.env*)` | A `VITE_*` value fails the schema in `src/config/env.ts` |
| Every API call 404s / goes to the wrong host | The backend is not on `DEV_PROXY_TARGET`, or `VITE_API_BASE_URL` was changed |
| Logged in, then immediately logged out over plain HTTP | Set `BE_COOKIE_SECURE=false` in the backend `.env` (Secure cookies need HTTPS) |
| "Server unavailable" screen | Backend down or `/auth/me` returning 5xx; the screen has a retry |
| Port 3000 busy | `strictPort` is on; free the port (Vite will not pick another) |
