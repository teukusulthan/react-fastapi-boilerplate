---
name: fastapi-crud-collection
description: Scaffold a provider-agnostic CRUD resource in apps/backend (works on MongoDB AND Supabase/Postgres) — EntitySchema in db/schema.py + Supabase migration + dto/<x>.py + service/<x>.py (CrudService) + router/<x>.py registered in router/__init__.py, with the house endpoints add/update/delete/get-one/get-all and the shared FindDTO filter/search/sort/pagination contract (whitelists, 422 on unknown fields). Use when adding a brand-new resource/table/collection, or when copying the group/role/permission module shape.
---

# fastapi-crud-collection — Provider-agnostic CRUD resource

The directory name is historical ("collection"); the pattern now targets **one entity** that
works on both database providers (`BE_DB_PROVIDER=mongo` | `supabase`). Services talk only to
`db.base.Repository`; the Mongo and Postgres adapters translate.

## Use this skill when

- Adding a new resource with `POST /x/add`, `PUT /x/update`, `DELETE /x/delete?id=`,
  `GET /x/get-one?id=`, `POST /x/get-all`.
- Copying the shape of an existing module (group, role, permission, user, upload).
- Changing a module's list whitelists (filterable / searchable / sortable fields).

Related skills: `fastapi-api-design` (envelope, status codes, router rules), `fastapi-data`
(repository API, filters), `fastapi-auth` (RBAC deps), `fastapi-mongo` / `fastapi-database-init`
(provider internals), `fastapi-unit-test`.

## Reference modules (read these first — they are the canonical pattern)

| Module | Files | What it shows |
|---|---|---|
| role (minimal) | `apps/backend/router/role.py`, `apps/backend/service/role.py`, `apps/backend/dto/role.py` | Plain CRUD + parent hierarchy (`ensure_valid_parent`), children detached on delete |
| group | `apps/backend/router/group.py`, `apps/backend/service/group.py`, `apps/backend/dto/group.py` | + reference guard: delete refused (409) while users reference it |
| permission | `apps/backend/router/permission.py`, `apps/backend/service/permission.py`, `apps/backend/dto/permission.py` | + unique `alias` pre-check, extra endpoint `PUT /update-partial`, lockout guard |
| user | `apps/backend/router/user.py`, `apps/backend/service/user.py`, `apps/backend/dto/user.py` | Rich admin module: custom response building, uniqueness, token revocation, self-service route |
| upload | `apps/backend/router/upload.py`, `apps/backend/service/upload.py`, `apps/backend/dto/upload.py` | Owner scoping (`extra_where`), multipart form (see `fastapi-file-upload`) |

Per-module notes: `references/role.md`, `references/permission.md`, `references/user.md`.

Domain resources (e.g. a `topic`, `workspace` or `dashboard` table from another project) are not
part of this boilerplate; each one is just another instance of the recipe below. Keep the domain
logic from skills such as `fastapi-topic`, but build the module on this foundation (entity +
repository + `CrudService`), not on that skill's legacy Mongo helpers.

## Rules

MUST
- Declare the entity once in `apps/backend/db/schema.py` (`EntitySchema` + add it to the
  `ENTITIES` tuple). Storage field names are **snake_case**; the API is camelCase automatically.
- Include `id` (`FieldType.ID`, `nullable=False`) and `*audit_fields()` (`created_by`,
  `created_at`, `updated_at`) — `EntitySchema` refuses to build without `id/created_at/updated_at`.
- Mark list whitelists on the fields: `filterable`, `searchable`, `sortable` (the private helper
  `_f(name, type, q="fso")` in `db/schema.py` sets them). Secrets get `sensitive=True` (never
  queryable, never in DTOs).
- Add `TABLE_<X>: str = "<x>"` to `Settings` in `apps/backend/core/config.py` and
  `BE_TABLE_<X>=<x>` to `apps/backend/.env.example`; point `table_setting="TABLE_<X>"` at it.
- Ship a Supabase migration next to `apps/backend/migrations/supabase/001_init.sql` that mirrors
  the entity exactly (see "Migration" below). Mongo indexes are derived automatically.
- DTOs inherit `dto.common.BaseSchema`; create/update DTOs use `ConfigDict(extra="forbid")`
  (mass-assignment → 422). Update DTOs carry `id` + all-optional fields (PATCH semantics).
- List DTO: `class Find<X>DTO(FindDTO): pass` — never add free-form filter fields.
- Service: subclass `service.CrudService`, set `not_found_message`, build it per request with a
  `get_<x>_service` provider and expose `<X>ServiceDep = Annotated[<X>Service, Depends(...)]`.
- Router: `APIRouter(prefix="/<x>", tags=["<x>"], dependencies=[Depends(<auth dep>)])`, sync
  `def` routes, `response_model=ApiResponse[...]` on **every** route, `ok()` / `created()` /
  `paginated()` from `core.responses`, `IdParam` for `?id=`.
- `created_by` comes from the principal (`actor_id=user.id`), never from the body.
- Register the router: add `RouterSpec("<x>", "router.<x>")` to `ROUTERS` in
  `apps/backend/router/__init__.py`.
- Tests under `apps/backend/tests/modules/` (Mongo always; Postgres when `TEST_POSTGRES_DSN` is set).

MUST NOT
- Import `pymongo` / `psycopg` in services or routers, or build provider-specific queries.
- Return storage dicts without `response_model` (that is what converts to camelCase and drops
  unknown/sensitive fields).
- Catch exceptions and convert to `HTTPException`; raise `core.errors.*` and let the global
  handlers render the envelope.
- Generate ids yourself (repositories set `str(uuid4())`), or derive ids from content (md5 etc.).
- Add `async def` routes that call repositories (they are blocking).

## Recipe — a `note` resource (verified end to end against this foundation)

The example below is a recipe: none of these `note` files exist in the boilerplate — create them.

### 1. Entity (edit `apps/backend/db/schema.py`)

```python
# db/schema.py  (append; then add NOTES to the ENTITIES tuple at the bottom)
NOTES = EntitySchema(
    name="notes",
    table_setting="TABLE_NOTES",
    fields=(
        ID,
        _f("title", q="fso", nullable=False),
        _f("body", q="s"),
        _f("pinned", FieldType.BOOL, q="f", nullable=False, default=False),
        _f("tags", FieldType.LIST, q="f", nullable=False, default=list),
        *audit_fields(),
    ),
)
```

`ENTITIES` drives Mongo index creation and the Postgres "tables exist" check on startup and on
`GET /health/ready`. Declaring in `db/schema.py` (not `register_entity()` inside your service
module) guarantees the entity is known before `ensure_schema()` runs — including in the test
`database` fixture, which creates indexes before any router is imported.

Field types: `ID` (uuid string; Postgres `uuid`), `STR`, `INT`, `FLOAT`, `BOOL`, `DATETIME`
(aware UTC; Postgres `timestamptz`), `JSON` (dict; `jsonb`), `LIST` (list of scalars; `jsonb` array).
`unique=True` → Mongo `uniq_<field>` index / Postgres `<table>_<field>_key` constraint → 409 on
violation. Nullable unique fields allow many nulls in both providers.

### 2. Settings

Add `TABLE_NOTES: str = "notes"` next to the other `TABLE_*` settings in `core/config.py`, and
`BE_TABLE_NOTES=notes` next to `BE_TABLE_UPLOADS` in `.env.example`.

### 3. Migration (Supabase provider)

Create it at `apps/backend/migrations/supabase/002_notes.sql` (never edit an applied file).
Rules from `apps/backend/migrations/supabase/README.md`: idempotent (`create table if not exists`),
column names = storage names, `id uuid primary key default gen_random_uuid()`, `created_by text`,
`created_at/updated_at timestamptz not null default now()`, unique constraints named
`<table>_<field>_key`, checks `<table>_<field>_check` (the repository maps those names back to the
API field in 409/422 responses), `set_updated_at` trigger, RLS enabled + grants revoked from
`anon`/`authenticated` (copy the lockdown block of `001_init.sql`). FK violations surface as 422.

```sql
create table if not exists public.notes (
  id          uuid primary key default gen_random_uuid(),
  title       text not null,
  body        text,
  pinned      boolean not null default false,
  tags        jsonb not null default '[]'::jsonb,
  created_by  text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint notes_tags_check check (jsonb_typeof(tags) = 'array')
);
create index if not exists notes_created_at_idx on public.notes (created_at desc);
drop trigger if exists set_updated_at on public.notes;
create trigger set_updated_at before update on public.notes
  for each row execute function public.set_updated_at();
alter table public.notes enable row level security;
do $$
declare r text;
begin
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then   -- roles exist only on Supabase
      execute format('revoke all on table public.notes from %I', r);
    end if;
  end loop;
end;
$$;
```

Wrap the file in `begin; … commit;` like `001_init.sql`. Apply it the same way (SQL editor,
`psql "$BE_SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f …`, or `supabase db push`).

### 4. DTOs

```python
# dto/note.py
from datetime import datetime
from typing import Annotated, Any

from pydantic import ConfigDict, Field, StringConstraints, field_validator

from dto.common import BaseSchema, FindDTO

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
STRICT = ConfigDict(extra="forbid")


def _not_null(value: Any) -> Any:
    if value is None:
        raise ValueError("cannot be null")
    return value


class NoteDTO(BaseSchema):
    model_config = STRICT
    title: Title
    body: str | None = Field(default=None, max_length=10_000)
    pinned: bool = False
    tags: list[str] = Field(default_factory=list, max_length=20)


class UpdateNoteDTO(BaseSchema):
    model_config = STRICT
    id: str = Field(min_length=1, max_length=64)
    title: Title | None = None
    body: str | None = Field(default=None, max_length=10_000)
    pinned: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=20)

    _required = field_validator("title", "pinned", "tags", mode="before")(_not_null)  # non-nullable columns


class FindNoteDTO(FindDTO):
    """``POST /note/get-all`` body (whitelists come from db.schema.NOTES)."""


class NoteResponse(BaseSchema):
    id: str
    title: str
    body: str | None = None
    pinned: bool = False
    tags: list[str] = Field(default_factory=list)
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
```

`dto.to_storage(exclude_unset=False)` → full snake_case dict for creates (defaults included);
`dto.to_storage(exclude_unset=True, exclude={"id"})` → only fields the client sent, for updates.
An explicit `null` in an update clears an optional field; guard non-nullable ones with a
`_not_null` validator (as `dto/group.py` does for `name`) or the repository raises `ValueError` (500).

### 5. Service

```python
# service/note.py
from typing import Annotated, Any

from fastapi import Depends

from core.deps import CurrentUser, get_repository
from core.errors import NotFoundError
from db import Condition, Op, Repository
from db.schema import NOTES
from dto.common import FindDTO
from service import CrudService


class NoteService(CrudService):
    not_found_message = "Note not found"

    def _owned(self, id: str, actor: CurrentUser) -> dict[str, Any]:
        note = self.get(id)  # 404 if missing
        if not actor.is_superuser and note.get("created_by") != actor.id:
            raise NotFoundError(self.not_found_message)  # don't reveal other users' notes
        return note

    def get_for(self, id: str, actor: CurrentUser) -> dict[str, Any]:
        return self._owned(id, actor)

    def list_for(self, query: FindDTO, actor: CurrentUser):
        scope = () if actor.is_superuser else (Condition("created_by", Op.EQ, actor.id),)
        return self.list(query, extra_where=scope)  # client filters can never remove extra_where

    def update_for(self, id: str, changes: dict[str, Any], actor: CurrentUser):
        self._owned(id, actor)
        return self.update(id, changes)

    def delete_for(self, id: str, actor: CurrentUser) -> None:
        self._owned(id, actor)
        self.delete(id)


def get_note_service(repo: Repository = Depends(get_repository(NOTES))) -> NoteService:
    return NoteService(repo)


NoteServiceDep = Annotated[NoteService, Depends(get_note_service)]
```

`CrudService` (in `apps/backend/service/__init__.py`) gives `get(id)` (404), `list(query,
extra_where=, filterable=, searchable=, sortable=)` → `(items, total)`, `create(data,
actor_id=)` (drops `id`, sets `created_by`), `update(id, changes)` (404; ignores
id/created_by/created_at/updated_at) and `delete(id)` (404).

Domain rules go in the subclass:
- Hierarchy (`parent_id`): call `ensure_valid_parent(self.repo, parent_id, record_id=id)` from
  `service` (422 for missing parent, self-parent, cycles) — see `service/role.py`.
- Delete with children: `self.repo.update_many({"parent_id": id}, {"parent_id": None})` before
  `super().delete(id)` (mirrors Postgres `on delete set null`).
- Referenced by another entity: count and raise `ConflictError` (409) — see `GroupService.delete`.
- Friendly uniqueness message: pre-check with `find_one`, but the DB constraint is the guarantee.
- Multiple repositories: use the `Annotated` aliases in `core/deps.py` (`UsersRepo`,
  `GroupsRepo`, …) or `Depends(get_repository(ENTITY))` — see `get_group_service`.

### 6. Router

```python
# router/note.py
from fastapi import APIRouter, Depends

from core.deps import CurrentUserDep, require_auth
from core.responses import ApiResponse, created, ok, paginated
from dto.common import IdParam, MessageData
from dto.note import FindNoteDTO, NoteDTO, NoteResponse, UpdateNoteDTO
from service.note import NoteServiceDep

router = APIRouter(prefix="/note", tags=["note"], dependencies=[Depends(require_auth)])


@router.post("/add", status_code=201, response_model=ApiResponse[NoteResponse])
def add(dto: NoteDTO, service: NoteServiceDep, user: CurrentUserDep):
    return created(service.create(dto.to_storage(exclude_unset=False), actor_id=user.id))


@router.put("/update", response_model=ApiResponse[NoteResponse])
def update(dto: UpdateNoteDTO, service: NoteServiceDep, user: CurrentUserDep):
    return ok(service.update_for(dto.id, dto.to_storage(exclude={"id"}), user), message="Updated")


@router.delete("/delete", response_model=ApiResponse[MessageData])
def delete(id: IdParam, service: NoteServiceDep, user: CurrentUserDep):
    service.delete_for(id, user)
    return ok(MessageData(message="Note deleted"))


@router.get("/get-one", response_model=ApiResponse[NoteResponse])
def get_one(id: IdParam, service: NoteServiceDep, user: CurrentUserDep):
    return ok(service.get_for(id, user))


@router.post("/get-all", response_model=ApiResponse[list[NoteResponse]])
def get_all(query: FindNoteDTO, service: NoteServiceDep, user: CurrentUserDep):
    items, total = service.list_for(query, user)
    return paginated(items, query.page, query.size, total)
```

RBAC choices (all in `core/deps.py`): admin-managed catalog like group/role/permission →
router-level `Depends(get_current_user)` (reads for any principal incl. `X-Internal-Token`) +
`AdminUserDep` on write routes. Per-user data → `Depends(require_auth)` (users only) + owner
scoping. Fine-grained → `Depends(require_privilege("note:write"))`.

### 7. Register

```python
# router/__init__.py — inside ROUTERS
RouterSpec("note", "router.note"),
```

The name is the `BE_ENABLED_ROUTERS` toggle. A registered module that fails to import fails
`create_app()` loudly — run the tests.

### 8. Tests

Create `apps/backend/tests/modules/test_notes.py` (new file). The package `conftest.py` mounts only the five
built-in modules, so override `app_routers` in your test file:

```python
# tests/modules/test_notes.py
import pytest

from router import HEALTH, RouterSpec


@pytest.fixture
def app_routers():
    return [HEALTH, RouterSpec("note", "router.note")]


def test_crud_and_whitelist(client, user_headers):
    r = client.post("/note/add", json={"title": "Hello", "tags": ["a"]}, headers=user_headers)
    assert r.status_code == 201 and r.json()["metaData"]["responseCode"] == 201
    bad = client.post(
        "/note/get-all",
        json={"filters": [{"field": "body", "operator": "is", "value": {"is": "x"}}]},
        headers=user_headers,
    )
    assert bad.status_code == 422  # body is searchable, not filterable
```

Fixtures (`client`, `admin_headers`, `user_headers`, `internal_headers`, `user_factory`,
`auth_headers`, …) come from `apps/backend/tests/conftest.py`. The `database` fixture in
`apps/backend/tests/modules/conftest.py` also runs every test against Postgres when
`TEST_POSTGRES_DSN` is set — add your table to its `APP_TABLES` string (truncate/drop list) so the
Postgres run starts clean. If you add your module to that package's `MODULES`, also add its routes to
the `ENDPOINTS` matrix in `tests/modules/test_rbac.py` (it asserts every mounted module route is
covered).

Run from `apps/backend`: `.venv/bin/python -m pytest tests/modules -q` and `.venv/bin/ruff check .`
(or `npm run test` / `npm run lint` from the repo root).

## The list contract (`POST /x/get-all`)

Body = `FindDTO` (`apps/backend/dto/common.py`): `page` ≥1, `size` 1..`BE_MAX_PAGE_SIZE`,
`search`, `searchBy` (or legacy `search_by`), `orderBy` (default `createdAt`), `order` asc|desc,
`filters: [{field, operator, value: {is, isOneOf, gte, lte}, operatorType: and|or}]`.
Operators: `is`, `is not`, `is one of`, `is not one of`, `greater than equals`,
`less than equals`, `is between`, `is not between`, `is exist`, `is not exist`, `is contains`,
`is not contains`, `all`. `db.query.build_query_spec` validates against the entity whitelists
(camelCase or snake_case names), coerces values to the field type, escapes search text, and
raises one 422 listing every bad field. Response: `paginated(...)` →
`metaData.pagination = {page, size, totalElements, totalPages}`, `data` = array.
Different whitelist for one endpoint: `self.list(query, filterable={...}, searchable={...},
sortable={...})` (storage names).

## Checklist

- [ ] Entity in `db/schema.py` + added to `ENTITIES`; `id` + `audit_fields()`; whitelists flagged; secrets `sensitive=True`
- [ ] `TABLE_<X>` in `core/config.py` + `BE_TABLE_<X>` in `.env.example`
- [ ] `migrations/supabase/00N_<x>.sql` mirrors the entity (names, nullability, defaults, uniques `<table>_<field>_key`, RLS)
- [ ] `dto/<x>.py`: strict create/update DTOs, `Find<X>DTO(FindDTO)`, `<X>Response` (no secrets)
- [ ] `service/<x>.py`: `CrudService` subclass, `not_found_message`, provider + `<X>ServiceDep`
- [ ] `router/<x>.py`: prefix/tags, RBAC deps, `response_model=ApiResponse[...]` everywhere, 201 on add
- [ ] `RouterSpec("<x>", "router.<x>")` in `ROUTERS`
- [ ] Tests: CRUD, 404, 422 (unknown field, whitelist), 409 (unique), RBAC (401/403), owner scoping
- [ ] `ruff check .`, `ruff format --check .`, `pytest` green (and with `TEST_POSTGRES_DSN` if you touched SQL)
- [ ] Web side (if needed): endpoint constants in `apps/web/src/services/api-endpoints.ts` + a `<x>.service.ts`

## Common mistakes

- Declaring the entity but forgetting the migration → Supabase `/health/ready` reports the database
  unavailable ("Missing tables") and every call to the table fails.
- Using camelCase keys in repository calls (`{"createdBy": …}`) → `ValueError` "Unknown field(s)" → 500.
  Repositories take storage (snake_case) names.
- Passing `dto.to_storage()` (default `exclude_unset=True`) on create → defaults missing from the dict
  (the repository still fills entity defaults, but DTO-level defaults are lost).
- Forgetting `response_model` → raw snake_case dicts leak (and any sensitive field with them).
- Sending `null` for a non-nullable column on update without a `_not_null` guard → 500 instead of 422.
- Adding `status_code=201` on the decorator but returning `ok(...)` → `metaData.responseCode` says 200;
  use `created(...)`.
- Scoping lists by adding a filter the client controls instead of `extra_where`.
- Copying a `user`-style module for a simple resource — start from `role`.
