---
name: data
description: "Backend (apps/backend) service & data layer: provider-agnostic Repository (db/base.py) for MongoDB or Supabase/Postgres (BE_DB_PROVIDER), entity declarations in db/schema.py, Condition/AnyOf/AllOf/Op filters, QuerySpec + build_query_spec(FindDTO), CrudService base, per-request service DI (get_repository, UsersRepo…, XServiceDep), Redis via RedisDep + redis_key, ConflictError on unique violations. Use when creating services, querying data, adding an entity/field, or implementing business logic."
---

# data — Services & provider-agnostic data access

## Use this skill when

- Writing or changing a service in `apps/backend/service/`
- Querying/inserting/updating records, building list queries, scoping data to a user
- Declaring a new entity or field (`db/schema.py`)
- Using Redis from application code

Related: HTTP shapes → `fastapi-api-design`; full new resource → `fastapi-crud-collection`;
Mongo specifics → `fastapi-mongo`; adding a DB provider → `fastapi-database-init`.

## Key files

| File | Contents |
|---|---|
| `apps/backend/db/base.py` | `Repository`, `Database` ABCs; `Condition`, `AnyOf`, `AllOf`, `Op`, `QuerySpec`, `SortSpec`, `SortDirection`, `Where` |
| `apps/backend/db/schema.py` | `Field`, `FieldType`, `EntitySchema`, `audit_fields()`, `register_entity()`, `USERS` `PERMISSIONS` `GROUPS` `ROLES` `UPLOADS` |
| `apps/backend/db/query.py` | `build_query_spec(dto, entity, filterable=, searchable=, sortable=, extra_where=)` |
| `apps/backend/db/records.py` | `prepare_insert` / `prepare_update` (defaults, uuid ids, UTC ms timestamps, field checks) |
| `apps/backend/db/factory.py` | `create_database(settings)` → `MongoDatabase` or `PostgresDatabase` |
| `apps/backend/service/__init__.py` | `CrudService`, `ensure_valid_parent()` |
| `apps/backend/core/deps.py` | `get_repository(entity)`, `UsersRepo`, `PermissionsRepo`, `GroupsRepo`, `RolesRepo`, `UploadsRepo`, `RedisDep`, `SettingsDep`, `TokenStoreDep` |
| `apps/backend/core/redis.py` | `create_redis()`, `redis_key(settings, *parts)` |
| Reference services | `service/group.py` (simple), `service/permission.py`, `service/user.py` (rich rules), `service/upload.py` (owner scoping) |

## Rules

### MUST

- Access data **only** through `db.Repository` (from `from db import ...`). Records are plain dicts with
  snake_case keys, `id` (uuid4 string), aware-UTC `created_at` / `updated_at`; every declared field is present.
- Build services per request: constructor receives repositories (+ `Settings`, `Redis`, `TokenStore` if needed);
  expose `get_x_service(...)` and `XServiceDep = Annotated[XService, Depends(get_x_service)]` at the bottom of the module.
- Extend `CrudService` for resources: `get` (404), `list`, `create(data, actor_id=)`, `update` (404), `delete` (404);
  set `not_found_message`.
- Validate list queries through `build_query_spec` (via `CrudService.list`) — whitelists come from the entity
  (`filterable`/`searchable`/`sortable` flags); use `extra_where=` for server-side scoping the client cannot remove.
- Raise `core.errors` classes for business failures (`NotFoundError`, `ConflictError`, `ValidationError.for_field`, …).
- Lower-case emails before storing/querying; set `created_by` from the principal (`actor_id=user.id`).
- Use `ensure_valid_parent(repo, parent_id, record_id=)` for any hierarchical resource (cycle + existence checks).
- Pass `limit=` to `find_all` on user-facing data.
- Namespace Redis keys with `redis_key(settings, "feature", ...)` (prefix `BE_REDIS_KEY_PREFIX`).
- Keep `db/schema.py` and `migrations/supabase/*.sql` in sync (both providers must behave identically).

### MUST NOT

- Never import `pymongo`, `psycopg`, `bson` or a driver client in `service/`, `router/` or `dto/`.
- No module-level DB/Redis clients, no `os.getenv` (use `Settings`), no global service singletons.
- No string-built queries; no raw user dicts as filter values (dict values are rejected → 422/ValueError).
- No multi-statement transactions assumptions (each repository call is atomic on its own).
- Don't return storage dicts without a `response_model` (secrets would leak) — see `fastapi-api-design`.
- Don't catch `ConflictError` just to re-raise a generic 400; let it propagate (or pre-check for a friendlier message).

## Repository API (`db/base.py`)

```python
repo.get_by_id(id) -> dict | None                 # non-uuid/unknown ids -> None
repo.get_many_by_ids(ids) -> list[dict]
repo.find_one(where) -> dict | None
repo.find(spec: QuerySpec) -> tuple[list[dict], int]          # (page, total)
repo.find_all(where=None, *, sort=None, limit=None) -> list[dict]
repo.count(where=None) -> int ; repo.exists(where) -> bool
repo.insert(data) -> dict                         # id/created_at/updated_at/defaults filled
repo.update(id, changes) -> dict | None           # partial $set, never upserts
repo.update_many(where, changes) -> int ; repo.delete(id) -> bool ; repo.delete_many(where) -> int  # empty where refused
repo.entity                                       # its EntitySchema
```

`Where` = `{"field": value}` (equality AND, `None` = is null) | `Condition` | `AnyOf`/`AllOf` | list of those.
`Op`: `EQ NE IN NIN GT GTE LT LTE EXISTS NOT_EXISTS CONTAINS NOT_CONTAINS ALL`. On `LIST` fields EQ = contains
element, IN = any, ALL = all, NIN = none. CONTAINS is a literal, case-insensitive substring (escaped).

```python
from db import AnyOf, Condition, Op, QuerySpec, SortDirection, SortSpec

users.find_one(AnyOf(Condition("email", Op.EQ, ident.lower()), Condition("username", Op.EQ, ident)))
users.count({"group_id": group_id})
spec = QuerySpec.of({"status": "active"}, sort=[SortSpec("created_at", SortDirection.DESC)], page=1, size=20)
items, total = users.find(spec.and_where(Condition("created_by", Op.EQ, actor.id)))
```

## Canonical service (`service/group.py`)

```python
class GroupService(CrudService):
    not_found_message = "Group not found"

    def __init__(self, groups: Repository, users: Repository) -> None:
        super().__init__(groups)
        self.users = users

    def delete(self, id: str) -> None:
        self.get(id)
        members = self.users.count({"group_id": id})
        if members:
            raise ConflictError(f"Group is assigned to {members} user(s); reassign them first",
                                details=[{"field": "id", "message": f"referenced by {members} user(s)"}])
        self.repo.update_many({"parent_id": id}, {"parent_id": None})
        super().delete(id)

def get_group_service(groups: GroupsRepo, users: UsersRepo) -> GroupService:
    return GroupService(groups, users)

GroupServiceDep = Annotated[GroupService, Depends(get_group_service)]
```

For an entity without a ready-made alias: `repo: Repository = Depends(get_repository(NOTES))`.

## Declaring an entity / field

1. `EntitySchema` in `db/schema.py` (or `register_entity(EntitySchema(...))` in your module) with `id`,
   `created_at`, `updated_at` (`*audit_fields()` also adds `created_by`). Flags: `filterable`, `searchable`,
   `sortable`, `unique`, `nullable`, `sensitive`, `default`, `type=FieldType.X`.
2. `TABLE_<X>: str = "<x>"` in `core/config.py` `Settings` + `BE_TABLE_<X>` in `apps/backend/.env.example`.
3. `migrations/supabase/00N_<x>.sql` (unique constraints named `<table>_<field>_key`, checks
   `<table>_<field>_check`, RLS on + revoke anon/authenticated) — see `apps/backend/migrations/supabase/README.md`.
4. Mongo indexes are derived automatically on startup (`db/mongo/indexes.py`).

## Redis

```python
def get_widget_cache(redis: RedisDep, settings: SettingsDep) -> WidgetCache:
    return WidgetCache(redis, settings)              # sync redis.Redis (decode_responses)
# inside: self.redis.set(redis_key(self.settings, "widget", widget_id), payload, ex=300)
```
Sessions/token revocation already live in `core.security.TokenStore`; rate limits in `core.rate_limit.RateLimiter`.

## Checklist — new service

- [ ] Subclass `CrudService` (or plain class) with repositories injected
- [ ] Business rules raise `AppError` subclasses with camelCase `details` fields
- [ ] `get_x_service` + `XServiceDep` defined in the same module
- [ ] List uses `self.list(query, extra_where=...)`; never hand-parses `FindDTO.filters`
- [ ] New entity/field mirrored in `db/schema.py`, `Settings`, `.env.example`, migration
- [ ] Tests run on both providers (`tests/modules/conftest.py` parametrizes `database`)

## Common mistakes

| Mistake | Fix |
|---|---|
| `repo.insert({... "createdBy": ...})` | storage keys are snake_case: `created_by` |
| Unknown key in insert/update → `ValueError` (500) | declare the field in `db/schema.py` or validate in the DTO |
| `repo.update(...)` result unchecked | it returns `None` when missing → raise `NotFoundError` (or use `CrudService.update`) |
| Filtering on a field not flagged `filterable` | flag it in the entity or pass `filterable=` for that endpoint |
| Case-sensitive email lookups | `.strip().lower()` first |
| `datetime.now()` (naive) | `util.helper.utc_now()` |

Detailed rules: [references/data-rules.md](references/data-rules.md)
