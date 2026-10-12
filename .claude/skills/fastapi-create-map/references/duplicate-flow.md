# Duplicate Flow — Full Map Clone Logic

## Overview

The `duplicate()` method deep-clones a map with all its layers and widgets, optionally duplicating the underlying queries. This is used when copying maps between dashboards or creating map variants.

## Entry Point: Map Duplication

```python
def duplicate(self, map_id: str, created_by: str, dashboard_id: str,
              name: str = None, description: str = None,
              workspace_id: str = None, new_map_id: str = None,
              duplicate_query: bool = False) -> dict:
    map_doc = self.collection.find_one({"_id": map_id})
    old_map_id = map_doc.pop("_id")
    new_map_id = new_map_id or get_md5(str(old_map_id + str(datetime.now().timestamp())))
    created_time = datetime.now()

    map_doc["name"] = name or f"{map_doc['name']} (Copy)"
    map_doc["createdAt"] = created_time
    map_doc["createdBy"] = created_by
    map_doc["updatedAt"] = created_time

    old_dashboard_id = map_doc.get("dashboardId")
    map_doc["dashboardId"] = dashboard_id

    # Duplicate queries ONLY if crossing dashboards or explicitly requested
    create_new_query = (old_dashboard_id != dashboard_id) or duplicate_query

    map_doc["layers"] = self.duplicate_layers(
        old_map_id, new_map_id, created_by, dashboard_id, create_new_query
    )

    if map_doc.get("widgets"):
        map_doc["widgets"] = self.duplicate_widgets(
            map_doc["widgets"], created_by, dashboard_id
        )

    self.collection.update_one({"_id": new_map_id}, {"$set": map_doc}, upsert=True)
    return {"old_id": old_map_id, "new_id": new_map_id}
```

### Decision: When to Duplicate Queries

```
Duplicate queries?
├─ old_dashboardId != new_dashboardId  → YES (different dashboard = separate query namespace)
├─ duplicate_query == True             → YES (explicitly requested)
└─ Otherwise                           → NO  (same dashboard, share queries)
```

## Layer Duplication

```python
def duplicate_layers(self, old_map_id: str, new_map_id: str,
                     created_by: str, dashboard_id: str,
                     create_new_query: bool = False) -> list:
    layers = list(self.collection_layer.find({"mapsId": old_map_id}))
    if not layers:
        return []

    new_layer_ids = []
    bulk_writes = []        # Accumulate UpdateOne operations
    query_writes = []       # Accumulate duplicated query writes
    batch_size_bytes = 0
    queries_cache = {}

    # Pre-fetch all queries in one batch (if duplicating queries)
    if create_new_query:
        query_ids = [l.get("metaData", {}).get("params", {}).get("queryId") for l in layers]
        query_ids = [qid for qid in query_ids if qid]
        if query_ids:
            queries_cache = {
                q["_id"]: q
                for q in load_queries_by_ids(query_ids)
            }

    for layer in layers:
        # Size guard: skip layers > 15MB
        layer_str = json.dumps(layer, default=str)
        if len(layer_str) > 15_000_000:
            logger.error(f"Layer exceeds 15MB limit: {layer.get('_id')}")
            continue

        # Batch flush: every 100 layers or 5MB
        if batch_size_bytes + len(layer_str) > 5_000_000 or len(bulk_writes) >= 100:
            self.collection_layer.bulk_write(bulk_writes)
            bulk_writes = []
            batch_size_bytes = 0

        new_layer_id = get_md5(str(datetime.now().timestamp()))
        layer.pop("_id")
        layer["mapsId"] = new_map_id
        layer["createdAt"] = datetime.now()
        layer["updatedAt"] = datetime.now()
        layer["createdBy"] = created_by

        # Duplicate the underlying query (if applicable)
        if create_new_query:
            query_id = layer.get("metaData", {}).get("params", {}).get("queryId")
            query_def = queries_cache.get(query_id)
            if query_def:
                new_query_name = f"{query_def.get('name')}_{dashboard_id}"
                new_query_id = get_md5(new_query_name)
                new_query = {**query_def}
                new_query["name"] = new_query_name
                del new_query["_id"]
                query_writes.append(
                    UpdateOne({'_id': new_query_id}, {'$set': new_query}, upsert=True)
                )
                layer["metaData"]["params"]["queryId"] = new_query_id

        bulk_writes.append(
            UpdateOne({"_id": new_layer_id}, {"$set": layer}, upsert=True)
        )
        new_layer_ids.append(new_layer_id)
        batch_size_bytes += len(layer_str)

    # Flush remaining
    if bulk_writes:
        self.collection_layer.bulk_write(bulk_writes)
    if query_writes:
        bulk_write_queries(query_writes)

    return new_layer_ids
```

### Batch Processing Rules

| Threshold | Action |
|-----------|--------|
| 100 layers accumulated | Flush batch |
| 5MB accumulated size | Flush batch |
| Layer > 15MB | Skip (log error) |
| End of loop | Flush remaining |

### Query Dedup Pattern

Pre-fetch all query IDs in a single `$in` query, map by `_id`, then reuse across layers. This avoids N+1 query lookups.

### Query Naming Convention

Duplicated queries are dashboard-scoped: `{original_name}_{dashboardId}`. This prevents name collisions when the same query is duplicated to multiple dashboards.

## Widget Duplication

```python
def duplicate_widgets(self, widgets: list, created_by: str,
                      dashboard_id: str) -> list:
    current_time = datetime.now()

    # Create a new menu for the duplicated map's widgets
    new_menu_id = self.widget_service.create_menu(dashboard_id, created_by, "map")

    # Batch-fetch all widget documents
    widget_ids = [w["widgetId"] for w in widgets]
    widget_docs = list(self.collection_widget.find({'_id': {'$in': widget_ids}}))

    # Prepare paste DTOs
    paste_data = [
        UpdateWidgetDTO(
            **{**doc, 'id': doc['_id'],
               'name': doc.get('name') or doc.get('widgetConfig', {}).get('name', '')}
        )
        for doc in widget_docs
    ]
    paste_param = PasteWidgetsDTO(
        menuId=new_menu_id, dashboardId=dashboard_id,
        isChild=True, data=paste_data,
        source_widget="map", pastedBy=created_by
    )
    duplicated_widgets = self.widget_service.paste_widgets(paste_param)

    # Rewire to new dashboard + menu
    widget_writes = []
    for i, w in enumerate(duplicated_widgets):
        w_data = w.model_dump()
        w_data.update({
            "createdAt": current_time,
            "updatedAt": current_time,
            "createdBy": created_by,
            "updatedBy": created_by
        })
        widget_writes.append(
            UpdateOne({"_id": w_data["id"]}, {"$set": w_data}, upsert=True)
        )

    if widget_writes:
        self.collection_widget.bulk_write(widget_writes)

    # Rewire references in the map's widgets array
    for widget in widgets:
        widget["dashboardId"] = dashboard_id
        widget["pageId"] = new_menu_id
        widget["widgetId"] = get_md5(f"{dashboard_id}_{widget.get('widgetId')}_map")

    return widgets
```

### Widget ID Rewiring

When `source_widget="map"` and `isChild=True`, widget IDs become deterministic:

```python
# PasteWidgetsDTO ID generation
if isChild and source_widget:
    new_widget_id = get_md5(f"{dashboardId}_{old_widget_id}_{source_widget}")
```

New widget ID = `md5({dashboardId}_{oldWidgetId}_map)` — deterministic per dashboard. Same old widget + same dashboard → same new ID.

## Object Dependency Graph During Duplication

```
Map (new _id)
  ├── new_name = f"{old_name} (Copy)"
  ├── new_dashboardId
  ├── Layers[]  (new _ids, re-pointed mapsId)
  │     └── metaData.params.queryId → (optional: duplicated query with scoped name)
  └── Widgets[] (new _ids, new menu, re-pointed dashboardId)
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Duplicating queries unnecessarily (same dashboard) | Only duplicate when crossing dashboards or explicitly requested |
| N+1 query lookups during layer duplication | Pre-fetch all query IDs in one `$in`, map by `_id` |
| Not handling large layers | Skip layers > 15MB with error log |
| Not batching writes | Accumulate `UpdateOne` ops, flush at thresholds |
| Forgetting to update `createdAt`/`createdBy` on duplicates | Set all lifecycle fields on every duplicated document |
| Losing dashboard scope on query names | Append `_{dashboardId}` to duplicated query names |
