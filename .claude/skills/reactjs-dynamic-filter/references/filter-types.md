---
name: filter-types-reference
description: Complete reference for all 6 dynamic filter types — scope rules, store behavior, and merge priority.
---

# Dynamic Filter — Types Reference

## Filter Store Structure

```ts
// Zustand store shape
{
  urlFilters: FilterState[]                   // from URL params
  globalFilters: FilterState[]                // from global/widget emit
  widgetFilters: Map<widgetId, FilterState[]> // from widget-to-widget
  filterMap: WidgetFilterMap                  // scope config per widget
}
```

## FilterState Shape

```ts
interface FilterState {
  key: string           // filter name, e.g. "period", "orderId"
  value: unknown        // filter value
  source: 'url' | 'global' | 'widget'
  scope: 'all' | 'partial' | 'exclude-self'
  targets?: string[]    // widgetId[], required when scope = "partial"
}
```

## WidgetFilterConfig Shape

```ts
interface WidgetFilterConfig {
  scope?: 'all' | 'partial' | 'exclude-self'
  targets?: string[]      // widgets that receive this filter
  useAsFilter?: boolean   // this widget can emit filters to other widgets
  emitKey?: string        // key to emit (for use-as-filter)
  excludeSelf?: boolean   // do not filter self
  listenFrom?: string[]   // only listen to filters from specific emitters
  listenGlobal?: boolean  // receive global filters
  listenUrl?: boolean     // receive URL filters
}
```

---

## 6 Filter Types

### Type 1 — URL Filter (scope: all)

All filters from URL query params are automatically stored in `urlFilters` with `scope: "all"`.

```
Priority: LOWEST — can be overridden by global/widget filters
Target:   All widgets on the page
Trigger:  Page load / navigation
```

```ts
// filter-map: no special config needed
// URL: /dashboard?period=2026-01&region=west-java
// → urlFilters = [{ key: "period", value: "2026-01", scope: "all" }, ...]
```

---

### Type 2 — Global Filter → All Widgets (scope: all)

A filter that affects every widget on the page.

```
Priority: MEDIUM
Target:   All widgets
Trigger:  User selects a value in the filter component
```

```ts
// filter-map
'filter-period': { scope: 'all' }

// Component
<Filter id="filter-period" filterKey="period" config={filterMap['filter-period']} ... />
```

**Store behavior:** value is stored in `globalFilters` with `scope: "all"`. `isApplicable(widgetId)` always returns `true`.

---

### Type 3 — Global Filter → Partial Widgets (scope: partial)

A filter that only affects the widgets listed in `targets`.

```
Priority: MEDIUM
Target:   Widgets in targets[] only
Trigger:  User selects a value in the filter component
```

```ts
// filter-map
'filter-category': {
  scope: 'partial',
  targets: ['chart-revenue', 'table-orders']  // only these 2 widgets
}
```

**Store behavior:** value is stored in `globalFilters` with `scope: "partial"` and a defined `targets`. `isApplicable(widgetId)` returns `true` only when `widgetId` is in `targets`.

---

### Type 4 — Connect to Other Filter (dependsOnKey)

One filter is "connected" to another — its value depends on and auto-resets when the referenced filter changes. This is not limited to `DependentFilter` (Select) — **any filter component** can be a consumer or provider in this relationship.

```
Priority: MEDIUM (scope: all / partial depending on config)
Target:   Per config scope
Trigger:  User selects a value, OR the depended-on filter changes (auto-reset)
```

**Use cases:**
- `filter-province` → `filter-district` → `filter-subdistrict`
- `filter-category` → `filter-product` (Select → Select)
- `filter-brand` → `filter-model` (Select → MultiSelectAsync)
- `filter-report-type` → `filter-metric` (Radio → Checkbox)

```ts
// filter-map — each filter is registered independently
'filter-province':     { scope: 'partial', targets: ['table-orders'] },
'filter-district':     { scope: 'partial', targets: ['table-orders'] },
'filter-subdistrict':  { scope: 'partial', targets: ['table-orders'] },
```

**Chain pattern (Province → District → Sub-district):**

```tsx
// Province — provider level 1, depends on nothing
<Filter
  id="filter-province"
  filterKey="province"
  options={PROVINCE_OPTIONS}
  config={filterMap['filter-province']}
/>

// District — consumer of province, provider for sub-district
<DependentFilter
  id="filter-district"
  filterKey="district"
  dependsOnKey="province"           // connected to filter-province
  options={DISTRICT_OPTIONS}        // each option has dependsOnValue: "west-java" etc.
  config={filterMap['filter-district']}
/>

// Sub-district — consumer of district
<DependentFilter
  id="filter-subdistrict"
  filterKey="subdistrict"
  dependsOnKey="district"           // connected to filter-district
  options={SUBDISTRICT_OPTIONS}
  config={filterMap['filter-subdistrict']}
/>
```

**Auto-reset cascade:** When `province` changes → `district` resets → triggers `subdistrict` reset automatically, because each `dependsOnKey` reads from the store reactively.

**Non-Select component as consumer:**

```tsx
// MultiSelectAsync whose options depend on another filter
// → use the parent value as a param inside fetchOptions
<MultiSelectAsync
  id="filter-model"
  filterKey="model"
  fetchOptions={(search) => fetchModels(search, parentBrandValue)}  // parentBrandValue from store
  config={filterMap['filter-model']}
/>
```

For components without a built-in `dependsOnKey` prop (e.g. `MultiSelectAsync`), read the parent value directly from the store at the page or parent component level, then pass it as a parameter to `fetchOptions`.

**Store read pattern — always read directly from raw store:**

```ts
// CORRECT — read directly from raw store
const parentValue = useFilterStore((s) => {
  const inGlobal = s.globalFilters.find((f) => f.key === dependsOnKey)
  const inUrl = s.urlFilters.find((f) => f.key === dependsOnKey)
  return (inGlobal ?? inUrl)?.value as string | undefined
})

// WRONG — resolve() will miss it because scope does not target the filter itself
const parentValue = useFilterStore((s) => s.resolve('filter-district').find(...))
```

---

### Type 5 — Use as Filter: Widget → Other Widgets (useAsFilter)

Non-filter widgets (charts, tables, maps) that emit filters to other widgets when the user interacts with them (click, select).

```
Priority: MEDIUM (scope: partial / exclude-self)
Target:   Widgets in targets[]
Trigger:  User clicks/selects an element inside the widget
```

```ts
// filter-map
'table-orders': {
  useAsFilter: true,
  scope: 'partial',
  targets: ['chart-revenue', 'chart-trend']
}

// Inside the widget component
const { emit } = useFilterEmitter({
  emitterId: 'table-orders',
  scope: filterMap['table-orders'].scope,
  targets: filterMap['table-orders'].targets,
})

// When user clicks a row
emit('orderId', 'ORD-001')
```

**Toggle/deselect pattern:** Read `activeId` from `globalFilters`. Clicking the same row again → `clearFilterKey(key)`.

```ts
const activeId = useFilterStore((s) =>
  s.globalFilters.find((f) => f.key === 'orderId')?.value as string | undefined
)

function handleClick(id: string) {
  if (activeId === id) clearFilterKey('orderId')
  else emit('orderId', id)
}
```

---

### Type 6 — Use as Filter → All Except Self (scope: exclude-self)

A variant of Type 5 where the filter applies to all widgets except the one emitting it.

```
Priority: MEDIUM
Target:   All widgets except the emitter
Trigger:  User interaction inside the widget
```

```ts
// filter-map
'chart-region': {
  useAsFilter: true,
  scope: 'exclude-self',
  targets: ['chart-revenue', 'table-orders', 'chart-trend'],
}
```

**isApplicable logic:** `scope === 'exclude-self'` → `targets[0] !== widgetId`.

---

## Merge Priority (resolve)

```
resolve(widgetId) = merge(urlFilters, globalFilters, widgetFilters)

Priority order (highest → lowest):
  1. widgetFilters[widgetId]     ← highest
  2. globalFilters (applicable)  ← only those whose scope covers this widgetId
  3. urlFilters                  ← lowest, always present

Conflict resolution: same key → higher priority wins (overwrite)
```

---

## clearFilterKey vs reset

| Method | Scope | Use when |
|--------|-------|----------|
| `clearFilterKey(key)` | Remove 1 key from all filter sources | Deselect or parent filter changes |
| `reset(widgetId)` | Remove all filters for 1 widget | Widget unmounts or full reset |
| `reset()` | Remove all filters on the page | Page unmounts / navigating away |
