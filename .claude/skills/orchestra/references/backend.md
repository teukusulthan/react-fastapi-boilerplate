# Backend Agent

Handles all backend tasks in `apps/backend/` (FastAPI). Other `apps/be*` folders may be added by a project; detect them by content.

---

## Step 0 — Read the guides

1. `apps/backend/AI_GUIDE.md` — project structure, file locations, critical rules.
2. The contract you are touching: `docs/api-spec.md` + `docs/api/<module>.md`, and `docs/database-schema.md` for storage changes.

---

## Step 1 — Detect Active Backend Stack

List folders under `apps/` that contain a backend. Detect by content, not by name:

| Indicator files | Stack |
|----------------|-------|
| `api.py` + `core/app_factory.py` + `requirements.txt` | This boilerplate's FastAPI backend (`apps/backend/`) |
| `pyproject.toml`/`requirements.txt` with `fastmcp` | FastMCP server (see `mcp-builder`) |
| `Cargo.toml` | Rust (Axum) |

If multiple backends exist, all are in scope.

---

## Step 2 — Pick the skill(s)

| Task | Skill |
|------|-------|
| New endpoint / DTO / module boundaries, envelope, status codes | `fastapi-api-design` |
| New CRUD resource (entity + DTO + service + router + tests), Mongo **and** Supabase | `fastapi-crud-collection` |
| Repositories, filters, `QuerySpec`, services, DI | `fastapi-data` |
| Login, tokens, cookies, RBAC deps, internal token, Supabase auth | `fastapi-auth` |
| Settings / env vars (`BE_*`), router toggles, middleware, startup | `fastapi-config` |
| Mongo specifics (indexes, collection names, URI) | `fastapi-mongo` |
| Provider abstraction / adding a DB provider | `fastapi-database-init` |
| File upload / S3 / Kafka extraction | `fastapi-file-upload` |
| Tests (pytest fixtures, mongomock, fakeredis, Postgres integration) | `fastapi-unit-test` |
| Logging (loguru) | `fastapi-logging` |
| File / module naming | `fastapi-file-naming` |
| Sync vs async, threadpool, blocking I/O | `fastapi-async-performance` |
| Adding a Python dependency / venv | `fastapi-dependency-constraints`, `fastapi-virtual-environment` |
| Supabase project / local stack bootstrap | `supabase-init` |

Domain recipes from other company projects (API gateway, topic monitoring, map/tile engine, map creation, Elasticsearch filters, multi-DB dispatcher) are archived in `.claude/skills-library/` (see `.claude/skills-library/README.md`) and are **not** auto-loaded. They describe features that are **not** in this boilerplate. Use one only when the task asks for that feature: copy it into `.claude/skills/` and read its "Adapting to the current foundation" section before copying code.

---

## Step 3 — Verify

From the repo root: `npm run lint`, `npm run format:check`, `npm run test` (or the full `npm run ci`).
Inside `apps/backend`: `.venv/bin/python -m pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`.
Smoke run: `npm run dev:backend` → `GET http://localhost:8020/health/ready`, Swagger at `http://localhost:8020/docs`.

---

## Multi-Stack Coordination

When the task spans more than one backend:

1. Detect all active backends first
2. Implement independently per stack — do not mix patterns
3. Sync shared contracts via `docs/api-spec.md`

---

## Never

- Query the DB from a router, or import `pymongo` / `psycopg` in a service — go through `db.Repository` (see `fastapi-data`)
- Add endpoints without checking `docs/api-spec.md` for an existing contract (and update it when you add one)
- Leave a protected route without an auth dependency (`require_auth`, `require_admin`, `require_privilege(...)`, or a router-level `dependencies=[...]`)
- Return data without `response_model=ApiResponse[...]`
- Use `print()` for logging — use `from loguru import logger` with `{}` formatting
- Read env vars with `os.getenv` — add a field to `core/config.py` `Settings` (`BE_*`) and `.env.example`
