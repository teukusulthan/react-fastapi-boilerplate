# CLAUDE.md

@AGENTS.md

## Essentials (read even if you skip everything else)

**What this is:** a company React + FastAPI boilerplate (Nx monorepo).
- `apps/backend`: FastAPI on :8020, MongoDB **or** Supabase Postgres, local **or** Supabase JWT auth,
  and RBAC.
- `apps/web`: React 18 + Vite on :3000. It reaches the backend through `/api/v1/apps` with httpOnly
  cookie auth.

**Before you code:** read the AI guide of the app you touch: `apps/backend/AI_GUIDE.md` and/or
`apps/web/AI_GUIDE.md`. The contract is `docs/api-spec.md`; stack and placement rules are in
`.claude/rules/architecture.md`.

**Golden rules**
1. Backend layers: router → service → `db.Repository`. Never import pymongo or psycopg outside `db/`, and
   keep business logic out of routers.
2. Every route sets `response_model=ApiResponse[...]` and returns `ok()`, `created()` or `paginated()`.
   Errors are **raised** (`core/errors.py`), never returned or turned into `HTTPException(str(e))`.
3. Every router declares auth (`require_auth`, `get_current_user` or `require_admin`;
   `require_privilege("x:y")` for fine-grained access). `created_by` comes from the token. Input DTOs use
   `extra="forbid"`.
4. Lists are `POST /x/get-all` with `FindDTO`, limited to the whitelists in `db/schema.py`.
5. Schema changes go to `db/schema.py` **and** a new `migrations/supabase/NNN_*.sql`.
6. Settings go only in `core/config.py` + `.env.example` (`BE_*`) and `src/config/env.ts` +
   `env/.env.example` (`VITE_*`). Never `os.getenv`, and never `import.meta.env` outside `env.ts`.
7. No `print()`; use loguru with `{}` placeholders. Never log secrets.
8. Web layers: component → TanStack Query hook → service (`createResourceService`/`apiRequests`). No
   axios or fetch in components; server data lives in TanStack Query, not Zustand.
9. Each new page gets a route **and** a menu entry (`src/config/menu/*`). Domain UI goes in
   `src/features/<domain>/<feature>/`.
10. Tests ship with the change. When the API or schema changes, update `docs/api-spec.md`,
    `docs/api/*.md`, `docs/database-schema.md` and `changelog/*.md` in the same change.
11. Extend through the documented patterns. Change existing code when the task needs it, with tests.
    Copy the `role` module for new CRUD resources.
12. UI work: follow `.claude/rules/web/ui-design.md` and load the `reactjs-ui-design` skill first; shadcn
    first; review with `npm run ui:snapshot`.

**Verify (paste real results, never assume):**

```bash
npm run ci                                   # repo root: lint + format-check + typecheck + test + build, both apps, + docs:check
# backend only (apps/backend)
.venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check . && .venv/bin/python -m pytest
# web only (apps/web)
npm run typecheck && npm run lint && npm run format:check && npm run test:ci && npm run build
```

**Run:** `npm run setup` → `npm run seed` → `npm run dev`. Docker: `npm run docker:up`
(http://localhost:8080).

**Where to look first:** `apps/backend/router/__init__.py` (router registry),
`apps/backend/core/deps.py` (DI + RBAC), `apps/backend/db/schema.py` (entities + whitelists),
`apps/web/src/routes/`, `apps/web/src/services/`, `apps/web/src/config/menu/`.

Use Python via `apps/backend/.venv/bin/python` (or `node scripts/py.mjs`), not a bare `python3`.
