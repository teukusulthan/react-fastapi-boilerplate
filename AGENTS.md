# AGENTS.md — Guide for AI coding agents (and humans)

This repository is a **company boilerplate**: a FastAPI backend (`apps/backend`) and a React + Vite
web app (`apps/web`) in one Nx-orchestrated monorepo. You build features on top of it. Everything below
matches the current code. If you find a mismatch, trust the code, fix the doc in the same change, and
mention it.

**Read order for any coding task**

1. This file. The essentials are also in `CLAUDE.md`.
2. [`.claude/rules/architecture.md`](.claude/rules/architecture.md): the stack and its enforcement rules.
3. The AI guide of the app you touch: [`apps/backend/AI_GUIDE.md`](apps/backend/AI_GUIDE.md) and/or
   [`apps/web/AI_GUIDE.md`](apps/web/AI_GUIDE.md). These hold the conventions, recipes with code, and
   testing details.
4. The contract: [`docs/api-spec.md`](docs/api-spec.md) (endpoints, envelope, error codes) and
   [`docs/database-schema.md`](docs/database-schema.md).
5. Only then, the one or two skills the task needs (§10). For larger tasks, start with the
   [`orchestra`](.claude/skills/orchestra/SKILL.md) skill. **For any UI task, the first skill is
   [`reactjs-ui-design`](.claude/skills/reactjs-ui-design/SKILL.md)** (with the always-on
   [`.claude/rules/web/ui-design.md`](.claude/rules/web/ui-design.md)).

Do not write files until you know where they belong (§4) and which existing module to copy.

---

## 1. Repository map

| Path | What it is |
|---|---|
| `apps/backend/` | FastAPI service (port **8020**): `api.py`, `core/` (config, app factory, DI, errors, envelope, security, rate limit), `db/` (repository layer: `mongo/`, `supabase/`, `schema.py`), `dto/`, `service/`, `router/` (+ registry), `util/`, `migrations/supabase/`, `scripts/seed.py`, `templates/email/`, `tests/` |
| `apps/web/` | React SPA (dev port **3000**): `src/{components,config,features,modules,pages,routes,services,stores,types,utils,hooks,lib,styles,test}`, `env/`, `vite.config.ts` |
| `apps/orchestra.md` | Short index of features and key files in `apps/` |
| `docs/` | `api-spec.md` (endpoint registry), `api/<module>.md`, `database-schema.md`, `mock-data.md` |
| `changelog/` | `backend.md`, `web.md`, `mobile.md`, `sprint-planning.md`: append-only, newest first |
| `sprint/` | `01-sprint-planning.md`, `backlog/`, `active/`, `archive/` (managed by the `sprint-builder` skill) |
| `brief/`, `mockup/` | Outputs of the brief and HTML-mockup skills (empty in the bare boilerplate) |
| `data/` | Source mock datasets (`data/mock/*.json`) |
| `scripts/` | Cross-platform Node helpers: `setup.mjs`, `dev.mjs`, `py.mjs` (runs the backend venv Python), `web-tool.mjs`, `docker/postgres/*` |
| `.claude/` | `rules/` (always-on rules), `skills/` (on-demand know-how), `commands/` (slash commands), `settings.json` |
| `package.json`, `nx.json` | Root scripts and Nx targets (projects `backend` and `web` via `apps/*/project.json`) |
| `docker-compose.yml` | mongo, redis, optional postgres (profile `postgres`), backend, web (nginx on **8080**) |
| `.gitlab-ci.yml` | Jobs `backend:lint`, `backend:test`, `backend:test-postgres`, `web:lint`, `web:test`, `web:build`, `docker:build` |
| `.pre-commit-config.yaml` | Hygiene hooks, ruff (backend), prettier + eslint (web) |
| `.mcp.json` | MCP servers: github (`GITHUB_TOKEN`), filesystem, design-token-generator (`DESIGN_TOKEN_MCP_URL`) |

There is no `design/` folder and no mobile app in this repo. Rules that mention them apply only once
they exist. Without a `design/` theme, the web UI follows the default look in
[`.claude/rules/web/ui-design.md`](.claude/rules/web/ui-design.md).

## 2. Quick start

Prerequisites: Node ≥ 20.19 (24 recommended), Python ≥ 3.10 (uv recommended), MongoDB and Redis (or
Docker), and libmagic (`apt install libmagic1` / `brew install libmagic`).

```bash
npm install                 # root tooling (Nx)
npm run setup               # backend venv + deps + apps/backend/.env (random secrets); web deps + apps/web/env/.env
npm run docker:infra        # optional: Mongo + Redis in Docker (see docker-compose.yml for the Redis password)
npm run seed                # permissions admin/user + bootstrap admin (credentials printed by setup)
npm run dev                 # backend http://localhost:8020 (/docs) + web http://localhost:3000
```

| Task | Command (repo root) |
|---|---|
| Full quality gate (what CI enforces) | `npm run ci` (= `nx run-many -t lint format-check typecheck test build`) |
| One app only | `npm run dev:backend`, `npm run dev:web`, `npx nx run backend:test`, `npx nx run web:build` |
| Lint / format / tests / types / build | `npm run lint`, `npm run format` (`format:check`), `npm test`, `npm run typecheck`, `npm run build` |
| Docker full stack | `npm run docker:up` → http://localhost:8080 (`docker:down`, `docker:logs`) |
| Docker with Postgres provider | `DB_PROVIDER=supabase docker compose --profile postgres up -d --build` |
| Pre-commit | `uv tool install pre-commit && pre-commit install` |
| UI screenshots for review (light/dark, desktop/mobile, mocked API) | `cd apps/web && npm run ui:snapshot -- --route <path>` → PNGs in `apps/web/.ui-snapshots/` |
| See every UI primitive and pattern | `/ui-kit` route in the dev build (`npm run dev:web`) |

The per-app commands (pytest flags, vitest, Postgres integration tests) are in each app's `README.md`
and `AI_GUIDE.md`.

## 3. Architecture

### How the pieces connect

```
Browser ──► web (Vite :3000 in dev / nginx :8080 in Docker)
              │  /api/v1/apps/*  ──(prefix stripped)──►  backend :8020
              │  httpOnly cookies `token` + `refresh_token` (same origin through the proxy)
              ▼
backend: CORS → RequestContext (X-Request-ID) → [global rate limit] → [payload encryption] → router
         router (thin) → service (rules, raises AppError) → Repository (Mongo | Postgres) ; Redis for sessions/OTP/limits
         every response: {"metaData": {...}, "data": ...}
```

### Backend (details: `apps/backend/AI_GUIDE.md`)

- **App factory:** `core/app_factory.py:create_app()`. Settings come from `core/config.py`
  (pydantic-settings, `BE_*` env, `apps/backend/.env`). Routers are mounted **only** through the
  registry in `router/__init__.py` (`ROUTERS`; toggle with `BE_ENABLED_ROUTERS`).
- **Layers:** `router/` → `service/` → `db.Repository`. Routes and services are **sync** (`def`) and
  run in the threadpool. DI is plain FastAPI `Depends`: providers in `core/deps.py` build repositories
  and services per request (`UsersRepo`, `get_repository(ENTITY)`, `XServiceDep`).
- **DB provider abstraction:** `BE_DB_PROVIDER=mongo` (default) or `supabase` (Postgres via psycopg 3).
  `db/schema.py` declares every entity once: fields, types, unique flags, defaults and the query
  whitelists. Mongo indexes are derived from it at startup. Postgres DDL lives in
  `migrations/supabase/*.sql`. Storage is snake_case with uuid4 ids; JSON is camelCase.
- **Auth provider:** `BE_AUTH_PROVIDER=local` (own HS256 JWT with `sub/exp/iat/jti/type/iss/sid`,
  httpOnly cookies plus body tokens, rotating single-use refresh tokens, Redis revocation, OTP and 2FA,
  lockout) or `supabase` (verify Supabase JWTs, auto-provision users; only `/auth/me` and `/auth/logout`
  are mounted). `X-Internal-Token: $BE_INTERNAL_TOKEN` authenticates system-to-system calls.
- **RBAC:** user → `permission_id` → permission `{alias, privileges[]}`. `role` = the alias. Aliases in
  `BE_SUPERUSER_ALIASES` (`admin,owner`) are superusers. The deps are `require_auth`, `require_admin`,
  `require_privilege("x:y")`, `require_internal_token`, `get_current_user` (user or internal). The
  `roles` resource is a catalogue, not RBAC.
- **Envelope and errors:** `core/responses.py` (`ok`, `created`, `paginated`, `ApiResponse[T]` as the
  `response_model`) and `core/errors.py` (raise `NotFoundError`, `ConflictError`, … and the global
  handlers render `{metaData: {status: false, errorCode, …}, data}`).
- **Lists:** `POST /x/get-all` with `FindDTO` (`page`, `size`, `search`, `searchBy`, `orderBy`, `order`,
  `filters[]`). Only whitelisted fields are accepted; anything else returns 422.
- **Modules:** health, auth, user, group, permission, role (the reference CRUD module), upload (S3).

### Web (details: `apps/web/AI_GUIDE.md`)

- `src/main.tsx` → `AppProviders` (ErrorBoundary, QueryClient, Tooltip, Toaster) → `routes/index.tsx`
  (`createBrowserRouter`: `auth.routes`, `main.routes` with `AuthGuard` + `AppLayout`, `admin.routes`
  with `RoleGuard`, 404).
- Data flow: page (thin) → feature component → TanStack Query hook → service (`createResourceService`
  or `apiRequests`) → `api-client.ts` (axios, `withCredentials`, refresh-on-401, `ApiError`).
- Session: `useAuthStore` (Zustand, not persisted) mirrors `GET /auth/me`; the httpOnly cookies are the
  source of truth.
- Navigation is config-driven: `src/config/menu/app.menu.ts` (`APP_MENU`) and `administrator.menu.ts`
  (`ADMINISTRATOR_MENU`).
- Env vars are read only through `src/config/env.ts` (`VITE_API_BASE_URL` default `/api/v1/apps`).

## 4. Golden rules (cross-cutting)

1. **Respect the layers.** Backend: router → service → repository; never import pymongo or psycopg
   outside `db/`. Web: component → hook → service; never call axios or fetch in components.
2. **One contract.** The backend returns the envelope through `response_model=ApiResponse[...]`. The web
   app consumes it only through `apiRequests` or `createResourceService`. When you change an endpoint,
   update `docs/api-spec.md`, `docs/api/<module>.md`, the web types in `src/types/models.d.ts`, and the
   changelogs **in the same change**.
3. **Security by default.** Every backend router declares an auth dependency. Writes check the
   role or privilege. Input DTOs use `extra="forbid"`. `created_by` comes from the token. Secrets never
   appear in responses or logs. Only whitelisted query fields are allowed.
4. **Schema changes hit both providers:** `db/schema.py` **and** a new `migrations/supabase/NNN_*.sql`.
5. **Configuration** lives only in `apps/backend/core/config.py` + `.env.example` (`BE_*`) and
   `apps/web/src/config/env.ts` + `env/.env.example` (`VITE_*`). There are no hardcoded URLs, secrets or
   ports in code.
6. **No `print()`** in Python (use loguru `{}`-style); use no `console.log` noise in the web app.
7. **Tests come with the change.** Run the verification commands (§8) and report their real output.
   Never claim success you did not observe.
8. **Pages get a route and a menu entry together**, unless the task explicitly says the route is hidden.
9. **Place files by the decision tree** in `.claude/rules/architecture.md`. Domain UI goes in
   `src/features/<domain>/<feature>/`, never directly in `src/components/`.
10. **No new dependencies** (pip or npm) without checking what is installed and saying why. The core
    stack is fixed (§10, Tech stack warning in the architecture rules).
11. **Extend via the documented patterns.** Change existing code when the task needs it, update its
    tests, and do not leave dead code or TODO stubs behind.
12. **UI is shadcn-first and reviewed visually.** Follow `.claude/rules/web/ui-design.md` and the
    `reactjs-ui-design` playbook: shadcn primitives (`src/components/ui/`, install missing ones with
    `npx shadcn@latest add`), page patterns from `src/components/common/`, lists via
    `src/modules/data-table/`, semantic tokens only, modern-minimal and slightly rounded. Look at the
    result with `npm run ui:snapshot` before reporting done.

## 5. Recipes

Each recipe lists the exact files. Code templates are in the app AI guides.

### 5.1 Add a backend resource end to end (e.g. `note`)

Full walk-through with code: [`apps/backend/AI_GUIDE.md` §5.1](apps/backend/AI_GUIDE.md#51-add-a-resource-entity--crud-endpoints-end-to-end).
The reference module to copy is `role` (`dto/role.py`, `service/role.py`, `router/role.py`).

1. `apps/backend/db/schema.py`: add `NOTES = EntitySchema(name="notes", table_setting="TABLE_NOTES", fields=(ID, …, *audit_fields()))` and include it in `ENTITIES`.
2. `apps/backend/core/config.py`: add `TABLE_NOTES: str = "notes"`. `apps/backend/.env.example`: add `BE_TABLE_NOTES=notes`.
3. `apps/backend/migrations/supabase/002_notes.sql`: idempotent DDL, named constraints,
   `set_updated_at` trigger, and the RLS lockdown.
4. `apps/backend/core/deps.py`: `get_notes_repo = get_repository(NOTES)` and the `NotesRepo` alias (or
   use `Depends(get_repository(NOTES))`).
5. `apps/backend/dto/note.py`: `NoteDTO`, `UpdateNoteDTO`, `FindNoteDTO(FindDTO)`, `NoteResponse`.
6. `apps/backend/service/note.py`: `NoteService(CrudService)`, `get_note_service`, `NoteServiceDep`.
7. `apps/backend/router/note.py`: `APIRouter(prefix="/note", tags=["note"], dependencies=[Depends(require_auth)])`
   with add/update/delete/get-one/get-all, each with `response_model`.
8. `apps/backend/router/__init__.py`: append `RouterSpec("note", "router.note")` to `ROUTERS`.
9. `apps/backend/tests/modules/test_notes.py`: CRUD, 404, 409, 422 (whitelist), RBAC. If it is added to
   `MODULES` in `tests/modules/conftest.py`, also add its rows to `tests/modules/test_rbac.py`.
10. Docs: `docs/api-spec.md` (registry rows), `docs/api/note.md`, `docs/database-schema.md`,
    `changelog/backend.md`.
11. If the web app uses it, follow 5.5 and 5.4.
12. Verify: `npm run ci`, plus the Postgres integration tests if you can (§7).

### 5.2 Add an auth-protected, admin or privileged endpoint

- Any signed-in user: router-level `dependencies=[Depends(require_auth)]`, and `user: CurrentUserDep` in
  the route.
- Admin only: `admin: AdminUserDep` in the route (or `Depends(require_admin)` on the router).
- Privilege: `dependencies=[Depends(require_privilege("note:write"))]`. Then grant the privilege by
  adding the string to a permission (`PUT /permission/update-partial {id, addPrivileges: ["note:write"]}`
  or `apps/backend/scripts/seed.py` for defaults).
- Service-to-service: `InternalDep` or `UserOrInternalDep`; the caller sends `X-Internal-Token`.
- Public but abusable: add `dependencies=[Depends(rate_limit("note:public"))]`.
- Add the endpoint to the RBAC tests (401 anonymous, 403 wrong role or internal token) and mark its
  **Auth** column in `docs/api-spec.md`.

### 5.3 Add a setting

- Backend: a typed field in `apps/backend/core/config.py` (`Settings`) → `BE_<NAME>` in
  `apps/backend/.env.example` → a row in `apps/backend/README.md` §Environment. Read it via
  `SettingsDep` (routes) or `get_settings()`. Optional integrations must not break startup; raise
  `ConfigurationError` (503) when used unconfigured.
- Web: the `VITE_<NAME>` key in `apps/web/env/.env.example` → the zod schema and `AppEnv` in
  `apps/web/src/config/env.ts` → a row in `apps/web/README.md` §Environment. Read it as `env.<group>.<key>`.

### 5.4 Add a web page (route + menu)

Details: [`apps/web/AI_GUIDE.md` §5.1](apps/web/AI_GUIDE.md#51-add-a-page-route--menu). Visuals:
load [`reactjs-ui-design`](.claude/skills/reactjs-ui-design/SKILL.md) first and pick its page recipe
(§5: dashboard, list/CRUD, form, detail, auth).

1. `src/features/<domain>/<feature>/components/<Name>View.tsx`, plus hooks and constants as needed,
   exported from `index.ts`.
2. `src/pages/<area>/<Name>Page.tsx`: a thin default export.
3. A lazy route in `src/routes/main.routes.tsx` (signed-in), `admin.routes.tsx` (admin) or
   `auth.routes.tsx` (public auth).
4. A menu entry in `src/config/menu/app.menu.ts` or `administrator.menu.ts` (unique `id`, `path` equal to
   the route, Phosphor `icon`, `seo.title`).
5. Compose the view from `PageHeader` + shadcn primitives + `components/common` patterns (`DataTable`
   from `src/modules/data-table/` for lists), with designed loading, error and empty states.
6. Review it: `npm run ui:snapshot -- --route <path>` (from `apps/web`), open the PNGs, fix issues, then
   `npm run typecheck && npm run lint && npm run test:ci`.

### 5.5 Add a web service for an endpoint

1. Add the types in `apps/web/src/types/models.d.ts`, mirroring the backend response DTO (camelCase,
   nullable where the backend allows it).
2. Add the path in `apps/web/src/services/api-endpoints.ts` (relative, e.g. `NOTE: { BASE: '/note' }`).
3. Create `apps/web/src/services/note.service.ts` using `createResourceService<Note, ICreate, IUpdate>(API_ENDPOINTS.NOTE.BASE)`,
   or `apiRequests.*` for non-CRUD calls.
4. Add a TanStack Query hook in the consuming feature (`hooks/useNoteList.ts`) with query keys in
   `constants/`.
5. Add a service test with `src/test/axios-mock.ts` (pattern: `src/services/module-services.test.ts`).

### 5.6 Add a feature module (web)

`apps/web/src/features/<domain>/<feature>/{components,hooks,constants,config,types,utils,store,schemas}/` +
`index.ts`. Create only the folders you need. Cross-domain features go under `features/shared/`. Generic,
domain-agnostic code reused by 2+ features goes in `src/modules/<name>/` (see the `reactjs-modules`
skill). Follow `.claude/skills/reactjs-features/SKILL.md`.

### 5.7 Change an existing API contract

Update the backend DTO, service and tests → `docs/api-spec.md` + `docs/api/<module>.md` → the web types
and service plus their tests → `changelog/backend.md` and `changelog/web.md` (mark **BREAKING** if
clients must change). Run `npm run ci`.

## 6. Testing strategy

| | Backend (`apps/backend/tests`) | Web (`apps/web/src/**/*.test.ts(x)`) |
|---|---|---|
| Runner | pytest (`--import-mode=importlib`) | Vitest 4 + jsdom + Testing Library |
| Isolation | `conftest.py` scrubs `BE_*` env, ignores `.env`, uses **mongomock** behind the real `MongoRepository` and **fakeredis**; no services needed | axios mock adapter (`src/test/axios-mock.ts`), `renderWithProviders` (`src/test/render.tsx`) |
| Key fixtures and helpers | `make_settings`, `make_app`, `client`, `app_routers` (override to mount routers), `user_factory`, `admin_headers`, `user_headers`, `internal_headers`, `login(user)` | `createMockAdapter`, `ok()`, `fail()`, `createTestQueryClient` |
| Real Postgres | `TEST_POSTGRES_DSN=postgresql://… pytest -m integration` (module tests also run on Postgres; migrations applied automatically). CI job `backend:test-postgres`. | — |
| Must cover | happy path, 404, 409, 422 (DTO and whitelist), RBAC (401/403), no secret leakage | services (paths, payloads, unwrapping), hooks and guards logic, components with logic |

## 7. Definition of done

A task is done only when all of these hold:

- [ ] The code follows the layer and placement rules (§4, the AI guides).
- [ ] Tests were added or updated, and these pass (paste the real result):
  - `npm run ci` from the repo root (lint, format-check, typecheck, test and build for both apps), or
    the narrower equivalents:
  - backend (`apps/backend`): `.venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check . && .venv/bin/python -m pytest`
  - web (`apps/web`): `npm run typecheck && npm run lint && npm run format:check && npm run test:ci && npm run build`
- [ ] **Web UI work:** built per `.claude/rules/web/ui-design.md` (shadcn primitives, `components/common`
  patterns, `DataTable`, semantic tokens, loading/empty/error states), and reviewed visually: run
  `npm run ui:snapshot -- --route <path>` in `apps/web`, open the light/dark and desktop/mobile PNGs,
  check them against the `reactjs-ui-design` §8 checklist and fix what you see.
- [ ] Contract docs are updated (`docs/api-spec.md`, `docs/api/*.md`, `docs/database-schema.md`) where
  the API or schema changed.
- [ ] New settings are documented (`.env.example`/`env/.env.example` and the app README).
- [ ] `changelog/<stack>.md` has an entry (newest first).
- [ ] If the work came from a sprint task file, that file's TODOs, `**Status:**` and the sprint index
  are updated (Sprint Closure Enforcement in `.claude/rules/architecture.md`).

## 8. Pitfalls and gotchas

| Gotcha | What to know |
|---|---|
| Ports | Dev: backend **8020**, web **3000** (`strictPort`). Docker: web/nginx **8080** (`WEB_PORT`), backend published on 127.0.0.1:8020. `vite preview`: 4173. |
| Secure cookies over HTTP | `BE_COOKIE_SECURE` defaults to `true` in code (`false` in `.env.example`). Over plain HTTP (a LAN IP, Docker :8080), keep it `false`, or login "works" but every next call is 401. Production requires `true` and HTTPS. |
| Refresh cookie path | `BE_COOKIE_REFRESH_PATH` matches the **browser** path (`/api/v1/apps/auth/refresh` behind the proxy). Leave `/` unless you know the public path. |
| `BE_ROOT_PATH` | Leave it empty (the proxies strip `/api/v1/apps`). Set `/api/v1/apps` only to use Swagger through the proxy; then direct `:8020/docs` breaks. |
| Emails in dev | `BE_EMAIL_BACKEND=auto` without SMTP prints OTPs and links to the backend log (`[email:console]`). In production without SMTP, email flows return 503 `CONFIGURATION_ERROR`. |
| Rate limits | Auth endpoints: `BE_RATE_LIMIT_AUTH` (10) per IP per 60 s, so repeated manual logins can return 429. |
| Supabase DB mode | The backend never creates tables. Apply `apps/backend/migrations/supabase/*.sql` first, or `/health/ready` stays 503. |
| Supabase auth mode | The web app has no Supabase client yet and `/auth/refresh` is not mounted, so it is API-only. Run the seed after the admin's first sign-in to promote them. |
| libmagic | Required for upload MIME detection (and its tests). Without it, uploads return 503. |
| Redis | Required for sessions, OTP, revocation and rate limits. `npm run docker:infra` sets a Redis password; put it in `BE_REDIS_PASSWORD`. |
| `uv` / `python3` shims | Some agent sandboxes put restricted shims on PATH. Run Python via `apps/backend/.venv/bin/python` or `node scripts/py.mjs`. If `uv pip` is blocked, call the real binary (e.g. `~/.local/bin/uv`) or `npm run setup:backend -- --no-uv`. |
| Watch mode | `npm run test` in `apps/web` is watch mode; scripts and agents use `npm run test:ci` (root `npm test` already does). |
| Strict router registry | A router that fails to import aborts `create_app()`. Use `BE_ENABLED_ROUTERS=health,auth` to isolate the problem. |
| Production guards | `BE_ENVIRONMENT=production` refuses the placeholder `BE_JWT_SECRET`, `BE_COOKIE_SECURE=false`, `BE_RELOAD=true` and `BE_EMAIL_BACKEND=console`. `npm run dev` sets `BE_RELOAD=true`, so do not run it with a production `.env`. |
| Missing web pages | Register, forgot-password, change-password and 2FA settings have services (`auth.service.ts`) but no pages yet. The admin user page is read-only. |

## 9. Not included (and where it would come from)

- **No agent-management plane.** The backend does **not** ship an `agent_mgmt` router or any
  `/agent-mgmt/*` endpoints. The `agent-builder` skill assumes a backend with that router (its Step 0e),
  and its examples use `apps/be/` and `BE_INTERNAL_API_TOKEN`. In this repo the backend is
  `apps/backend/` and the header token is `BE_INTERNAL_TOKEN`. If a project needs a workforce of agents,
  the sprint plan's first sprint (`00-workforce-scaffold`, `sprint-builder` skill) must first add that
  router to the backend as a new module (recipe 5.1, with `InternalDep`/`AdminUserDep` auth and Postgres
  migrations). Only then run `/agent-builder`.
- No mobile app, no `design/` folder, no `.ai/` scaffold CLI, and no `deployment.json` until a command
  creates them.

## 10. AI workflow

### Tech stack (enforced; see `.claude/rules/architecture.md`)

Backend: Python/FastAPI · DB: MongoDB or Supabase Postgres (`BE_DB_PROVIDER`) · Auth: local JWT or
Supabase JWT (`BE_AUTH_PROVIDER`) + `X-Internal-Token` · Web: React 18 + TypeScript + Vite 7 + React
Router 7 + TanStack Query 5 + Zustand 5 + Zod 4 + Tailwind v4 + shadcn/Radix. If a request needs a
different core technology, issue a **TECH STACK WARNING** and stop.

### Context loading

`.claude/rules/**/*.md` are project instructions; Claude Code loads them automatically. The root files
(`architecture.md`, `project-scope.md`) always apply. The nested `backend/orchestra.md` and
`web/orchestra.md` are routers: follow them when you work on that stack. They point to the AI guides and
skills.

| Task size | Load |
|---|---|
| Micro (typo, 1-line) | nothing extra |
| Small (one file) | the app AI guide section and at most one skill |
| Medium (feature, multi-file) | the app AI guide, the stack orchestra rule, and the relevant skills |
| Large (cross-stack) | the `orchestra` skill; parallelize independent backend and web work |

### Skill index

All skills live in `.claude/skills/<name>/SKILL.md`. Load **only** what the task needs.

| Task | Skill |
|---|---|
| **Any UI task** — create/build/design a page, screen, component, dashboard, form, table, dialog or settings page; restyle; "make it look better / less boring"; "buatkan ui", "buatkan halaman", "bikin tampilan" | [`reactjs-ui-design`](.claude/skills/reactjs-ui-design/SKILL.md) **first** (+ `.claude/rules/web/ui-design.md`), then the placement/data skills (`reactjs-architecture`, `reactjs-features`, `reactjs-data-display`, `reactjs-form`, `reactjs-administrator`, …) |
| Any coding task (classify and route) | [`orchestra`](.claude/skills/orchestra/SKILL.md) |
| Backend conventions (API, data, auth, config, async, logging, tests, uploads, naming, deps) | `fastapi-api-design`, `fastapi-data`, `fastapi-crud-collection`, `fastapi-auth`, `fastapi-config`, `fastapi-async-performance`, `fastapi-logging`, `fastapi-unit-test`, `fastapi-file-upload`, `fastapi-file-naming`, `fastapi-dependency-constraints`, `fastapi-virtual-environment` (index: `apps/backend/AI_GUIDE.md` §9) |
| Backend domain patterns from other projects (use only when the task asks for them) | `fastapi-api-gateway`, `fastapi-build-filter-elasticsearch`, `fastapi-create-map`, `fastapi-render-map`, `fastapi-topic`, `fastapi-data-management`, `fastapi-database-init`, `fastapi-mongo` |
| Web conventions (architecture, features, services, state, forms, guards, layout, menus, charts, maps…) | `reactjs-*` (index: `apps/web/AI_GUIDE.md` §10); visual rules always from `reactjs-ui-design` |
| TDD loop for features and bug fixes | [`tdd-workflow`](.claude/skills/tdd-workflow/SKILL.md) |
| HTML mockup pages (only when "HTML mockup"/"static HTML" is explicit; "build a UI/page" in this repo means the React app in `apps/web`) | [`html-ui-styling`](.claude/skills/html-ui-styling/SKILL.md) |
| Convert an HTML mockup into a React feature | [`html-to-react`](.claude/skills/html-to-react/SKILL.md) |
| Copy design-system CSS assets into a folder (init mockup folder) | [`design-apply`](.claude/skills/design-apply/SKILL.md) |
| Generate a new design system (tokens, DESIGN.md) | [`design-system-builder`](.claude/skills/design-system-builder/SKILL.md) |
| Brand, logo, banner, icon design | [`design`](.claude/skills/design/SKILL.md) |
| Apply design tokens / Figma / mockup to app code | `reactjs-ui-design` first, then [`uiux`](.claude/skills/uiux/SKILL.md), `reactjs-slicing-ui`, `reactjs-design-system`, `reactjs-switch-theme` |
| Meta tags / SEO / favicon | [`meta-seo`](.claude/skills/meta-seo/SKILL.md), `reactjs-seo-html` |
| Fuzzy search on local data | [`search-localdata`](.claude/skills/search-localdata/SKILL.md) |
| Product tour / onboarding | [`tour`](.claude/skills/tour/SKILL.md) |
| Brief (client documentation, workforce manifest) | [`brief-builder`](.claude/skills/brief-builder/SKILL.md) |
| App spec (page inventory) | [`spec-builder`](.claude/skills/spec-builder/SKILL.md) |
| Sprint planning, task files, closure | [`sprint-builder`](.claude/skills/sprint-builder/SKILL.md) |
| Local Supabase stack | [`supabase-init`](.claude/skills/supabase-init/SKILL.md) |
| LLM agent (Agno + FastMCP) | [`agent-builder`](.claude/skills/agent-builder/SKILL.md) (read §9 first) |
| Bespoke MCP server | [`mcp-builder`](.claude/skills/mcp-builder/SKILL.md) |
| Author or refine a skill | [`skill-creator`](.claude/skills/skill-creator/SKILL.md) |

If a skill contradicts the code or the AI guides, follow the code and the guides, and report the stale
skill.

### Project lifecycle (run once per project)

| Phase | Invoke | Output |
|---|---|---|
| 1. Brief | `/brief-builder` | `brief/00_OVERVIEW.md`, `brief/NN_FEATURE.md` |
| 2. App spec | skill `spec-builder` | `sprint/00-app-spec.md` |
| 3. Design tokens (optional; without a `design/` theme the default look in `.claude/rules/web/ui-design.md` applies) | skill `design-system-builder` | `design/{platform}/{theme}/` (`DESIGN.md`, CSS) |
| 4. HTML mockups (optional) | skill `html-ui-styling` (+ `design-apply` for CSS assets) | `mockup/{web,mobile}-html/` |
| 5. Supabase (only with `BE_DB_PROVIDER=supabase` / `BE_AUTH_PROVIDER=supabase`) | `/supabase-init` | credentials → `BE_SUPABASE_*` in `apps/backend/.env` |
| 6. Apply design to the app | `/switch-design-system` | tokens in `apps/web/src/styles/` |
| 7. Sprint plan | `/sprint-builder` (or `/setup-sprint`, `/add-sprint`) | `sprint/01-sprint-planning.md`, `sprint/{backlog,active,archive}/…` |
| 8. Agents / MCP (only if the brief has a workforce) | `/agent-builder`, `/mcp-builder` | `apps/agents/<role>/`, `apps/mcp/<server>/` (see §9) |

The apps are **already scaffolded** in this repo. `/bootstrap-project`, `/design-system-setup` and
`/html-ui-slicing` refer to scaffold-system skills that are not bundled in `.claude/skills/`. Skip
`/bootstrap-project` here, and use `design-apply` instead of `/design-system-setup`.

### Development cycle (per task)

1. If the work comes from `sprint/`, check `sprint/active/` (promote from `backlog/` with
   `sprint-builder` if needed) and open the task file.
2. Classify the task size → load the rules, app guide and skill (above).
3. Implement via the recipes (§5) with tests (`tdd-workflow` for features and bug fixes).
4. Verify (§7, including the UI review loop for web UI), update the docs and changelogs, and close the
   sprint task (Sprint Closure Enforcement).

Routine commands: `/generate-api`, `/generate-ui` (React UI, follows `reactjs-ui-design`), `/test-suite`, `/sync-types`, `/review`,
`/fix-issue`, `/dockerize`, `/deploy` (see `.claude/commands/`).

### Decision tree

| Situation | Action |
|---|---|
| New project from this boilerplate | brief → spec → design → (supabase) → switch design system → sprint plan |
| New feature in this project | Check `sprint/active/`. Backend part: recipe 5.1/5.2. Web part: recipes 5.4–5.6. |
| Bug fix | `/fix-issue` flow: reproduce → failing test → fix → `npm run ci` |
| New backend file | `apps/backend/AI_GUIDE.md` §2 (layout) and §5 |
| New web file | `.claude/rules/architecture.md` placement table → `apps/web/AI_GUIDE.md` §2 and §5 |
| "Build/design a UI, page or screen" | React app in `apps/web` (not an HTML mockup unless "HTML mockup" is explicit): `reactjs-ui-design` → recipe 5.4 → review loop (`npm run ui:snapshot`) |
| "The UI looks basic/boring" | `reactjs-ui-design` §1 + §8 checklist; restyle with shadcn primitives and `components/common` patterns, not new CSS |
| Need an agent or MCP tool | §9 first, then `/agent-builder` or `/mcp-builder` |

### Forbidden

- Do not read or explore `mockup/` unless the user asks. Those files are output artifacts.
- Do not read `tailwind.css`, `variable.css` or `variable_dark.css` under `design/` (if present). Use
  `design/design-system.md` → `design/{platform}/{theme}/DESIGN.md`.
- Do not commit secrets or real `.env` files (only `*.env.example`).
- Do not weaken security to make a test pass (CORS `*`, disabling auth deps, `extra="allow"`, catching
  and swallowing errors).
- Do not bypass repositories, the envelope or the router registry.
