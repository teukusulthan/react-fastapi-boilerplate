# Data, Safety & Performance Rules

Companion to [../SKILL.md](../SKILL.md). Verified against `apps/backend/db/` and `apps/backend/service/`.

## Provider abstraction

- `BE_DB_PROVIDER=mongo` (default) → `db/mongo/` (`MongoDatabase`, `MongoRepository`, `translator.py`, `indexes.py`).
- `BE_DB_PROVIDER=supabase` → `db/supabase/` (`PostgresDatabase` on a psycopg 3 pool, `PostgresRepository`,
  `SqlTranslator` — SQL composed only with `psycopg.sql`).
- Both implement `db.base.Repository` with identical semantics (tested in `tests/db/` and, with
  `TEST_POSTGRES_DSN`, by every module test in `tests/modules/`). Service code must not care which one runs.
- The app builds the provider in its lifespan (`core/app_factory.py` → `db/factory.py::create_database`) and
  exposes it as `app.state.database`; `core/deps.py::get_database` / `get_repository(entity)` hand it out.

## Record conventions

| Topic | Rule |
|---|---|
| ids | app-generated `str(uuid.uuid4())` (`util.helper.new_id`); Mongo `_id` holds it, Postgres `id uuid` |
| keys | snake_case storage names; the API is camelCase (DTO aliases) |
| timestamps | aware UTC, truncated to milliseconds (`db/records.py::to_storage_datetime`); use `util.helper.utc_now()` |
| defaults | every declared field is present after insert (`Field.default`, callables invoked) |
| immutables | `id`, `created_at` ignored by `update`; `updated_at` refreshed automatically |
| secrets | `sensitive=True` fields (e.g. `password_hash`, `two_factor_secret`) can never be filtered/sorted/searched |
| uniqueness | DB unique index/constraint is the guarantee → `ConflictError` (409) naming the field |
| references | Postgres FK/CHECK violations → `ValidationError` (422); check references in services for both providers |

## List queries

- `FindDTO` → `build_query_spec` → `QuerySpec` → `repo.find(spec)` → `(items, total)` → `paginated(...)`.
- All problems are collected and raised as **one** 422 listing every bad field (`filters[0].field`, `orderBy`, …).
- Values are coerced to the field type (ISO / epoch-ms datetimes, `"true"`/`"false"`, ints, uuids); objects rejected.
- `search` without `searchBy` searches every searchable field; with `searchBy` only those (must be searchable).
- Default sort `created_at desc`; Mongo adds `_id` as a tie-breaker for stable pagination.
- Page size cap: `BE_MAX_PAGE_SIZE` (default 100).

## Concurrency & performance

- Repositories are blocking and thread-safe; call them from sync `def` routes/deps (threadpool sized by
  `BE_THREADPOOL_SIZE`). Never from `async def` without `anyio.to_thread.run_sync`.
- Prefer `get_many_by_ids` / `count` over N+1 loops (see `service/user_profile.py::load_user_profiles`).
- Non-atomic multi-step checks (e.g. "last superuser", "still referenced") are acceptable but document them;
  there are no cross-statement transactions.
- Connection pooling is owned by the provider (`MongoClient` / `psycopg_pool.ConnectionPool`); never create
  clients per request.

## Forbidden patterns

| Forbidden | Instead |
|---|---|
| `from pymongo import ...` / `import psycopg` in services | `from db import Repository, Condition, Op, ...` |
| f-string / `%` SQL, `$where`, `$regex` built from user input | `Condition(..., Op.CONTAINS, text)` (escaped) |
| Passing request dicts straight into `find_one` | build `Condition`s from validated DTO fields |
| `delete_many({})` | refused by design; add a filter |
| Storing `password` / OTPs in plain text | `core.security.hash_password`, `hash_otp`, `encrypt_secret` |
| Unbounded `find_all()` on user data | `find(spec)` with pagination, or `find_all(limit=...)` |
