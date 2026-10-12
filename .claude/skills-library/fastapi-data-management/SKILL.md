---
name: fastapi-data-management
description: Use when implementing multi-database CRUD operations with a dispatcher pattern — routing add/update/delete/get-all/get-by-id/get-fields/get-tables/get-option operations to MongoDB, Elasticsearch, PostgreSQL, or MySQL backends, with data validation, audit logging, and MDM-aware cascade delete
---

# data-management — Multi-Database CRUD Dispatcher

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
| per-database "management" modules (Mongo / Elasticsearch / PostgreSQL / MySQL) | the boilerplate's own data access is `db.Repository` (Mongo or Supabase via `BE_DB_PROVIDER`). External, user-configured connections are a different concern: keep them in dedicated modules, compose SQL with `psycopg.sql` (never string formatting) and add drivers to `requirements.txt` |
| audit log via Kafka | `util.kafka.publish(...)`, best effort when `settings.kafka_configured` |

## Overview

This skill documents the dispatcher pattern for multi-database CRUD operations. A single `DataManagement` service class routes operations to database-specific management modules based on `connection.databaseType`. Every operation is audit-logged with execution time, and data is validated through a `fieldConfig` system that controls ID generation and timestamp injection.

**Core principle:** One entry point, four backends. The service resolves the connection, validates and transforms the data, dispatches to the correct backend module (MongoDB / Elasticsearch / PostgreSQL+MySQL), logs the operation, and returns the result. The caller never knows which backend was used.

## When to Use

- Implementing a new multi-database CRUD service
- Adding a new database type to an existing data management service
- Understanding the data validation and fieldConfig system
- Debugging why operations fail on specific database types
- Implementing audit logging for CRUD operations
- Understanding MDM (Master Data Management) cascade delete logic

## Architecture

```
                         DataManagement Service
                                │
                    get_connection()  ← MongoDB (connection store)
                    validate_data()   ← fieldConfig processing
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
    databaseType:    databaseType:    databaseType:
    "mongodb"        "elasticsearch"  "postgresql" / "mysql"
            │             │             │
            ▼             ▼             ▼
    mongo_management  elastic_management  postgresql_management
    (mm)              (em)                (pm)
            │             │             │
            └─────────────┼─────────────┘
                          │
                    update_log()  → MongoDB (audit log collection)
```

## Dispatcher Pattern

Every public method follows the same dispatch pattern:

```python
def operation(self, dto):
    # 1. Resolve connection
    connection = self.get_connection(dto.connectionId, source_id)

    # 2. Override database name if provided in DTO (for PG/MySQL)
    if connection.databaseType in ["postgresql", "mysql"] and dto.database:
        connection.database = dto.database

    # 3. Dispatch by database type
    if connection.databaseType == "mongodb":
        result = mm.operation(connection, dto)
    elif connection.databaseType == "elasticsearch":
        result = em.operation(connection, dto)
    elif connection.databaseType in ["postgresql", "mysql"]:
        result = pm.operation(connection, dto)
    else:
        raise Exception(f"Database type {connection.databaseType} is not supported")

    # 4. Log and return
    self.update_log(dto, action, start_time)
    return result
```

**Supported database types:** `mongodb`, `elasticsearch`, `postgresql`, `mysql`

**Exception for unsupported types:** PostgreSQL and MySQL share the same module (`pm`) and are treated identically. Other types raise an error.

## Connection Resolution

The `get_connection()` method resolves a connection document and applies credential overrides:

```python
def get_connection(connection_id, source_id=None):
    # 1. Fetch connection document from connection store
    connection = connection_store.find_one({"_id": connection_id})

    # 2. Apply rw_access credential override (if present)
    rw_access = connection.get("rw_access")
    if rw_access:
        connection["username"] = rw_access.get("username", connection["username"])
        connection["password"] = rw_access.get("password", connection["password"])
        connection["port"] = rw_access.get("port", connection["port"])

    # 3. Validate and normalize into ConnectionDTO
    connection = ConnectionDTO(**connection)

    # 4. For PostgreSQL: attach database name from data source
    if connection.databaseType == "postgresql" and source_id:
        source = data_source_store.find_one({"_id": source_id})
        connection.database = source.get("database")

    return connection
```

### The `rw_access` Pattern

Connections can have a `rw_access` sub-document with separate credentials for write operations. This is checked and applied on every connection resolution — read credentials are overridden when `rw_access` exists.

### PostgreSQL Database Resolution

For PostgreSQL, the `database` field is not always stored on the connection itself. It is resolved from the data source document (`source.get("database")`). This is critical — without this step, PostgreSQL connections may have no database set.

## Data Validation: `fieldConfig` System

Before dispatching, `validate_data()` transforms the raw DTO into a validated `DataManagementDTO` by processing the `fieldConfig`:

```python
def validate_data(dto, action):
    idField = "_id"       # default ID field name
    idType = "md5"         # default ID generation strategy
    hashField = []         # fields to include in ID hash
    timenow = datetime.now(timezone.utc)

    if dto.fieldConfig:
        # Extract ID config (and remove from fieldConfig for further processing)
        if "id" in dto.fieldConfig:
            idField = dto.fieldConfig["id"].get("field", "_id")
            idType = dto.fieldConfig["id"].get("type", "md5")
            hashField = dto.fieldConfig["id"].get("hadhField", [])
            del dto.fieldConfig["id"]

        # Process timestamp fields
        for key, value_format in dto.fieldConfig.items():
            if action == "update" and key == "createdAt":
                continue  # Don't overwrite createdAt on update

            if value_format.get("type") == "timestamp":
                field = value_format.get("field", key)
                value = timenow
                _format = value_format.get("format")

                # Format the timestamp value
                if _format == "epoch_millis":
                    value = timenow.timestamp() * 1000
                elif _format == "epoch_second":
                    value = timenow.timestamp()
                elif _format in date_string_formats:
                    value = timenow.strftime(python_format)

            # Apply to every data row
            for datum in dto.data:
                datum[field] = value

    return DataManagementDTO(
        fieldConfig=dto.fieldConfig,
        connectionId=dto.connectionId,
        createdBy=dto.createdBy,
        data=dto.data,
        table=dto.table,
        keepLastData=dto.keepLastData,
        fieldId=idField,
        idType=idType,
        hashField=hashField,
        database=dto.database,
    )
```

### fieldConfig Structure

```json
{
    "id": {
        "field": "_id",           // which field holds the ID
        "type": "md5",            // "md5" | "auto_increment"
        "hashField": []           // subset of fields to hash for ID
    },
    "createdAt": {
        "field": "created_at",    // DB column name
        "type": "timestamp",      // field type
        "format": "epoch_millis"  // timestamp output format
    },
    "updatedAt": {
        "field": "updated_at",
        "type": "timestamp",
        "format": "yyyy-MM-dd HH:mm:ss"
    }
}
```

### Timestamp Format Reference

| Format String | Output Example | Use Case |
|--------------|----------------|----------|
| `epoch_millis` | `1719000000000` | Elasticsearch date fields |
| `epoch_second` | `1719000000` | Unix timestamp columns |
| `yyyy-MM-dd` | `2025-06-24` | Date-only columns |
| `yyyy-MM-dd HH:mm:ss` | `2025-06-24 15:30:00` | Standard datetime |
| `yyyy-MM-dd HH:mm:ss.SSS` | `2025-06-24 15:30:00.123` | Millisecond precision |
| `yyyy-MM-ddTHH:mm:ss` | `2025-06-24T15:30:00` | ISO 8601 without timezone |

### ID Generation Strategies

| `idType` | Behavior | Used By |
|----------|----------|---------|
| `md5` | `get_md5(json.dumps(data))` — deterministic hash of all fields | MongoDB, Elasticsearch |
| `md5` + `hashField` | `get_md5(subset of fields)` — hash only specified fields | When not all fields should determine identity |
| `auto_increment` | Returns `None` — database assigns ID (SERIAL, AUTO_INCREMENT) | PostgreSQL, MySQL |
| Pre-existing `id` in row | Uses `data["id"]` directly | Update operations |

> See also: [`fastapi-create-map` references/upsert-and-lifecycle.md](../fastapi-create-map/references/upsert-and-lifecycle.md) for the ID generation pattern comparison (md5 timestamp vs md5 payload).

## Add / Update Flow

```
add(dto)  ─┐
            ├──► add_or_update(dto, action)
update(dto)─┘         │
                      ├──► get_connection()
                      ├──► validate_data(dto, action)
                      ├──► [dispatch to mm/em/pm.add_or_update()]
                      ├──► update_log(dto, action)
                      └──► return data
```

Both `add()` and `update()` call the same `add_or_update()` method, differing only in the `action` parameter (`"add"` vs `"update"`). The action string affects:

1. **validate_data()**: `createdAt` timestamp is skipped on update
2. **elastic_management**: On update, the index name has digits replaced with `*` for cross-index searching

### Per-Backend Behavior

| Backend | Add Behavior | Update Behavior |
|---------|-------------|-----------------|
| MongoDB | `bulk_write([UpdateOne(upsert=True)])` — idempotent | Same as add |
| Elasticsearch | `helpers.bulk()` with `doc_as_upsert=True` | Index name digits → `*`, pre-fetch to resolve correct index per doc. If `keepLastData`, uses scripted upsert with `data_history` |
| PostgreSQL | `INSERT INTO ... VALUES %s RETURNING id` via `execute_values()` | `UPDATE ... SET ... WHERE id = %s` via `execute_batch()` |

## Delete Flow

```
delete(dto)
    │
    ├──► get_connection()
    ├──► get_mdm_data(dto.mdmId)          ← resolve MDM config
    ├──► resolve child_tables from MDM    ← cascade delete chain
    │       │
    │       └──► formConfig.dataChildren.children[]
    │               └──► get_mdm_data(child.tableId).table
    │
    ├──► [dispatch to mm/em/pm.delete()]
    │       │
    │       └──► pm.delete() receives child_tables for cascade
    │
    └──► update_log(dto, "delete")
```

### MDM Cascade Delete (PostgreSQL only)

When `dto.mdmId` is set, the service resolves the Master Data Management configuration:

```python
mdm_data = get_mdm_data(dto.mdmId)

child_tables = []
if mdm_data has formConfig.dataChildren.children:
    for child in children:
        child_mdm = get_mdm_data(child["tableId"])
        child_tables.append(child_mdm["table"])

# child_tables passed to pm.delete() for cascade DELETE statements
```

Each child table gets a `DELETE FROM {child_table} WHERE id_parent = {id}` statement after the main delete. This is only implemented for PostgreSQL — MongoDB and Elasticsearch ignore child tables.

### PostgreSQL-Specific: Materialized View Refresh

When `dto.refresh` and `dto.materialized_view` are set:
- Executes `REFRESH MATERIALIZED VIEW [CONCURRENTLY] {view_name}` after the delete
- `CONCURRENTLY` is the default unless `dto.is_concurrent == False`

## Get Operations

### get_by_id

```
get_by_id(id, connection_id, table, field_id, database)
    │
    ├──► get_connection()
    ├──► [dispatch]
    │       ├──► mm.get_one()    → find_one({"_id": id})
    │       ├──► em.get_one()    → client.get(index, id)
    │       └──► pm.get_one()    → SELECT * FROM table WHERE field_id = id
    │
    └──► update_log(data_log, "get_one")
```

### get_all

```
get_all(dto: DataManagementFindDTO)
    │
    ├──► get_connection()
    ├──► [dispatch]
    │       ├──► mm.get_all()    → mongo_query_builder() + .skip().limit().sort()
    │       ├──► em.get_all()    → query_builder_elastic() + search() with from/size/sort
    │       └──► pm.get_all()    → query_builder_sql() + PostgreSqlQueryBuilder.exec_query_with_filter()
    │
    └──► update_log(dto, "get_all")
```

Returns: `(data, count, additional_info)` — where `additional_info` includes the generated query for debugging.

**Filter building:** Uses the database-specific filter builders. See related skills:
- [`fastapi-build-filter-elasticsearch`](../fastapi-build-filter-elasticsearch/SKILL.md)
- MongoDB: no separate skill in this repo — the boilerplate's own whitelisted filter translation is `apps/backend/db/query.py` + `db/mongo/translator.py` (see `fastapi-data`)
- SQL: no separate skill in this repo — see `apps/backend/db/supabase/translator.py` (`psycopg.sql` composition)

### get_fields

Returns the schema/fields of a table/index/collection:
- **MongoDB**: `find_one({})` → extract keys and Python types
- **Elasticsearch**: `indices.get_mapping()` → extract `properties`
- **PostgreSQL/MySQL**: Query `information_schema.columns` with fallback to `pg_attribute`

### get_tables

Lists available tables/indices/collections:
- **MongoDB**: `list_collection_names()`
- **Elasticsearch**: `cat.indices()` with optional `*{search}*` filter
- **PostgreSQL**: Union of `information_schema.tables` + `pg_matviews` + `information_schema.views`
- **MySQL**: `information_schema.tables` filtered by database

## Get Option Values (Unique Values for Dropdowns)

```
get_option(dto: DataManagementGetOptionDTO)
    │
    ├──► get_connection()
    ├──► [dispatch to Tools]
    │       ├──► tools.mongo_filter()      → $match → $group → $sort → $limit
    │       ├──► tools.elasticsearch()     → terms agg + bucket_sort pagination
    │       └──► tools.sql()               → SELECT DISTINCT + query_builder_sql() + LLM merge
    │
    └──► return list of unique values
```

The `Tools` service provides a higher-level abstraction for fetching unique/distinct values. Unlike `get_all`, this uses aggregation/grouping rather than raw document retrieval.

### Tools.elasticsearch() — Unique Values via Aggregation

Builds a terms aggregation with bucket_sort pagination:
- String fields: `replace_es_field_mapping()` to resolve `.keyword` suffix
- Dict fields (nested): wraps in `nested` aggregation with optional `filter` for search
- Filters: positive filters become `include`, negative filters become `exclude` on the terms agg
- Search: adds `wildcard` queries in `must` for non-nested, `filter` for nested fields
- `case_insensitive` fallback: if ES rejects `case_insensitive`, retries without it

### Tools.mongo_filter() — Unique Values via Aggregation

```python
pipeline = [
    {"$match": {column: {"$ne": None}}},         # not null
    {"$match": {column: {"$regex": search}}},     # if search provided
    {"$group": {"_id": f"${column}"}},             # distinct values
    {"$sort": {"_id": order}},                     # asc/desc
    {"$limit": size}                               # pagination (no offset)
]
```

### Tools.sql() — Unique Values via SQL

1. Builds a `SELECT DISTINCT` query with `LIKE` search, `ORDER BY`, `LIMIT/OFFSET`
2. If filters exist: uses `query_builder_sql()` + `PostgreSqlQueryBuilder.exec_query_with_filter()` with LLM prompt to merge filter WHERE into the base query
3. Fallback: direct `psycopg2`/`mysql.connector` execution of the SELECT DISTINCT

## Bulk Operations (PostgreSQL only)

```
bulk_operation(dto: BulkOperationDTO)
    │
    ├──► get_connection()   ← PostgreSQL ONLY
    └──► pm.bulk_operation()
            │
            └──► BFS traversal of operations[]
                    │
                    ├──► group by (table, operation)
                    ├──► ensure_id() — generate UUID if missing
                    ├──► get_metadata_field() — timestamps + createdBy
                    ├──► prepare children (relations) for next BFS level
                    │
                    └──► auto_insert_table() or auto_update_table()
                            │
                            ├──► SQLAlchemy ORM
                            ├──► Auto-create table if missing (infer column types)
                            └──► bulk insert() or update() with insert fallback
```

### Operation Types

```python
class OperationType(Enum):
    INSERT = "insert"
    UPDATE = "update"
```

### BFS (Breadth-First) Processing

Operations can have `relations` (child data referencing the parent). The bulk processor handles this level-by-level:

```
Level 0: Parent table INSERT/UPDATE
    │
    ├──► After parent row gets an ID, children inherit it via relation.localField
    │
    Level 1: Child table INSERT/UPDATE (with parent ID in relation.localField)
    │
    └──► ... deeper nesting ...
```

Each level groups rows by `(table, operation)` and executes one batch per group.

### Auto Table Creation

If the target table doesn't exist, `auto_insert_table()` creates it using SQLAlchemy:
- Infers column types from sample data: `bool→Boolean`, `int→Integer`, `datetime→DateTime`, `list→ARRAY(String)`, `str>255→Text`, `str→String`
- Creates the table with `metadata.create_all()`
- Then proceeds with the insert

### Update with Insert Fallback

`auto_update_table()` uses `UPDATE ... WHERE key_field = value`. If `rowcount == 0` (row doesn't exist), it falls back to `INSERT`.

## Audit Logging

Every operation is logged to an audit collection:

```python
def update_log(dto, action, start_time):
    executionTime = get_execution_time(start_time)

    data = dto.dict() if not isinstance(dto, dict) else dto
    _id = get_md5(f"{time.time()}{data}")   # Unique log entry ID

    data["action"] = action                  # "add" | "update" | "delete" | "get_all" | "get_one"
    data["createdAt"] = datetime.now()
    data["executionTime"] = executionTime

    audit_collection.update_one({"_id": _id}, {"$set": data}, upsert=True)

    data["id"] = _id
    if "data" in data:
        data.pop("data")                     # Remove payload from log (too large)
    return data
```

**Log entries include:** action, createdAt, executionTime, and the full DTO (minus the `data` payload array).

## DTO Inheritance Chain

```
BaseFindDTO                        BaseModel
  ├─ search, search_by,            ├─ connectionId
  │  operator, orderBy,            ├─ data[]
  │  order, page, size             ├─ table
  │                                ├─ createdBy
  └─► FindDTO                      ├─ database
       ├─ workspaceId              ├─ sourceId
       ├─ filters[]                ├─ metaData
       └─ organizationId           └─ mdmId
              │
              └─► DataManagementFindDTO
                    ├─ connectionId
                    ├─ table
                    ├─ orderBy
                    └─ database

DataManagementGetOptionDTO extends DataManagementFindDTO:
  + field: str   ← the column to get unique values for
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting to attach `database` from data source for PostgreSQL | Always call `source.find_one()` for PG connections with `source_id` |
| Using `connection.database` without checking `dto.database` override | Check `dto.database` first — it takes precedence over the connection default |
| Calling `add_or_update` directly instead of `add()`/`update()` | Use `add()` or `update()` — they set the correct `action` string |
| Forgetting `createdAt` skip on update in `validate_data` | Check `action == "update" and key == "createdAt"` before applying timestamp |
| Not passing `child_tables` to `pm.delete()` | MDM cascade delete requires `child_tables` — only PostgreSQL supports it |
| Using `get_option` for non-PG MySQL without setting `dto.database` | MySQL needs `connection.database` set — override from DTO if needed |
| Assuming `bulk_operation` works on all backends | Only PostgreSQL is supported — other backends raise an error |
| Not including the `data` field in logs | Always `pop("data")` before storing the log entry — data payload can be huge |

---

> **Related skills:**
> - [`fastapi-data`](../../skills/fastapi-data/SKILL.md) — repositories (`db.Repository`), `QuerySpec`/`build_query_spec`, services + DI
> - [`fastapi-database-init`](../../skills/fastapi-database-init/SKILL.md) — Connection initialization and management
> - [`fastapi-create-map`](../fastapi-create-map/SKILL.md) — Upsert pattern, ID generation strategies, createdAt/updatedAt lifecycle
> - [`fastapi-build-filter-elasticsearch`](../fastapi-build-filter-elasticsearch/SKILL.md) — Elasticsearch filter query building
