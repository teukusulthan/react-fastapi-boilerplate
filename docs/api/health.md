# API — Health (`/health`)

Code: `apps/backend/router/health.py`. The health router is always mounted (it cannot be disabled with
`BE_ENABLED_ROUTERS`). It is public, never rate limited, never payload-encrypted, and kept out of the
access log.

## `GET /health/live`

The process is up. Use it for liveness probes; the Docker `HEALTHCHECK` calls it.

```json
{ "metaData": { "status": true, "responseCode": 200, "message": "Success", "executionTime": 1, "requestId": "…", "pagination": null },
  "data": { "status": "ok" } }
```

## `GET /health/ready`

Pings the database and Redis. With the Mongo provider it also ensures the indexes exist; with the
Supabase provider it checks that the migrated tables exist. Use it for readiness probes.

| Result | Response |
|---|---|
| Ready | 200 `data: { "status": "ready", "checks": { "database": "ok", "redis": "ok" } }` |
| Not ready | 503 `SERVICE_UNAVAILABLE`, `data: { "database": "ok" \| "unavailable", "redis": "ok" \| "unavailable" }` |

The usual cause of `database: unavailable` with `BE_DB_PROVIDER=supabase` is that
`migrations/supabase/*.sql` has not been applied yet.
