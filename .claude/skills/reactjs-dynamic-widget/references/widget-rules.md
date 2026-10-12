---
name: widget-rules-reference
description: Mandatory rules, anti-patterns, and implementation checklist for the dynamic-widget module.
---

# Dynamic Widget — Rules Reference

## File Structure

```
src/modules/dynamic-widget/
├── types/
│   └── widget.types.ts
├── adapters/
│   ├── default.adapter.ts
│   ├── chart.adapter.ts
│   ├── stat.adapter.ts
│   ├── table.adapter.ts
│   └── index.ts
├── hooks/
│   └── use-widget-data.ts
├── components/
│   ├── WidgetShell.tsx
│   ├── ChartWidget.tsx
│   ├── StatWidget.tsx
│   ├── ListWidget.tsx
│   ├── TableWidget.tsx
│   ├── CardGridWidget.tsx
│   ├── WordCloudWidget.tsx
│   └── DynamicWidget.tsx
└── index.ts

src/pages/{page}/
├── config/
│   ├── {page}.filter-map.ts    ← filter scope & targets
│   └── {page}.widget-map.ts   ← widget filter-listen config
└── {page}.tsx
```

---

## Mandatory Rules

### WidgetShell

- ✅ Every visible widget MUST be wrapped in `WidgetShell` — never build a custom frame/card
- ✅ Always pass `loading` and `error` props — never leave async states unhandled
- ✅ Use the `actions` slot for widget-level controls (export, refresh, settings)
- ✅ Use the `footer` slot for pagination or "X Total Data" — never put it inside children
- ❌ Do not create wrapper divs around `WidgetShell` just to add a border or shadow — use `WidgetShell` props
- ✅ `WidgetShell` is built on shadcn `Card` (`rounded-xl border-border bg-card shadow-xs`); loading = content-shaped skeletons, error = `Alert` + Retry, empty = `EmptyState` (visual rules: `reactjs-ui-design`)
- ❌ No cards inside the shell's content (no nested bordered boxes); separate inner groups with spacing or `Separator`

### ChartWidget

- ✅ One `ChartWidget` component handles all chart types via `chartType` config
- ✅ `ChartWidget` is an ECharts-only facade over `EChartWrapper`
- ✅ New chart variant → add a case inside `ChartWidget.tsx`
- ❌ Never create a separate file for a new chart type (e.g., `BarChart.tsx`, `LineChart.tsx`)
- ❌ Never introduce Recharts, Chart.js, ApexCharts, Nivo, Victory, or custom SVG/canvas chart implementations
- ❌ Never hardcode colors — use `options.colors` with the semantic chart tokens (`var(--chart-1)` … `var(--chart-5)`) or the theme palette from `useChartTheme`

### ListWidget

- ✅ One `ListWidget` component handles all list variants via `listType` config
- ✅ New list variant → add a case inside `ListWidget.tsx`
- ❌ Never create a separate file for a new list type

### Adapters

- ✅ All response transformation lives in `adapters/` — never inside a component or hook
- ✅ Add a new file in `adapters/` for a new non-standard response shape
- ✅ Name adapters after the widget type they serve: `chart.adapter.ts`, `stat.adapter.ts`
- ❌ Never call `.map()`, `.reduce()`, or shape-transform logic inside a component

### Data Fetching

- ✅ All API calls go through `use-widget-data` (for `DynamicWidget`) or a custom hook in the parent
- ✅ `use-widget-data` must call `useResolvedFilterParams(widgetId)` and re-fetch when filters change
- ❌ Never `fetch()` or `axios` directly inside a widget component
- ❌ Never use `useState` for fetched data inside a widget — use the hook return values

### widget-map.ts

- ✅ Every page with widgets that listen to filters MUST have `{page}/config/{page}.widget-map.ts`
- ✅ Merge `widget-map` into `filter-map` via `setFilterMap({ ...filterMap, ...widgetMap })`
- ✅ Add `listenGlobal: true` for widgets that respond to global filters
- ✅ Add `listenUrl: true` for widgets that respond to URL params
- ✅ Cleanup on unmount: `return () => setFilterMap({})` in `useEffect`
- ❌ Do not hardcode `listenGlobal`/`listenUrl` directly in the component — read from widget-map

---

## Anti-Patterns

| ❌ Anti-Pattern | ✅ Correct Approach |
|---|---|
| Custom card/frame instead of `WidgetShell` | Always use `WidgetShell` as the outer container |
| Separate `BarChart.tsx`, `LineChart.tsx` files | Add `chartType` case in single `ChartWidget.tsx` |
| `recharts` / `chart.js` / `apexcharts` inside a widget | Keep charts on `ChartWidget` backed by `EChartWrapper` |
| Response transform inside a component | Move logic to an adapter in `adapters/` |
| `fetch()` inside a widget component | Use `use-widget-data` or parent hook |
| `useState` for async data in a widget | Use hook return value `{ data, loading, error }` |
| Missing `loading` / `error` props on `WidgetShell` | Always handle both async states |
| Widget listening to filters without widget-map entry | Register in `{page}.widget-map.ts` |
| Hardcoded colors in chart options | Use `var(--chart-N)` tokens or `options.colors` |
| Importing adapters directly in components | Adapters are called only from `use-widget-data` |

---

## Implementation Checklist

### When adding a new widget to a page:

- [ ] Decide: `DynamicWidget` (auto-fetch) or `WidgetShell` + children (manual data)?
- [ ] Choose the correct inner component: `ChartWidget`, `StatWidget`, `ListWidget`, `TableWidget`, `CardGridWidget`, `WordCloudWidget`
- [ ] If widget listens to filters → add entry in `{page}.widget-map.ts`
- [ ] If using `DynamicWidget` → define `dataSource` with correct `adapter`
- [ ] If response is non-standard → add adapter in `adapters/` before using `DynamicWidget`
- [ ] Always pass `loading` and `error` to `WidgetShell`
- [ ] Test: filter changes → widget re-fetches with new params

### When adding a new chart type:

- [ ] Add a new `chartType` case inside `ChartWidget.tsx`
- [ ] Keep rendering on top of `EChartWrapper` only
- [ ] Add corresponding option types to `widget.types.ts`
- [ ] Update the chart options table in `SKILL.md`
- [ ] ❌ Do NOT create a new file

### When adding a new list variant:

- [ ] Add a new `listType` case inside `ListWidget.tsx`
- [ ] Add corresponding item type to `widget.types.ts`
- [ ] ❌ Do NOT create a new file

### When adding a new adapter:

- [ ] Create `{type}.adapter.ts` in `src/modules/dynamic-widget/adapters/`
- [ ] Export from `adapters/index.ts`
- [ ] Register the adapter key in `WidgetDataSource.adapter` type union in `widget.types.ts`
- [ ] Update adapter table in `SKILL.md`
