---
name: filter-widget-integration-reference
description: How dynamic-filter and dynamic-widget interact on the same page — 4 interaction patterns, shared store, and page setup checklist.
---

# Filter ↔ Widget Integration Reference

Both modules share one Zustand store from `dynamic-filter`. This document covers how they interact when used together on the same page.

---

## Shared Store Flow

```
dynamic-filter → dispatch() → useFilterStore → resolve(widgetId)
                                                     ↓
                                         dynamic-widget → use-widget-data → API fetch
```

---

## 4 Interaction Patterns

### Pattern 1 — Filter Component → All Widgets (Global)

A filter bar at the top of the page updates data in every widget.

```
FilterWidget (scope: 'all')
  → globalFilters
  → all DynamicWidget with listenGlobal: true re-fetch
```

```ts
// dashboard.filter-map.ts
'date-filter': { scope: 'all' }

// dashboard.widget-map.ts
'exposure-trend': { listenGlobal: true }
'sentiment-chart': { listenGlobal: true }
```

---

### Pattern 2 — Filter Component → Specific Widgets (Partial)

A filter only applies to listed target widgets.

```
FilterWidget (scope: 'partial', targets: ['chart-a', 'chart-b'])
  → globalFilters with targets defined
  → only chart-a and chart-b re-fetch
```

```ts
// dashboard.filter-map.ts
'platform-filter': { scope: 'partial', targets: ['exposure-trend', 'top-influencer'] }
```

---

### Pattern 3 — Widget → Widget (Inter-Widget Filter)

Clicking a row/element in one widget filters another widget.

```
TableWidget row click (emitter)
  → emit('influencerId', id)
  → widgetFilters['statement-cards']
  → DynamicWidget id="statement-cards" re-fetches
```

```ts
// dashboard.filter-map.ts
'top-influencer': { useAsFilter: true, scope: 'partial', targets: ['statement-cards'] }

// Inside TopInfluencerWidget:
const { emit } = useFilterEmitter({
  emitterId: 'top-influencer',
  scope: filterMap['top-influencer'].scope,
  targets: filterMap['top-influencer'].targets,
})
```

---

### Pattern 4 — URL Params → All Widgets

Filter state loaded from URL on page entry — enables shared links.

```
URL: ?date=2026-05-01&platform=twitter
  → useUrlFilters() → urlFilters
  → all widgets with listenUrl: true re-fetch on load
```

```ts
// dashboard.widget-map.ts
'exposure-trend': { listenGlobal: true, listenUrl: true }
```

---

## Page Setup — Combined filter-map + widget-map

```ts
// src/pages/dashboard/config/dashboard.filter-map.ts
export const dashboardFilterMap: WidgetFilterMap = {
  'date-filter':      { scope: 'all' },
  'platform-filter':  { scope: 'partial', targets: ['exposure-trend', 'top-influencer'] },
  'top-influencer':   { useAsFilter: true, scope: 'partial', targets: ['statement-cards'] },
}

// src/pages/dashboard/config/dashboard.widget-map.ts
export const dashboardWidgetMap: WidgetFilterMap = {
  'exposure-trend':   { listenGlobal: true, listenUrl: true },
  'sentiment-chart':  { listenGlobal: true },
  'top-influencer':   { listenGlobal: true },
  'statement-cards':  {},
}
```

```tsx
// DashboardPage.tsx
export default function DashboardPage() {
  useUrlFilters()

  const setFilterMap = useFilterStore((s) => s.setFilterMap)
  useEffect(() => {
    setFilterMap({ ...dashboardFilterMap, ...dashboardWidgetMap })
    return () => setFilterMap({})
  }, [setFilterMap])

  return (
    <div>
      {/* Filter bar */}
      <Filter id="date-filter" filterKey="date" options={DATE_OPTIONS}
        config={dashboardFilterMap['date-filter']} />

      {/* Auto-fetch widget */}
      <DynamicWidget id="exposure-trend" widgetType="chart"
        title="Exposure Trend"
        dataSource={{ type: 'api', endpoint: '/analytics/exposure', adapter: 'chart' }}
        options={{ chartType: 'bar', xKey: 'time', yKey: 'count' }} />

      {/* Manual widget (inter-widget emitter) */}
      <TopInfluencerWidget />

      {/* Receiver — re-fetches when top-influencer emits */}
      <DynamicWidget id="statement-cards" widgetType="card-grid"
        title="Influencer Statements"
        dataSource={{ type: 'api', endpoint: '/statements', adapter: 'default' }}
        options={{ template: 'statement', cols: 2 }} />
    </div>
  )
}
```

---

## Filter Resolution Priority (per widget)

When `use-widget-data` calls `resolve(widgetId)` before each fetch:

```
1. widgetFilters[widgetId]     ← highest (direct inter-widget emit)
2. globalFilters               ← filtered by scope/targets matching this widget
3. urlFilters                  ← lowest
─────────────────────────────
= resolvedParams               → merged into API params
```

---

## Page Setup Checklist

- [ ] `useUrlFilters()` called at page level if URL sync is needed
- [ ] `setFilterMap({ ...filterMap, ...widgetMap })` with cleanup in `useEffect`
- [ ] Every `FilterWidget` has an entry in `filter-map` with correct `scope` / `targets`
- [ ] Every `DynamicWidget` that listens to global filters has `listenGlobal: true` in `widget-map`
- [ ] Every `DynamicWidget` that listens to URL has `listenUrl: true` in `widget-map`
- [ ] Every inter-widget emitter has `useAsFilter: true` + `targets[]` in `filter-map`
- [ ] All widget `id` props are unique per page
- [ ] Filter-map and widget-map entries are combined before calling `setFilterMap`
