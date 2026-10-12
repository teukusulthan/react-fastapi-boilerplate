---
name: fastapi-api-gateway
description: Use when implementing an API gateway proxy service — forwarding REST/SSE requests to external endpoints with SSRF protection, file response detection with S3 offload, multipart form upload, Kafka audit logging, Elasticsearch log querying, and MongoDB-backed gateway configuration CRUD
---

# api-gateway — API Gateway Proxy Service

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
| `settings.ALLOWED_GATEWAY_NETWORKS`, Elasticsearch settings | not existing settings — add `ALLOWED_GATEWAY_NETWORKS: CsvList` (and ES connection fields) to `Settings` in `core/config.py` + `.env.example` |
| outbound HTTP with `requests` | `httpx` (already a dependency) with explicit timeouts; a sync `httpx.Client` inside `def` routes, `httpx.AsyncClient` only for the SSE streaming route |
| gateway config collection in MongoDB (local + central fallback) | a `gateways` entity via `register_entity(...)`; works on Mongo and Supabase. A second "central" store needs its own repository/provider (see `fastapi-database-init`) |

## Overview

This skill documents the API Gateway proxy pattern — a service that stores gateway configurations in MongoDB and forwards client requests to external endpoints. It provides SSRF (Server-Side Request Forgery) protection through IP allowlisting, automatically detects file responses and offloads them to S3, streams SSE (Server-Sent Events) responses, handles multipart form uploads, and logs every execution to Kafka for indexing in Elasticsearch.

**Core principle:** The gateway is a configurable proxy. Gateway definitions (endpoint, method, params, headers, body template) are stored in MongoDB. Client requests reference a `gatewayId`, the service resolves the full configuration, validates the target against SSRF rules, forwards the request, processes the response (file → S3, JSON → passthrough), and logs the result.

## When to Use

- Implementing a configurable API proxy/gateway service
- Adding SSRF protection to outbound HTTP requests
- Building a file-response proxy that offloads binary responses to S3
- Implementing Kafka-based audit logging for API calls
- Querying gateway execution logs from Elasticsearch
- Handling multipart/form-data proxy with file upload support
- Implementing SSE streaming proxy

## Architecture

```
Client Request (gatewayId + params)
         │
         ▼
  get_gateway(gatewayId)          ← MongoDB (local + central fallback)
  get_enpoint(gateway)            ← resolve prod/non-prod endpoint
  validate_ssrf(endpoint)         ← IP allowlist check
         │
         ├──► protocol == "sse" ──► requests.get/post(stream=True) ──► return raw Response
         │
         └──► protocol == "rest"
                    │
                    ├──► requests.request(method, endpoint, ...)
                    ├──► detect content-type
                    │       │
                    │       ├──► is binary/document? → upload to S3 → return S3 path
                    │       └──► is JSON/text?       → return inline
                    │
                    └──► dto.logging? → send to Kafka → Elasticsearch index
```

## Gateway Configuration CRUD

### Gateway Document Structure

```json
{
    "name": "report-download",
    "endpoint": "http://internal-api/reports",
    "endpointProd": "http://prod-api/reports",
    "type": "report",
    "protocol": "rest",
    "method": "post",
    "params": {"format": "pdf"},
    "body": {"reportType": "daily"},
    "headers": {"Authorization": "Bearer {{token}}"},
    "responseMapper": "data.results",
    "picUserId": "user_123",
    "workspaceId": "ws_001",
    "dashboardId": "db_001"
}
```

| Field | Purpose |
|-------|---------|
| `endpoint` | Base URL to forward requests to |
| `endpointProd` | Production endpoint override (used when `IS_FUSION_APP_PROD` is true) |
| `type` | Gateway type for log categorization (e.g., `"report"`) |
| `protocol` | `"rest"` or `"sse"` (Server-Sent Events streaming) |
| `method` | `"post"`, `"get"`, `"put"`, `"delete"`, or `"all"` (client chooses) |
| `params` | Default query parameters (overridden by DTO) |
| `body` | Default request body (overridden by DTO). `"{{file}}"` placeholder for form file fields |
| `headers` | Default headers |
| `responseMapper` | JMESPath expression to transform the response before returning |

### ID Generation

Gateway configs use content-based deterministic IDs:

```python
_id = get_md5(json.dumps(dto.dict()))
```

This makes gateway creation idempotent — same config always produces the same ID. Duplicate creation raises an error.

### Dual Collection Fallback

Gateway lookups check two MongoDB collections:

```python
def get_gateway(gatewayId):
    gateway = local_collection.find_one({"_id": gatewayId})
    if not gateway:
        gateway = central_collection.find_one({"_id": gatewayId})
    return gateway
```

This supports a **central gateway registry** (shared across deployments) with **local overrides**. If a gateway is not found locally, it falls back to the central collection.

### CRUD Operations

Standard MongoDB upsert pattern (see [`fastapi-create-map` references/upsert-and-lifecycle.md](../fastapi-create-map/references/upsert-and-lifecycle.md)):

| Operation | Key Behavior |
|-----------|-------------|
| `add()` | Deterministic ID from payload. Rejects duplicates |
| `update()` | Fetch existing → upsert with same ID |
| `delete()` | `delete_one({"_id": id})` |
| `get_by_id()` | `find_one` + `_id` → `id` normalization |
| `get_all()` | `mongo_query_builder()` + view collection + pagination |

---

## Gateway Execution — `execute()`

### Flow

```
1. get_gateway(gatewayId)
2. get_enpoint(gateway)          → resolve prod/non-prod endpoint
3. Build final endpoint          → base + additionalPath (with path traversal guard)
4. validate_ssrf(endpoint)       → IP allowlist check
5. Merge params                  → gateway defaults ← DTO params ← DTO additionalParams
6. Generate log_id + log_index   → MD5 hash + date-patterned ES index name
7. Determine HTTP method         → gateway.method or DTO.method (when method="all")
8. Execute request
9. Detect response type:
   ├── is_file_response? → upload to S3 → return {s3Path, path, mimeType, filesize, storage}
   └── else → response.json() or response.text()
10. If dto.logging → send to Kafka
11. Return result
```

### Step 3: Additional Path Handling

```python
if dto.additionalPath:
    # Path traversal guard
    if ".." in dto.additionalPath or ":" in dto.additionalPath:
        raise ValueError("Input path tidak valid")

    # Safe URL concatenation
    if not end_point.endswith('/') and not dto.additionalPath.startswith('/'):
        end_point += '/'
    end_point += dto.additionalPath
```

### Step 4: SSRF Protection

```python
def validate_ssrf(url):
    parsed = urlparse(url)

    # Only allow http/https
    if parsed.scheme not in ['http', 'https']:
        raise ValueError("Protocol not allowed")

    hostname = parsed.hostname

    # Resolve hostname → IP
    ip_addr = socket.gethostbyname(hostname)
    ip = ipaddress.ip_address(ip_addr)

    # Check against allowed networks
    allowed_networks = [ipaddress.ip_network(net) for net in ALLOWED_NETWORKS]

    for network in allowed_networks:
        if ip in network:
            return True

    raise ValueError(f"Access to {ip_addr} is denied by security policy")
```

**Configuration:** Allowed networks are loaded from `settings.ALLOWED_GATEWAY_NETWORKS` (set in `.env` as `BE_ALLOWED_GATEWAY_NETWORKS`) — a comma-separated string of CIDR ranges (e.g., `"10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16"`).

### Step 5: Parameter Merging

Priority order (highest wins):
1. `dto.additionalParams` — overrides everything
2. `dto.params` — client-provided params
3. `gateway.params` — gateway defaults

### Step 6: Log ID & Index

```python
log_id = get_md5(f"{json.dumps(dto.dict(), default=str)}{datetime.now().timestamp()}")
log_index = f"gateway-logs-{executed_time.strftime('%Y.%m.%d')}"
```

The log index uses a date pattern so logs are partitioned by day for efficient querying and retention management.

### Step 7: HTTP Method Resolution

```python
if gateway.method == "all":
    method = dto.method        # client chooses
else:
    method = gateway.method    # fixed by gateway config
```

Supported methods: `get`, `post`, `put`, `delete`.

### Step 8: Request Execution

```python
# GET: params as query string, body as JSON
# POST/PUT/DELETE: body as JSON, params as query string
# If dto.appendedLog: inject log_id and log_index into body

response = requests.request(method, endpoint, params=params, json=body,
                            headers=headers, stream=is_sse, timeout=60)

# Retry on ChunkedEncodingError (SSE connection drops):
except ChunkedEncodingError:
    response = requests.request(method, endpoint, json=body, ...)  # without params
```

**SSE streaming:** When `dto.protocol == "sse"`, `stream=True` is set and the raw `requests.Response` is returned immediately — no processing, no logging.

### Step 9: File Response Detection & S3 Offload

After execution, the response `Content-Type` is checked against a list of document/binary MIME types:

**Detected file types:**
- PDF, ZIP, octet-stream
- Microsoft Word: `.doc`, `.docx`
- Microsoft Excel: `.xls`, `.xlsx`, `.csv`
- Microsoft PowerPoint: `.ppt`, `.pptx`
- OpenDocument: `.odt`, `.ods`, `.odp`
- Plain text, RTF
- All `image/*` types

When a file response is detected AND status is 200:

```python
# 1. Extract filename from Content-Disposition header
filename = re.findall(r'filename\*?=?(?:UTF-8\'\')?"?([^";]+)"?', content_disposition)

# 2. Fallback: extract from URL path
if not filename:
    filename = os.path.basename(urlparse(endpoint).path)

# 3. Fallback: "document"
if not filename:
    filename = "document"

# 4. Sanitize: remove special chars, truncate to 50 chars
clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', name.replace(' ', '_'))[:50]

# 5. Build S3 path: gateway_files/YYYY/MM/DD/{log_id[:8]}_{clean_name}{ext}
file_path = f"gateway_files/{datetime.now().strftime('%Y/%m/%d')}/{short_id}_{clean_name}{ext}"

# 6. Upload to S3
s3.upload_fileobj(BytesIO(file_content), Bucket=bucket, Key=file_path,
                  ExtraArgs={"ContentType": mime_type})

# 7. Return S3 reference
result["response"] = {
    "s3Path": f"s3://{bucket}/{file_path}",
    "path": file_path,
    "mimeType": mime_type,
    "filesize": file_size,
    "storage": "s3"
}
```

**Non-file responses:** Return `response.json()` or fallback to `response.text()`.

### Step 10: Kafka Audit Logging

If `dto.logging` is enabled:

```python
log_result = copy.deepcopy(result)
log_result["createdAt"] = executed_time.strftime("%Y-%m-%dT%H:%M:%S.%f") + 'Z'
log_result["execution_time"] = execution_time
log_result["applicationType"] = "fusion_app" if IS_FUSION_APP else "fusion_builder"

producer.send(KAFKA_TOPIC_API_GATEWAY,
              value={**log_result, "type": gateway.get("type"), "id": log_id})
```

The log includes: the full result, execution time, gateway type, and the generated log ID. This is consumed and indexed into Elasticsearch.

---

## Form Execution — `execute_form()`

Handles `multipart/form-data` requests with file upload support:

```
execute_form(dto, file)
    │
    ├──► Validate: method must be POST
    ├──► Build endpoint (same as execute)
    ├──► Build multipart payload:
    │       ├── gateway.body: if value == "{{file}}", put file in files[]
    │       ├── dto.body: each key → files[(None, value)]
    │       └── dto.additionalFileParams → files[(None, value)]
    │
    ├──► requests.post(endpoint, files=files, params=params, stream=is_sse)
    │
    ├──► If SSE → return raw response
    │
    └──► Parse JSON response → apply responseMapper (JMESPath) → log to Kafka
```

### The `{{file}}` Placeholder

In the gateway's `body` config, values can be `"{{file}}"` to indicate a file upload slot:

```python
if gateway_body[key] == "{{file}}" and file is None:
    files[key] = (None, file)           # empty file slot
elif gateway_body[key] == "{{file}}" and file:
    files[key] = (file.filename, file.file, file.content_type)  # actual file
```

For non-file body entries, each key-value is sent as both a form field AND a file part (for maximum compatibility).

### Response Mapping

After receiving the response, if the gateway has a `responseMapper`:

```python
result["response"] = jmespath.search(gateway["responseMapper"], result["response"])
```

This transforms the upstream response using JMESPath — useful for extracting nested data or reshaping the response before returning to the client.

---

## Log Operations

### Query Execution Logs — `get_all_log()`

Queries gateway execution logs from Elasticsearch with date-patterned indexes:

```python
# Build filter from DTO
query_filter = query_builder_elastic(dto.filters)   # see build-filter-elasticsearch skill

# Add dashboardId filter if present
if dto.dashboardId:
    query_filter["filter"].append({"match": {"dashboardId": dto.dashboardId}})

# Add sessionId filter if present
if dto.sessionId:
    query_filter["filter"].append({"match": {"sessionId": dto.sessionId}})

# Date range → date-patterned index
if dto.startDate and dto.endDate:
    index = f"gateway-logs-{get_pattern_index(startDate, endDate, 'YYYY.MM.DD')}"
    query_filter["filter"].append({
        "range": {
            "createdAt": {
                "gte": "2025-01-01 00:00:00",
                "lte": "2025-12-31 23:59:59",
                "format": "yyyy-MM-dd HH:mm:ss",
                "time_zone": "+07:00"
            }
        }
    })
else:
    index = "gateway-logs-*"   # search all date partitions

# Add client filter if present
if dto.client:
    query_filter["filter"].append({"match": {"client.keyword": dto.client}})

# Execute search with sort, from, size
response = es.search(index=index, body={
    "query": {"bool": query_filter},
    "sort": [{orderBy: {"order": "desc/asc"}}],
    "from": (page - 1) * size,
    "size": size,
    "_source": dto.fields or True
})
```

Returns: `(list_of_hits_with_id, total_count)`.

> See [`fastapi-build-filter-elasticsearch`](../fastapi-build-filter-elasticsearch/SKILL.md) for the filter builder used.

### Update Log — `update_log()`

Updates a log entry's `result` field by re-sending to Kafka:

```python
def update_log(dto):
    # 1. Fetch existing document from ES
    doc = es.get(index=dto.logIndex, id=dto.logId)["_source"]

    # 2. Fallback to hardcoded index if not found
    # (handles logs that were indexed before the date-patterned index change)

    # 3. Update result field
    doc["result"] = dto.updateValue

    # 4. Re-send to Kafka (re-indexed by consumer)
    producer.send(KAFKA_TOPIC_API_GATEWAY, value={**doc, "id": dto.logId})
```

> The update is not direct to Elasticsearch — it goes through Kafka, so the ES index is eventually consistent.

### Delete Log — `delete_log()`

```python
es.delete_by_query(index="gateway-logs-2026", body={"query": {"match": {"_id": id}}})
```

## Supported MIME Types for File Detection

| Category | MIME Types |
|----------|-----------|
| PDF | `application/pdf` |
| Archives | `application/zip`, `application/x-zip-compressed` |
| Binary | `application/octet-stream` |
| Images | `image/*` |
| Word | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Excel | `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/csv` |
| PowerPoint | `application/vnd.ms-powerpoint`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| OpenDocument | `application/vnd.oasis.opendocument.text`, `.spreadsheet`, `.presentation` |
| Text | `text/plain`, `application/rtf` |

## SSRF Protection — Network Allowlist Pattern

```
User Request (gatewayId)
        │
        ▼
  Resolve gateway endpoint URL
        │
        ▼
  Parse URL → extract hostname
        │
        ▼
  DNS resolve hostname → IP address
        │
        ▼
  Check IP against allowed CIDR list
        │
        ├──► IP in allowed network → proceed
        └──► IP not allowed → raise RuntimeError("Security Policy Violation")
```

**Configuration requirement:** `BE_ALLOWED_GATEWAY_NETWORKS` (field `ALLOWED_GATEWAY_NETWORKS`) must be set as a comma-separated CIDR string (e.g., `"10.0.0.0/8, 172.16.0.0/12"`). If not set, all gateway requests fail.

**Blocked:** Non-HTTP schemes, unresolved hostnames, IPs outside allowed networks.

## Comparison: `execute()` vs `execute_form()`

| Aspect | `execute()` | `execute_form()` |
|--------|------------|-----------------|
| Content-Type | `application/json` | `multipart/form-data` |
| Method | Any (get/post/put/delete) | POST only |
| File upload | Not supported | Via `{{file}}` placeholder in gateway body |
| Body format | JSON object | Form fields + file parts |
| SSE support | Yes | Yes |
| File → S3 | Yes (from response) | No (response is JSON) |
| Response mapper | No | Yes (JMESPath) |
| Kafka logging | Optional (`dto.logging`) | Optional (`dto.logging`) |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Not setting `BE_ALLOWED_GATEWAY_NETWORKS` in `.env` | All gateway requests will fail — configure CIDR ranges |
| Using `..` or `:` in `additionalPath` | These are blocked as path traversal — validate input before passing |
| Forgetting `endpointProd` for production | Set `endpointProd` on gateways that have different production URLs |
| Central collection gateway not found | Always check both local and central collections in `get_gateway()` |
| Large file responses stored inline | File responses are auto-detected by Content-Type and offloaded to S3 |
| `responseMapper` on `execute()` | Only `execute_form()` applies `responseMapper` — `execute()` returns raw response |
| `dto.params` vs `dto.body` confusion on POST | For POST: params are query string, body is JSON. For GET: body is JSON, params are query string |
| SSE response not streamed | Set `dto.protocol == "sse"` — returns raw `requests.Response` for client-side streaming |
| Log update not appearing immediately | Updates go through Kafka — Elasticsearch is eventually consistent |

---

> **Related skills:**
> - [`fastapi-data`](../fastapi-data/SKILL.md) — MongoDB CRUD patterns, Services factory, view collections
> - [`fastapi-create-map` references/upsert-and-lifecycle.md](../fastapi-create-map/references/upsert-and-lifecycle.md) — Upsert pattern, ID generation, `_id` ↔ `id` normalization
> - [`fastapi-build-filter-elasticsearch`](../fastapi-build-filter-elasticsearch/SKILL.md) — Elasticsearch filter query building for log queries
