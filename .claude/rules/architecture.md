# Architecture & Tech Stack

## Tech Stack

| Layer | Allowed stack (as installed in this repo) |
|-------|--------------|
| Backend | Python ≥ 3.10 / FastAPI (`apps/backend`), Pydantic v2 + pydantic-settings, loguru, sync services in the threadpool. (`be-rust` / Axum is allowed for new services only by explicit decision.) |
| Database | **MongoDB** (default) **or** **Supabase Postgres**, chosen with `BE_DB_PROVIDER=mongo\|supabase`, always behind the repository layer (`apps/backend/db/`). Redis for sessions, OTPs, revocation and rate limits. |
| Auth | `BE_AUTH_PROVIDER=local` (own HS256 JWT: httpOnly cookies `token`/`refresh_token` + Bearer) **or** `supabase` (verify Supabase-issued JWTs), plus `X-Internal-Token` for system-to-system calls. RBAC = user → permission `{alias, privileges}`. |
| Web | React 18 + TypeScript 5.9 + Vite 7 + React Router 7 + TanStack Query 5 + Zustand 5 + React Hook Form 7 + Zod 4 + Tailwind CSS v4 + shadcn/ui (Radix) (`apps/web`) |
| File storage | S3-compatible (AWS S3 / MinIO / Supabase Storage) via boto3 (`apps/backend/util/s3.py`) |
| Mobile | Flutter MVVM + Provider (`mobile-flutter`); not present in this repo |
| Agent | Agno + FastMCP, OpenRouter LLM (`agent-python`); not present in this repo (see `AGENTS.md` §9) |
| MCP | FastMCP (`mcp-python`): bespoke tools when no hub server fits |
| Telemetry | Agno OpenInference instrumentor → Langfuse OTLP (agents only) |
| Tooling | Nx 23 (root), uv/pip, ruff, pytest, ESLint 9, Prettier, Vitest 4, Docker Compose, GitLab CI |

---

## Enforcement

Validate the stack before generating any code. If the requested tech is not listed above:
- Issue a ⚠️ TECH STACK WARNING and stop.
- Stack changes are allowed only after the user updates this file.
- Additive libraries (charting, date utils) that don't replace a core layer are exempt. You still need
  to check `package.json` / `requirements.txt` first and justify the addition.

---

## Backend Enforcement

Applies to `apps/backend`. Details and recipes: `apps/backend/AI_GUIDE.md`.

- **Layering:** `router/` (thin: DTO in, deps, call service, envelope out) → `service/` (business
  rules) → `db.Repository` (from `core/deps.py`). Services never import `fastapi.Request`/`Response`,
  `pymongo` or `psycopg`. Routers never touch repositories directly.
- **Repositories only:** all persistence goes through `db/` (`get_repository(ENTITY)`, `UsersRepo`, …).
  No ad-hoc DB clients and no raw queries outside `db/mongo` and `db/supabase` (Postgres SQL only via
  `psycopg.sql`).
- **Router registry:** a router is mounted only by adding a `RouterSpec` to `ROUTERS` in
  `router/__init__.py`.
- **Envelope:** every route sets `response_model=ApiResponse[XResponse]` and returns `ok()`,
  `created()` or `paginated()` from `core/responses.py`. Errors are raised from `core/errors.py` and
  rendered by the global handlers. Do not catch an exception only to re-raise it as an
  `HTTPException` with the exception text.
- **RBAC:** every router has an auth dependency (`require_auth`, `get_current_user` or
  `require_admin`). Writes check `AdminUserDep` or `require_privilege(...)`. `created_by` comes from the
  token.
- **DTOs:** `BaseSchema` (camelCase JSON). Inputs use `extra="forbid"`; updates use PATCH semantics.
  Validators are pure (no DB, Redis or HTTP). No secrets in response models.
- **Queries:** list endpoints are `POST /x/get-all` with `FindDTO`. Fields are restricted to the entity
  whitelists in `db/schema.py`; sensitive fields are never queryable.
- **Async:** routes and services are sync `def`. Never call blocking I/O (repositories, Redis, SMTP,
  boto3, bcrypt, `requests`) inside an `async def` route.
- **Settings:** only via `core/config.py` (`BE_*`, documented in `.env.example`). Optional integrations
  must not break startup; raise `ConfigurationError` when they are used unconfigured.
- **Schema:** entity changes go to `db/schema.py` **and** a new `migrations/supabase/NNN_*.sql`
  (idempotent, named constraints, RLS lockdown). Never edit an applied migration.
- **Logging:** loguru with `{}` placeholders. No `print()` or `traceback.print_exc()`. Mask PII
  (`censor_email`) and never log tokens, passwords or OTPs.
- **Quality gate:** `ruff check .`, `ruff format --check .` and `pytest` must pass. New endpoints need
  tests, including RBAC.

---

## Web UI Enforcement

Applies to any app under `apps/` that uses shadcn/ui. **Visual direction, component priority, tokens,
states and the review loop are defined in [`web/ui-design.md`](web/ui-design.md)** (always on) and the
playbook skill [`reactjs-ui-design`](../skills/reactjs-ui-design/SKILL.md). Load the skill before you
build or restyle UI. The rules below are the structural contract around it.

- **shadcn first.** Primitives in `src/components/ui/` are the default for every interactive element.
  Their styling, re-themed to our semantic tokens (`src/styles/variable.css` → `tailwind.css`), **is**
  the baseline look: modern, minimal, slightly rounded (`rounded-md` controls, `rounded-xl` surfaces).
  If shadcn has the component but it is not installed, add it (`npx shadcn@latest add <name>` from
  `apps/web`) and apply the post-install checklist in the playbook. Never hand-build dropdowns, selects,
  dialogs, popovers, tabs, tooltips, checkboxes, switches, date pickers or toasts.
- **Compose before you write.** Page patterns come from `src/components/common/` (`PageHeader`,
  `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`, `ConfirmDialog`, `LoadingState`, …) and every
  list uses `DataTable` from `src/modules/data-table/`. Hand-written markup is only for static,
  behavior-less surfaces.
- **Semantic tokens only.** Use the shadcn semantic classes (`bg-background`, `bg-card`,
  `text-muted-foreground`, `border-border`, `bg-primary`, …). No raw hex/rgb, Tailwind palette colors or
  arbitrary values. Legacy aliases (`bg-background-primary`, `text-font-*`, `border-border-primary`)
  still resolve for old code but are not used in new code.
- **Re-branding** happens only in the semantic variables (`--primary`, `--ring`, `--radius`, chart
  colors), never per component. If a `design/` folder exists, resolve the active theme from
  `design/design-system.md` → `design/[platform]/[theme]/DESIGN.md` and map it onto those variables
  (`/switch-design-system`). A theme may change radius/shadow only if its `DESIGN.md` says so
  explicitly; otherwise the `ui-design.md` defaults apply. Without a `design/` folder (the bare
  boilerplate), `ui-design.md` + `src/styles/variable.css` are the design authority.
- Preserve shadcn behavior props such as `asChild`, `aria-*`, `data-*`, refs (`React.forwardRef` on
  React 18), controlled values, focus rings and portal structure.
- Icons are Phosphor only (`<i className="ph ph-…" />`); replace `lucide-react` in shadcn output.
- App shell regions must not overlap. Header, sidebar and main content must each have reserved layout
  space; do not rely on z-index to hide structural overlap.
- If you use the shadcn Sidebar with a full-width header, account for the sidebar's fixed desktop
  positioning: offset it below the header and reduce its height by the header height.
- Sidebar and header navigation must be config-driven. Define menu entries in `src/config/menu/*`
  (`APP_MENU` in `app.menu.ts`, `ADMINISTRATOR_MENU` in `administrator.menu.ts`, aggregated by
  `index.ts`) and render from those arrays. Do not hardcode route or menu arrays in layout components.
- **Look at it before you say done:** `npm run ui:snapshot -- --route <path>` (from `apps/web`), review
  the light/dark, desktop/mobile PNGs against the playbook checklist, and fix what you see.

The current shell (`apps/web/src/components/layouts/AppLayout.tsx`) follows the non-overlap baseline:
- root (`SidebarProvider`) `flex h-svh flex-col overflow-hidden bg-sidebar` (the sidebar color is the
  shell canvas);
- header `h-12 shrink-0`, full width;
- body `flex min-h-0 flex-1 overflow-hidden`;
- sidebar (`AppSidebar`: `<Sidebar variant="inset" collapsible="icon" className="top-12 h-[calc(100svh-3rem)]">`)
  is fixed on desktop, offset below the header; its width is `--sidebar-width` = 15rem (240px), 3.25rem
  when collapsed to icons (`SIDEBAR_WIDTH*` in `src/components/ui/sidebar.tsx`), and an in-flow gap
  element reserves that width so content never sits under it;
- main area is `SidebarInset`: an inset rounded panel on `md+` (`rounded-xl border shadow-xs`, `mr-2 mb-2`,
  `bg-background`) with a `PerfectScrollArea` inside; page padding and `max-w-7xl` are owned there.

**Map views:** any Mapbox map must **fill its designated container frame** (the same footprint as the
hosting card, panel or slot). Preserve a proper flex height chain (`flex-1 min-h-0` on ancestors and a
full-width, full-height wrapper around the map). If the canvas is shorter than the visible frame, fix the
layout; do not leave empty padding inside the map chrome. Rules:
`.claude/skills/reactjs-map/references/map-rules.md` (§ Container & frame contract) and
`.claude/skills/reactjs-map/SKILL.md` (Layout).

**Scrollable UI:** bounded scroll regions inside the app (main column, sidebar body, drawers, panels,
feeds, fixed-height lists) **must** use **`react-perfect-scrollbar`** through **`PerfectScrollArea`**
(`apps/web/src/components/wrappers/PerfectScrollArea.tsx`). Global thumb and rail theming uses design
tokens in **`apps/web/src/styles/components.css`** (`.ps__thumb-*`, `.ps__rail-*`) so scrollbars match
the active theme. Do **not** use raw `overflow-auto` or `scrollbar-thin` as the default for those
regions. Exceptions and patterns: `.claude/skills/reactjs-responsive/SKILL.md` § *Scrollable regions*.

---

## Component Placement Enforcement

**Before you create any component, classify it with this decision tree. No exceptions.**

| Question | Answer | Where |
|----------|--------|-------|
| Is it a shadcn/Radix primitive or design-system binding? | Yes | `src/components/ui/` |
| Is it app shell structure (layout, header, sidebar, footer)? | Yes | `src/components/layouts/` |
| Is it a 3rd-party lib adapter (map wrapper, scroll wrapper, providers)? | Yes | `src/components/wrappers/` |
| Is it a generic, domain-agnostic page pattern used across the app (`PageHeader`, `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`, `ConfirmDialog`, loading/error/status screens)? | Yes | `src/components/common/` |
| Is it a generic, domain-agnostic system reused by 2+ features (e.g. `src/modules/data-table/`)? | Yes | `src/modules/{name}/` |
| Is it domain-specific (even if only one page uses it)? | Yes | `src/features/{domain}/{feature}/components/` |
| Is it a route entry? | Yes | `src/pages/{area}/{Name}Page.tsx`: one thin file, no `parts/` or `hooks/` subfolders |

**❌ NEVER place domain-specific components directly in `src/components/`.**
Any component that belongs to a business domain (tactical, billing, dashboard, etc.) is a domain
component: panel content, data displays, domain widgets, status indicators. It must live under
`src/features/{domain}/{feature}/components/`. Placing it in `src/components/sidebar/`,
`src/components/analytics/`, etc. is a structure violation.

When you create a domain component, consult `.claude/skills/reactjs-features/SKILL.md` to choose the
correct domain bucket (`features/{domain}/` vs `features/shared/`) before writing any code.

---

## Sprint Closure Enforcement

**Every time a unit of work that came from a sprint task is completed, these steps are MANDATORY
before you move on:**

1. Open the active sprint task file in `sprint/active/NN-<slug>/<stack>/NN-<task>.md`.
2. Mark every `- [ ]` in `## TODOs` → `- [x]`.
3. Update `**Status:**` to `✅ Done`.
4. When ALL tasks in the sprint are `[x]`, move the sprint folder from `sprint/active/` to
   `sprint/archive/`.
5. Update `sprint/01-sprint-planning.md`: set the status to `✅ Done`, set `Completed At`, and fix the
   folder link to `./archive/`.

**Never leave task files with unchecked todos after work is delivered. A sprint is not done until every
task file reflects `✅ Done`.**

Additional invariants:

- The task file's top-level `**Status:**` header is the source of truth. A checked closing-checklist
  line does **not** count if the header still says `📋 Planned` or `🚧 In Progress`.
- If work was scoped by a file under `sprint/`, re-open that file before the final response and verify
  that the header, `## TODOs` and changelog state are synchronized.
- Do not treat a task as complete based on code changes alone. Sprint/task documentation must be
  updated in the same unit of work.

Full closure procedure: `.claude/skills/sprint-builder/SKILL.md` § Step 4 (Execute) and § Step 5
(Archive).
