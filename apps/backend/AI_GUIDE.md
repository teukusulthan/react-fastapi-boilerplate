# AI Guide — Backend (FastAPI)

The canonical guide for working in `apps/backend`. Read it before you change backend code.
Repository-wide rules are in [`../../AGENTS.md`](../../AGENTS.md). For setup, commands and the full
environment-variable table, see [`README.md`](README.md). The endpoint contract is in
[`../../docs/api-spec.md`](../../docs/api-spec.md).

> When a skill under `.claude/skills/fastapi-*` disagrees with the code or with this guide, the
> **code wins**, then this guide. Several fastapi-* skills describe patterns from other projects
> (Elasticsearch, maps, gateways, topics). They are not part of this boilerplate.

## 1. Mental model

- **Stack:** Python ≥ 3.10 (Docker/CI use 3.12), FastAPI 0.143, Pydantic v2 + pydantic-settings, loguru,
  PyJWT, bcrypt, Redis, and MongoDB (pymongo) **or** Supabase Postgres (psycopg 3 + psycopg_pool).
- **Sync services.** Routes and dependencies are plain `def` and run in FastAPI's threadpool, whose size
  is set by `BE_THREADPOOL_SIZE`. Repositories, Redis, bcrypt and SMTP all block. Only write `async def`
  for a route that does no blocking I/O.
- **Two pluggable axes, chosen at startup:**
  - `BE_DB_PROVIDER=mongo|supabase`. Services only see the `db.Repository` interface. `db/mongo` and
    `db/supabase` implement it with identical semantics.
  - `BE_AUTH_PROVIDER=local|supabase`. `local` means our own JWT, login/register/OTP/2FA and httpOnly
    cookies. `supabase` means we verify Supabase-issued JWTs and auto-provision a `users` row.
- **Storage is snake_case. JSON is camelCase.** IDs are app-generated `uuid4` strings. Timestamps are
  timezone-aware UTC with millisecond precision.
- **One envelope for everything:** `{metaData, data}`. Errors come from global exception handlers, so
  routes never build error responses themselves.

### Request lifecycle

```
HTTP ─► CORSMiddleware (explicit origins, credentials)
     ─► RequestContextMiddleware   (X-Request-ID, access log, executionTime, last-resort 500)
     ─► GlobalRateLimitMiddleware  (only if BE_RATE_LIMIT_GLOBAL > 0)
     ─► PayloadEncryptionMiddleware (only if BE_ENC_ACTIVE=true; AES-256-GCM {"payload": "..."})
     ─► router (router/<name>.py)  — thin: parse DTO, resolve deps (auth/RBAC, service), call service
          └─► service (service/<name>.py) — business rules, raises core.errors.*
                └─► Repository (db/mongo | db/supabase) — dicts in/out, snake_case, uuid ids
     ◄─ ApiResponse[T] (response_model re-validates → camelCase, unknown/secret fields dropped)
     ◄─ AppError / HTTPException / RequestValidationError → global handlers → error envelope
```

## 2. Layout

```
apps/backend/
├── api.py                 app = create_app(); `python api.py` runs uvicorn with BE_HOST/PORT/WORKERS/RELOAD
├── core/
│   ├── config.py          Settings (env prefix BE_), get_settings() (cached), load_settings()
│   ├── app_factory.py     create_app(settings=None, *, database=None, redis=None, routers=None), lifespan
│   ├── deps.py            DI: SettingsDep, repos (UsersRepo…), get_repository(entity), CurrentUser, RBAC deps
│   ├── errors.py          AppError hierarchy, ErrorCode, global exception handlers
│   ├── responses.py       ApiResponse[T], MetaData, Pagination, ok(), created(), paginated()
│   ├── security.py        bcrypt, JWT (create/decode), TokenStore (Redis revocation/sessions), cookies,
│   │                      X-Internal-Token check, OTP hashing, secrets at rest, SupabaseTokenVerifier
│   ├── rate_limit.py      rate_limit() dependency, RateLimiter, GlobalRateLimitMiddleware, client_ip()
│   ├── middleware.py      RequestContextMiddleware, PayloadEncryptionMiddleware (pure ASGI)
│   ├── context.py         request-id / execution-time contextvars
│   ├── logging.py         setup_logging() — loguru, stdlib intercepted, JSON optional
│   └── redis.py           create_redis(), redis_key(settings, *parts)
├── db/
│   ├── base.py            Repository / Database ABCs, Condition, AnyOf, AllOf, Op, QuerySpec, SortSpec
│   ├── schema.py          EntitySchema + Field: USERS, PERMISSIONS, GROUPS, ROLES, UPLOADS, register_entity()
│   ├── query.py           build_query_spec(FindDTO, entity, …) → QuerySpec (whitelists, coercion, 422s)
│   ├── records.py         prepare_insert / prepare_update (defaults, ids, UTC timestamps, field checks)
│   ├── factory.py         create_database(settings) → MongoDatabase | PostgresDatabase
│   ├── mongo/             client.py, repository.py, translator.py, indexes.py (unique indexes on startup)
│   └── supabase/          client.py (psycopg pool), repository.py, translator.py (psycopg.sql only)
├── dto/                   Pydantic request/response models (common.py: BaseSchema, FindDTO, IdParam, MessageData)
├── service/               Business logic. __init__.py: CrudService, ensure_valid_parent(); auth/ package
├── router/                APIRouters. __init__.py = the router REGISTRY (the only place routers are wired)
├── util/                  helper.py (utc_now, new_id, to_camel…), crypto.py, s3.py, kafka.py, email.py, email_templates.py
├── templates/email/       <name>.txt (first line "Subject: …") + optional <name>.html, _layout.html
├── migrations/supabase/   001_init.sql + README.md (Postgres DDL; Mongo needs none)
├── scripts/seed.py        python -m scripts.seed — default permissions + bootstrap admin (idempotent)
├── tests/                 conftest.py (fixtures), core/, db/, auth/, modules/
├── pyproject.toml         ruff + pytest config (deps are in requirements*.txt)
├── requirements.txt       runtime deps, pinned direct deps only
├── requirements-dev.txt   -r requirements.txt + pytest, pytest-cov, ruff, mongomock, fakeredis
├── .env.example           every BE_* setting with comments (copy to .env)
├── Dockerfile             python:3.12-slim, uv, libmagic1, non-root, :8020
└── project.json           Nx targets: serve, lint, format, format-check, test, seed
```

**Reference module:** the `role` resource (`dto/role.py`, `service/role.py`, `router/role.py`) is the
smallest complete CRUD module. Copy its shape for new resources. Tests for it live in
`tests/modules/test_groups_roles.py`.

## 3. Golden rules

1. **Layering:** router → service → repository. Routers hold no business logic and never touch a
   repository or driver. Services never import `fastapi.Request`/`Response`, `pymongo` or `psycopg`.
2. **Repositories only:** all data access goes through `db.Repository` from `core.deps`
   (`UsersRepo`, `get_repository(ENTITY)`…). Never create a Mongo or Postgres client yourself, and never
   query a collection or table by hand.
3. **Every route sets `response_model=ApiResponse[XResponse]`** and returns `ok()`, `created()` or
   `paginated()`. The response model is the safety net: it turns snake_case storage dicts into
   camelCase and drops undeclared fields such as `password_hash`.
4. **Errors are raised, not returned.** Raise `core.errors.*`. Never write
   `except Exception: raise HTTPException(400, str(e))`, and never put library exception text in a message.
5. **RBAC on every router.** Put a router-level dependency on it (`require_auth`, `get_current_user` or
   `require_admin`) and per-route deps for writes. `created_by` always comes from the token
   (`actor_id=user.id`), never from the body.
6. **Strict DTOs:** inputs use `model_config = ConfigDict(extra="forbid")` so unknown or privileged
   fields get a 422. Updates use PATCH semantics (`to_storage(exclude_unset=True)`). Validators are pure:
   no DB, Redis or HTTP calls.
7. **List endpoints** are `POST /x/get-all` with a `FindDTO` body. Filtering, search and sort are limited
   to the entity whitelists in `db/schema.py`.
8. **Settings** live only in `core/config.py` and `.env.example` (`BE_` prefix). Never call `os.getenv`.
   In routes, use `SettingsDep`; elsewhere, use `get_settings()`.
9. **Logging** uses `from loguru import logger` with `{}` placeholders
   (`logger.info("user {} created", uid)`). No `print()` and no `traceback.print_exc()` (ruff `T20`
   enforces this). Mask emails with `censor_email()`. Never log tokens, passwords or OTPs.
10. **Schema changes go to both providers:** update `db/schema.py` (which drives Mongo indexes and
    whitelists) **and** add a new `migrations/supabase/NNN_*.sql`.
11. **Tests are part of the change** (§7). Run `ruff check .`, `ruff format --check .` and `pytest`
    before you finish.
12. **Contract docs:** when you add or change an endpoint, update `docs/api-spec.md` and
    `docs/api/<module>.md`. When you change an entity, update `docs/database-schema.md`. Add a line to
    `changelog/backend.md`.

Extend through these patterns. Changing existing code is allowed when the task needs it, as long as you
update its tests and docs.

## 4. Building blocks (cheat sheet)

### Responses — `core/responses.py`

```python
from core.responses import ApiResponse, ok, created, paginated


@router.get("/get-one", response_model=ApiResponse[RoleResponse])
def get_one(id: IdParam, service: RoleServiceDep):
    return ok(service.get(id))  # 200, message "Success"


@router.post("/add", status_code=201, response_model=ApiResponse[RoleResponse])
def add(dto: RoleDTO, service: RoleServiceDep, admin: AdminUserDep):
    return created(service.create(dto.to_storage(exclude_unset=False), actor_id=admin.id))  # 201


@router.post("/get-all", response_model=ApiResponse[list[RoleResponse]])
def get_all(query: FindRoleDTO, service: RoleServiceDep):
    items, total = service.list(query)
    return paginated(items, query.page, query.size, total)  # metaData.pagination filled
```

To set cookies, declare `response: Response` as a parameter, mutate it, and return the envelope as usual
(see `router/auth.py`).

### Errors — `core/errors.py`

| Raise | HTTP | `errorCode` |
|---|---|---|
| `BadRequestError(msg)` | 400 | `BAD_REQUEST` |
| `AuthenticationError(msg)` | 401 | `AUTHENTICATION_ERROR` (adds `WWW-Authenticate: Bearer`) |
| `PermissionDeniedError(msg)` | 403 | `PERMISSION_ERROR` |
| `NotFoundError(msg)` | 404 | `RESOURCE_NOT_FOUND` |
| `ConflictError(msg, details=[{field, message}])` | 409 | `CONFLICT` |
| `ValidationError(msg, details=[…])` / `ValidationError.for_field("parentId", msg)` | 422 | `VALIDATION_ERROR` |
| `RateLimitedError(msg, retry_after=s)` | 429 | `RATE_LIMITED` (+ `Retry-After`) |
| `ConfigurationError(msg)` | 503 | `CONFIGURATION_ERROR` (SMTP/S3/Kafka/Google not configured) |
| `ServiceUnavailableError(msg)` | 503 | `SERVICE_UNAVAILABLE` (also automatic for Mongo/Postgres/Redis connection errors) |
| `AppError(msg, status_code=…, error_code=…)` or a subclass | any | custom (see `service/upload.py` for 413 `PAYLOAD_TOO_LARGE` and 415 `UNSUPPORTED_MEDIA_TYPE`) |

The handlers also produce 405 `METHOD_NOT_ALLOWED` and 500 `INTERNAL_ERROR`. A 500 always has the
message "Internal server error"; the details go only to the log. `details` becomes `data` in the error
envelope. Use camelCase field names in details. `core.errors.ValidationError` is **not** Pydantic's
ValidationError.

### DTOs — `dto/common.py`

- `BaseSchema` is the base for every model. Attributes are snake_case and JSON is camelCase; it accepts
  both on input and serializes by alias. `dto.to_storage(exclude_unset=True, exclude={"id"})` returns a
  snake_case dict for repositories.
- Per resource, define `XDTO` (create), `UpdateXDTO` (`id` plus optional fields), `FindXDTO(FindDTO)`
  (empty subclass) and `XResponse`. Use `extra="forbid"` on inputs. To make a required column reject an
  explicit `null` on update, add a `_not_null` field validator (see `dto/role.py`).
- `IdParam` is the `?id=` query param. `MessageData{message}` is the body for deletes and actions.
- Use `EmailStr` for emails and lowercase them in a `mode="before"` validator.

### Data layer — `db/`

```python
from db import Condition, AnyOf, AllOf, Op, QuerySpec, SortSpec, SortDirection

repo.get_by_id(id) -> dict | None            # bad/non-uuid id -> None
repo.get_many_by_ids(ids) -> list[dict]
repo.find_one(where) -> dict | None           # where = {"field": value} | Condition | AnyOf/AllOf | list
repo.find(spec: QuerySpec) -> (items, total)
repo.find_all(where=None, *, sort=None, limit=None) -> list[dict]
repo.count(where=None) / repo.exists(where)
repo.insert(data) -> dict                     # sets id, created_at, updated_at, declared defaults
repo.update(id, changes) -> dict | None       # partial update, never upserts
repo.update_many(where, changes) -> int
repo.delete(id) -> bool / repo.delete_many(where) -> int   # empty filter refused
```

- `Op` values: `EQ, NE, IN, NIN, GT, GTE, LT, LTE, EXISTS, NOT_EXISTS, CONTAINS, NOT_CONTAINS, ALL`.
  Both providers give the same results. On `LIST` fields, `EQ` means "contains element".
- A unique violation becomes `ConflictError` (409) that names the field. A Postgres FK or CHECK
  violation becomes `ValidationError` (422). A `ValueError` from a repository (unknown field, or `None`
  in a non-nullable field) is a programming bug and surfaces as a 500. Validate in DTOs instead.
- There are no multi-statement transactions. Pre-check uniqueness in services when you want a friendlier
  message; the DB constraint is the real guarantee.

### List queries — `FindDTO` → `QuerySpec`

`CrudService.list(query, extra_where=(), filterable=None, searchable=None, sortable=None)` calls
`db.query.build_query_spec`. Field names may be camelCase or snake_case and must be in the entity
whitelist (`Field(..., q="fso")` in `db/schema.py`: f = filterable, s = searchable, o = sortable).
`sensitive=True` fields can never be used. Unknown fields, bad values, or object values all produce one
422 listing every problem (for example `{"field": "filters[0].field", …}`). Search is a literal,
case-insensitive contains. Use `extra_where` for server-side scoping, such as "only my rows", that the
client cannot remove.

### Auth and RBAC — `core/deps.py`

| Dependency / alias | Allows |
|---|---|
| `get_current_user_optional` / `OptionalUserDep` | anyone; `None` without credentials (invalid credentials still 401) |
| `get_current_user` / `PrincipalDep` | any authenticated principal: user **or** `X-Internal-Token` |
| `require_auth` / `CurrentUserDep` | authenticated **user** (an internal token gets 403) |
| `require_admin` / `AdminUserDep` | user whose permission alias is in `BE_SUPERUSER_ALIASES` (default `admin,owner`) |
| `require_privilege("note:write", …, any_of=False, allow_internal=False)` | superuser, or a user holding the privilege(s) |
| `require_internal_token` / `InternalDep` | only a valid `X-Internal-Token` |
| `require_user_or_internal` / `UserOrInternalDep` | user or internal |

Credentials are resolved in this order: the `X-Internal-Token` header (if present it must be valid) →
`Authorization: Bearer <access>` → the `token` cookie. The resulting `CurrentUser` has `id, username,
email, role, privileges, permission_id, group_id, is_superuser, is_internal, record` (the full users row)
and `has_privilege(p)`. The RBAC model: user → `permission_id` → permission `{name, alias,
privileges[]}`, and `role` is the permission alias. The `roles` collection is a plain CRUD resource and
is **not** used for authorization.

### Settings — `core/config.py`

`settings.X` reads the env var `BE_X`. The env file is `BE_ENV_FILE` (default `.env`), looked up in the
working directory and then in `apps/backend/`. Real environment variables override the file. List
settings accept CSV or a JSON array. Cross-field checks run at startup: production requires
`COOKIE_SECURE=true`, a non-placeholder `JWT_SECRET` and `RELOAD=false`; `DB_PROVIDER=supabase` requires
`SUPABASE_DB_URL`; and so on.

### Rate limiting — `core/rate_limit.py`

```python
@router.post("/send", dependencies=[Depends(rate_limit("note:send", limit=lambda s: 30, window=lambda s: 60))])
```

This is a fixed window per client IP, stored in Redis, and it fails open if Redis errors. Client IPs
honour `X-Forwarded-For` only when `BE_TRUST_PROXY_HEADERS=true`.

## 5. Recipes

### 5.1 Add a resource (entity + CRUD endpoints), end to end

Example: a `note` resource. Copy `role` and rename.

1. **Entity:** in `db/schema.py`, add the declaration and include it in `ENTITIES`:
   ```python
   NOTES = EntitySchema(
       name="notes",
       table_setting="TABLE_NOTES",
       fields=(
           ID,
           _f("title", q="fso", nullable=False),
           _f("body", q="s"),
           _f("pinned", FieldType.BOOL, q="f", nullable=False, default=False),
           _f("tags", FieldType.LIST, q="f", nullable=False, default=list),
           *audit_fields(),  # created_by, created_at, updated_at
       ),
   )
   ENTITIES = {e.name: e for e in (USERS, PERMISSIONS, GROUPS, ROLES, UPLOADS, NOTES)}
   ```
   Mongo unique and FK indexes come from this declaration automatically on startup
   (`db/mongo/indexes.py`).
2. **Setting:** add `TABLE_NOTES: str = "notes"` to `Settings` in `core/config.py`, and
   `BE_TABLE_NOTES=notes` to `.env.example`.
3. **Postgres migration:** create `migrations/supabase/002_notes.sql`. Make it idempotent
   (`create table if not exists`). Use `id uuid primary key`, snake_case columns,
   `created_at/updated_at timestamptz not null default now()`, `jsonb` for JSON/LIST fields, unique
   constraints named `<table>_<field>_key` and checks named `<table>_<field>_check`. Attach the
   `set_updated_at` trigger. **Enable RLS and revoke `anon`/`authenticated`** (copy the lockdown block
   in `001_init.sql`). Never edit an applied migration.
4. **Repository dep:** in `core/deps.py`, follow the existing pattern
   (`get_notes_repo = get_repository(NOTES)`, `NotesRepo = Annotated[Repository, Depends(get_notes_repo)]`),
   or use `Depends(get_repository(NOTES))` directly in the service provider.
5. **DTOs:** create `dto/note.py` with `NoteDTO`, `UpdateNoteDTO`, `FindNoteDTO(FindDTO)` and
   `NoteResponse` (shape as in `dto/role.py`).
6. **Service:** create `service/note.py` with `class NoteService(CrudService)` and
   `not_found_message = "Note not found"`. Add domain rules here (ownership via `extra_where`, parent
   checks via `ensure_valid_parent`). Then add the provider and alias:
   ```python
   def get_note_service(notes: NotesRepo) -> NoteService:
       return NoteService(notes)


   NoteServiceDep = Annotated[NoteService, Depends(get_note_service)]
   ```
7. **Router:** create `router/note.py` with
   `router = APIRouter(prefix="/note", tags=["note"], dependencies=[Depends(require_auth)])`.
   Add the five house-style routes: `POST /add` (201), `PUT /update`, `DELETE /delete?id=`,
   `GET /get-one?id=`, `POST /get-all`. Each sets `response_model=ApiResponse[...]`. Writes get
   `AdminUserDep` or `require_privilege(...)` as needed.
8. **Registry:** in `router/__init__.py`, append `RouterSpec("note", "router.note")` to `ROUTERS`. The
   name is what `BE_ENABLED_ROUTERS` toggles. An import failure fails startup on purpose.
9. **Tests:** add `tests/modules/test_notes.py` covering CRUD, 404, 422 (whitelist and DTO), 409, and
   RBAC (anon 401, wrong role 403). Mount it with an `app_routers` fixture override (§7). If you add the
   router to `MODULES` in `tests/modules/conftest.py`, also add its rows to `ENDPOINTS` in
   `tests/modules/test_rbac.py`; the matrix test fails if any mounted route is missing.
10. **Docs:** add the endpoints to `docs/api-spec.md`, create `docs/api/note.md`, add the entity to
    `docs/database-schema.md` and an entry to `changelog/backend.md`. If the web app uses it, add a web
    service (see `apps/web/AI_GUIDE.md`).
11. **Verify:** run `ruff check . && ruff format --check . && pytest`. With Postgres available, also run
    `TEST_POSTGRES_DSN=… pytest -m integration`.

### 5.2 Add a field to an existing entity

1. Add the `Field` in `db/schema.py`, with whitelist flags only if clients may filter, search or sort on
   it. Mark secrets `sensitive=True`.
2. Add a new migration `migrations/supabase/00N_<table>_<field>.sql` containing
   `alter table public.<table> add column if not exists <field> <type> …;`.
   Mongo needs no migration: existing documents simply lack the key, and it reads as the default/None.
   If you need backfill, write a script in `scripts/`.
3. Add it to the request DTOs (create/update) and the `XResponse`. Without `XResponse`, it never reaches
   clients.
4. Update the tests, `docs/database-schema.md`, `docs/api/<module>.md` and the web types
   (`apps/web/src/types/models.d.ts`).

### 5.3 Protect an endpoint

- **Signed-in users only:** use a router-level `dependencies=[Depends(require_auth)]` and take
  `user: CurrentUserDep` to read the identity.
- **Admins only (superuser aliases):** add `admin: AdminUserDep` to the route, or use
  `dependencies=[Depends(require_admin)]` on the router.
- **A fine-grained privilege:** use `dependencies=[Depends(require_privilege("report:export"))]`. Seed or
  assign the privilege string in a permission's `privileges` list (`/permission/update-partial`).
- **Machine-to-machine:** use `InternalDep` (internal token only) or `UserOrInternalDep`. The caller
  sends `X-Internal-Token: $BE_INTERNAL_TOKEN` (≥ 32 chars; empty means internal calls are disabled).
- **Public:** put it on a router without auth deps, and add `rate_limit(...)` if it can be abused.
- Owner-scoped data: filter with `extra_where=(Condition("created_by", Op.EQ, user.id),)` unless
  `user.is_superuser`. Answer 404 rather than 403 for other users' rows.

### 5.4 Add a setting

1. Add a typed field to `Settings` in `core/config.py`, with a default that is safe for local dev. If
   blank should mean "unset", add it to the `_blank_to_none` or `_blank_secret_to_none` validator. Use
   `SecretStr` for secrets.
2. Document it in `.env.example` (`BE_<NAME>=…` with a comment) and in `README.md` §Environment.
3. If it is optional infrastructure, add a `*_configured` property and raise `ConfigurationError` when a
   feature that needs it is used. Never fail startup because an optional integration is missing.
4. Add a test in `tests/core/test_config.py` if it has validation logic.

### 5.5 Send an email

1. Add `templates/email/<name>.txt` (the first line is `Subject: …`) and optionally `<name>.html`, which
   extends `_layout.html`.
2. In the service, call `mailer.send("<name>", to_email, **context)` (see `service/auth/registration.py`)
   and call `mailer.require_available()` before flows that depend on email. With `BE_EMAIL_BACKEND=auto`
   in development, messages are printed to the log as `[email:console] …`.

### 5.6 Files (S3) and events (Kafka)

- `util.s3.get_s3_storage(settings)` returns an `S3Storage` with `put_object`, `upload_fileobj(key,
  fileobj, content_type, content_disposition=, metadata=, transfer_config=)`, `get_object`,
  `delete_object` and `presigned_get_url`. It raises `ConfigurationError` when S3 is not configured, and
  it blocks, so call it from sync code. The full upload pipeline (streaming size cap, magic-byte MIME
  check via libmagic, resize, presigned download) is in `service/upload.py`.
- `util.kafka.publish(settings, topic, value, key=None)` uses a lazy shared producer. Check
  `settings.kafka_configured` for best-effort sends.

## 6. Commands

Run from `apps/backend` with the venv created by `npm run setup:backend`. The Nx targets run the same
commands from the repo root through `node scripts/py.mjs`.

```bash
.venv/bin/python api.py                         # dev server on :8020 (BE_RELOAD=true for auto-reload)
.venv/bin/python -m pytest                      # unit + API tests (mongomock + fakeredis; no services needed)
.venv/bin/python -m pytest tests/modules -k note -x
TEST_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/app_test .venv/bin/python -m pytest -m integration
.venv/bin/python -m ruff check .   &&   .venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff format .               # apply formatting
.venv/bin/python -m scripts.seed                # default permissions + bootstrap admin
```

From the repo root: `npm run dev:backend`, `npx nx run backend:test`, `npx nx run backend:lint`,
`npm run seed`, `npm run ci`.

## 7. Testing

- **Isolation.** `tests/conftest.py` scrubs every `BE_*` env var, ignores `.env`, and runs the real
  `MongoRepository` on **mongomock** with **fakeredis** and bcrypt cost 4. No services are needed. pytest
  runs with `--import-mode=importlib` and `pythonpath=["."]`, so test basenames may repeat and you need
  no `__init__.py`.
- **Main fixtures:** `make_settings(**overrides)`, `settings`, `database`, `redis_client`,
  `users_repo`/`permissions_repo`/`groups_repo`/`roles_repo`/`uploads_repo`, `app_routers` (default
  `[HEALTH]`), `make_app(app_settings=None, routers=None)`, `app`, `client` (TestClient with lifespan),
  `permission_factory`, `user_factory(password=…, permission=…, **fields)`, `admin_permission`,
  `user_permission`, `admin_user`, `regular_user`, `login(user)`, `auth_headers(user)`,
  `admin_headers`, `user_headers`, `internal_headers`.
- **Mounting routers:** override `app_routers` in the test module or a package `conftest.py`:
  ```python
  from router import HEALTH, RouterSpec


  @pytest.fixture
  def app_routers():
      return [HEALTH, RouterSpec("note", "router.note")]
  ```
- **Other settings for one test:** `with TestClient(make_app(make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET="x" * 32))) as c: ...`
- **Postgres:** `tests/modules/conftest.py` parametrizes `database`, so every module test also runs
  against real Postgres when `TEST_POSTGRES_DSN` is set. The tests apply `migrations/supabase/*.sql`
  themselves and truncate per test. Those cases carry `@pytest.mark.integration`. CI runs them in the
  `backend:test-postgres` job.
- **What to assert:** status code, `metaData.errorCode`, and the `data` shape (camelCase); that no
  secrets leak; RBAC (401 anonymous, 403 wrong role or internal token); 422 for non-whitelisted fields.
- **S3 in tests:** `tests/modules/conftest.py` provides `fake_storage` (it overrides
  `service.upload.get_storage_factory`).
- **libmagic:** upload tests need the system `libmagic` library (Debian/Ubuntu: `apt install libmagic1`;
  macOS: `brew install libmagic`).

## 8. Pitfalls

- `create_app()` imports every registered router. A broken import fails app creation (this is by design).
  For a partial app, use `BE_ENABLED_ROUTERS=health,auth` or `create_app(settings, routers=[...])`.
- `BE_JWT_SECRET` is required (≥ 32 chars). Without it, `Settings()` raises at startup.
- `FindDTO.size` is capped by the **global** `get_settings().MAX_PAGE_SIZE`, not by the app's injected
  settings.
- In Supabase mode, Postgres tables are **not** created by the app. Startup and `/health/ready` only
  check for them. Apply `migrations/supabase/*.sql` yourself (see `migrations/supabase/README.md`).
  Migrations assume the default table names.
- Postgres `jsonb` and Mongo store JSON/LIST fields natively. Never `json.dumps` them yourself.
- Emails are stored lowercased, and the unique constraint is case-sensitive, so always normalise.
- `BE_COOKIE_SECURE` defaults to `true` in code; `.env.example` sets it to `false` for plain-HTTP
  development. Over plain HTTP (LAN IP, Docker on :8080), browsers drop Secure cookies, so login appears
  to succeed but the next request is 401.
- `BE_COOKIE_REFRESH_PATH` is matched against the **browser-visible** path
  (`/api/v1/apps/auth/refresh` behind the proxy). Keep `/` unless you know the public path.
- `BE_ROOT_PATH` only affects generated URLs (Swagger/OpenAPI). Leave it empty when the proxy strips
  `/api/v1/apps` (the default for both the Vite proxy and nginx). Setting it fixes `/api/v1/apps/docs`
  through the proxy but breaks `:8020/docs` directly.
- The auth endpoints are rate limited (`BE_RATE_LIMIT_AUTH=10` per 60 s per IP by default). Repeated
  manual logins can return 429.
- Some agent environments put a restricted `uv`/`python3` shim on PATH. Run Python via
  `.venv/bin/python` (or `node scripts/py.mjs`). If `uv pip` is refused, call the real binary (for
  example `~/.local/bin/uv`) or run `npm run setup:backend -- --no-uv`.

## 9. Documentation map

| Need | Read |
|---|---|
| Endpoint contract (all modules), envelope, error codes | [`docs/api-spec.md`](../../docs/api-spec.md), [`docs/api/*.md`](../../docs/api/) |
| Entities, indexes, migrations | [`docs/database-schema.md`](../../docs/database-schema.md), [`migrations/supabase/README.md`](migrations/supabase/README.md) |
| Setup, env vars, Docker, troubleshooting | [`README.md`](README.md) |
| API/DTO conventions | `.claude/skills/fastapi-api-design/SKILL.md` |
| Auth, JWT, RBAC | `.claude/skills/fastapi-auth/SKILL.md` |
| Services / repositories / queries | `.claude/skills/fastapi-data/SKILL.md`, `.claude/skills/fastapi-crud-collection/SKILL.md` |
| Settings, startup, middleware | `.claude/skills/fastapi-config/SKILL.md` |
| Async vs sync, blocking calls | `.claude/skills/fastapi-async-performance/SKILL.md` |
| Logging | `.claude/skills/fastapi-logging/SKILL.md` |
| Uploads / S3 | `.claude/skills/fastapi-file-upload/SKILL.md` |
| Tests | `.claude/skills/fastapi-unit-test/SKILL.md` |
| File naming, new modules | `.claude/skills/fastapi-file-naming/SKILL.md` |
| Adding dependencies / venv | `.claude/skills/fastapi-dependency-constraints/SKILL.md`, `.claude/skills/fastapi-virtual-environment/SKILL.md` |

## 10. Definition of done (backend)

- [ ] Router → service → repository; no driver imports outside `db/`.
- [ ] Every route has `response_model=ApiResponse[...]` and the right RBAC dependency.
- [ ] Input DTOs use `extra="forbid"`; updates use PATCH semantics; no secrets in response models.
- [ ] Entity changes are in `db/schema.py` **and** in a new `migrations/supabase/NNN_*.sql`.
- [ ] New settings are in `core/config.py` **and** `.env.example` (and in the README table).
- [ ] Tests are added or updated; `ruff check .`, `ruff format --check .` and `pytest` are green.
- [ ] `docs/api-spec.md`, `docs/api/<module>.md`, `docs/database-schema.md` and `changelog/backend.md`
  are updated.
