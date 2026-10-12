---
name: fastapi-database-init
description: "How the apps/backend database provider abstraction works (db/base.py Repository + Database ABCs, filter tree / QuerySpec, db/records.py, db/factory.py, Mongo and Supabase/Postgres adapters, lifespan open/ensure_schema/close, readiness, error mapping) and how to add a new provider/adapter (e.g. MySQL, another Postgres flavour) or a secondary data source (Elasticsearch, analytics DB). Use when the user asks to add/replace a database type, connect an extra datastore, or change how repositories talk to the database."
---

# fastapi-database-init — Provider abstraction & adding a provider

The backend supports two interchangeable **primary** databases selected by `BE_DB_PROVIDER`:
`mongo` (default, pymongo) and `supabase` (Supabase/any Postgres via psycopg 3 + psycopg_pool,
SQL composed only with `psycopg.sql`). Services never import a driver; they get a
`db.base.Repository` per entity. Provider-specific details: `fastapi-mongo` (Mongo),
`apps/backend/migrations/supabase/README.md` (Postgres).

## Use this skill when

- Adding a new primary provider (MySQL, CockroachDB, …) that must run every module unchanged.
- Adding a *secondary* datastore for one feature (Elasticsearch, ClickHouse, an external API).
- Changing repository semantics (a new filter operator, a new field type).
- Debugging startup/readiness ("Missing tables", 503 `SERVICE_UNAVAILABLE`).

## How it fits together

```
core/config.py      Settings.DB_PROVIDER: Literal["mongo", "supabase"] (+ MONGO_*, SUPABASE_DB_* settings, TABLE_* names)
db/factory.py       create_database(settings) -> Database        (imports the driver lazily)
db/base.py          Database ABC: repository(entity), ping(), ensure_schema(), close(), open() hook
                    Repository ABC: get_by_id, get_many_by_ids, find_one, find(QuerySpec) -> (items, total),
                    find_all, count, exists, insert, update, update_many, delete, delete_many; .entity
                    Filter tree: Condition(field, Op, value) | AnyOf | AllOf | {"field": value}; Where; normalize_where()
                    QuerySpec(where, sort, offset, limit, page, size), QuerySpec.of(...), .and_where(...); SortSpec
db/schema.py        EntitySchema/Field/FieldType + USERS PERMISSIONS GROUPS ROLES UPLOADS, ENTITIES, register_entity()
db/records.py       prepare_insert / prepare_update / check_fields / to_storage_datetime (shared by all providers)
db/query.py         build_query_spec(FindDTO, entity, ...) -> QuerySpec (whitelists, coercion, one 422 for all errors)
db/mongo/           MongoDatabase, MongoRepository, translator.translate_where, indexes.ensure_indexes
db/supabase/        PostgresDatabase (ConnectionPool), PostgresRepository, translator.SqlTranslator
core/app_factory.py lifespan: create_database -> database.open() -> _ensure_schema() ; shutdown: database.close()
                    _register_infrastructure_errors(): driver outage exceptions -> 503 SERVICE_UNAVAILABLE
core/deps.py        get_database (app.state.database), get_repository(entity), UsersRepo/GroupsRepo/... aliases
router/health.py    GET /health/ready -> database.ping() (+ ensure_schema() until it succeeds) and redis.ping()
scripts/seed.py     builds its own database with create_database(settings)
```

All paths are under `apps/backend/`.

### Contract every provider must honour (identical semantics)

- Records are plain dicts with **snake_case** keys, `id` = uuid4 string, aware-UTC datetimes
  truncated to milliseconds; every declared field present (defaults from the entity).
- Writes go through `prepare_insert` / `prepare_update` (unknown field or `None` in a non-nullable
  field → `ValueError`); `update` is partial, never upserts, returns `None` when missing.
- Unique violation → `core.errors.ConflictError` with `details=[{"field": "<camelCase>", "message": "already exists"}]`.
  Postgres FK/CHECK violations → `core.errors.ValidationError` (422) naming the field.
- Operators (`db.base.Op`): `EQ NE IN NIN GT GTE LT LTE EXISTS NOT_EXISTS CONTAINS NOT_CONTAINS ALL`.
  `NE`/`NIN`/`NOT_CONTAINS` also match null; on `LIST` fields `EQ` = contains element, `IN` =
  contains any, `ALL` = contains all, `NIN` = contains none; `CONTAINS` = case-insensitive **literal**
  substring (escaped); non-uuid values on `ID` fields never match (no driver error); dict values are
  rejected. `AnyOf()` empty = match nothing, `AllOf()` empty = match everything.
- `find()` returns `(page_items, total)` and sorts deterministically (tie-break on id).
- `delete_many` refuses an empty filter.
- Thread-safe: services are sync and run in FastAPI's threadpool (`BE_THREADPOOL_SIZE`).

The executable spec is the test-suite: `tests/db/test_mongo_repository.py`,
`tests/db/test_mongo_translator.py`, `tests/db/test_supabase_translator.py`,
`tests/db/test_supabase_integration.py` (real Postgres, `TEST_POSTGRES_DSN`), `tests/db/test_query.py`,
and every module test in `tests/modules/` (parametrized over mongo + postgres in
`tests/modules/conftest.py`).

## Rules

MUST
- Keep services/routers provider-agnostic: only `db` (`Repository`, `Condition`, `Op`, …),
  `db.schema`, `db.query`. Drivers are imported only inside `db/<provider>/` (and in
  `core/app_factory.py` for exception mapping).
- Implement the full `Repository` / `Database` ABCs and reuse `db/records.py` so defaults, ids and
  timestamps are identical across providers.
- Compose SQL with the driver's safe composition API (`psycopg.sql.Identifier`/placeholders in the
  existing adapter). Identifiers come only from the `EntitySchema`; values are always bound params.
- Translate driver errors: unique → `ConflictError`, FK/check → `ValidationError`, connection loss →
  register the driver's exception class in `_register_infrastructure_errors` (503).
- Read configuration from `Settings` (`BE_*` env, secrets as `SecretStr`), validate cross-field
  requirements in `Settings._cross_field_checks`, and document every key in `.env.example`.
- Make `open()` non-blocking for startup (Postgres opens the pool with `wait=False`) — readiness
  reports the outage instead of crashing the app.

MUST NOT
- Add a second code path in services (`if settings.DB_PROVIDER == ...`).
- Build query strings with f-strings / `%` formatting of identifiers or values.
- Run DDL from the app for SQL providers — schema comes from migrations; `ensure_schema()` only verifies
  (Mongo creates indexes because they are idempotent and data-safe).
- Create module-level clients at import time; clients are created in the lifespan (or injected in
  tests: `create_app(settings, database=..., redis=...)`).

## Recipe A — add a new primary provider (e.g. `mysql`)

Everything below is a recipe; the `mysql` files do not exist — create them.

1. **Settings** (`core/config.py`): extend `DB_PROVIDER: Literal["mongo", "supabase", "mysql"]`, add
   `MYSQL_URL: SecretStr | None = None` (+ pool sizes/timeouts), add a `_cross_field_checks` error when
   `DB_PROVIDER == "mysql"` and the URL is missing, add the blank-to-None validator entry, document
   `BE_MYSQL_*` in `.env.example`.
2. **Adapter package**: create `apps/backend/db/mysql/` with `client.py` (`MySqlDatabase(Database)`,
   `provider = "mysql"`, pool in `__init__`, `open()`, `repository(entity)` cached per entity with a
   `threading.Lock` like `db/supabase/client.py`, `ping()`, `ensure_schema()` that checks every
   `ENTITIES` table exists, `close()`), `repository.py` (`MySqlRepository(Repository)` — start by
   copying `db/supabase/repository.py`), `translator.py` (copy `db/supabase/translator.py` and port
   JSON/list operators, `ILIKE` → `LIKE … COLLATE`, uuid handling), `__init__.py` exporting both.
3. **Factory** (`db/factory.py`): add the branch with a lazy import.
4. **Infra errors** (`core/app_factory.py::_register_infrastructure_errors`): add the driver's
   connection/timeout exception classes.
5. **Migrations**: create `apps/backend/migrations/mysql/001_init.sql` mirroring `db/schema.py` (names,
   nullability, defaults, unique constraints named `<table>_<field>_key` so the conflict mapper can
   name the field) + a README on how to apply.
6. **Dependencies**: pin the driver in `requirements.txt` (direct deps only); add a test-only fake to
   `requirements-dev.txt` if one exists.
7. **Tests**: port `tests/db/test_supabase_translator.py` (pure SQL generation) and
   `tests/db/test_supabase_integration.py` (real DB behind an env DSN, `@pytest.mark.integration`);
   add a provider param to `tests/modules/conftest.py::database` so every module test runs on it.
8. **Ops**: compose service/profile and CI job (repo-level files — coordinate with their owners).

Done when the full `pytest` suite passes on the new provider with no change in `service/` or `router/`.

## Recipe B — a secondary datastore for one feature (Elasticsearch, external API…)

Not a `Database` provider (it does not store users/permissions). Keep it out of `db/`:

- Client factory in `apps/backend/util/<name>.py`, modelled on `util/s3.py` / `util/kafka.py`:
  created lazily from `Settings`, cached per configuration behind a lock, raises
  `ConfigurationError` (503) when its settings are missing, so the app still boots without it.
- Settings `BE_<NAME>_*` in `core/config.py` + `.env.example`, plus a `<name>_configured` property.
- Inject into the feature service through a provider dependency (see `get_storage_factory` in
  `service/upload.py`) so tests can swap a fake via `app.dependency_overrides`.
- Close long-lived clients in the lifespan shutdown if the library needs it (like `close_kafka_producer`).
- Optional: add a check to `router/health.py` only if the app cannot serve traffic without it.

## Checklist

- [ ] No driver import outside `db/<provider>/` (`grep -rn "import pymongo\|import psycopg" service router dto`)
- [ ] `Settings` Literal + validation + `.env.example`
- [ ] `create_database()` branch; lifespan `open/ensure_schema/close` work; `/health/ready` reports outages
- [ ] Unique → 409, FK/check → 422, outage → 503 (registered exception classes)
- [ ] Migrations mirror `db/schema.py`
- [ ] `tests/db` equivalents + module tests parametrized over the provider; `ruff check .` clean

## Common mistakes

- Returning driver types (`ObjectId`, `uuid.UUID`, naive datetimes, `Decimal`) — normalise in the
  repository (`_from_row` / `_from_doc`).
- Forgetting that `ensure_schema()` iterates `ENTITIES` — an entity registered late (inside a service
  module) is missed by scripts/tests that call it before importing routers. Declare entities in
  `db/schema.py`.
- Letting `ConnectionPool(open=True)` block startup when the DB is down.
- Implementing search with a raw pattern (`LIKE '%' || $1 || '%'` without escaping) — `%`/`_` must be
  escaped (`escape_like` in `db/supabase/translator.py`).
- Changing semantics in one translator only; both providers must keep passing the same module tests.
