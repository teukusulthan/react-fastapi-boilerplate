# Orchestra — Rules › Backend

> Read this file FIRST before any backend work, then load only what the task needs.

## Installed backend

| App | Template | Path |
|-----|----------|------|
| FastAPI (Python) | `be-python` | `apps/backend/` |

There is no Rust backend in this repo. If one is ever added under `apps/`, add a row here and a section
below. Template-specific nested rule folders (`python/`, `rust/`) are **not** used. The durable backend
rules live in the files listed next.

## What to read

| Task | Read |
|------|------|
| Any backend change | `.claude/rules/architecture.md` § *Backend Enforcement* → `apps/backend/AI_GUIDE.md` §1–§4 |
| New resource / endpoint | `apps/backend/AI_GUIDE.md` §5.1–§5.3 (copy the `role` module), then `docs/api-spec.md` |
| Entity / column change | `apps/backend/AI_GUIDE.md` §5.2 + `docs/database-schema.md` + `apps/backend/migrations/supabase/README.md` |
| Auth, RBAC, tokens | `apps/backend/AI_GUIDE.md` §4 (Auth and RBAC) + `docs/api/auth.md` + `.claude/skills/fastapi-auth/SKILL.md` |
| Settings / env / startup | `apps/backend/AI_GUIDE.md` §5.4 + `apps/backend/README.md` § Environment + `.claude/skills/fastapi-config/SKILL.md` |
| Tests | `apps/backend/AI_GUIDE.md` §7 + `.claude/skills/fastapi-unit-test/SKILL.md` |
| Uploads / S3 | `docs/api/upload.md` + `.claude/skills/fastapi-file-upload/SKILL.md` |
| Async / blocking calls | `.claude/skills/fastapi-async-performance/SKILL.md` |
| Logging | `.claude/skills/fastapi-logging/SKILL.md` |

## Non-negotiables (summary)

- router → service → `db.Repository`; register routers only in `apps/backend/router/__init__.py`.
- `response_model=ApiResponse[...]` on every route; raise `core.errors.*`.
- An auth dependency on every router; `extra="forbid"` on input DTOs; queries limited to the
  `db/schema.py` whitelists.
- Schema changes in `db/schema.py` **and** `migrations/supabase/NNN_*.sql`.
- Verify with `ruff check .`, `ruff format --check .` and `pytest` (from `apps/backend`), or
  `npm run ci` from the root.
