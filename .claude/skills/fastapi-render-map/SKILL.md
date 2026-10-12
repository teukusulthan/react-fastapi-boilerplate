---
name: fastapi-render-map
description: Use when writing code that renders MVT tiles, runs map analytics, fetches GeoJSON, or extracts coordinates. Covers TWO patterns — (1) Migration Pattern for mapPlugin widgets driven by a static maps.json manifest (simpler, no MongoDB), and (2) the full ERP tile engine with MongoDB-backed query catalog, filter DTO, Redis cache, and geometry filter.
---

# fastapi-render-map — MVT Rendering & Map Query Logic

---

## Adapting to the current foundation

> This skill documents a **domain feature that is not part of this boilerplate** (no such router/service/DTO exists in `apps/backend`). Its snippets were written against an older backend foundation. Keep the domain logic, but when you implement it here, translate every infrastructure call with the table below and follow `fastapi-crud-collection` (resource layout), `fastapi-api-design` (envelope, errors, routing) and `fastapi-data` (repositories). Reference module to copy: `router/group.py` + `service/group.py` + `dto/group.py`.

| Old foundation (in the snippets below) | Current foundation (`apps/backend`) |
|---|---|
| `from config import settings` / `config.base` | `settings: SettingsDep` in routes/deps, `core.config.get_settings()` elsewhere (`core/config.py`). New keys = `Settings` fields (env `BE_<KEY>`) + `.env.example`; never `os.getenv`. |
| `settings.MONGO_COLLECTION_<X>` + raw collections | declare an `EntitySchema` in `db/schema.py` (`table_setting="TABLE_<X>"`, filter/search/sort flags) + `TABLE_<X>: str` in `Settings`; Supabase needs `migrations/supabase/00N_<x>.sql` (see `fastapi-crud-collection`) |
| `Services.mongo()` / `Services.redis()` / `BaseMongoRepository` subclasses | a plain service class receiving `db.Repository` objects via `Depends(get_repository(ENTITY))` and `RedisDep` (`core/deps.py`); services never import `pymongo`/`psycopg` (see `fastapi-data`) |
| `mongo_query_builder(dto, text_type=...)` + `FindDTO` dicts | `CrudService.list(query, extra_where=...)` or `db.query.build_query_spec(dto, ENTITY, searchable=...)` → `repo.find(spec)`; whitelists come from the entity |
| `change_field_id(docs)` / `v_<collection>` views | not needed — repositories return dicts with `id`; enrich in the service (pattern: `service/user_profile.py:load_user_profiles`) |
| md5 / timestamp / content-derived `_id` | app-generated uuid4 (`repo.insert` sets it; `util.helper.new_id()` when you need it earlier). For idempotent upserts look up by a unique field instead |
| `BaseResponse(data=..., metaData=MetadataSuccess(...))` / `get_execution_time(start)` | `ok(data)` / `created(data)` / `paginated(items, page, size, total)` with `response_model=ApiResponse[T]` (`core/responses.py`); `executionTime` is filled automatically |
| `HTTPException(400, str(e))` / `BaseResponseFailed` | raise `core.errors` classes: `BadRequestError`, `NotFoundError`, `ConflictError`, `ValidationError.for_field(...)`, `ConfigurationError` (feature not configured) — the global handlers build the error envelope |
| `APIRouter(**router_param_builder(tag))`, `ROUTER_MODULES`, `--routers` | `APIRouter(prefix="/x", tags=["x"])` + `RouterSpec("x", "router.x")` in `router/__init__.py`; toggle with `BE_ENABLED_ROUTERS` (empty = all) |
| `JWTBearer` / `JWTChangeUserId` / user id taken from the body | `CurrentUserDep`, `AdminUserDep`, `require_privilege("x:write")`, `InternalDep` (`core/deps.py`); `created_by` = `user.id` |
| `print(...)`, `traceback.print_exc()`, f-string logs | `from loguru import logger`; `logger.info("x {}", value)` (see `fastapi-logging`) |
| `util.kafka_util`, `util.s3_filesystem`, `util.aes_encryption` | `util.kafka.publish(settings, topic, value)`, `util.s3.get_s3_storage(settings)`, `util.crypto` (see `fastapi-file-upload`) |
| `async def` routes calling blocking clients | sync `def` routes/services (FastAPI threadpool); see `fastapi-async-performance` |
| `from util.pg import _get_pool` (psycopg2 pool from `PG_PROD_2_*` env vars) | the boilerplate uses psycopg 3 (`psycopg[binary]`, `psycopg_pool`). For a separate GIS database create `util/gis_db.py` with a `psycopg_pool.ConnectionPool` built from a new `BE_GIS_DB_URL` setting (pattern: `db/supabase/client.py`); compose SQL with `psycopg.sql` |
| `Services.handler_mvt()` / `Services.handler_geospatial()` factories | plain service classes provided by `get_<x>_service` dependencies (`Annotated[XService, Depends(...)]`) |
| `VITE_MAP_TILE_URL=http://localhost:8000/api/map` | tiles go through the web proxy: `/api/v1/apps/map/...` (backend :8020). Add the variable to `apps/web/src/config/env.ts` + `apps/web/env/.env.example` (see `reactjs-manage-env`) |
| Redis via a global client | `RedisDep` / `request.app.state.redis` (`core/redis.py:redis_key(settings, ...)` for key prefixes) |

## Which pattern to use?

| Scenario                                                                   | Pattern                                        |
| -------------------------------------------------------------------------- | ---------------------------------------------- |
| Migrated dashboard with `mapPlugin` widgets, SQL embedded in `maps_*.json` | **Migration Pattern** — Section A (read first) |
| Full ERP tile server with MongoDB query catalog, filter DTO, cluster mode  | **ERP Pattern** — Section B                    |

---

## Section A — Migration Pattern: Static `maps.json` Manifest

Use this when the FE `MapPluginWidget` calls `/api/map/{layerId}/{z}/{x}/{y}.pbf`.
SQL and connection config are read from the static `maps.json` file (built by `fetch_map_queries.py`
or embedded directly in `maps_*.json`). No MongoDB query catalog, no complex filter DTO.

### Data flow

```
FE: tiles source url → /api/map/{layerId}/{z}/{x}/{y}.pbf
                                  │
                         router/map.py  GET /{layer_id}/{z}/{x}/{y}.pbf
                                  │
                         service/map.py
                           ├─ lookup layer in _MAPS_MANIFEST by layers_id
                           ├─ build conn_config from layer embedded fields
                           ├─ substitute ST_TileEnvelope(z,x,y) in queryContentMaps
                           ├─ Redis cache check  MVT:{md5(query+conn_key)}
                           ├─ execute raw SQL → bytea
                           ├─ parse_id_properties  (assign UUID feature IDs)
                           ├─ gzip compress
                           └─ return Response(content, Content-Encoding: gzip, application/x-protobuf)

FE: tooltip/analytic    → /api/map/{layerId}/data
                                  │
                         service/map.py
                           ├─ lookup layer in manifest
                           ├─ execute queryContent (base SQL, not MVT)
                           └─ return JSON rows
```

### Manifest loading — `service/map.py`

The manifest is loaded **once at module import** from the path resolved relative to `__file__`.
Three levels up because `service/map.py` is at `apps/backend/service/map.py` and the
manifest is at `<project-root>/dashboard-migrator/maps.json`.

```python
# service/map.py
import os, json, re, gzip, hashlib, time
from io import BytesIO
from uuid import uuid4
from pathlib import Path
import mapbox_vector_tile

_MANIFEST_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../dashboard-migrator/maps.json")
)

_MAPS_MANIFEST: dict[str, dict] = {}   # key = layers_id → layer dict

def _load_manifest() -> None:
    global _MAPS_MANIFEST
    if not os.path.exists(_MANIFEST_PATH):
        return
    with open(_MANIFEST_PATH, encoding="utf-8-sig") as f:
        data = json.load(f)
    for map_entry in data:
        for layer in map_entry.get("layers", []):
            lid = layer.get("layers_id")
            if lid:
                _MAPS_MANIFEST[lid] = layer

_load_manifest()   # executed once at import time
```

> **After any change to `_MANIFEST_PATH` or manifest file:** restart the BFF — the dict is cached
> in memory. `_load_manifest()` is **not** called per-request.

### Connection — use the shared pool, not embedded JSON credentials

> **CRITICAL:** Do **NOT** open a direct `psycopg2.connect()` using the credentials embedded in
> `maps.json`. The JSON fields (`host`, `database`, `port`) are often wrong — e.g. `database:
"postgres"` instead of the real DB, or `port: 5432` instead of the custom port configured in
> `.env`. Always use the shared pool from `util/pg.py` which reads from `PG_PROD_2_*` env vars.

```python
# ✅ Correct — pool is env-configured (PG_PROD_2_HOST/PORT/DB/USER/PASSWORD)
from util.pg import _get_pool

pool = _get_pool()
conn = pool.getconn()
try:
    with conn.cursor() as cur:
        cur.execute(sql)
        row = cur.fetchone()
finally:
    pool.putconn(conn)

# ❌ Wrong — JSON embeds wrong database/port; causes cross-db errors or connection failures
import psycopg2
with psycopg2.connect(
    host=layer["host"],
    dbname=layer["database"],   # ← often "postgres" instead of the real DB
    port=layer.get("port", 5432),
    user=layer["connectionUsername"],
    password=layer["connectionPassword"],
) as conn: ...
```

### Cross-database SQL qualifier stripping

SQL exported from the legacy ERP often contains cross-database table references like `"phe".public.basin_ihs`.
PostgreSQL does **not** support cross-database queries — this will raise:
`cross-database references are not implemented: "phe".public.basin_ihs`

Strip the database qualifier before executing any SQL from the manifest:

```python
def _strip_db_qualifier(sql: str) -> str:
    """Remove "dbname". prefix from table references — PG does not support cross-db queries."""
    return re.sub(
        r'"[^"]+"\s*\.\s*((?:public|[a-zA-Z_][a-zA-Z0-9_]*)\s*\.)',
        r'\1',
        sql,
    )
```

Apply to **both** `queryContentMaps` (tile SQL) and `queryContent` (analytics SQL):

```python
sql = _strip_db_qualifier(sql)
sql = _substitute_tile_envelope(sql, z, x, y)
```

### MVT tile service

```python
def render_tile(layer_id: str, z: int, x: int, y: int) -> bytes:
    layer = _MAPS_MANIFEST.get(layer_id)
    if not layer:
        raise ValueError(f"Layer '{layer_id}' not found in manifest")

    query = layer.get("queryContentMaps") or layer.get("contentMaps")
    if not query:
        raise ValueError(f"Layer '{layer_id}' has no MVT query (queryContentMaps)")

    # Substitute tile coordinates
    query = re.sub(
        r"ST_TileEnvelope\(\d+,\s*\d+,\s*\d+\)",
        f"ST_TileEnvelope({z}, {x}, {y})",
        query,
    )

    conn = _conn_config(layer)
    conn_key = f"{conn['host']}:{conn['database']}"
    cache_key = f"MVT:{hashlib.md5((query + conn_key).encode()).hexdigest()}"

    # Redis cache check
    cached = _redis_get(cache_key)
    if cached:
        decoded = json.loads(cached)
        return _encode_and_compress(decoded)

    # Execute SQL
    raw_bytes = _exec_mvt_sql(conn, query)
    decoded = mapbox_vector_tile.decode(raw_bytes)

    # Assign UUID-based feature IDs
    composite = decoded.get("composite")
    if composite:
        for feat in composite["features"]:
            feat["id"] = int(str(uuid4().int)[:16])
        raw_bytes = mapbox_vector_tile.encode({
            "features": composite["features"],
            "name": "composite",
        })
        _redis_set(cache_key, json.dumps(decoded), ex=300)

    return _compress_gzip(raw_bytes)


def _exec_mvt_sql(conn: dict, query: str) -> bytes:
    import psycopg2
    with psycopg2.connect(
        host=conn["host"], port=conn.get("port", 5432),
        dbname=conn["database"],
        user=conn["username"], password=conn["password"],
    ) as pg:
        with pg.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            return bytes(row[0]) if row else b""


def _compress_gzip(data: bytes) -> bytes:
    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as f:
        f.write(data)
    return buf.getvalue()


def _encode_and_compress(decoded: dict) -> bytes:
    composite = decoded.get("composite")
    if not composite:
        return b""
    raw = mapbox_vector_tile.encode({
        "features": composite["features"],
        "name": "composite",
    })
    return _compress_gzip(raw)
```

### Analytics / tooltip data service

```python
def get_layer_data(layer_id: str) -> list[dict]:
    """Run queryContent (base SQL) — used for tooltip / analytic data."""
    layer = _MAPS_MANIFEST.get(layer_id)
    if not layer:
        raise ValueError(f"Layer '{layer_id}' not found in manifest")

    query = layer.get("queryContent") or layer.get("content")
    if not query:
        raise ValueError(f"Layer '{layer_id}' has no base query (queryContent)")

    conn = _conn_config(layer)
    import psycopg2
    with psycopg2.connect(
        host=conn["host"], port=conn.get("port", 5432),
        dbname=conn["database"],
        user=conn["username"], password=conn["password"],
    ) as pg:
        with pg.cursor() as cur:
            cur.execute(query)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
```

### Router — `router/map.py`

New file — **separate from** the ERP `router/maps.py` (maps CRUD + ERP tile engine). Written in the current backend style (sync `def` because the pool and Redis are blocking; errors raised as `core.errors`; JSON wrapped by `ok()` + `response_model`).

```python
# router/map.py
from typing import Any

from fastapi import APIRouter, Depends, Response

from core.deps import require_auth
from core.errors import NotFoundError
from core.responses import ApiResponse, ok
from service.map import get_layer_data, render_tile

router = APIRouter(prefix="/map", tags=["map"], dependencies=[Depends(require_auth)])


@router.get("/{layer_id}/{z}/{x}/{y}.pbf")
def mvt_tile(layer_id: str, z: int, x: int, y: int) -> Response:
    """Serve MVT tile for a migrated mapPlugin layer (binary, not enveloped)."""
    try:
        content = render_tile(layer_id, z, x, y)
    except ValueError as exc:  # unknown layer id
        raise NotFoundError("Layer not found") from exc
    return Response(content=content, headers={"Content-Encoding": "gzip"}, media_type="application/x-protobuf")


@router.get("/{layer_id}/data", response_model=ApiResponse[list[dict[str, Any]]])
def layer_data(layer_id: str):
    """Return base analytic rows for tooltip / table."""
    try:
        return ok(get_layer_data(layer_id))
    except ValueError as exc:
        raise NotFoundError("Layer not found") from exc
```

Unexpected exceptions are not caught: the global handler logs them and returns a 500 envelope without leaking the message. `require_auth` works for tiles because the browser sends the httpOnly `token` cookie on same-origin requests through the `/api/v1/apps` proxy; drop it only if the tiles are deliberately public.

### Router registration — `router/__init__.py`

Add the spec to the registry, otherwise the module is never imported:

```python
# apps/backend/router/__init__.py
ROUTERS: tuple[RouterSpec, ...] = (
    ...,
    RouterSpec("map", "router.map"),
)
```

`BE_ENABLED_ROUTERS` is optional: empty means "mount every registered router". If a deployment sets it, the list must include `map` (exact name; unknown names abort startup).

### Environment variable

```bash
# apps/web/env/.env.development — tile URL consumed by FE (add VITE_MAP_TILE_URL to src/config/env.ts first)
VITE_MAP_TILE_URL=/api/v1/apps/map
```

### File structure

```
apps/backend/
├── router/
│   └── map.py              ← new — migrated mapPlugin tile + data endpoints
├── service/
│   └── map.py              ← new — manifest loader, render_tile, get_layer_data
└── dashboard-migrator/
    └── maps.json           ← resolved by fetch_map_queries.py (or maps_*.json copy)
```

### Guardrails

| Rule                                                                          | Reason                                                                                                  |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `router/map.py` is **separate** from `router/maps.py`                         | maps.py = ERP CRUD + ERP tile engine; map.py = migration-only tile server                               |
| Add `map` to `BE_ENABLED_ROUTERS` in `.env`                                   | Router never loads without it → silent 404 on all tile requests                                         |
| Path loading uses `../../../` (3 levels) from `service/map.py`                | service file is 3 dirs deep from project root; using 2 levels silently returns empty manifest           |
| After changing path or manifest file → **restart BFF**                        | `_MAPS_MANIFEST` is cached at import time                                                               |
| Use `_get_pool()` from `util/pg.py`, not embedded JSON credentials            | JSON fields `database`/`port` are often wrong (e.g. `"postgres"` instead of `"phe"`)                    |
| Call `_strip_db_qualifier(sql)` before any `execute()`                        | Exported SQL contains `"dbname".schema.table` cross-db refs that PostgreSQL rejects                     |
| `queryContentMaps` preferred over `contentMaps` for tile SQL                  | field name in export is `queryContentMaps`; `contentMaps` is the resolved alias                         |
| `queryContent` for analytics, `queryContentMaps` for tiles — never swap       | `queryContent` returns rows; `queryContentMaps` returns MVT protobuf bytea                              |
| Always `pool.putconn(conn)` in a `finally` block                              | Leaked connections exhaust the pool                                                                     |
| Add `psycopg2-binary` to `requirements.txt`                                   | `psycopg2` is used in `service/map.py` — omitting it causes `ModuleNotFoundError` at first tile request |
| Connection password is in plaintext in `maps.json` — keep file out of commits | Add `dashboard-migrator/maps_*.json` to `.gitignore`                                                    |

---

## Section B — ERP Pattern: Full Tile Engine

## Overview

This skill documents the patterns for MVT (Mapbox Vector Tile) rendering, map analytics querying, and coordinate extraction. It covers the full pipeline: resolving connection/database config, building SQL filters, executing tile queries, caching MVT results, and walking the Menu→Widget→Map→Layer reference chain to extract rendering parameters.

**Core principle:** MVT tile rendering is a 12-step pipeline from tile request to gzip-compressed protobuf response. Map analytics follows a parallel pipeline for non-tile queries. Both share the same connection resolution, filter building, caching, and execution patterns.

## Architecture

```
Tile Request (z/x/y)              Map Analytics Request            Coordinate Extraction
       │                                  │                                │
       ├─ Route handler                  ├─ Service method                ├─ URL → Menu
       │   ├─ Parse DTO                  │   ├─ Resolve static query      │   ├─ Menu → Widget (mapPlugin)
       │   ├─ Resolve geometry filter    │   ├─ Resolve connection        │   ├─ Widget → Map
       │   └─ Delegate to tile engine    │   ├─ Resolve data source       │   ├─ Map → Layer
       │                                  │   ├─ Build SQL with filters   │   └─ Extract MVT params
       ▼                                  │   ├─ Redis cache check        │
Tile Engine                              │   ├─ Execute via driver       │
  ├─ Resolve static query                │   ├─ LLM fallback on error    │
  ├─ Resolve connection + data source    │   ├─ Date mapping              │
  ├─ Substitute ST_TileEnvelope(z,x,y)   │   └─ Cache result             │
  ├─ Extract coordinate field            │                                │
  ├─ Build SQL filters                   │                                │
  ├─ Inject filter geometry              │                                │
  ├─ Redis cache check (MVT:{hash})      │                                │
  ├─ Execute raw SQL → protobuf bytes    │                                │
  ├─ Parse & assign feature IDs           │                                │
  ├─ Compress with gzip                   │                                │
  └─ Cache + return bytes                 │                                │
```

## Static Query Resolution (replaces Query Catalog)

> The query catalog pattern (MongoDB-stored queries) is no longer used across projects. Queries are now stored as static JSON or YAML files in a user-specified directory.

### Query File Convention

```
queries/                          ← user-specified base directory
  ├── <query_name>.json           ← standard query definition
  └── <query_name>_mvt.json       ← MVT-specific variant (optional)
```

### Query Document Shape

```json
{
  "name": "population_density",
  "workspaceId": "ws_abc123",
  "connectionId": "conn_xyz",
  "sourceId": ["src_001"],
  "content": "SELECT ... FROM ... WHERE ...",
  "contentMaps": "SELECT ST_AsMVTGeom(geom, ST_TileEnvelope(8,206,128)) AS geometry, ... FROM ... WHERE ..."
}
```

### Resolution Logic

```python
def resolve_query(query_name: str, query_dir: str, mvt: bool = False) -> dict:
    """Resolve a query from static JSON files."""
    base_path = Path(query_dir)

    # Try primary query file
    query_file = base_path / f"{query_name}.json"
    if query_file.exists():
        query = json.loads(query_file.read_text())

        # For MVT: prefer contentMaps, fallback to _mvt variant
        if mvt:
            if query.get("contentMaps"):
                return query
            mvt_file = base_path / f"{query_name}_mvt.json"
            if mvt_file.exists():
                return json.loads(mvt_file.read_text())

        return query

    raise FileNotFoundError(f"Query '{query_name}' not found in {query_dir}")
```

Key patterns:

- `contentMaps` field in the query JSON = MVT-specific SQL (preferred for tiles)
- `{name}_mvt.json` = fallback MVT query file (separate file, same directory)
- `connectionId` and `sourceId` can be embedded in the query file → auto-resolved

## Connection & Database Resolution

**REQUIRED SKILL:** Use `fastapi-database-init` for understanding how connections are created and managed.

For rendering, the connection config is built from these sources:

1. **Connection document** — host, port, username, password, database_type
2. **Data source document** — attaches the specific `database` name to the connection
3. **Static query file** — provides `connectionId` and `sourceId` if not in the request DTO

```python
def resolve_connection(connection_id: str, source_ids: list[str]) -> dict:
    """Build connection config for query execution."""
    conn = get_connection(connection_id)  # → {host, port, username, password, database_type}

    # Attach database name from data source
    if source_ids:
        data_source = get_data_source(source_ids[0])
        conn["database"] = data_source.get("database")

    return conn
```

## Tile Engine — `HandlerMVT.run()` and `HandlerMVT.postgresql()`

This section shows the complete tile rendering service that `mv_handler` calls via `Services.handler_mvt().run(dto, gzip=True)`. It is composed of three layers:

```
handler_mvt().run(dto, gzip=True)         ← entry point (called by mv_handler)
  ├── .postgresql(dto)                    ← build query, resolve config, execute, cache
  │     ├── resolve static query + conn   ← Steps 1–2
  │     ├── ST_TileEnvelope substitution  ← Step 3
  │     ├── parse ST_AsMVTGeom            ← Step 4
  │     ├── build SQL filters             ← Step 5
  │     ├── filter geometry injection     ← Step 6
  │     ├── Redis cache check             ← Step 7
  │     └── _execute_query()              ← Step 8 (or cluster)
  ├── .parse_id_properties(output)        ← decode → assign UUID IDs → re-encode
  └── .compress_gzip(output)              ← gzip for transport
```

### `run()` — Entry Point

```python
class HandlerMVT:
    """Tile rendering engine. Instantiated via service factory: Services.handler_mvt()"""

    def run(self, dto, gzip: bool = True) -> bytes:
        """Main entry point called by mv_handler. Returns gzip-compressed MVT protobuf."""
        if dto.database_type != 'postgresql':
            raise ValueError(f'MVT rendering only supports postgresql, got: {dto.database_type}')

        # 1. Build query, resolve config, execute SQL, handle cache
        output = self.postgresql(dto)

        # 2. Ensure bytes (numpy array → bytes if needed)
        if not isinstance(output, bytes):
            output = output.tobytes()

        # 3. Decode MVT, assign UUID-based feature IDs, re-encode
        output = self.parse_id_properties(output)

        # 4. Compress for transport
        return self.compress_gzip(output) if gzip else output

    def run_and_extract(self, dto, gzip: bool = True) -> dict:
        """Decode variant — returns decoded dict instead of compressed bytes."""
        resp = self.run(dto, gzip)
        return self.decode_object_memory(resp)
```

### `postgresql()` — Full Query Build + Execute + Cache

This is the core method. Every step is shown in exact order as executed:

```python
    def postgresql(self, dto) -> bytes:
        # ═══════════════════════════════════════════════════════
        # STEP 1–2: Resolve static query + connection + data source
        # ═══════════════════════════════════════════════════════
        query_config = resolve_static_query(dto.queryId, query_dir=dto.queryDir)
        assert query_config, f'Query {dto.queryId} not found'

        # Prefer contentMaps for MVT, fallback to {name}_mvt query file
        query = query_config.get('contentMaps', None)
        if query is None:
            mvt_config = resolve_static_query(
                f"{query_config['name']}_mvt", query_dir=dto.queryDir
            )
            assert mvt_config, f'MVT variant for query {dto.queryId} not found'
            query = mvt_config.get('content')

        assert query, f"Query {dto.queryId} has no MVT content"

        # Auto-resolve connectionId + sourceId from query config if missing in DTO
        if query_config.get('connectionId') and query_config.get('sourceId'):
            dto.connectionId = dto.connectionId or query_config['connectionId']
            dto.sourceId = dto.sourceId or query_config['sourceId']

        # Lookup connection config
        conn_config = get_connection(dto.connectionId)
        assert conn_config, f'Connection {dto.connectionId} not found'

        # Attach database name from data source
        if dto.sourceId and len(dto.sourceId) > 0:
            data_source = get_data_source(dto.sourceId[0])
            conn_config['database'] = data_source.get('database')
            assert conn_config['database'], 'Database name cannot be empty'

        # ═══════════════════════════════════════════════════════
        # STEP 3: Substitute ST_TileEnvelope(z, x, y)
        # ═══════════════════════════════════════════════════════
        query = re.sub(
            r"ST_TileEnvelope\(\d+,\s*\d+,\s*\d+\)",
            f"ST_TileEnvelope({dto.bbox['z']}, {dto.bbox['x']}, {dto.bbox['y']})",
            query
        )

        # ═══════════════════════════════════════════════════════
        # STEP 4: Extract coordinate field from ST_AsMVTGeom(...)
        # ═══════════════════════════════════════════════════════
        # Clean SQL comments first
        clean_query = re.sub(r"--.*?$", "", query, flags=re.MULTILINE)
        clean_query = re.sub(r"/\*.*?\*/", "", clean_query, flags=re.DOTALL)

        # Find the ST_AsMVTGeom(...) expression
        match = re.search(
            r",\s*(ST_AsMVTGeom\(.*?\))\s*(?:AS geometry|AS \"geometry\"|$)",
            clean_query, re.IGNORECASE | re.DOTALL
        )
        if not match:
            raise Exception("Query must include ST_AsMVTGeom() function")

        coordinate_expr = match.group(1).strip()
        coordinate_expr = " ".join(
            item.strip() for item in coordinate_expr.splitlines() if item.strip()
        )

        # Extract just the geometry column name (first argument of ST_AsMVTGeom)
        geom_match = re.compile(r'ST_AsMVTGeom\((.*)\)', re.I).findall(coordinate_expr)
        col_match = re.compile(r'^(.*)\,', re.I).findall(geom_match[0])
        coordinate_field = str(col_match[0]).strip()

        # ═══════════════════════════════════════════════════════
        # STEP 5: Build SQL filters from DTO filters
        # ═══════════════════════════════════════════════════════
        filters = []
        pg_builder = PostgreSqlQueryBuilder(query='', connection_config=conn_config)

        if dto.filterChat:
            filters.extend(self._process_filter_chat(dto.filterChat, pg_builder))
        if dto.filters:
            filters.extend(dto.filters)

        query_filter_template, query_filter_values = query_builder_sql(filters)

        # Check if filter template uses {{COORDINATE_FIELD}} for distance filtering
        has_direction = '{{COORDINATE_FIELD}}' in query_filter_template
        if has_direction:
            # Inject ST_X/ST_Y alongside ST_AsMVTGeom in the SELECT
            query = re.sub(
                r'ST_AsMVTGeom',
                f'ST_X(ST_TRANSFORM({coordinate_field}, 4326)) as longitude, '
                f'ST_Y(ST_TRANSFORM({coordinate_field}, 4326)) as latitude, '
                f'ST_AsMVTGeom',
                query
            )

        # ═══════════════════════════════════════════════════════
        # STEP 5a: Inject WHERE clause into query
        # ═══════════════════════════════════════════════════════
        pg_builder = PostgreSqlQueryBuilder(query=query, connection_config=conn_config)

        if query_filter_template:
            # Replace {{COORDINATE_FIELD}} with actual coordinate field name
            query_filter_template = query_filter_template.replace(
                '{{COORDINATE_FIELD}}', coordinate_field
            )
            query = pg_builder.get_query_with_filter({
                "template": query_filter_template,
                "value": query_filter_values
            })

            # If distance filtering: inject ST_Distance + ORDER BY distance LIMIT 5
            if has_direction:
                # Extract the source coordinate from ST_Envelope(ST_Buffer(...))
                envelope_match = re.findall(
                    r'ST_Envelope\(ST_Buffer\((.*)\)\)', query
                )
                src_match = re.compile(r'^(.*)\,').findall(envelope_match[0])
                source_coordinate = src_match[0]

                # Inject distance column
                query = re.sub(
                    r'ST_AsMVTGeom',
                    f'ST_Distance({source_coordinate}, {coordinate_field}) as distance, '
                    f'ST_AsMVTGeom',
                    query
                )

                # Wrap datas subquery with ORDER BY distance LIMIT 5
                datas_match = re.findall(r'datas as \((.*)\)', query, re.S | re.I)
                datas_content = re.sub(
                    r'(\)[^)]*)(SELECT([^)]*)ST_AsMVT)(\()(.*)(\))',
                    '',
                    f'{datas_match[0]})'
                )
                query = query.replace(
                    datas_content,
                    f'\nSELECT * FROM ({datas_content})\nORDER BY distance LIMIT 5'
                )

        # ═══════════════════════════════════════════════════════
        # STEP 6: Inject filter geometry (if drawing tools used on map)
        # ═══════════════════════════════════════════════════════
        if dto.filterGeometry:
            query = self._inject_original_geom(query)
            query = self._build_filtered_mvt_query(query, dto.filterGeometry)

        # ═══════════════════════════════════════════════════════
        # STEP 7: Redis cache check
        # ═══════════════════════════════════════════════════════
        hash_id = hashlib.md5(
            f'{query}_{pg_builder.connection_key}_{dto.thresholdCluster}'.encode()
        ).hexdigest()
        cache_key = f'MVT:{hash_id}'

        cached = redis.get_history(cache_key)
        if cached and cached.get('composite'):
            features = cached['composite']['features']
            # Re-encode from cached decoded features
            return mapbox_vector_tile.encode({
                'features': features,
                'name': 'composite'
            })

        # ═══════════════════════════════════════════════════════
        # STEP 8: Execute query → raw protobuf bytes
        # ═══════════════════════════════════════════════════════
        result = self._execute_query(pg_builder, query, dto)

        # Cache decoded result (not compressed bytes)
        redis.insert_to_history(cache_key, mapbox_vector_tile.decode(result))

        return result
```

### Helper: `_execute_query()`

```python
    def _execute_query(self, pg_builder, query: str, dto) -> bytes:
        """Execute SQL and return raw protobuf bytes."""
        # Cluster mode: delegate to cluster engine (returns GeoJSON, not MVT)
        if dto.mapType == 'cluster':
            conn = pg_builder.check_connection()
            cluster = ClusterMaps(
                request=ClusterMapsRequest(
                    query=query,
                    connection=conn,
                    minimum_cluster=dto.thresholdCluster
                )
            )
            return cluster.execute()

        # Standard mode: execute raw SQL, extract bytea from first row, first column
        start = time.time()
        result = pg_builder.exec_own_query(query)
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f'MVT execution time: {elapsed_ms:.2f}ms')
        return list(result[0].values())[0]
```

### Helper: `parse_id_properties()`

```python
    def parse_id_properties(self, output: bytes) -> bytes:
        """Decode MVT → assign UUID-based feature IDs → re-encode."""
        decoded = mapbox_vector_tile.decode(output)
        composite = decoded.get('composite')
        if composite:
            for feature in composite['features']:
                # Unique 16-digit integer ID per feature
                feature['id'] = int(str(uuid4().int)[:16])
            return mapbox_vector_tile.encode({
                'features': composite['features'],
                'name': 'composite'
            })
        return output
```

### Helper: `_build_filtered_mvt_query()`

```python
    def _build_filtered_mvt_query(self, query: str, geometries: list[str]) -> str:
        """Wrap query with ST_Intersects filter as a CTE."""
        # Parse original query structure
        mvt_match = re.search(
            r"SELECT\s+ST_AsMVT\(\s*datas\.\*\s*,\s*([^)]+)\)\s+FROM\s+datas",
            query, re.IGNORECASE
        )
        if not mvt_match:
            raise ValueError("Cannot find 'SELECT ST_AsMVT(datas.*, ...)' in query")

        layer_name = mvt_match.group(1).strip()

        # Extract column aliases from the datas CTE
        datas_match = re.search(
            r"datas\s+AS\s+\(\s*SELECT\s+(.*?)\s+FROM\b",
            query, re.IGNORECASE | re.DOTALL
        )
        raw_columns = datas_match.group(1)
        alias_columns = []
        for col in raw_columns.split(","):
            alias_match = re.search(
                r'\bas\s+"?([a-zA-Z0-9_]+)"?\s*$', col.strip(), re.IGNORECASE
            )
            if alias_match and alias_match.group(1).lower() != "original_geom":
                alias_columns.append(alias_match.group(1))
        select_filtered = ",\n                ".join(alias_columns)

        # Build filtered CTE with ST_Intersects for each geometry
        subquery = f"""(
            SELECT {select_filtered}
            FROM datas
            WHERE 1=1
        )"""

        for geom in geometries:
            filter_clause = (
                f"ST_Intersects("
                f"original_geom, "
                f"ST_SetSRID(ST_GeomFromGeoJSON('{geom}'), 4326)"
                f")"
            )
            subquery = subquery.replace("WHERE 1=1", f"WHERE 1=1 OR {filter_clause}")
        subquery = subquery.replace("1=1 OR ", "")  # Remove placeholder

        # Replace original ST_AsMVT with filtered version
        replacement = (
            f", filtered AS {subquery} "
            f"SELECT ST_AsMVT(filtered.*, {layer_name}) FROM filtered"
        )
        return re.sub(mvt_match.re, replacement, query, flags=re.IGNORECASE)

    def _inject_original_geom(self, sql: str) -> str:
        """Ensure ST_AsMVTGeom contains an 'original_geom' alias for geometry filtering."""
        # If ST_AsMVTGeom uses ST_Transform(geom, 3857), add original_geom alias
        pattern = (
            r"ST_AsMVTGeom\s*\(\s*ST_Transform\s*\(\s*(.+?),\s*3857\s*\)"
            r"\s*,\s*bbox\.geom\s*\)"
        )
        match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
        if match:
            original_geom = match.group(1).strip()
            # Wrap the geometry column with an alias
            sql = re.sub(
                pattern,
                f"ST_AsMVTGeom(ST_Transform({original_geom} as original_geom, 3857), bbox.geom)",
                sql,
                flags=re.IGNORECASE | re.DOTALL
            )
        return sql
```

### Helper: `compress_gzip()` and `decode_object_memory()`

```python
    def compress_gzip(self, data: bytes) -> bytes:
        """Compress data using gzip."""
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
            f.write(data)
        return buffer.getvalue()

    def decode_object_memory(self, data: bytes) -> dict:
        """Decompress gzip then decode MVT → Python dict."""
        return mapbox_vector_tile.decode(gzip.decompress(data))
```

### Complete Call Chain from Router to Tile Engine

```
mv_handler(body, x, y, z)
  ├── Parse DTO from JSON header + tile coords
  ├── Resolve filter geometries from Redis
  └── Services.handler_mvt().run(dto, gzip=True)
        ├── .postgresql(dto)
        │     ├── resolve_static_query()           → query JSON file
        │     ├── get_connection()                  → connection config
        │     ├── get_data_source()                 → attach database name
        │     ├── ST_TileEnvelope subst             → regex replacement
        │     ├── extract ST_AsMVTGeom              → coordinate field
        │     ├── query_builder_sql(filters)        → SQL WHERE clause
        │     ├── get_query_with_filter()           → inject WHERE into query
        │     ├── [ST_Distance injection]           → if {{COORDINATE_FIELD}}
        │     ├── [CTE geometry filter wrap]        → if dto.filterGeometry
        │     ├── Redis cache check: MVT:{hash}     → return cached if hit
        │     └── _execute_query()                  → exec SQL → bytea column
        ├── .parse_id_properties(output)            → decode → assign IDs → encode
        └── .compress_gzip(output)                  → gzip for transport
```

> **Cache detail:** Redis stores **decoded** MVT dict (from `mapbox_vector_tile.decode()`), NOT compressed bytes. On cache hit, features are re-encoded with `mapbox_vector_tile.encode()`. This allows feature manipulation before encoding if needed.

## Router Placement — MVT Endpoints in Maps Router

**CRITICAL:** All MVT rendering endpoints MUST be placed in the **maps router** (`router/maps.py`), alongside map CRUD endpoints. Do NOT create a separate MVT router. The maps router is the single entry point for all map operations — CRUD, tile rendering, analytics, GeoJSON, and bounding box queries.

### Why the Maps Router?

1. **Shared service instance** — the `MapsService` instance (`obj = MapsService()`) is used by both CRUD endpoints and MVT endpoints. The MVT handler needs access to the maps service for `payload_mvt_coordinate()`, Redis connections, and geometry filter resolution.
2. **Single router tag** — all map endpoints share the same OpenAPI tag (`maps`), keeping the API docs organized.
3. **Consistent URL prefix** — tiles are served under the same `/maps/` prefix as the rest of the map API.

### Router File Structure

```
router/maps.py
├── Imports + service init
├── obj = MapsService()
├── tag = "maps"
├── router = APIRouter(**router_param_builder(tag))
│
├── # CRUD Endpoints
├── POST   /add          → obj.add(dto)
├── PUT    /update       → obj.update(dto)
├── DELETE /delete       → obj.delete(id)
├── POST   /get-all      → obj.get_all(dto)
├── GET    /get-one      → obj.get_by_id(id)
├── POST   /duplicate    → obj.duplicate(...)
│
├── # MVT & Geospatial Endpoints
├── GET    /mvt                  → mv_handler (tile rendering)
├── GET    /mvt-mobile           → mv_handler (mobile variant)
├── POST   /get_mvt_coordinate   → coordinate extraction
├── GET    /min_max              → bounding box bounds
├── GET    /geojson              → GeoJSON features in bbox
├── POST   /analytic             → map data analytics
├── POST   /analyticFromCoordinate → analytics from lat/lon
│
├── # Utility
├── POST   /set-filter-geometry  → save drawn polygon to Redis
│
└── def mv_handler(body, x, y, z):  ← module-level sync function
```

### MVT Tile Endpoint — `GET /mvt`

The MVT endpoint is a `GET` request because tile coordinates (`z/x/y`) are URL path parameters. The filter DTO is passed via a **Header** (`body`), not a request body, because `GET` requests conventionally don't have bodies:

```python
# router/maps.py
import asyncio
import json
import traceback
from fastapi import Header, Query, Response
from fastapi import APIRouter, HTTPException

@router.get('/mvt')
async def mvt(
    body: str = Header(None),   # ← filter DTO as JSON string in header
    x: int = 206,               # ← tile x from URL query param
    y: int = 128,               # ← tile y from URL query param
    z: int = 8,                 # ← zoom level from URL query param
):
    if body is None:
        raise HTTPException(status_code=400, detail="No body found in header")

    # Offload synchronous MVT rendering to a thread
    return await asyncio.to_thread(mv_handler, body, x, y, z)
```

### Mobile MVT Variant — `GET /mvt-mobile`

Same as `/mvt` but accepts `body` as a query parameter (not header) for mobile clients that cannot set custom headers:

```python
@router.get('/mvt-mobile')
async def mvt_mobile(
    body: str = None,
    x: int = 206,
    y: int = 128,
    z: int = 8,
    token: str = Query(default=None),
):
    if body is None:
        raise HTTPException(status_code=400, detail="No body found in parameter")
    return await asyncio.to_thread(mv_handler, body, x, y, z)
```

### The `mv_handler` Function — Module-Level Sync Function

Defined at the bottom of `router/maps.py` as a regular (non-async) function. This is the single entry point for all MVT rendering logic:

```python
# router/maps.py — module-level (outside any class or route handler)

def mv_handler(body: str, x: int = 206, y: int = 128, z: int = 8):
    """Synchronous MVT tile renderer — called via asyncio.to_thread()."""
    try:
        # 1. Parse DTO from JSON header + tile coordinates
        dto = HandlerMVTDTO_V2(
            **json.loads(body),
            bbox={'x': x, 'y': y, 'z': z}
        )

        # 2. Resolve filter geometries from Redis cache
        if dto.filterGeometryId:
            if isinstance(dto.filterGeometryId, str):
                dto.filterGeometryId = [dto.filterGeometryId]

            list_of_geometry = []
            for geom_id in dto.filterGeometryId:
                redis_key = f"geometry:filter:{geom_id}"
                geom_json = obj.redis.get(redis_key)   # ← uses map service's Redis
                if geom_json:
                    list_of_geometry.append(geom_json)
            dto.filterGeometry = list_of_geometry

        # 3. Execute tile rendering → gzip-compressed protobuf bytes
        content = Services.handler_mvt().run(dto, gzip=True)

        # 4. Return protobuf response with gzip encoding header
        return Response(
            content=content,
            headers={'Content-Encoding': 'gzip'},
            media_type="application/x-protobuf"
        )
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(error))
```

**Key details:**

- `body` is a **JSON string** passed via an HTTP header, not a request body
- `dto.bbox` is constructed from the `x`, `y`, `z` URL parameters
- `obj.redis` — the `mv_handler` accesses the maps service instance's Redis connection directly (same `obj` used by CRUD endpoints)
- `Services.handler_mvt().run()` — the tile engine is obtained from a service factory, not instantiated inline
- The function is **synchronous** — `asyncio.to_thread()` offloads it from the async event loop
- Geometry filters are resolved from Redis with key format `geometry:filter:{id}`

### Coordinate Extraction Endpoint — `POST /get_mvt_coordinate`

Resolves MVT parameters from a URL and returns the first 10 feature coordinates:

```python
@router.post('/get_mvt_coordinate')
async def get_mvt_coordinate(dto: MVTCoordinateDTO):
    start_time = time()
    try:
        # Walk URL → Menu → Widget → Map → Layer to extract MVT params
        body = obj.payload_mvt_coordinate(dto)
        mvt_dto = HandlerMVTDTO_V2(**body, bbox={'x': 0, 'y': 0, 'z': 0})

        # Execute MVT rendering and extract coordinates
        hm_service = Services.handler_mvt()
        data = hm_service.run_and_extract(mvt_dto)

        # Return first 10 coordinate pairs
        coords = jmespath.search("composite.features[:10].geometry.coordinates", data) or []
        data = [{"x": c[0], "y": c[1]} for c in coords]
        return BaseResponse(data=data, metaData=MetadataSuccess(executionTime=get_execution_time(start_time)))
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=BaseResponseFailed(...).dict())
```

### Bounding Box Endpoints — `GET /min_max` and `GET /geojson`

Both receive the filter DTO as a **Header** and bounding box coordinates as query parameters:

```python
@router.get('/min_max')
async def min_max(
    body: str = Header(None),
    toplon: float = 109.156380,
    toplat: float = -0.176811,
    botlon: float = 109.705696,
    botlat: float = 0.105057,
):
    dto = HandlerMVTDTO_V2(
        **json.loads(body),
        bbox={'toplon': toplon, 'toplat': toplat, 'botlon': botlon, 'botlat': botlat}
    )
    content = Services.handler_geospatial().run(dto)
    return BaseResponse(data=content, ...)


@router.get('/geojson')
async def geojson(
    body: str = Header(None),
    toplon: float = 109.156380,
    toplat: float = -0.176811,
    botlon: float = 109.705696,
    botlat: float = 0.105057,
):
    body = json.loads(body)
    if body.get('database_type') != 'postgresql':
        raise HTTPException(status_code=400, detail='Database type must be postgresql')

    dto = HandlerMVTDTO_V2(
        **body,
        bbox={'toplon': toplon, 'toplat': toplat, 'botlon': botlon, 'botlat': botlat}
    )
    raw = Services.handler_geospatial().exec_bounding_box_query(dto)
    body['chartType'] = body.get('chart', '')
    content = {'geojson': mapParser(data=raw, **body).get('geojson')}
    return BaseResponse(data=content, ...)
```

> The `geojson` endpoint validates `database_type == "postgresql"` — GeoJSON rendering currently only supports PostgreSQL/PostGIS.

### Analytics Endpoints — `POST /analytic` and `POST /analyticFromCoordinate`

Standard POST endpoints that accept DTOs as request bodies:

```python
@router.post('/analytic')
async def get_analytic(dto: MVTAnalyticDTO):
    data, count, queries = obj.mvt_analytic(dto)
    return BaseResponse(
        data=data,
        metaData=MetadataSuccess(
            pagination=Pagination.count_total_pages(
                dto.size if dto.size is not None else 1, count
            ),
            executionTime=get_execution_time(start_time),
            message=queries
        )
    )


@router.post('/analyticFromCoordinate')
async def get_analytic_from_coordinate(dto: MVTAnalyticFromCoordinateDTO):
    # Exclude geometry column from results
    if dto.excludeFields is None:
        dto.excludeFields = []
    dto.excludeFields.append('geometry')
    data, count, queries = obj.mvt_analytic(dto)
    return BaseResponse(data=data, ...)
```

### Summary: All MVT Endpoints in Maps Router

| Method | Path                      | DTO Source                         | Handler                                                   |
| ------ | ------------------------- | ---------------------------------- | --------------------------------------------------------- |
| GET    | `/mvt`                    | Header `body` + query `x,y,z`      | `mv_handler` (sync, via thread)                           |
| GET    | `/mvt-mobile`             | Query param `body` + query `x,y,z` | `mv_handler` (sync, via thread)                           |
| POST   | `/get_mvt_coordinate`     | Request body                       | `obj.payload_mvt_coordinate()` + tile engine              |
| GET    | `/min_max`                | Header `body` + query `toplon,...` | `Services.handler_geospatial().run()`                     |
| GET    | `/geojson`                | Header `body` + query `toplon,...` | `Services.handler_geospatial().exec_bounding_box_query()` |
| POST   | `/analytic`               | Request body                       | `obj.mvt_analytic()`                                      |
| POST   | `/analyticFromCoordinate` | Request body                       | `obj.mvt_analytic()`                                      |
| POST   | `/set-filter-geometry`    | Request body                       | `obj.save_filter_geometry()`                              |

### Geometry Filter Cache Convention

- Redis key format: `geometry:filter:{id}`
- Stored as JSON string (GeoJSON geometry)
- TTL: 24 hours
- Saved by `/set-filter-geometry` endpoint when users draw filter polygons
- Resolved by `mv_handler` before executing tile rendering

## Map Analytics Pipeline

For non-tile map queries (data tables, charts from map selections):

```
1. Resolve static query           → get query content from JSON file
2. Resolve connection + source    → auto-resolve if missing from DTO
3. Strip existing LIMIT            → remove from base query (will re-add)
4. Build WHERE clause:
   - If id filter:                → field_id = ANY(%(_filter_ids)s)
   - If lon/lat filter:           → st_intersects(geometry, POINT(lon, lat))
5. Merge with DTO filters         → query_builder_sql()
6. Inject WHERE into query        → at last WHERE position or append
7. Append ORDER BY + LIMIT/OFFSET → pagination
8. Redis cache check              → fusion_mvt_analytic:{queryId}:{md5(dto + query)}
9. Execute via database driver    → parameterized query execution
10. On syntax error               → LLM fallback for query repair
11. Handle date mapping           → apply timezone offset to date fields
12. Cache result                  → Redis write-through
```

### Redis Cache Key for Analytics

```python
cache_key = f"fusion_mvt_analytic:{query_name}:{md5(json.dumps(dto) + query)}"
```

### LLM Fallback Pattern

When the database driver reports a syntax error, attempt AI-powered query repair:

```python
try:
    cursor.execute(query, values)
except Exception as e:
    if "syntax error" in str(e).lower():
        connection.rollback()
        # Use LLM to repair the query
        repaired = llm_repair_query(query_filter=query_filter)
        query = repaired["query"]
        cursor.execute(query, repaired.get("value", {}))
    else:
        raise
```

### Date Mapping

Apply timezone offsets to date columns in the result set:

```python
if dto.dateMapping:
    date_fields = dto.dateMapping.get("fields", [])
    timezone = dto.dateMapping.get("timeZone", "Asia/Jakarta")
    for row in result:
        for key, value in row.items():
            if key in date_fields and value:
                row[key] = apply_timezone_offset(str(value), timezone)
```

## Coordinate Extraction — URL → MVT Params

The reverse-resolution chain walks references from a URL to extract MVT rendering parameters:

```
URL path
  → Menu document        (find by path)
    → Widget document     (find by menuId + type="mapPlugin")
      → Map document      (find by widget.referenceId)
        → Layer document  (find by mapsId + layer name)
          → MVT params    (extract from layer.metaData.params)
```

### Step-by-Step Resolution

```python
def resolve_mvt_params(url: str, layer_name: str) -> dict:
    # 1. Find menu by URL path
    menu = find_menu({"path": urlparse(url).path})

    # 2. Find widget of type "mapPlugin" under that menu
    widget = find_widget({"menuId": menu["_id"], "type": "mapPlugin"})

    # 3. Find the map referenced by the widget
    map_doc = find_map({"_id": widget["referenceId"]})

    # 4. Find the specific layer by name (within the map)
    layer = find_layer({
        "mapsId": map_doc["_id"],
        "config.label": layer_name
    })

    # 5. Merge filters from layer config + map filterConfig
    filters = extract_enabled_filters(layer)  # from config.filter
    map_filters = map_doc.get("mapStyle", {}).get("filterConfig", {})

    # Merge: each enabled filter inherits map-level filterConfig values
    filters = [merge_filter_config(f, map_filters) for f in filters]

    # Handle relative date ranges
    for f in filters:
        if f.get("enableRelativeType"):
            f["value"]["gte"], f["value"]["lte"] = get_relative_range(
                f.get("relativeType", 7)  # default: last 7 days
            )

    # 6. Extract MVT params from layer metadata
    payload = layer.get("metaData", {}).get("params", {})
    payload = {
        k: v for k, v in payload.items()
        if k in ["connectionId", "queryId", "database_type", "sourceId"]
    }
    payload["lookup_fields"] = []
    payload["filters"] = filters
    return payload
```

### Filter Extraction Pattern

Only enabled filters are included. The `fieldType` from the filter key becomes the filter's type:

```python
def extract_enabled_filters(layer: dict) -> list:
    raw_filters = layer.get("config", {}).get("filter", {})
    return [
        {"fieldType": key, **value}
        for key, value in raw_filters.items()
        if isinstance(value, dict) and value.get("enable") == True
    ]
```

## GeoJSON / Bounding Box Queries

For endpoints that return GeoJSON features or min/max bounds within a bounding box:

```python
def build_bounding_box_query(dto) -> str:
    query = resolve_static_query(dto.queryId)
    bbox_wkt = (
        f"ST_MakeEnvelope("
        f"{dto.bbox.toplon}, {dto.bbox.toplat}, "
        f"{dto.bbox.botlon}, {dto.bbox.botlat}, "
        f"4326)"
    )
    # Inject ST_Intersects WHERE clause
    where_clause = f"ST_Intersects(geometry_column, {bbox_wkt})"
    return inject_where(query, where_clause)
```

## MVT Cluster Mode

For map types that require clustering, the rendering delegates to a cluster engine that:

1. Accepts the same DTO as standard MVT rendering
2. Returns clustered GeoJSON features instead of MVT protobuf
3. Uses the same connection/query/filter resolution pipeline

The cluster vs. tile mode is selected by `dto.mapType`:

- `mapType == "cluster"` → cluster engine
- Default → standard MVT rendering

## Key Dependencies

| Library                            | Purpose                                                                |
| ---------------------------------- | ---------------------------------------------------------------------- |
| `mapbox_vector_tile`               | Encode/decode MVT protobuf format                                      |
| `gzip`                             | Compress MVT response (required for transport)                         |
| Database driver (e.g., `psycopg2`) | Execute SQL queries returning bytea                                    |
| `hashlib`                          | Build deterministic cache keys                                         |
| `jmespath`                         | Extract values from nested dicts (query resolution, filter extraction) |
| `re`                               | Pattern substitution (ST_TileEnvelope, ST_AsMVTGeom)                   |

## Common Mistakes

| Mistake                                                     | Fix                                                              |
| ----------------------------------------------------------- | ---------------------------------------------------------------- |
| Using `content` instead of `contentMaps` for tile rendering | Always check `contentMaps` first, fallback to `{name}_mvt.json`  |
| Forgetting to substitute `ST_TileEnvelope`                  | Must replace with actual `z, x, y` from tile request             |
| Skipping feature ID assignment                              | MVT features must have unique IDs — use UUID-based integers      |
| Not decompressing before decode                             | `mapbox_vector_tile.decode()` needs raw bytes, not gzip          |
| Caching compressed bytes instead of decoded dict            | Cache decoded dict; re-encode on retrieval                       |
| Wrong Redis key format for geometry filter                  | Must be `geometry:filter:{id}` with 24h TTL                      |
| Only supporting PostgreSQL                                  | MVT rendering currently only supports PostgreSQL/PostGIS         |
| Not handling syntax error retry                             | Catch and rollback on syntax errors; optionally use LLM fallback |
