---
name: fastapi-build-filter-elasticsearch
description: Use when building Elasticsearch filter queries from dashboard filter DTOs — converting user-facing filter operators into ES bool query DSL, handling nested fields, index patterns, order/sort, pagination, and date/time range filters
---

# build-filter-elasticsearch — Elasticsearch Filter Query Builder

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
| ES filter DTO dicts | reuse the boilerplate's filter vocabulary: `dto.common.FilterItem` / `FilterValue` / `FilterOperator` (same operator strings) and validate fields against a whitelist like `db.query.build_query_spec` does; reject object values |
| Elasticsearch client | not in the boilerplate — add the `elasticsearch` package and settings; the translator should mirror `db/mongo/translator.py` (pure function, escapes user text) |

## Overview

This skill documents the pattern for translating dashboard filter configurations into Elasticsearch query DSL. The pipeline converts a list of filter objects into `must`, `filter`, `must_not`, and `should` clauses that get merged into an existing ES query's `bool` block, then applies order/sort and pagination.

**Core principle:** Filters are independent query clauses built per-operator, routed to the correct bool section based on operator type (negation → `must_not`, OR logic → `should`, range/terms → `filter`, everything else → `must`), then merged into the base query with deduplication.

## When to Use

- Adding a new filter operator to an Elasticsearch query builder
- Debugging why a filter doesn't produce the expected ES query
- Understanding how filter → ES DSL translation works end-to-end
- Implementing order/sort or pagination for ES-backed dashboards
- Working with nested field filters or nested aggregations
- Troubleshooting `.keyword` field mapping or index pattern issues

## Filter Object Shape

Each filter dict from the frontend follows this structure:

```python
{
    "field": "username",                          # field name (string)
    # OR multi-field:
    "field": ["field1", "field2"],                # list for multi_match / multi-field
    # OR nested field:
    "field": {                                    # dict with nested path info
        "field": "ann_statements.value",
        "parents": [
            {"field": "ann_statements", "type": "nested"}
        ]
    },
    "table": "",                                  # ignored for ES
    "fieldType": "string" | "date" | "datetime" | "number",
    "field_type_origin": "text" | "keyword" | "datetime" | ...,
    "operator": "is" | "is one of" | ...,
    "value": {
        "is": "value",                            # for single-value operators
        "isOneOf": ["a", "b"],                    # for multi-value operators
        "gte": 100, "lte": 200,                   # for range operators
        "timezone": "Asia/Jakarta",               # optional
        "interval": "day" | "week" | "month",     # optional — date histogram interval
    },
    "operatorField": "and" | "or",                # logical combinator between filters
    "operator_type": "and" | "or",                # routing: and→must/filter, or→should
    "queryType": "dsl",                           # optional — raw DSL passthrough
}
```

## Pipeline Overview

The full filter-to-query pipeline follows this sequence:

```
1. Index pattern resolution    → replace date placeholders in index names (e.g., logs-YYYY-MM-DD)
2. Field mapping correction    → append .keyword suffix to text fields that have keyword sub-fields
3. Filter → ES DSL translation → convert each filter dict into ES bool query clauses
4. Query merging & dedup       → merge new clauses into existing query, removing duplicates
5. Nested agg filter injection → inject nested filters into aggregation sub-queries
6. Date histogram intervals    → override date_histogram aggregations with filter interval config
7. Order / sort                → apply ordering at aggregation level (terms.order) or document level (sort)
8. Pagination                  → apply bucket_sort (aggregations) or from/size (documents) or scroll
```

## Step 1: Index Pattern Resolution

When index names contain date placeholders (`YYYY`, `MM`, `DD`), resolve them from the query's timeframe:

```
Input index:        "logs-YYYY-MM-DD-*"
Query timeframe:    gte=2025-01-15, lte=2025-01-20
Resolved index:     "logs-2025-01-1*"
```

**Logic:**
1. Extract gte/lte from the query's `bool.filter[].range` or `bool.must[].range`
2. Compare start/end dates to determine which date parts vary
3. Substitute `YYYY`/`MM`/`DD` tokens with actual values
4. Save the original index name for later reference

## Step 2: Field Mapping Correction (`.keyword` Suffix)

For string/text/keyword fields, fetch the actual Elasticsearch field mapping. If a field has both `text` and `keyword` sub-types, append `.keyword` to target the keyword field for exact matching.

**Skip this step for:** `is contain`, `match phrase` operators (these need the text field, not keyword).

**Caching:** Field mapping results should be cached (e.g., in Redis) to avoid repeated `get_field_mapping` calls.

## Step 3: Filter → ES DSL Translation

### Operator Mapping Table

| Operator | ES Clause | Bool Section |
|----------|-----------|--------------|
| `is` | `{"match": {field: value}}` | `must` |
| `is not` | `{"match": {field: value}}` | `must_not` |
| `is one of` | `{"terms": {field: [values]}}` | `filter` |
| `is not one of` | `{"terms": {field: [values]}}` | `must_not` |
| `greater than equals` | `{"range": {field: {"gte": value}}}` | `filter` |
| `less than equals` | `{"range": {field: {"lte": value}}}` | `filter` |
| `is between` | `{"range": {field: {"gte": X, "lte": Y}}}` | `filter` |
| `is not between` | `{"range": {field: {"gte": X, "lte": Y}}}` | `must_not` |
| `match phrase` | `{"match_phrase": {field: value}}` | `must` |
| `multi match` | `{"multi_match": {query, fields, type, operator}}` | `must` |
| `is exist` | `{"exists": {"field": field}}` | `must` |
| `is not exist` | `{"exists": {"field": field}}` | `must_not` |
| `is contains` | `{"query_string": {query, default_field: field}}` | `must` |
| `is not contains` | `{"query_string": {query, default_field: field}}` | `must_not` |
| `is contains with and` | `{"query_string": {query: "(A AND B) OR (C AND D)"}}` | `must` |
| `is contains with or` | `{"query_string": {query: "(A OR B) OR (C OR D)"}}` | `must` |
| `wildcard` / `search` | `{"wildcard": {field: {"value": "*term*", "case_insensitive": true}}}` | `must` |
| `unique values` | Sets `query["collapse"] = {"field": field}` | N/A (collapse) |
| `dsl` (via queryType) | Raw value appended directly to `must` | `must` |

### Date/Time in Range Operators

When `fieldType == "date"` or `field_type_origin == "datetime"`:
- Add `"format": "epoch_millis"` to the range clause
- Values are expected in epoch milliseconds

When NOT a date field but `timezone` is present:
- Add `"time_zone"` to the range clause

### Date Histogram Interval Override

When an `is between` filter includes `value.interval`:
- Store the range config separately for later injection into `date_histogram` aggregations
- For ES >= 7: use `calendar_interval`
- For ES < 7: use `interval`
- This allows the frontend's time range picker to control the aggregation bucket size

> **Different mechanism than the dedicated per-widget pattern.** This section covers the GENERIC
> filter-object pipeline (`value.interval` embedded in a filter dict, injected in Step 6 below). The
> `erp-backend-per-widget` dedicated pattern instead exposes `interval` as its own optional DTO field,
> resolved server-side by `_resolve_interval()` with an explicit-value-wins-else-auto-detect-from-range
> rule, and mirrored by an identical threshold ladder on the frontend so ES bucket size and chart x-axis
> label format never disagree — see `../erp-backend-per-widget/references/dynamic-time-series-interval.md`.
> Don't mix the two: a dedicated per-widget menu module does NOT run filter objects through this pipeline.

### Multi-Field Handling

When `operatorField` is set and `field` is a list:
- Use `field[0]` as the primary field for the current filter
- Duplicate the filter for each additional field (`field[1:]`) and append copies to the filter list
- Each copy inherits the `operator_type` from `operatorField`

Special operators (`is contains`, `search`, `multi match`, etc.) skip this — they use the full list as `fields` in the query clause.

### Nested Field Handling

When a filter's field has `parents` (nested field path):

1. Sort parents by field depth (number of `.` segments)
2. Wrap the query value recursively:

```python
# Single nested parent:
{"nested": {"path": "ann_statements", "query": <original_query_value>}}

# Multiple nested parents (recursive):
{"nested": {"path": "outer", "query": {"nested": {"path": "inner", "query": <original>}}}}
```

3. **Positive nested filters** (not containing "not" in operator): also store a deep copy for later injection into aggregation sub-filters
4. **Negative nested filters** (`is not`, `is not one of`, etc.): go to `must_not` only — never leak into aggregation filters

### Bool Section Routing

After building the query clause, route it to the correct bool section:

| Condition | Section |
|-----------|---------|
| Operator contains `"not"` | `must_not` |
| `operator_type == "or"` | `should` |
| Operator is `is between`, `greater than equals`, `less than equals`, `is one of` | `filter` |
| Everything else | `must` |

### Special Operator: Topic Management

`is contain topic management` expands a topic document into query clauses:

1. Fetch the topic document from MongoDB by `value.is`
2. Extract the topic's `queries` (per-platform query_string clauses)
3. Extract `filters.general` (media_tags term/terms/match filters)
4. If the topic has no queries → recursively build filters from the topic's sub-filters
5. Append media_tags filters directly to `must` or `must_not`

### Special Operator: Account Management

`is contain account management` expands account IDs:

1. Fetch account documents by `value.isOneOf` IDs
2. Extract account identifiers from each document
3. Build `should` queries with `terms` clauses across all specified fields

## Step 4: Query Merging & Deduplication

When merging new filter clauses into an existing query's `bool`:

**Always-append operators:** `query_string` and `exists` clauses are always added — never considered duplicates.

**Nested clause merging:** If two nested queries share the same `path`, their inner queries are collected and wrapped into a single `{"bool": {"must": [...]}}` structure.

**Other operators:** Deduplicated by `(operator, field_name)` pair — if the existing query already has a `match` on `"username"`, a second one is skipped.

**Self-dedup:** After merging, scan for multiple nested queries with the same path within the same bool section and merge them.

## Step 5: Nested Aggregation Filter Injection

For positive nested filters (stored in Step 3), inject them into the aggregation tree:

```
For each nested path with stored filters:
  Find the aggregation with "nested": {"path": <path>}
  Add a "nested_filter" sub-aggregation:
    {"filter": <nested_query>, "aggs": <original_sub_aggs>}
```

This ensures dashboard aggregations respect the same nested filters applied at the query level.

## Step 6: Date Histogram Interval Override

Inject interval configurations (from Step 3) into matching `date_histogram` aggregations:

- Match by field name between the interval config and the aggregation's `date_histogram.field`
- Set `calendar_interval` or `interval` from the config
- Set `extended_bounds` (min/max) from the config's gte/lte
- For weekly intervals: calculate the correct `offset` based on the start date's day of week

## Step 7: Order / Sort

### Aggregation-Based Ordering (when query has `aggs.*.terms`)

Find the deepest aggregation matching the `orderBy` field and set:

```python
terms["order"] = {orderBy: "DESC" | "ASC"}
```

### Document-Level Sorting (no aggregation terms)

```python
query["sort"] = [{orderBy: {"order": "DESC" | "ASC"}}]
```

### Post-View Ordering Fallback

For post-view mode without explicit sort, walk the aggregation tree to find the field used for terms bucket ordering. Default to the document `id` field if nothing is found.

## Step 8: Pagination

### Aggregation Pagination (bucket_sort)

When the query has terms aggregations AND page/size are set:

```python
terms["size"] = page * size                              # enough buckets to cover the page window
terms["aggs"]["pagination"] = {
    "bucket_sort": {
        "sort": [{order_key: {"order": "desc"}}],
        "from": (page - 1) * size,
        "size": size
    }
}
```

Add a `totalData` cardinality or value_count aggregation to get total document count.

### Document-Level Pagination (from/size)

When no terms aggregations:

```python
query["size"] = size
query["from"] = (page - 1) * size
```

### Cursor-Based Pagination (Search After / Scroll)

For deep pagination:
- Extract `scroll_id` and `search_after` from the request
- Remove `from` parameter (incompatible with `search_after`)
- Set `search_after` on the query body

## Value Validation

Before building any query, validate that each filter has the required value keys:

| Operator Category | Required `value` Keys |
|-------------------|----------------------|
| `is`, `is not`, `match phrase`, `multi match`, `is contains`, `is not contains`, `is contains with or`, `is contains with and`, `wildcard`, `search`, `is contain topic management` | `value.is` (non-null) |
| `is one of`, `is not one of`, `is contain account management` | `value.isOneOf` (non-empty list) |
| `greater than equals` | `value.gte` (non-null) |
| `less than equals` | `value.lte` (non-null) |
| `is between`, `is not between` | BOTH `value.gte` AND `value.lte` (non-null) |
| `is exist`, `is not exist`, `unique values` | field only — no value keys required |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Nested filter values leaking from `must_not` into aggregation filters | Only positive filters (no "not" in operator) populate nested agg filters |
| Shared object reference mutating both `must` array and `nested` agg dict | Deep-copy when storing filters into both locations |
| `.keyword` appended to fields used with `match_phrase` | Skip `.keyword` correction for `match phrase` and `is contain` — they need text fields |
| Duplicate nested queries with same path after merging | Run self-dedup pass after every merge operation |
| `field` is a list but operator is special (`is contains`, `search`, etc.) | Special operators use the full list as `fields` — don't coerce to single field |
| Forgetting `precision_threshold` on cardinality aggregations | Set it explicitly — default is only 3000 |
| `search_after` with `from` parameter | Remove `from` — `search_after` is incompatible with it |
