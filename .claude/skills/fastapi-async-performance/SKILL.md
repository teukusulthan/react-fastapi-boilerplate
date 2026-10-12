---
name: async-performance
description: "Concurrency & performance rules for the backend (apps/backend): routes, dependencies and services are sync def (repositories, Redis, bcrypt, boto3, SMTP are blocking) and run in FastAPI's threadpool sized by BE_THREADPOOL_SIZE (anyio limiter set in core/app_factory.py lifespan); async def only for non-blocking code, offload with anyio.to_thread.run_sync; streaming uploads, pooled clients, pagination limits, no N+1. Load when writing endpoints, calling blocking code, adding background work, or tuning throughput."
---

# Async & performance (backend)

## Use this skill when

- Choosing `def` vs `async def` for a route or dependency
- Calling something slow (DB, Redis, S3, SMTP, external HTTP, image processing, bcrypt)
- Handling large payloads, long lists or CPU-heavy work
- Tuning workers/threads

## How the app runs

- Uvicorn (`api.py`, `BE_WORKERS` processes). Each process runs sync `def` routes **and** sync dependencies in
  anyio's worker threads; the limiter is set to `BE_THREADPOOL_SIZE` (default 40) in
  `core/app_factory.py::lifespan`.
- Every data/infra client is blocking and thread-safe: `pymongo.MongoClient`, `psycopg_pool.ConnectionPool`
  (`BE_SUPABASE_DB_POOL_MIN/MAX`), `redis.Redis`, boto3 (`util/s3.py`), kafka producer (`util/kafka.py`).
  They are created once per process (lifespan / lazy cached) — never per request.
- All built-in routes are sync `def` (see `router/*.py`). Google OAuth uses a sync `httpx.Client` in a `def` route.

## Rules

### MUST
- Write routes, dependencies and services as plain `def`. FastAPI offloads them to the threadpool.
- Use `async def` only when the body awaits truly async I/O and calls **nothing** blocking (rare here:
  e.g. a pure computation or an `httpx.AsyncClient` call with no repository access).
- If async code must call blocking code, offload it: `await anyio.to_thread.run_sync(func, *args)`
  (the lifespan does this for `database.open` / `ensure_schema`).
- Bound everything user-controlled: page size (`BE_MAX_PAGE_SIZE`), `find_all(..., limit=)`, upload size
  (`BE_UPLOAD_MAX_SIZE_MB`, enforced while streaming by `router/upload.py::UploadLimitRoute`), encrypted body size.
- Batch lookups (`get_many_by_ids`, `count`) instead of per-row queries (see `service/user_profile.py::load_user_profiles`).
- Stream large files (spooled temp files + `S3Storage.upload_fileobj` multipart) instead of reading them into memory.
- Treat side effects that may be slow and are not essential (Kafka publish, notification email) as best effort:
  log failures, don't fail the request (pattern: `service/upload.py::_publish_extraction`).

### MUST NOT
- No blocking call inside `async def` (repositories, `redis`, `bcrypt`, `boto3`, `smtplib`, sync `httpx.Client`,
  `time.sleep`, file I/O, Pillow) — it freezes the event loop for every request in that worker.
- No new clients/pools per request; no `asyncio.get_event_loop().run_until_complete` inside handlers.
- No custom thread pools / `set_default_executor` hacks and no threadpool monitoring endpoints — tune `BE_THREADPOOL_SIZE`.
- No long CPU-bound loops in a request; move heavy jobs to a worker (e.g. consume the Kafka topic) and return an id.
- No unbounded `find_all()` / full-collection scans in request paths.

```python
# ✅ default
@router.post("/get-all", response_model=ApiResponse[list[GroupResponse]])
def get_all(query: FindGroupDTO, service: GroupServiceDep):
    items, total = service.list(query)
    return paginated(items, query.page, query.size, total)

# ✅ async only with non-blocking work; offload anything blocking
@router.get("/report", response_model=ApiResponse[ReportResponse])
async def report(service: ReportServiceDep):
    data = await anyio.to_thread.run_sync(service.build)
    return ok(data)

# ❌ blocks the event loop
@router.get("/report")
async def report_bad(service: ReportServiceDep):
    return ok(service.build())        # repository calls inside
```

## Tuning knobs

| Setting | Effect |
|---|---|
| `BE_WORKERS` | processes (each has its own pools/threads); reload forces 1 |
| `BE_THREADPOOL_SIZE` | max concurrent sync routes/deps per process |
| `BE_SUPABASE_DB_POOL_MAX` | Postgres connections per process (keep ≥ expected concurrent DB work, ≤ server limits × workers) |
| `BE_MONGO_TIMEOUT_MS`, `BE_SUPABASE_DB_TIMEOUT` | fail fast → 503 `SERVICE_UNAVAILABLE` instead of hanging |
| `BE_RATE_LIMIT_GLOBAL` | optional per-client global budget |

## Checklist

- [ ] Route/dependency is `def` (or `async def` with zero blocking calls)
- [ ] Inputs bounded (page size, list limits, payload size)
- [ ] No N+1; batched lookups
- [ ] Slow optional side effects are best effort and logged
- [ ] Clients reused (from `app.state` / cached helpers)

## Common mistakes

| Mistake | Fix |
|---|---|
| `async def` route + `service.list(...)` | make it `def` |
| `requests.get` / sync `httpx` in `async def` | `def` route, or `httpx.AsyncClient` with no other blocking calls |
| `MongoClient(...)` inside a service | use the injected `Repository` |
| Reading the whole upload with `await file.read()` | stream the spooled file (`form.file.file`) |
