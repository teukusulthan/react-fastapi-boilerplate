# Upsert Pattern & Document Lifecycle

## Core Pattern: `add_or_update_process()`

The upsert-or-update pattern is the **single write path** for Maps, Layers, and Widgets. Every create and update flows through it:

```python
def add_or_update_process(self, data: dict, _id: str) -> dict:
    if "id" in data:
        data.pop("id")                              # Strip client-side id

    data["updatedAt"] = datetime.now()              # Always set updatedAt
    self.collection.update_one(
        {'_id': _id},
        {"$set": data},
        upsert=True                                  # Insert-or-update
    )

    data["id"] = _id                                 # Normalize _id → id for response
    return data
```

**Required fields before calling:**
- `data["createdAt"]` — set by the caller on create (preserved on update by re-fetching existing doc)
- `data["updatedAt"]` — always overwritten with current time

## ID Generation — Three Strategies

| Service | Method | Input | Deterministic? |
|---------|--------|-------|----------------|
| Maps | `md5(str(datetime.now().timestamp()))` | Current timestamp | No |
| MapsLayer | `md5(str(datetime.now().timestamp()))` | Current timestamp | No |
| Widget (mongo target) | `md5(json.dumps(full_payload))` | Entire serialized DTO | **Yes** |

### Why Widget Uses Content-Based ID

Widget creation with MongoDB target uses the full serialized payload (including `createdAt` string) as the hash input. This makes widget creation **idempotent** — calling add twice with the same payload at the exact same second produces the same ID. Different timestamps WILL produce different IDs.

```python
dto_as_dict = dto.dict()
dto_as_dict["createdAt"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z")
_id = get_md5(json.dumps(dto_as_dict))    # Full payload hash
```

### When to Use Each Strategy

| Strategy | Use When |
|----------|----------|
| `md5(timestamp)` | Simple documents that can tolerate duplicates if called at same millisecond |
| `md5(json.dumps(payload))` | Documents that should be idempotent — same input → same ID |

## createdAt / updatedAt Lifecycle

```
Create                          Update
───────                         ──────
data["createdAt"] = now()       [no change to createdAt]
data["updatedAt"] = now()       data["updatedAt"] = now()
         │                              │
         └────── upsert ────────────────┘
```

- **Create**: sets `createdAt` before calling `add_or_update_process`
- **Update**: fetches existing doc (preserves `createdAt`), merges non-null fields, re-upserts

## MongoDB View Convention

Reads go through **view collections** (not raw collections) when they need joined/denormalized data:

```python
def get_by_id(self, _id: str, with_detail: bool = False):
    col = self.collection_view
    if with_detail:
        col = self.collection_view_with_detail   # view with joined data

    data = col.find_one({"_id": _id})
    if data:
        data["id"] = data.pop("_id")             # Normalize for API response
        # Optional: resolve related documents
        if data.get("createdBy"):
            creator_docs = get_user_collection().find({"_id": data["createdBy"]})
            if creator_docs:
                data["creator"] = map_users(list(creator_docs))
        return data
    return {}
```

Key patterns:
1. `_id` → `id` normalization on every read
2. Creator/user resolution on reads (resolve `createdBy` → full user object)
3. View collections named `v_{collection_name}` for simple views, or custom names for complex joins

## Widget add_or_update_process — Dual Target

Widgets can be stored in Redis (ephemeral) or MongoDB (persistent):

```python
def add_or_update_process(self, data: dict, _id: str, target: str = "redis") -> dict:
    if target == "redis":
        # Validate dashboard exists
        dashboard = validate_dashboard(data['dashboardId'])

        # Redis key convention
        redis_key = f"{REDIS_PREFIX_DASHBOARD}:{data['dashboardId']}:{data['menuId']}:{_id}"
        redis.set(redis_key, json.dumps(data, default=date_converter))

    else:  # target == "mongo"
        if "id" in data:
            data.pop("id")
        updated_time = datetime.now()
        data = parse_string_dates(data, default_time=updated_time)  # Convert date strings
        data["updatedAt"] = updated_time
        self.collection.update_one({'_id': _id}, {"$set": data}, upsert=True)
        data["id"] = _id

    return data
```

**Redis key format:** `{REDIS_PREFIX_DASHBOARD}:{dashboardId}:{menuId}:{widgetId}`

**When to use MongoDB target:** Map plugin widgets must persist in MongoDB so they survive Redis eviction and are visible to the dashboard caching layer. The `/widget/add-widget` endpoint sends `target="mongo"`.

## Collections Reference Convention

| Document Type | Collection Config Key | View Config Key |
|---------------|----------------------|-----------------|
| Maps | `MONGO_COLLECTION_MAPS` | `v_{MONGO_COLLECTION_MAPS}` |
| Layers | `MONGO_COLLECTION_MAPS_LAYER` | `v_{MONGO_COLLECTION_MAPS_LAYER}` |
| Widgets | `MONGO_COLLECTION_WIDGET` | `v_{MONGO_COLLECTION_WIDGET}` |
| Menus | `MONGO_COLLECTION_MENU` | — |
| Connections | `MONGO_COLLECTION_CONNECTION` | — |
| Data Sources | `MONGO_COLLECTION_DATA_SOURCE` | — |
| Users | `MONGO_COLLECTION_USER` | — |

For connection initialization, refer to the `fastapi-database-init` skill.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting to strip `id` before upsert | MongoDB uses `_id` — client-side `id` causes field duplication |
| Forgetting `data["id"] = _id` after upsert | Response must return `id` (not `_id`) |
| Using Redis instead of MongoDB for map widgets | Map widgets must be MongoDB-backed |
| Not setting `createdAt` before create | Set explicitly before calling upsert |
| Overwriting `createdAt` on update | Fetch existing doc, merge, preserve original `createdAt` |
