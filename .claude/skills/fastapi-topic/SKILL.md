---
name: fastapi-topic
description: Use when implementing a topic/keyword monitoring service — building per-platform Elasticsearch queries, generating sequential topic codes, cloning topics across dashboards, resolving workspace sharing, bulk importing from Excel, and cross-database syncing to external systems
---

# topic — Topic Monitoring & Keyword Management

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
| Elasticsearch client / index helpers | not in the boilerplate — add the `elasticsearch` package, settings in `core/config.py`, and a small client module under `util/`; call it from sync services |
| sequential topic codes via `find().sort().limit(1)` | `repo.find_all(where, sort=[SortSpec("code", SortDirection.DESC)], limit=1)` (import from `db`) and a unique `code` field so races surface as 409 `ConflictError` |
| Excel bulk import with a thread pool | parse in the sync service (openpyxl must be added to `requirements.txt`); insert via `repo.insert` per row and collect `ConflictError`s per row |

## Overview

This skill documents the Topic service pattern — a system for managing monitored keywords/topics across multiple media platforms. Each topic defines per-platform filter configurations that are compiled into Elasticsearch `query_string` queries. Topics support workspace sharing, dashboard cloning, sequential code generation, bulk Excel import, and cross-database synchronization.

**Core principle:** A topic is a named collection of filters grouped by platform (Twitter, Facebook, news/online, etc.). Each platform's filters are compiled into an Elasticsearch bool query and stored in a `queries` dict. Topics can be shared across workspaces and cloned into dashboards with deterministic IDs.

## When to Use

- Implementing a keyword/topic monitoring service
- Building per-platform query configurations that compile to Elasticsearch queries
- Generating sequential auto-incrementing codes within a category
- Cloning topics from a shared registry into specific dashboards
- Implementing workspace sharing (feature sharing) for topic visibility
- Bulk importing topics from Excel files with parallel processing

## Architecture

```
Topic Service
    │
    ├── MongoDB (topics collection)        ← primary store
    ├── MongoDB (topic view)               ← read with joined data
    ├── MongoDB (clients collection)       ← client metadata enrichment
    ├── MongoDB (workspace sharing)        ← cross-workspace visibility
    ├── Redis                              ← topic code counter cache
```

## Topic Document Structure

```json
{
    "name": "Election Monitoring 2025",
    "description": "Monitor election-related keywords",
    "type": "social_media",
    "topicCode": "S0042",
    "active": true,
    "tags": ["politics", "election"],
    "workspaceId": "ws_001",
    "dashboardId": "db_001",
    "clientId": "client_123",
    "client": "acme_corp",
    "client_code": "ACME",
    "client_full_name": "Acme Corporation",
    "createdBy": "user_001",
    "createdAt": "2025-06-24T10:00:00Z",
    "updatedAt": "2025-06-24T15:30:00Z",
    "filters": {
        "general": [
            {
                "field": "content",
                "operator": "is contains",
                "value": {"is": "election AND voting", "gte": 0, "lte": 0, "isOneOf": []}
            },
            {
                "field": "media_tags",
                "operator": "is one of",
                "value": {"isOneOf": ["politics", "government"]}
            }
        ],
        "twitter": [
            {
                "field": "content",
                "operator": "is contains",
                "value": {"is": "@election_comm OR #Pemilu2025"}
            }
        ],
        "online": [...]
    },
    "queries": {
        "general": {"query": {"bool": {...}}},
        "twitter": {"query": {"bool": {...}}},
        "online": {"query": {"bool": {...}}}
    },
    "sharedWorkspace": [
        {"workspaceId": "ws_002", "workspaceName": "Marketing Team"}
    ]
}
```

### Supported Platforms

```
news:       online, printed, tv
social_media: twitter, facebook, instagram, youtube, tiktok
other:      general, telegram, whatsapp, threads
```

Each platform key in `filters` must be one of the allowed platforms. Validation happens on `add()`.

## ID Generation

Topics use **content-based deterministic IDs**:

```python
_id = dto.id if dto.id else get_md5(json.dumps(dto.dict()))
```

If the DTO provides an explicit `id` (e.g., from a clone operation), it is used directly. Otherwise, the full serialized DTO is hashed — making topic creation idempotent per payload.

> See [`fastapi-create-map` references/upsert-and-lifecycle.md](../fastapi-create-map/references/upsert-and-lifecycle.md) for the ID generation pattern comparison.

## Topic Code Generation

Each topic gets a sequential code based on its type:

| Type | Code Prefix | Example |
|------|------------|---------|
| `news` | `M` (Media) | `M0042` |
| `social_media` | `S` (Social) | `S0157` |
| Other | `SM` (default) | `SM0003` |

### Code Generation Flow

```python
def get_topic_code(topic_type):
    code = CODE_PREFIX_MAP.get(topic_type, "SM")

    # 1. Try Redis cache
    last_code = redis.get(f"topic_code_{code}")

    # 2. Fallback: query MongoDB for highest existing code
    if not last_code:
        last_code = get_last_code(code)    # regex search on topicCode field

    # 3. Increment + zero-pad to 4 digits
    last_code = int(last_code) + 1
    return f"{code}{str(last_code).zfill(4)}", code, last_code
```

### get_last_code — MongoDB Fallback

```python
def get_last_code(code):
    # Find documents whose topicCode matches the prefix pattern
    last = collection.find({"topicCode": {"$regex": code}}).sort("topicCode", -1).limit(1)
    # Extract numeric portion, return 0 if no existing codes
    return int("".join(c for c in last[0]["topicCode"] if c.isdigit())) if last else 0
```

**Caching:** After generating a code, the counter is stored in Redis:
```python
redis.set(f"topic_code_{code}", last_code)
```

This ensures fast increments without repeated MongoDB `$regex` queries.

---

## Add Flow

```
add(dto)
    │
    ├──► Validate platforms (each key in dto.filters must be in BASE_PLATFORM)
    ├──► Generate _id = dto.id or md5(json.dumps(dto.dict()))
    ├──► Check duplicate (get_by_id)
    ├──► Enrich with client metadata (if clientId provided)
    ├──► Strip internal fields (reprocess, createTopic)
    ├──► add_or_update_process(data, _id)
    │       │
    │       ├──► Generate topicCode
    │       ├──► Build queries dict: for each platform, query_builder_elastic(filters)
    │       ├──► Set updatedAt
    │       ├──► MongoDB upsert
    │       ├──► Update Redis topic_code counter
    │       └──► Return data
    │
    └──► Return topic_result
```

### Platform Validation

```python
BASE_PLATFORM = [
    "online", "printed", "tv",
    "twitter", "facebook", "instagram", "youtube", "tiktok",
    "general", "telegram", "whatsapp", "threads"
]

for platform in dto.filters.keys():
    if platform not in BASE_PLATFORM:
        raise ValueError(f"Platform must be one of: {BASE_PLATFORM}")
```

### Client Metadata Enrichment

When `dto.clientId` is provided, enrich the topic with client metadata:

```python
def add_metadata_client(data, clientId):
    client = client_collection.find_one({"_id": clientId})
    if client:
        data["client"] = client.get("percolateName")
        data["client_code"] = client.get("code")
        data["client_full_name"] = client.get("name")
        data["clientId"] = client.get("_id")
    return data
```

### Query Building Per Platform

For each platform in `dto.filters`, compile the filter list into an Elasticsearch bool query:

```python
queries = {}
for platform, filters in data["filters"].items():
    query = {
        "query": {
            "bool": query_builder_elastic(filters, topic_query_builder=True)
        }
    }
    queries[platform] = query

data["queries"] = queries
```

When `topic_query_builder=True`, `query_builder_elastic()` uses a relaxed mode that allows filters without a `field` property — needed because topic filters may be partial query_string clauses.

> See [`fastapi-build-filter-elasticsearch`](../fastapi-build-filter-elasticsearch/SKILL.md) for the filter builder details.

---

## Update Flow

```
update(dto)
    │
    ├──► get_by_id(dto.id) → must exist
    ├──► Enrich with client metadata (if clientId provided)
    ├──► add_or_update_process(dto_dict, dto.id, isUpdate=True)
    │       │
    │       ├──► Generate topicCode
    │       ├──► Rebuild queries dict from filters
    │       ├──► Set updatedAt
    │       ├──► MongoDB upsert
    │       └──► Return data
    │
    └──► Return updated topic
```

Update also goes through `add_or_update_process()`, which means the `queries` dict is rebuilt — keeping the Elasticsearch queries in sync with any filter changes.

---

## Delete Flow

```python
def delete(_id):
    data = collection.find_one({"_id": _id})
    if data:
        collection.delete_one({"_id": _id})
        return f"{_id} has been deleted."
    raise Exception(f"{_id} doesnt exists.")
```

Simple single-document delete. The topic is removed from MongoDB and any associated percolator documents (outside scope) are also deleted.

---

## Get All — Aggregation Pipeline with Lookups

`get_all()` uses a MongoDB aggregation pipeline that resolves four related entities:

```
Topic
  ├── author       ← v_author (by createdBy)
  ├── clientDetail ← client (by client)
  ├── workspaceDetail ← workspace (by workspaceId)
  └── sharedWorkspace ← workspace_feature_sharing → workspace
```

### Pipeline Structure

```python
pipeline = [
    # 1. Filter + Sort + Paginate FIRST (before expensive $lookups)
    {"$match": query},
    {"$sort": {orderBy: -1 | 1}},
    {"$skip": (page - 1) * size},
    {"$limit": size},

    # 2. Lookup author (preserve null — some topics may have no author)
    {"$lookup": {"from": "v_author", "localField": "createdBy", "foreignField": "id", "as": "author"}},
    {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}},

    # 3. Lookup client detail (project only needed fields)
    {"$lookup": {
        "from": "client", "localField": "client", "foreignField": "_id", "as": "clientDetail",
        "pipeline": [{"$project": {"_id": 0, "id": "$_id", "name": 1, "code": 1}}]
    }},
    {"$unwind": {"path": "$clientDetail", "preserveNullAndEmptyArrays": True}},

    # 4. Lookup workspace detail
    {"$lookup": {
        "from": "workspace", "localField": "workspaceId", "foreignField": "_id", "as": "workspaceDetail",
        "pipeline": [{"$project": {"_id": 1, "name": 1}}]
    }},
    {"$unwind": {"path": "$workspaceDetail", "preserveNullAndEmptyArrays": True}},

    # 5. Lookup shared workspaces with nested workspace detail lookup
    {"$lookup": {
        "from": "workspace_feature_sharing", "localField": "_id", "foreignField": "referenceId",
        "as": "sharedWorkspace",
        "pipeline": [
            {"$lookup": {"from": "workspace", "localField": "workspaceId", "foreignField": "_id", "as": "detail"}},
            {"$project": {"_id": 1, "workspaceId": 1, "workspaceName": {"$arrayElemAt": ["$detail.name", 0]}}}
        ]
    }}
]
```

### Why Sort/Paginate BEFORE Lookups?

`$lookup` is expensive. By placing `$match`, `$sort`, `$skip`, and `$limit` first, only the documents that will actually be returned (max = `dto.size`) go through the four `$lookup` stages. This keeps the aggregation performant even with millions of topics.

### Total Count

The total count is queried separately from the raw collection (with indexes, without `$lookup` overhead):
```python
total = collection.count_documents(query)
```

### Workspace Sharing Filter

When `dto.workspaceId` is provided, topics visible to that workspace include:
- Topics owned by the workspace (`workspaceId == dto.workspaceId`)
- Topics shared to the workspace via `workspace_feature_sharing`

```python
if dto.workspaceId:
    shared = workspace_sharing_collection.find({"workspaceId": dto.workspaceId}, {"referenceId": 1})
    shared_ids = [s["referenceId"] for s in shared]

    query["$and"].append({
        "$or": [
            {"workspaceId": dto.workspaceId},       # owned
            {"_id": {"$in": shared_ids}}             # shared
        ]
    })
```

---

## Clone Topics to Dashboard — `use_topic_to_application()`

Copies existing topics into a dashboard with new IDs and codes:

```python
def use_topic_to_application(dto):
    topics = collection.find({"_id": {"$in": dto.topicIds}})
    current_time = datetime.now()
    bulk_ops = []

    for topic in topics:
        parent_id = topic.pop("_id")
        topic["parentId"] = parent_id
        topic["dashboardId"] = dto.dashboardId
        topic["topicCode"], code, last_code = get_topic_code(topic["type"])
        topic["createdBy"] = dto.createdBy
        topic["createdAt"] = current_time
        topic["updatedAt"] = current_time

        # Deterministic clone ID
        _id = get_md5(f"{parent_id}_{dto.dashboardId}")
        bulk_ops.append(UpdateOne({"_id": _id}, {"$set": topic}, upsert=True))

        # Update Redis counter for each generated code
        redis.set(f"topic_code_{code}", last_code)

    collection.bulk_write(bulk_ops)
    return [op._id for op in bulk_ops]
```

**Key patterns:**
- **Deterministic clone ID:** `md5({parent_id}_{dashboardId})` — same parent + same dashboard always produces the same clone ID
- **New topic code:** Each clone gets its own sequential code
- **parentId tracking:** The original topic ID is preserved for lineage
- **Bulk upsert:** Uses `UpdateOne` with `upsert=True` for idempotent cloning

---


## Process Status Tracking — `update_process()`

Each topic can have a `process` dict tracking the status of various pipeline stages:

```python
def update_process(topicId, process_dict):
    collection.update_one({"_id": topicId}, {"$set": {"process": process_dict}}, upsert=True)
    return {"process": process_dict, "status": True}
```

Typical process stages (stored in the `process` dict):
- `create_topic` — topic creation status
- `raw` — raw data collection progress
- `enrichment` — data enrichment progress
- `process_event` — event processing status
- `pg_event` — PostgreSQL event sync status

Each stage has `{"status": "success" | "failed" | "on queue" | "disable" | "progress", "message": ""}`.

---

## Get Clients — `get_clients()`

Returns a deduplicated view of clients associated with topics:

```python
def get_clients(dto):
    query = mongo_query_builder(dto, text_type="name")
    data = clients_view.find(query).skip(...).limit(...).sort("name", 1)
    return change_field_id(list(data)), clients_view.count_documents(query)
```

Uses the `v_topic_clients` view — a pre-joined view that provides a distinct list of clients referenced by topics.

---

## Get Tags — `get_tags()`

Returns tags filtered to type `"topic"`:

```python
def get_tags(dto):
    query = mongo_query_builder(dto, text_type="name")
    query["$and"].append({"types": "topic"})   # only topic-type tags
    data = tags_view.find(query).skip(...).limit(...).sort("name", 1)
    # Strip the "types" field from results
    return clean_results, tags_view.count_documents(query)
```

---

## Bulk Import from Excel — `import_file()`

Imports topics from an uploaded Excel file with parallel processing:

```python
def import_file(contents, created_by, dashboardId):
    df = pd.read_excel(BytesIO(contents))
    data = df.to_dict(orient="records")

    for row in data:
        # Build default filter: "is contains" on "title" field
        filters = {
            "general": [{
                "field": "title",
                "fieldType": "string",
                "queryType": "default",
                "field_type_origin": "text",
                "operator": "is contains",
                "value": {"gte": 0, "is": row["Query"], "isOneOf": [], "lte": 0}
            }]
        }

        topic = TopicDTO(
            name=row["Topic Name"],
            description=row["Description"],
            filters=filters,
            tags=parse_tags(row["Tags"]),
            type="all",
            splitPercolatorByPlatform=False,
            sharedDashboard=[],
            sharedWorkspace=[],
            dashboardId=row.get("dashboardId", dashboardId)
        )
        inserted_topics.append(topic)

    # Process in chunks of 10% of total with ThreadPoolExecutor
    chunks = chunk(inserted_topics, ceil(len(inserted_topics) / 10))
    for idx, chunk_items in enumerate(chunks):
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(lambda t=t: add(t)): t.name for t in chunk_items}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    status[name] = future.result()
                except Exception as e:
                    status[name] = str(e)
```

### Expected Excel Columns

| Column | Purpose |
|--------|---------|
| `Topic Name` | Topic display name |
| `Description` | Topic description |
| `Query` | The keyword/search query string |
| `Tags` | Comma-separated tags in brackets `[tag1, tag2]` |
| `dashboardId` | (optional) Override the default dashboard ID |

### Chunked Parallel Processing

Topics are split into 10 chunks and processed via `ThreadPoolExecutor`. Each chunk runs its topics concurrently. This balances speed (parallelism) with resource usage (not all topics at once).

---

## Upsert Lifecycle

Topics use the standard upsert pattern — same as Maps, Layers, and API Gateways:

```python
def add_or_update_process(data, _id, isUpdate=False):
    if "id" in data:
        data.pop("id")

    data["updatedAt"] = datetime.now()
    collection.update_one({"_id": _id}, {"$set": data}, upsert=True)

    data["id"] = _id
    return data
```

> See [`fastapi-create-map` references/upsert-and-lifecycle.md](../fastapi-create-map/references/upsert-and-lifecycle.md) for the full upsert pattern documentation.

---

## Key Design Patterns

| Pattern | Where Used | Purpose |
|---------|-----------|---------|
| Content-based ID | `add()` | `md5(json.dumps(dto.dict()))` — idempotent creation |
| Deterministic clone ID | `use_topic_to_application()` | `md5({parent_id}_{dashboardId})` — reproducible clones |
| Sequential code + Redis cache | `get_topic_code()` | Fast increments with MongoDB fallback |
| Pipeline paginate-before-lookup | `get_all()` | `$match`/`$sort`/`$skip`/`$limit` before `$lookup` |
| Bulk upsert | `use_topic_to_application()` | `UpdateOne(upsert=True)` for idempotent batch operations |
| Chunked parallel import | `import_file()` | 10-chunk ThreadPoolExecutor for Excel imports |

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Platform key not in `BASE_PLATFORM` | Validate all keys in `dto.filters` against the allowed platforms list |
| `$lookup` before `$match`/`$limit` | Always filter and paginate before joining — keeps lookups scoped to returned documents |
| Forgetting to rebuild `queries` on update | `add_or_update_process()` always rebuilds queries from filters — make sure this is called on updates |
| Topic code collision | Redis cache + MongoDB regex fallback for highest-existing-code ensures monotonic increments |
| Client metadata not attached before query building | `add_metadata_client()` must be called before `add_or_update_process()` |
| Using `count_documents()` on the view with `$lookup` | Count from the raw collection — `$lookup` distorts counts |
| Forgetting `preserveNullAndEmptyArrays` on `$unwind` | Without it, topics without a client/author/workspace are dropped from results |
| Duplicate topic creation | Content-based ID means same payload → same ID → upsert, but `add()` explicitly rejects duplicates |
| Excel import using single-threaded loop | Use `ThreadPoolExecutor` with chunked processing for large imports |

---

> **Related skills:**
> - [`fastapi-data`](../fastapi-data/SKILL.md) — repositories (`db.Repository`), `QuerySpec`/`build_query_spec`, services + DI
> - [`fastapi-create-map` references/upsert-and-lifecycle.md](../fastapi-create-map/references/upsert-and-lifecycle.md) — Upsert pattern, ID generation strategies, `_id` ↔ `id` normalization
> - [`fastapi-build-filter-elasticsearch`](../fastapi-build-filter-elasticsearch/SKILL.md) — Elasticsearch filter query building (used for per-platform `queries`)
