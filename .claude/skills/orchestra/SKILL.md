---
name: orchestra
description: Master task router and orchestration guide for all development work in this workspace (React 18 + Vite web in apps/web, FastAPI backend in apps/backend with MongoDB or Supabase/Postgres). Use this skill at the start of every coding task to classify the task size, route it to the correct domain guide (web, backend, mobile, agent/MCP, review), pick the right skills, and run the right verification commands (npm run ci, lint, test, typecheck, build). Triggers: any implementation, bug fix, feature request, code review, or planning task — regardless of stack. Any UI task (page, screen, dashboard, form, table, restyle) routes to `reactjs-ui-design` first. Also handles sprint planning (sprint-builder), brief building (brief-builder), and **static HTML** work (`html-ui-slicing`, only when an HTML mockup is explicitly requested) routing.
---

# Orchestra

## Workspace facts (verify before assuming anything else)

| App | Path | Stack | Dev port | Entry points |
|-----|------|-------|----------|--------------|
| Backend | `apps/backend/` | FastAPI, Python ≥ 3.10 (CI/Docker 3.12), pydantic-settings, loguru, MongoDB **or** Supabase Postgres (`BE_DB_PROVIDER`), Redis | 8020 | `api.py` → `core/app_factory.py:create_app()`; routers registered in `router/__init__.py` |
| Web | `apps/web/` | React 18 + TypeScript + Vite 7 + React Router 7 + Zustand 5 + TanStack Query 5 + shadcn/ui + Tailwind v4 | 3000 | `src/main.tsx`, `src/routes/index.tsx`; API calls go to `/api/v1/apps` (dev proxy → `http://localhost:8020`) |

- Monorepo tooling: root `package.json` scripts orchestrated by Nx (`nx.json`, `apps/*/project.json`).
- There is **no** mobile app, agent app (`apps/agents/`) or MCP app (`apps/mcp/`) in this boilerplate. The mobile / agent / MCP routes below only apply once such an app has been created (see `agent-builder`, `mcp-builder`).
- Project-level guides: `AGENTS.md` (root), `apps/backend/AI_GUIDE.md`, `apps/web/AI_GUIDE.md`, API contract in `docs/api-spec.md` + `docs/api/*.md`, schema in `docs/database-schema.md`, rules in `.claude/rules/` (`architecture.md`, `project-scope.md`, `web/orchestra.md`, `backend/orchestra.md`).

---

## Before Loading Any Context

Classify task first:
- Micro (typo, rename, 1-line fix) → no context load, just do it
- Small (single file change) → load only the relevant skill
- Medium (feature, multi-file) → domain reference below → skill(s) → rules
- Large (new feature across backend + web) → full context load + parallelize agents

---

## Routing

| Task | Domain guide |
|------|-------|
| **Any UI** (create/build/design/restyle a page, screen, dashboard, form, table, component; "make it look better"; "buatkan ui/halaman") | [`reactjs-ui-design`](../reactjs-ui-design/SKILL.md) **first** + `.claude/rules/web/ui-design.md`, then [web.md](references/web.md). In this repo it means the React app in `apps/web` unless the user explicitly asks for an **HTML mockup** (→ Static HTML below). |
| Web frontend (`apps/web`) | [web.md](references/web.md) |
| Backend API / DB (`apps/backend`) | [backend.md](references/backend.md) |
| Mobile (only if an `apps/mobile*` app exists) | [mobile.md](references/mobile.md) |
| Agent (Agno + FastMCP) / MCP server | [agent.md](references/agent.md) |
| Code review | [review.md](references/review.md) |

---

## Verification (run before reporting work as done)

From the repo root:

| Command | What it runs |
|---------|--------------|
| `npm run ci` | Full gate: `nx run-many -t lint format-check typecheck test build` for backend + web |
| `npm run lint` | backend `ruff check .` + web `eslint . --max-warnings=0` |
| `npm run format:check` / `npm run format` | backend `ruff format --check .` + web `prettier --check .` (or write) |
| `npm run typecheck` | web `tsc` (app + node configs) |
| `npm run test` | backend `pytest` (mongomock + fakeredis, no services needed) + web `vitest` |
| `npm run build` | web `vite build` (output `apps/web/build/`) |

Single-app shortcuts: `npx nx run backend:test`, `npx nx run web:lint`, … or directly in `apps/backend`:
`.venv/bin/python -m pytest`, `.venv/bin/ruff check .`; in `apps/web`: `npm run typecheck`, `npm run test:ci`.
Postgres integration tests: `TEST_POSTGRES_DSN=postgresql://… .venv/bin/python -m pytest -m integration`.
UI work (in `apps/web`): `npm run ui:snapshot -- --route <path>` and **open the PNGs** (light/dark, desktop/mobile) against the `reactjs-ui-design` §8 checklist before reporting done.

Setup / run: `npm install && npm run setup` (creates `apps/backend/.venv`, `apps/backend/.env`, installs web deps), `npm run dev` (backend :8020 + web :3000), `npm run seed` (default permissions + bootstrap admin).

---

## When to Parallelize

Parallelize when tasks are **independent** (no shared state, no sequential dependency):

- Backend + web changes for the same feature once the API contract (`docs/api-spec.md`) is agreed → spawn both
- Multiple unrelated bug fixes on different files → parallel
- Read-only research across different domains → parallel

---

## Never

- Spawn subagent for Micro or Small tasks
- Parallelize tasks that are sequential (step B depends on step A output, e.g. web types that depend on a new backend DTO)
- Start implementation before the domain guide has been read
- Load more context after enough context to complete the task is already loaded
- Report a task as done without running the relevant verification command(s) above

---

## Planning & Sprint

- Sprint planning is owned by the `sprint-builder` skill
- Brief building is owned by the `brief-builder` skill
- Review sprint / update backlog?
  → use `sprint-builder` skill
  → Read `sprint/01-sprint-planning.md`
  → Read `brief/00_OVERVIEW.md` (the project blueprint) if it exists
- Check active sprint?
  → Read: `sprint/active/`
- Implementing work from a task file under `sprint/`?
  → use `sprint-builder` skill before coding, not only for planning
  → read the specific task file that scopes the work
  → before finalizing, reopen that task file and perform sprint closure sync (`TODOs` / `Status` / changelog) as required by `.claude/rules/architecture.md` § Sprint Closure Enforcement

---

## Static HTML — slicing & PoC (repo-level, not `apps/web`)

Use this branch only when the user **explicitly** asks for **standalone HTML** (an "HTML mockup", mockup folder or single-file HTML PoC). A plain "build/design a UI/page/screen" request in this repo is **Web** (`apps/web`, `reactjs-ui-design`), not static HTML.

| Task shape | Skill |
|------------|--------|
| **All** static HTML: mockup packages **or** single-file workspace PoC from spec/brief (`html-ui-slicing` **Mode A** vs **Mode B** — see that skill's Step 0) | [`/html-ui-slicing`](../../commands/html-ui-slicing.md) command (its `SKILL.md` body is not in this repo; only `.claude/skills/html-ui-slicing/references/` exists) |

**Heuristics**

- "Slice UI", mockup under `mockup/`, themed static pages from `design/` → **Mode A** in `html-ui-slicing`.
- "Design HTML", PoC dari `<cwd>/sprint/00-app-spec.md` atau `<cwd>/brief/`, satu file di `<cwd>/design/` → **Mode B** — follow [`references/workspace-spec-poc.md`](../html-ui-slicing/references/workspace-spec-poc.md) inside that skill.

Do **not** force-read `apps/web/AI_GUIDE.md` for pure static HTML unless the user wants a **port** into the app; then classify as **Web** after the artifact exists (`html-to-react`).

---

## Efficiency Rules

- Read the domain guide (references/*.md) BEFORE loading any detail file
- Load skills/rules ONLY when the task matches
- Load docs (`docs/api-spec.md`, `docs/database-schema.md`) ONLY when the task touches the API or DB
- If the task is small (1 file fix, typo, rename) → skip all context loading
- STOP loading more context once enough to complete the task
- NEVER load `design/*` unless the task is UI-related (the `design/` folder is created by `design-system-setup` / `design-system-builder`; it may not exist yet)
- NEVER load `brief/*` unless the task is planning-related
- NEVER ignore `sprint/*` when the user is working from a sprint task file or asks to complete/continue a sprint-scoped task
