---
name: fastapi-mongo
description: "MongoDB provider specifics for apps/backend (BE_DB_PROVIDER=mongo, the default): db/mongo MongoDatabase/MongoRepository/translator/indexes, collection naming via BE_TABLE_* settings, BE_MONGO_URI / BE_MONGO_DB / BE_MONGO_TIMEOUT_MS, uuid string _id, aware-UTC datetimes, unique indexes derived from db/schema.py, duplicate key → 409, mongomock in tests. Use when adding a collection, debugging Mongo queries/indexes, configuring the Mongo connection, or reviewing code that touches pymongo."
---

# fastapi-mongo — MongoDB provider (`BE_DB_PROVIDER=mongo`)

MongoDB is the **default** provider. It is one of two adapters behind the provider-agnostic
repository layer (the other is Supabase/Postgres — see `fastapi-database-init`). Application
code never sees pymongo; it uses `db.base.Repository`.

## Use this skill when

- Adding a new collection (= a new entity) or renaming one.
- Configuring `BE_MONGO_URI` / `BE_MONGO_DB` for an environment.
- Debugging what a filter turns into, a missing/duplicate index, or a 409 on insert.
- Reviewing code that imports `pymongo` (it almost certainly should not).

## Where things live

| File | Role |
|---|---|
| `apps/backend/db/mongo/client.py` | `MongoDatabase(settings, client=None)`: builds `MongoClient(MONGO_URI, tz_aware=True, uuidRepresentation="standard", serverSelectionTimeoutMS/connectTimeoutMS=MONGO_TIMEOUT_MS, appname=APP_NAME)`, caches one `MongoRepository` per entity, `ping()`, `ensure_schema()`, `close()` |
| `apps/backend/db/mongo/repository.py` | `MongoRepository(collection, entity)` implementing `db.base.Repository`; `conflict_from_duplicate()` maps `DuplicateKeyError` → `ConflictError` (409) naming the field |
| `apps/backend/db/mongo/translator.py` | `translate_where(filters)` / `translate_condition(cond)`: filter tree → query document; `mongo_field("id") == "_id"` |
| `apps/backend/db/mongo/indexes.py` | `index_specs(entity)` + `ensure_indexes(db, settings)` — idempotent, run on startup and by `/health/ready` until it succeeds |
| `apps/backend/db/schema.py` | Entities (`USERS`, `PERMISSIONS`, `GROUPS`, `ROLES`, `UPLOADS`, + yours): fields, types, `unique`, defaults, whitelists |
| `apps/backend/db/factory.py` | `create_database(settings)` picks `MongoDatabase` when `DB_PROVIDER == "mongo"` |

## Rules

MUST
- Go through repositories: `Depends(get_repository(ENTITY))` or the `UsersRepo`/`GroupsRepo`/…
  aliases in `apps/backend/core/deps.py`. Filters are `db.Condition` / `AnyOf` / `AllOf` / plain
  `{"field": value}` mappings with **storage (snake_case) names**.
- Name collections through a setting: entity `table_setting="TABLE_<X>"` → `Settings.TABLE_<X>`
  (default value = plural snake_case, e.g. `"notes"`) → env `BE_TABLE_<X>`. The same setting is the
  Postgres table name, so one name works for both providers.
- Declare uniqueness on the entity field (`unique=True`); the index is created for you.
- Keep datetimes aware UTC (`util.helper.utc_now()`); the client is `tz_aware=True` and repositories
  return aware datetimes truncated to milliseconds (Mongo precision; Postgres is truncated the same way).
- Use `mongomock` through the real `MongoRepository` in tests (fixtures in `apps/backend/tests/conftest.py`).

MUST NOT
- `import pymongo` / `MongoClient` in `service/`, `router/`, `dto/` — only `db/mongo/*` and
  `core/app_factory.py` (exception mapping) do.
- Hard-code collection names (`db["users"]`) or read `os.environ` — use the entity + settings.
- Put user input into operator keys or `$where`/`$regex` yourself. The translator only puts values in
  operands, rejects dict values (no operator injection) and escapes search text (`re.escape`).
- Create views (`v_*` collections) or extra indexes by hand in app code — derive them from the entity
  (or add a startup step in `db/mongo/indexes.py`).
- Generate `_id` from content (md5 etc.). Ids are `str(uuid.uuid4())` from `util.helper.new_id()`.

## Document shape

- `_id` = the app id (uuid4 **string**); records returned by the repository expose it as `id`
  (`_from_doc` renames it). `Condition("id", …)` is translated to `_id`.
- Every declared field is always present: `db/records.py::prepare_insert` fills entity defaults
  (`None`, `False`, `[]`…), sets `id`, `created_at`, `updated_at`. `update` is a partial `$set`,
  never upserts, refreshes `updated_at`, ignores `id`/`created_at`.
- Unknown keys or `None` in a non-nullable field → `ValueError` (programming error → 500). Validate
  in DTOs first.

## Indexes (`db/mongo/indexes.py`)

Derived from each registered entity (`ENTITIES` in `db/schema.py`):

| Index name | When | Notes |
|---|---|---|
| `uniq_<field>` | field has `unique=True` | nullable unique fields get a `partialFilterExpression` on `$type`, so many `null`s are allowed (same as Postgres `UNIQUE`) |
| `idx_created_at` | always | descending, default list sort |
| `idx_<field>` | every non-unique `FieldType.ID` field except `id` | e.g. `idx_permission_id`, `idx_parent_id` |

Startup (`core/app_factory.py` lifespan) calls `database.ensure_schema()`; on failure it logs and
`GET /health/ready` retries. Unique emails are case-sensitive at the index level — services store
emails lowercased.

## Query translation (`db/mongo/translator.py`)

`Op.EQ` → `{f: v}`, `NE` → `$ne` (also matches null/missing), `IN`/`NIN`/`ALL` → `$in`/`$nin`/`$all`,
`GT/GTE/LT/LTE` → `$gt…`, `EXISTS` → `{f: {"$ne": None}}`, `NOT_EXISTS` → `{f: None}`,
`CONTAINS` → escaped case-insensitive `$regex`, `NOT_CONTAINS` → `$not` regex. `AnyOf` → `$or`
(empty = match nothing), several filters → `$and`. On list fields Mongo's native semantics give
"EQ = contains element, IN = contains any". `find()` adds `_id` as a tie-breaker to the sort so
pagination is deterministic.

## Connection settings (`apps/backend/core/config.py`, `apps/backend/.env.example`)

| Env | Default | Meaning |
|---|---|---|
| `BE_DB_PROVIDER` | `mongo` | provider switch |
| `BE_MONGO_URI` | `mongodb://localhost:27017` | full connection string (secret; credentials, replica set, `authSource`, TLS options go here) |
| `BE_MONGO_DB` | `app` | database name |
| `BE_MONGO_TIMEOUT_MS` | `5000` | server-selection + connect timeout |
| `BE_TABLE_USERS` … `BE_TABLE_UPLOADS` | `users` … `uploads` | collection names |

Choosing `BE_MONGO_DB`: one database per deployed app/environment (e.g. `myapp`, `myapp_staging`).
When several apps share a cluster, give each its own `BE_MONGO_DB` rather than prefixing
collections. Local dev: `npm run docker:infra` starts Mongo + Redis from the root
`docker-compose.yml` (bound to 127.0.0.1).

## Errors

- Duplicate key → `ConflictError` 409 `{"field": "<camelCase field>", "message": "already exists"}`.
  The field comes from `keyPattern`, else the `uniq_<field>` index name in the message, else a probe
  query (mongomock raises a bare `E11000`).
- Connection failures (`pymongo.errors.ConnectionFailure`) anywhere in a request → 503
  `SERVICE_UNAVAILABLE` (handler registered in `core/app_factory.py`).

## Testing

`apps/backend/tests/conftest.py` builds `MongoDatabase(settings, client=mongomock.MongoClient(tz_aware=True))`
and calls `ensure_schema()`; repository fixtures (`users_repo`, `groups_repo`, …) and the app share it.
Provider-level tests: `apps/backend/tests/db/test_mongo_repository.py`,
`apps/backend/tests/db/test_mongo_translator.py`. mongomock limitations seen so far: duplicate-key
errors lack `keyPattern` (handled by the probe), and `create_indexes()` drops partial filters (the
code calls `create_index` once per index for that reason).

## Checklist — new collection

- [ ] Entity in `db/schema.py` (added to `ENTITIES`), snake_case fields, `unique=True` where needed
- [ ] `TABLE_<X>` in `Settings` + `BE_TABLE_<X>` in `.env.example`
- [ ] Supabase migration too (the entity must work on both providers — see `fastapi-crud-collection`)
- [ ] No pymongo import outside `db/mongo/`
- [ ] Test the 409 path and any filter you rely on

## Common mistakes

- Querying `{"_id": …}` or `{"createdAt": …}` through a repository → use `id` / `created_at`.
- Expecting `update()` to create a missing document — it returns `None` (service raises 404).
- Relying on Mongo-only behaviour (regex operators, `$elemMatch`, aggregation) in a service: the
  Supabase provider cannot run it. Extend the `Op` vocabulary in both translators instead.
- Treating `BE_MONGO_URI` as non-secret (it is a `SecretStr`; never log it).
