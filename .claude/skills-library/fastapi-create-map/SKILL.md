---
name: fastapi-create-map
description: Use when writing code that creates maps, layers, or map-plugin widgets — replicating the same logic as the existing Maps, MapsLayer, and Widget service classes including ID generation, MongoDB upsert patterns, Geoserver integration, and widget reference resolution
---

# fastapi-create-map — Map, Layer & Widget Creation Logic

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
| `update_one(..., upsert=True)` add-or-update | `repo.update(id, changes)` returns `None` when missing → then `repo.insert({...})`; repositories never upsert. Timestamps are set by the repository (`created_at`, `updated_at`, aware UTC) |
| camelCase storage keys (`createdAt`, `dashboardId`) | snake_case storage fields (`created_at`, `dashboard_id`); camelCase only in DTO JSON (`BaseSchema`) |
| Geoserver REST calls | not in the boilerplate — add settings + a sync `httpx.Client` helper under `util/`; raise `ConfigurationError` when unconfigured |

## Overview

This skill documents the patterns for creating maps, layers, and map-plugin widgets. It covers ID generation strategies, MongoDB upsert patterns, the document lifecycle (`createdAt`/`updatedAt`), Geoserver integration for raster layers, and widget reference wiring.

**Core principle:** Maps, Layers, and Widgets share a common `add_or_update_process()` upsert pattern but differ in ID generation strategy. Widgets use content-based IDs for idempotency; Maps and Layers use timestamp-based IDs. All three store in MongoDB; widgets additionally support Redis storage.

## Architecture

```
Map Creation                    Layer Creation                  Widget Creation (mongo target)
     │                              │                                │
     ├─ _id = md5(timestamp)        ├─ _id = md5(timestamp)         ├─ _id = md5(json.dumps(dto))
     ├─ data["createdAt"] = now     ├─ data["createdAt"] = now      ├─ data["createdAt"] = now (str)
     ├─ upsert()                    ├─ [Geoserver if enabled]       ├─ upsert()
     │   ├─ strip "id"              │   └─ upsert()                 │   ├─ parse date strings
     │   ├─ data["updatedAt"]=now   │                                │   ├─ strip "id"
     │   ├─ update_one(upsert=True) │                                │   ├─ data["updatedAt"]=now
     │   └─ data["id"] = _id        │                                │   ├─ update_one(upsert=True)
     └─ return data                 └─ return data                   │   └─ data["id"] = _id
                                                                     └─ return data
```

## Reference Documents

This skill has detailed reference documents covering specific patterns:

- **[upsert-and-lifecycle.md](references/upsert-and-lifecycle.md)** — `add_or_update_process()` pattern, ID generation strategies, createdAt/updatedAt lifecycle, view conventions, dual Redis/MongoDB storage
- **[duplicate-flow.md](references/duplicate-flow.md)** — full map duplication chain (map → layers → widgets → queries), batch processing, query dedup
- **[reference-resolution.md](references/reference-resolution.md)** — widget→map reference resolution, `get_widget_references()`, URL→MVT reverse chain, object relationship graph

## Step 1: Create Map

### ID Generation

Maps use timestamp-based MD5 hashing:

```python
from hashlib import md5

_id = md5(str(datetime.now().timestamp()).encode()).hexdigest()
```

This is **non-deterministic** — calling twice at different timestamps produces different IDs.

### Document Assembly

```python
data = dto.dict()                # Pydantic DTO → dict
data["createdAt"] = datetime.now()  # Set creation time
```

### MongoDB Upsert

Maps use the standard `add_or_update_process()` documented in [upsert-and-lifecycle.md](references/upsert-and-lifecycle.md):

```python
def add_or_update_process(self, data: dict, _id: str) -> dict:
    if "id" in data:
        data.pop("id")                              # Strip client-side id
    data["updatedAt"] = datetime.now()
    self.collection.update_one(
        {'_id': _id}, {"$set": data}, upsert=True
    )
    data["id"] = _id                                 # Return id (not _id) to caller
    return data
```

Complete map creation:

```python
def create_map(self, dto) -> dict:
    _id = md5(str(datetime.now().timestamp()).encode()).hexdigest()
    data = dto.dict()
    data["createdAt"] = datetime.now()
    return self.add_or_update_process(data, _id)
```

### Reading Maps — View Convention

Reads go through **view collections** for joined/denormalized data:

```python
def get_map(self, map_id: str, with_layers: bool = False) -> dict:
    col = self.collection_view
    if with_layers:
        col = self.collection_view_with_layers  # e.g., v_maps_with_detail_layers

    data = col.find_one({"_id": map_id})
    if data:
        data["id"] = data.pop("_id")    # Normalize for API response

        # Resolve creator user
        if data.get("createdBy"):
            users = list(self.user_collection.find({"_id": data["createdBy"]}))
            if users:
                data["creator"] = map_users(users)
        return data
    return {}
```

### Collections Used

| Purpose | Config Key Convention |
|---------|----------------------|
| Map documents | `MONGO_COLLECTION_MAPS` |
| Map view (with joins) | `v_{MONGO_COLLECTION_MAPS}` |
| Map view (with layer details) | `v_maps_with_detail_layers` |
| Layer documents | `MONGO_COLLECTION_MAPS_LAYER` |
| Widget documents | `MONGO_COLLECTION_WIDGET` |
| Menu documents | `MONGO_COLLECTION_MENU` |
| Connection configs | `MONGO_COLLECTION_CONNECTION` |
| Data sources | `MONGO_COLLECTION_DATA_SOURCE` |
| User documents | `MONGO_COLLECTION_USER` |

**REQUIRED SKILL:** For database connection initialization, use `fastapi-database-init`. For the MongoDB service layer pattern, use `fastapi-data`.

### MongoDB Access Pattern

All services access MongoDB through a service factory:

```python
from service import Services  # legacy foundation — see "Adapting to the current foundation"

class MapsService:
    def __init__(self):
        self.mongo = Services.mongo()             # Singleton MongoClient
        self.mongo_db = self.mongo[settings.MONGO_DB]
        self.collection = self.mongo_db[settings.MONGO_COLLECTION_MAPS]
        self.collection_view = self.mongo_db[f"v_{settings.MONGO_COLLECTION_MAPS}"]
```

## Step 2: Create Layer

### ID Generation

Layers use the same timestamp-based MD5 as Maps:

```python
if hasattr(dto, "id") and dto.id:   # Update path — use existing ID
    _id = dto.id
else:                                # Create path — generate new ID
    _id = md5(str(datetime.now().timestamp()).encode()).hexdigest()
```

### Geoserver Integration (Conditional)

Only triggered when the layer's geoserver config has `enable == True`:

```python
geoserver_config = dto.config.get("geoserverConfig", {})
if geoserver_config.get("enable"):
    layer_type = geoserver_config.get("type")

    if layer_type == "raster":
        # 1. Resolve connection from metaData.params.connectionId
        conn = get_connection(dto.metaData.params.connectionId)

        # 2. Resolve data source from metaData.params.sourceId
        datasource = get_data_source(dto.metaData.params.sourceId[0])

        # 3. Build unique store name
        store_name = f"{conn['_id']}_{datasource['_id']}_{conn['name']}"

        # 4. Ensure GeoServer datastore exists (create if not)
        if not geoserver.datastore_exists(store_name):
            geoserver.create_datastore(store_name, conn)

        # 5. Ensure GeoServer layer exists (create if not)
        layer_name = f"{datasource['name']}"
        if not geoserver.layer_exists(layer_name):
            geoserver.create_layer(layer_name, store_name)

        # 6. Store geoserver metadata in layer config
        dto.config["geoserverConfig"] = {
            "group": geoserver_config.get("group"),
            "workspace": geoserver_config.get("workspace"),
            "layer": layer_name,
            "style": geoserver_config.get("style", ""),
            "data_store": store_name,
            "srid": 4326,
        }

# Proceed with standard upsert
data = dto.dict()
data["createdAt"] = datetime.now()
data["mapsId"] = maps_id
return self.add_or_update_process(data, _id)
```

For non-raster types or disabled geoserver, the geoserver block is skipped entirely.

### Collections Used

| Purpose | Config Key Convention |
|---------|----------------------|
| Layer documents | `MONGO_COLLECTION_MAPS_LAYER` |
| Layer view | `v_{MONGO_COLLECTION_MAPS_LAYER}` |
| Dashboard documents | `MONGO_COLLECTION_DASHBOARD` |

## Step 3: Add Widget Map Plugin (MongoDB Target)

### ID Generation (Different from Maps!)

Widgets use **content-based ID** — MD5 of the entire serialized payload:

```python
dto_as_dict = dto.dict()
dto_as_dict["createdAt"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
_id = md5(json.dumps(dto_as_dict).encode()).hexdigest()
```

> **Critical difference:** Widget ID is the MD5 hash of the **entire serialized JSON payload** (including `createdAt` string), not a timestamp. This makes widget creation **idempotent** — identical payloads at the same second produce the same ID. Different timestamps produce different IDs.

### MongoDB Upsert (with Date Parsing)

Widgets have a dual-target upsert (Redis or MongoDB). For map plugins, always use MongoDB:

```python
def add_or_update_process(self, data: dict, _id: str, target: str = "redis") -> dict:
    if target == "mongo":
        if "id" in data:
            data.pop("id")
        updated_time = datetime.now()
        data = parse_date_strings(data, default_time=updated_time)
        data["updatedAt"] = updated_time
        self.collection.update_one({'_id': _id}, {"$set": data}, upsert=True)
        data["id"] = _id
    # target="redis" path writes to Redis instead (used for non-map widgets)
    return data
```

### Widget Map Plugin — Identity Fields

```json
{
    "type": "mapPlugin",
    "referenceType": "maps",
    "referenceId": "<map_id>"
}
```

### Widget Reference Resolution

When fetching widgets, references are resolved at read time. See [reference-resolution.md](references/reference-resolution.md) for the full pattern.

### Collections Used

| Purpose | Config Key Convention |
|---------|----------------------|
| Widget documents | `MONGO_COLLECTION_WIDGET` |
| Widget view | `v_{MONGO_COLLECTION_WIDGET}` |
| Menu documents | `MONGO_COLLECTION_MENU` |
| Dashboard documents | `MONGO_COLLECTION_DASHBOARD` |

## Router & Service Separation

**CRITICAL:** Maps and Layers must be implemented as **separate services in separate files**, each with its own router:

```
router/maps.py          → MapsService (in service/maps.py)
router/maps_layer.py    → MapsLayerService (in service/maps_layer.py)
```

This separation ensures:
- Each service owns only its own MongoDB collections
- Each router has its own URL prefix and tag
- The Maps service can reference layer logic without coupling the routers
- Layer CRUD operations (`add`, `update`, `delete`, `get-all`, `paste`, `duplicate`, `update-connection`) live independently from map operations

## Canonical Code: MapsService

```python
# service/maps.py
from datetime import datetime
from hashlib import md5
from service import Services, BaseMongoRepository  # legacy foundation — see "Adapting to the current foundation"

class MapsService(BaseMongoRepository):
    """Map CRUD + lifecycle + duplicate + MVT analytic + geometry filter."""

    def __init__(self):
        super().__init__()
        self.mongo = Services.mongo()
        self.redis = Services.redis()
        self.mongo_db = self.mongo[settings.MONGO_DB]
        self.collection = self.mongo_db[settings.MONGO_COLLECTION_MAPS]
        self.collection_view = self.mongo_db[f"v_{settings.MONGO_COLLECTION_MAPS}"]
        self.collection_view_with_layers = self.mongo_db["v_maps_with_detail_layers"]
        self.collection_layer = self.mongo_db[settings.MONGO_COLLECTION_MAPS_LAYER]
        self.collection_widget = self.mongo_db[settings.MONGO_COLLECTION_WIDGET]
        self.collection_menu = self.mongo_db[settings.MONGO_COLLECTION_MENU]
        self.collection_connection = self.mongo_db[settings.MONGO_COLLECTION_CONNECTION]
        self.collection_source = self.mongo_db[settings.MONGO_COLLECTION_DATA_SOURCE]

    # ── Upsert pattern ──
    def add_or_update_process(self, data: dict, _id: str) -> dict:
        if "id" in data:
            data.pop("id")
        data["updatedAt"] = datetime.now()
        self.collection.update_one({'_id': _id}, {"$set": data}, upsert=True)
        data["id"] = _id
        return data

    # ── Create ──
    def add(self, dto) -> dict:
        _id = md5(str(datetime.now().timestamp()).encode()).hexdigest()
        data = dto.dict()
        data["createdAt"] = datetime.now()
        return self.add_or_update_process(data, _id)

    # ── Update ──
    def update(self, dto) -> dict:
        existing = self.collection.find_one({"_id": dto.id})
        if not existing:
            raise ValueError(f"Map '{dto.id}' not found")
        merged = {**existing, **dto.dict()}
        merged["createdAt"] = existing["createdAt"]  # preserve
        return self.add_or_update_process(merged, dto.id)

    # ── Read ──
    def get_by_id(self, _id: str, with_layers: bool = False) -> dict:
        col = self.collection_view if not with_layers else self.collection_view_with_layers
        data = col.find_one({"_id": _id})
        if data:
            data["id"] = data.pop("_id")
            if data.get("createdBy"):
                users = list(self.mongo_db[settings.MONGO_COLLECTION_USER].find(
                    {"_id": data["createdBy"]}))
                if users:
                    data["creator"] = map_users(list(users))
            return data
        return {}

    # ── List ──
    def get_all(self, dto) -> tuple[list, int]:
        query = mongo_query_builder(dto, text_type="name,description")
        data = list(
            self.collection_view.find(query)
            .skip((dto.page - 1) * dto.size)
            .limit(dto.size)
            .sort(dto.orderBy, -1 if dto.order.lower() == "desc" else 1)
        )
        for datum in data:
            datum["id"] = datum.pop("_id")
        return data, self.collection_view.count_documents(query)

    # ── Delete ──
    def delete(self, _id: str) -> str:
        self.collection.delete_one({"_id": _id})
        return f"Map '{_id}' has been deleted."

    # ── Duplicate (see references/duplicate-flow.md) ──
    def duplicate(self, map_id: str, created_by: str, dashboard_id: str = None,
                  name: str = None, duplicate_query: bool = False) -> dict:
        # Full logic in references/duplicate-flow.md
        ...
```

## Canonical Code: MapsLayerService

```python
# service/maps_layer.py
from datetime import datetime
from hashlib import md5
from service import Services, BaseMongoRepository  # legacy foundation — see "Adapting to the current foundation"

class MapsLayerService(BaseMongoRepository):
    """Layer CRUD + Geoserver integration + paste/duplicate + multi-connection update."""

    def __init__(self):
        super().__init__()
        self.mongo = Services.mongo()
        self.mongo_db = self.mongo[settings.MONGO_DB]
        self.collection = self.mongo_db[settings.MONGO_COLLECTION_MAPS_LAYER]
        self.collection_view = self.mongo_db[f"v_{settings.MONGO_COLLECTION_MAPS_LAYER}"]
        self.collection_connection = self.mongo_db[settings.MONGO_COLLECTION_CONNECTION]
        self.collection_source = self.mongo_db[settings.MONGO_COLLECTION_DATA_SOURCE]
        self.collection_dashboard = self.mongo_db[settings.MONGO_COLLECTION_DASHBOARD]

    # ── Upsert pattern ──
    def add_or_update_process(self, data: dict, _id: str) -> dict:
        if "id" in data:
            data.pop("id")
        data["updatedAt"] = datetime.now()
        self.collection.update_one({'_id': _id}, {"$set": data}, upsert=True)
        data["id"] = _id
        return data

    # ── Create ──
    def add(self, dto) -> dict:
        # For V2 update path: reuse existing ID if provided
        if hasattr(dto, "id") and dto.id:
            _id = dto.id
        else:
            _id = md5(str(datetime.now().timestamp()).encode()).hexdigest()

        data = dto.dict()
        data["createdAt"] = datetime.now()

        # Optional: Geoserver integration
        geoserver_config = data.get("config", {}).get("geoserverConfig", {})
        if geoserver_config.get("enable") and geoserver_config.get("type") == "raster":
            data["config"]["geoserverConfig"] = self._setup_geoserver(data, geoserver_config)

        return self.add_or_update_process(data, _id)

    def _setup_geoserver(self, data: dict, geoserver_config: dict) -> dict:
        """Set up GeoServer datastore + layer for raster layers."""
        conn = self.collection_connection.find_one({
            "_id": data["metaData"]["params"]["connectionId"]
        })
        datasource = self.collection_source.find_one({
            "_id": data["metaData"]["params"]["sourceId"][0]
        })
        store_name = f"{conn['_id']}_{datasource['_id']}_{conn['name']}"
        layer_name = datasource['name']

        # Create datastore if missing
        if not geoserver.datastore_exists(store_name):
            geoserver.create_datastore(store_name, conn)

        # Create layer if missing
        if not geoserver.layer_exists(layer_name):
            geoserver.create_layer(layer_name, store_name)

        return {
            "group": geoserver_config.get("group"),
            "workspace": geoserver_config.get("workspace"),
            "layer": layer_name,
            "style": geoserver_config.get("style", ""),
            "data_store": store_name,
            "srid": 4326,
        }

    # ── Update ──
    def update(self, dto) -> dict:
        existing = self.collection.find_one({"_id": dto.id})
        if not existing:
            raise ValueError(f"Layer '{dto.id}' not found")
        merged = {**existing, **dto.dict()}
        merged["createdAt"] = existing["createdAt"]
        return self.add_or_update_process(merged, dto.id)

    # ── Read ──
    def get_by_id(self, _id: str) -> dict:
        data = self.collection_view.find_one({"_id": _id})
        if data:
            data["id"] = data.pop("_id")
            return data
        return {}

    # ── List ──
    def get_all(self, dto) -> tuple[list, int]:
        query = mongo_query_builder(dto, text_type="name")
        data = list(
            self.collection_view.find(query)
            .skip((dto.page - 1) * dto.size)
            .limit(dto.size)
            .sort(dto.orderBy, -1 if dto.order.lower() == "desc" else 1)
        )
        for datum in data:
            datum["id"] = datum.pop("_id")
        return data, self.collection_view.count_documents(query)

    # ── Delete ──
    def delete(self, _id: str) -> str:
        self.collection.delete_one({"_id": _id})
        return f"Layer '{_id}' has been deleted."

    # ── Paste layers (across maps) ──
    def paste_layers(self, dto) -> list:
        ...

    # ── Duplicate layers ──
    def duplicate_layers(self, dto) -> list:
        ...

    # ── Batch update connection ──
    def update_connection(self, dto) -> list:
        ...
```

## Key Differences Between Services

| Aspect | Maps | MapsLayer | Widget (mongo) |
|--------|------|-----------|----------------|
| ID generation | `md5(timestamp)` | `md5(timestamp)` | `md5(json.dumps(full_payload))` |
| Deterministic ID? | No | No | Yes (per payload+timestamp) |
| createdAt type | `datetime` object | `datetime` object | `datetime` object |
| createdAt in ID hash | No | No | Yes (string format in payload copy) |
| Upsert target | MongoDB only | MongoDB only | MongoDB or Redis (dual) |
| Date parsing on upsert | No | No | Yes (`parse_date_strings`) |
| External integration | None | Geoserver (raster) | None |
| Reference storage | N/A | N/A | `referenceType` + `referenceId` |

## Static Query Files (for Layer metaData)

Layers reference queries via `metaData.params.queryId`. With static query files (replacing the query catalog), ensure:

1. The query JSON file exists at `<query_dir>/<query_name>.json`
2. The query file contains at minimum: `connectionId`, `sourceId`, and the SQL `content`
3. The `queryId` stored in layer metadata should match the query file name (without `.json`)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using Map/MapLayer ID generation pattern for Widgets | Widgets use content-based `md5(json.dumps(payload))` — not `md5(timestamp)` |
| Using Redis instead of MongoDB for map widgets | Map widgets must persist in MongoDB (`target="mongo"`) |
| Forgetting to set `createdAt` before upsert | Always set explicitly before calling `add_or_update_process` |
| Overwriting `createdAt` on update | Fetch existing doc first, merge, preserve original `createdAt` |
| Not stripping `"id"` field before upsert | MongoDB uses `_id` — client-side `id` causes field duplication |
| Not normalizing `_id` → `id` in response | Response must return `id` (not `_id`) |
| Skipping Geoserver setup for raster layers | Check `geoserverConfig.enable` flag and handle the integration |
| Hardcoding collection names | Use settings/config keys — refer to `fastapi-data` skill for patterns |
