# Widget Reference Resolution

## Overview

Widgets are **references**, not containers. A widget of `type: "mapPlugin"` stores `referenceType: "maps"` and `referenceId: <map_id>`. The actual map data is resolved at read time — never embedded in the widget document.

This creates a **separation of concerns**: widgets define where and how to display, references define what data to display.

## Reference Resolution Chain (Widget → Map)

```
Widget (type="mapPlugin")
  ├─ referenceType = "maps"
  └─ referenceId = <map_id>
         │
         ▼
get_widget_references("maps", {<map_id>})
         │
         ▼
MONGO_COLLECTION_MAPS.find({_id: {$in: [<map_id>]}})
         │
         ▼
widget["referenceDetail"] = {full map document}
```

## Widget Fetch — Three-Phase Resolution

When fetching widgets (e.g., `get_all`), references are resolved in three phases:

```python
def get_all_with_references(self, query: dict) -> list:
    data = list(self.collection_view.find(query))

    # Phase 1: Group references by type
    type_map = {}
    for widget in data:
        ref_type = widget.get("referenceType")
        ref_id = widget.get("referenceId")
        if not ref_type or not ref_id:
            continue
        type_map.setdefault(ref_type, set()).add(ref_id)

    # Phase 2: Batch-fetch ALL reference documents (one query per type)
    for ref_type, ref_ids in type_map.items():
        type_map[ref_type] = self.resolve_references_by_type(ref_type, ref_ids)

    # Phase 3: Attach resolved references to each widget
    for widget in data:
        ref_type = widget.get("referenceType")
        ref_id = widget.get("referenceId")
        if ref_type in type_map and ref_id in type_map[ref_type]:
            widget["referenceDetail"] = type_map[ref_type][ref_id]

    return data
```

### Why Three Phases?

1. **Phase 1 (Group):** Collects all IDs by type. Multiple widgets may reference the same map — deduplication happens here.
2. **Phase 2 (Batch-fetch):** One database query per reference type, not one per widget. Avoids N+1 problem.
3. **Phase 3 (Attach):** Maps resolved documents back to widgets by reference ID.

## Reference Type → Collection Mapping

```python
def resolve_references_by_type(self, ref_type: str, ids: set) -> dict:
    """Resolve references for one type — one DB query for all IDs."""
    type_to_collection = {
        'maps':          settings.MONGO_COLLECTION_MAPS,
        'dataManager':   settings.MONGO_COLLECTION_MANAGEMENT_DATA_MANAGEMENT,
        'networkGraph':  settings.MONGO_COLLECTION_NETWORK_GRAPH,
        'aiAssistant':   f"v_{settings.MONGO_COLLECTION_AI_CHAT}",
    }

    if ref_type not in type_to_collection:
        return {}

    collection_name = type_to_collection[ref_type]
    collection = self.mongo_db[collection_name]

    # Single batch query for ALL ids of this type
    docs = list(collection.find({'_id': {'$in': list(ids)}}))

    # Normalize: _id → id
    for doc in docs:
        doc["id"] = doc.pop("_id")

    # Return as dict keyed by id
    return {doc["id"]: doc for doc in docs}
```

### Adding a New Reference Type

1. Add entry to `type_to_collection` mapping
2. Ensure the target collection's `_id` matches the `referenceId` stored in widgets
3. Follow the same `_id` → `id` normalization
4. Return dict keyed by `id` for Phase 3 attachment

## Reverse Resolution: URL → MVT Params

When the frontend loads a map page, the system walks the reference chain **backward** to extract MVT rendering parameters:

```python
def resolve_mvt_params_from_url(self, url: str, layer_name: str) -> dict:
    # 1. Find menu by URL path
    menu = self.collection_menu.find_one({"path": urlparse(url).path})

    # 2. Find the mapPlugin widget under that menu
    widget = self.collection_widget.find_one({
        "menuId": menu["_id"],
        "type": "mapPlugin"
    })

    # 3. Find the map referenced by the widget
    map_doc = self.collection_maps.find_one({"_id": widget["referenceId"]})

    # 4. Find the specific layer by name (within the map)
    layer = self.collection_layer.find_one({
        "mapsId": map_doc["_id"],
        "config.label": layer_name
    })

    # 5. Merge filters from layer config + map filterConfig
    filters = extract_layer_filters(layer)
    map_filters = map_doc.get("mapStyle", {}).get("filterConfig", {})

    # Only include enabled filters, merge with map-wide config
    filters = [
        {**f, **map_filters}
        for f in filters
        if f.get("enable") == True
    ]

    # Handle relative date ranges (e.g., "last 7 days")
    for f in filters:
        if f.get("enableRelativeType"):
            f["value"]["gte"], f["value"]["lte"] = get_relative_range(
                f.get("relativeType", 7)
            )

    # 6. Extract MVT params from layer metadata
    payload = layer.get("metaData", {}).get("params", {})
    mvt_keys = ["connectionId", "queryId", "database_type", "sourceId"]
    payload = {k: v for k, v in payload.items() if k in mvt_keys}
    payload["lookup_fields"] = []
    payload["filters"] = filters
    return payload
```

## Collection Reference Map

```
widget.referenceType ──────► target collection
────────────────────────────────────────────
"maps"                  → maps collection
"dataManager"           → data management collection
"networkGraph"          → network graph collection
"aiAssistant"           → AI chat collection (view)
```

## Object Relationship Graph

```
Dashboard
  └── Menu
        └── Widget (type="mapPlugin")
              ├── referenceType = "maps"
              └── referenceId ──────► Map
                                        ├── layers[] ──► Layer (via mapsId)
                                        │                   ├── metaData.params.connectionId
                                        │                   ├── metaData.params.queryId
                                        │                   └── metaData.params.sourceId[]
                                        └── widgets[] ──► Widget (via widgetId)
```

MVT rendering walks: **Widget → Map → Layer** to resolve connection/query/source params for PostgreSQL tile generation.

## Key Resolution Patterns

| Pattern | Description |
|---------|-------------|
| Forward resolution | Widget → referenceDetail (at widget read time) |
| Reverse resolution | URL → Menu → Widget → Map → Layer → MVT params |
| Batch dedup | Group all reference IDs by type, fetch once per type |
| id normalization | Always `_id` → `id` on reads, `id` → `_id` on writes |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Embedding map data in widget instead of using reference | Widget is a reference — resolve at read time, don't embed |
| Fetching one reference at a time (N+1) | Group by type, batch-fetch with `$in` |
| Not normalizing `_id` ↔ `id` | Read: `_id` → `id`, Write: `id` → `_id` |
| Forgetting to handle widget types without references | Check `referenceType` and `referenceId` exist before resolving |
| Hardcoding collection names | Use settings/config keys with consistent naming convention |
| Not handling the `v_` prefix for view collections | Some reference types use views (`v_`), some use raw collections |
