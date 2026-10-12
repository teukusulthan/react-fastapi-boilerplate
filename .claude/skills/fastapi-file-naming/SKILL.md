---
name: file-naming
description: "Backend (apps/backend) file naming and module layout: one snake_case module per feature across dto/<feature>.py, service/<feature>.py, router/<feature>.py (+ RouterSpec in router/__init__.py, entity in db/schema.py, tests in tests/modules/), class naming (XDTO, UpdateXDTO, FindXDTO, XResponse, XService, XServiceDep, get_x_service), where core/, db/, util/, scripts/, migrations/ code goes. Use when adding a feature module, creating new backend files, or organizing code."
---

# File naming & module structure (backend)

## Use this skill when

- Creating any new file under `apps/backend/`
- Adding a feature module (router + DTO + service)
- Deciding whether code belongs in `core/`, `db/`, `service/`, `util/` or `scripts/`

## Directory map

```
apps/backend/
  api.py                     ASGI entry (app = create_app())
  core/                      framework plumbing: config, app_factory, errors, responses, deps, security,
                             middleware, rate_limit, logging, redis, context
  db/                        data layer: base.py (contracts), schema.py (entities), query.py, records.py,
                             factory.py, mongo/, supabase/
  dto/<feature>.py           Pydantic models (common.py = shared building blocks)
  service/<feature>.py       business logic (+ service/auth/ package for the auth flows)
  router/<feature>.py        HTTP routes; router/__init__.py = registry
  util/                      stateless helpers & optional clients: helper.py, crypto.py, s3.py, kafka.py, email.py
  scripts/                   CLI entry points (python -m scripts.seed)
  migrations/supabase/       NNN_<what>.sql for the Postgres provider
  templates/email/           <name>.txt / <name>.html email templates
  tests/{core,db,auth,modules}/  pytest suites (conftest.py fixtures)
```

## New feature module — example `note` (files you create; one name everywhere)

| File | Contents |
|---|---|
| `dto/note.py` | `NoteDTO` (create), `UpdateNoteDTO` (patch, has `id`), `FindNoteDTO(FindDTO)`, `NoteResponse` |
| `service/note.py` | `NoteService(CrudService)`, `get_note_service(...)`, `NoteServiceDep` |
| `router/note.py` | `router = APIRouter(prefix="/note", tags=["note"], ...)` |
| `router/__init__.py` | add `RouterSpec("note", "router.note")` to `ROUTERS` |
| `db/schema.py` | `NOTES = EntitySchema(name="notes", table_setting="TABLE_NOTES", ...)` |
| `core/config.py` + `.env.example` | `TABLE_NOTES: str = "notes"` / `BE_TABLE_NOTES=notes` |
| `migrations/supabase/002_notes.sql` | table + constraints (Postgres provider) |
| `tests/modules/test_notes.py` | API tests (both providers via `tests/modules/conftest.py`) |

Real examples to mirror: `dto/group.py`, `service/group.py`, `router/group.py`, `tests/modules/test_groups_roles.py`.

## Naming rules

### MUST
- Files and packages: `snake_case.py`, singular feature name (`group.py`, not `groups.py` / `GroupRouter.py`).
- Router prefix and tag = feature name (`/group`, `tags=["group"]`); paths are kebab-case verbs (`/get-all`, `/update-partial`).
- DTO classes: `XDTO` (create), `UpdateXDTO`, `FindXDTO`, `XResponse`; other requests `VerbXDTO` / `XRequest`
  (auth uses `LoginRequest`, `ResetPasswordRequest`…). Shared types go in `dto/common.py`.
- Services: `XService`, provider function `get_x_service`, alias `XServiceDep`. Module-level helper functions are
  snake_case verbs (`ensure_valid_parent`, `load_user_profile`).
- Entities: plural lower-case `name="notes"`, constant `NOTES`, setting `TABLE_NOTES`.
- Settings fields UPPER_SNAKE without prefix; env keys `BE_` + field.
- Errors: subclasses of `AppError` named `<Thing>Error` (see `service/upload.py::UnsupportedMediaTypeError`).
- Tests: `tests/<area>/test_<feature>.py`; test functions `test_<behaviour>`.

### MUST NOT
- No `utils.py` dumping grounds inside features, no `helpers/` per module — shared code goes to `util/` or `core/`.
- No business logic in `util/` (it must not import `service/` or `router/`).
- No new top-level directories for ordinary features; no `models/`, `config/`, `exceptions/`, `middleware/`
  packages (their roles live in `dto/`, `core/config.py`, `core/errors.py`, `core/middleware.py`).
- No circular imports: `router → service → db | core | dto | util`; `dto` may import `core.config` only.

## Checklist

- [ ] Same feature name in dto/service/router/test file names and router prefix
- [ ] `RouterSpec` registered; entity declared; table setting + `.env.example`; migration for Postgres
- [ ] `npm run lint` (ruff: isort with first-party `core db dto router service util scripts tests`)

## Common mistakes

| Mistake | Fix |
|---|---|
| e.g. `router/notes_router.py` | create `router/note.py` instead |
| DTOs defined inside the router file | move them to e.g. `dto/note.py` |
| e.g. `service/note_service.py` with a module-level `service = NoteService()` | create `service/note.py` with `get_note_service` / `NoteServiceDep` |
| Router file added but not in `ROUTERS` | add the `RouterSpec` (otherwise 404) |

More detail: [references/file-naming-rules.md](references/file-naming-rules.md)
