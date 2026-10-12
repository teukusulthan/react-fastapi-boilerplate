---
name: reactjs-dynamic-widget
description: Build config-driven dashboard widgets. Covers WidgetShell (children ReactNode), ECharts-based `ChartWidget`, StatWidget, ListWidget, TableWidget, CardGridWidget, WordCloudWidget, and DynamicWidget (auto-fetch). Use when adding any widget to a dashboard page, connecting widgets to the dynamic-filter system, or wiring a widget to an API endpoint.
---

# Dynamic Widget Skill

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md` win over any markup here. This skill owns config-driven widgets (data sources, adapters, filter subscription, widget registry).

> **When to use this module vs. the common patterns.** A simple dashboard (a few KPIs, a chart, a recent
> list — playbook §5.2) is built from `StatCard`, `SectionCard` / shadcn `Card` and `DataTable`; it does
> **not** need this module. Create `src/modules/dynamic-widget/` only when a page needs config-driven
> widgets (`DynamicWidget` auto-fetch, widget maps, cross-widget filters via `reactjs-dynamic-filter`).
> Once the module exists on a page, the rule below applies to that page.

> ⛔ **STOP — READ BEFORE WRITING ANY WIDGET CODE**
>
> If your task involves a **dashboard page built on `dynamic-widget`** and you are about to write any of the following — **stop immediately and read this skill first**:
>
> - A `<div>` that acts as a card, panel, or section with a title/header
> - Any component with its own border + title + content structure
> - A stat block, chart container, list panel, or anomaly/log feed
> - Any component named `*Panel`, `*Card`, `*Widget`, `*Section`, `*Feed`, `*Gauge`
>
> All of the above **must** use `WidgetShell` from `src/modules/dynamic-widget/components/WidgetShell.tsx` as their outer container. **Never build a custom frame.**
>
> `WidgetShell` itself is a thin layer over shadcn `Card` with the same anatomy as `SectionCard`
> (`rounded-xl border border-border bg-card shadow-xs`; header = `text-base font-semibold` title +
> `text-sm text-muted-foreground` subtitle/source + actions slot; content `p-6`, compact `p-4`).
> Loading = skeletons shaped like the content, error = inline `Alert variant="destructive"` + Retry,
> empty = `EmptyState`. `StatWidget` renders through `StatCard` (`components/common/StatCard.tsx`)
> rather than re-implementing the KPI tile.

> **Status in this boilerplate:** `src/modules/dynamic-widget/` and `src/modules/dynamic-filter/` are **not present yet** — this skill is the build recipe; create the module at `apps/web/src/modules/dynamic-widget/` with the structure below (charts need `EChartWrapper`, see `reactjs-chart`; filters see `reactjs-dynamic-filter`). Wire `use-widget-data` to the real API layer: endpoint constants in `src/services/api-endpoints.ts`, requests through `apiRequests` (`src/services/api-factory.service.ts`) or `createResourceService` (`src/services/api-factory-crud.service.ts`) — services return unwrapped `data`, list endpoints an `ApiList<T>` = `{ items, pagination }`, caching via TanStack Query (`reactjs-tanstack-query`), errors as `ApiError` (`src/services/api-error.ts`). Backend list endpoints are `POST /x/get-all` with a `FindDTO` body (`page`, `size`, `search`, `searchBy`, `orderBy`, `order`, `filters`).

Every widget in a dashboard page is built from this module. Read this skill completely before writing any widget-related code.

Any widget that renders chart data must use `ChartWidget`, and `ChartWidget` must render through `EChartWrapper` from `.claude/skills/reactjs-chart/SKILL.md`. Do not introduce Recharts, Chart.js, ApexCharts, Nivo, Victory, or standalone SVG chart components inside `dynamic-widget`.

> Rules & anti-patterns → [references/widget-rules.md](references/widget-rules.md)
> Type specs → [references/widget-types.md](references/widget-types.md)
> Filter integration → [references/filter-widget-integration.md](references/filter-widget-integration.md)

---

## When This Skill Applies

Load this skill whenever you encounter any of these patterns in a task:

| Task keyword / pattern                                                      | Action                                  |
| --------------------------------------------------------------------------- | --------------------------------------- |
| "dashboard" + any section/widget                                            | Load this skill **before any code**     |
| Component named `*Panel`, `*Widget`, `*Card`, `*Feed`, `*Gauge`, `*Section` | Wrap in `WidgetShell`                   |
| A box with a title header + content body                                    | Use `WidgetShell`, not a custom `<div>` |
| Chart, stat number, list, table, progress bar inside a dashboard            | Use the matching inner component        |
| Any `border p-3` / `border px-4 py-2.5` pattern on a dashboard              | Replace with `WidgetShell` (or `SectionCard`/`StatCard` when the page doesn't use this module) |

---

## Stack

| Layer      | Library / File                                               |
| ---------- | ------------------------------------------------------------ |
| State      | Zustand — `src/modules/dynamic-widget/store/widget.store.ts` |
| Types      | `src/modules/dynamic-widget/types/widget.types.ts`           |
| Hooks      | `useWidgetData` — fetch + filter subscription                |
| Adapters   | `src/modules/dynamic-widget/adapters/` — response transform  |
| Components | `src/modules/dynamic-widget/components/` — 7 components      |
| Config     | `{page}/config/{page}.widget-map.ts` per page                |

---

## Module Structure

```
src/modules/dynamic-widget/
├── types/
│   └── widget.types.ts         ← WidgetConfig, WidgetType, WidgetDataSource, all options types
├── adapters/
│   ├── default.adapter.ts      ← extract data via dataKey, no transform
│   ├── chart.adapter.ts        ← response → { labels[], datasets[] }
│   ├── stat.adapter.ts         ← response → { value, breakdown[] }
│   ├── table.adapter.ts        ← response → { rows[], total }
│   └── index.ts
├── hooks/
│   └── use-widget-data.ts      ← fetch + subscribe to filter changes → { data, loading, error }
├── components/
│   ├── WidgetShell.tsx          ← primary container over shadcn Card: title, footer, loading, error, children ReactNode
│   ├── ChartWidget.tsx          ← ECharts-only bar/line/pie/gauge/area via chartType config
│   ├── StatWidget.tsx           ← metric KPI (via common StatCard) + optional proportion breakdown
│   ├── ListWidget.tsx           ← progress/alert/checklist/ranked via listType config
│   ├── TableWidget.tsx          ← column config → `DataTable` from `@/modules/data-table` + footer total
│   ├── CardGridWidget.tsx       ← card grid: news/statement via template config
│   ├── WordCloudWidget.tsx      ← keyword cloud weighted by value
│   └── DynamicWidget.tsx        ← resolver: picks component from widgetType + injects data
└── index.ts
```

---

## 7 Components — Quick Reference

| Component         | Config Key              | Variants / Options                                                                 |
| ----------------- | ----------------------- | ---------------------------------------------------------------------------------- |
| `WidgetShell`     | —                       | `title`, `subtitle`, `source`, `loading`, `error`, `actions`, `footer`, `children` |
| `ChartWidget`     | `chartType`             | ECharts-only `'bar'` `'line'` `'pie'` `'gauge'` `'area'`                           |
| `StatWidget`      | `layout`                | `'single'` `'proportion'`                                                          |
| `ListWidget`      | `listType`              | `'progress'` `'alert'` `'checklist'` `'ranked'`                                    |
| `TableWidget`     | `columns[]`             | `showFooter`, `showPagination`, `showAvatar`, `totalRows`                          |
| `CardGridWidget`  | `template`              | `'news'` `'statement'`                                                             |
| `WordCloudWidget` | `weightKey`, `labelKey` | `colorRange`                                                                       |

Use `DynamicWidget` when data is fetched from API. Use `WidgetShell` directly when data comes from the parent or a custom hook.

---

## Decision Tree

```
Need a new widget?
│
├── Data fetched from API automatically?
│   ├── Yes → DynamicWidget (config-driven, auto-fetch)
│   └── No  → WidgetShell + children (data from parent/hook)
│
├── Content type?
│   ├── Single metric / KPI number   → StatWidget
│   ├── Chart                        → ChartWidget (ECharts via `EChartWrapper`)
│   │   ├── Bar (vertical/horizontal/stacked) → chartType: 'bar'
│   │   ├── Line (single/multi-series)        → chartType: 'line'
│   │   ├── Pie / donut                       → chartType: 'pie'
│   │   ├── Circular score/gauge              → chartType: 'gauge'
│   │   └── Area                              → chartType: 'area'
│   ├── List                         → ListWidget
│   │   ├── Items with progress bars → listType: 'progress'
│   │   ├── Items with severity badge→ listType: 'alert'
│   │   ├── Checkable items          → listType: 'checklist'
│   │   └── Numbered ranked items    → listType: 'ranked'
│   ├── Data table                   → TableWidget
│   ├── Grid of cards                → CardGridWidget
│   │   ├── News articles            → template: 'news'
│   │   └── Statements / quotes      → template: 'statement'
│   ├── Word / keyword cloud         → WordCloudWidget
│   └── Mixed / custom content       → WidgetShell + children ReactNode
│
└── API response non-standard?
    ├── Yes → add new adapter in adapters/
    └── No  → use adapter: 'default' + dataKey
```

---

## Step 1 — Create widget-map.ts (pages with filter + widget)

Required when widgets on the page need to receive filters from `dynamic-filter`.

```ts
// src/pages/dashboard/config/dashboard.widget-map.ts
import { WidgetFilterMap } from "@/modules/dynamic-filter";

export const dashboardWidgetMap: WidgetFilterMap = {
  "exposure-trend": { listenGlobal: true, listenUrl: true },
  "sentiment-chart": { listenGlobal: true },
  "top-influencer": { listenGlobal: true },
  "statement-cards": { listenGlobal: false }, // only receives from top-influencer
};
```

Register this map alongside the filter-map in the page component:

```tsx
useEffect(() => {
  setFilterMap({ ...dashboardFilterMap, ...dashboardWidgetMap });
  return () => setFilterMap({});
}, [setFilterMap]);
```

---

## Step 2 — WidgetShell (manual data / custom content)

Use when you control the data source yourself or need custom children.

```tsx
import { WidgetShell } from "@/modules/dynamic-widget/components";

<WidgetShell
  title="Top Influencer"
  subtitle="10.000 Total Data"
  source="Mainstream Media"
  loading={isLoading}
  error={error?.message}
  actions={<Button size="sm">Export</Button>}
>
  <InfluencerList data={data} />
</WidgetShell>;
```

Two widgets sharing one layout, each with its own shell:

```tsx
<div className="grid gap-6 xl:grid-cols-2">
  <WidgetShell title="Top Influencer" source="Mainstream Media">
    <InfluencerList data={influencers} />
  </WidgetShell>

  <WidgetShell title="Influencer Statements" source="Mainstream Media">
    <StatementCardGrid data={statements} />
  </WidgetShell>
</div>
```

---

## Step 3 — DynamicWidget (auto-fetch from API)

Use when the widget fetches its own data. Filters are injected automatically.

```tsx
import { DynamicWidget } from "@/modules/dynamic-widget/components";

<DynamicWidget
  id="exposure-trend"
  widgetType="chart"
  title="Exposure Trend"
  source="Mainstream Media"
  dataSource={{
    type: "api",
    endpoint: "/analytics/exposure",
    dataKey: "data.items",
    adapter: "chart",
    params: { limit: 100 },
  }}
  options={{
    chartType: "bar",
    xKey: "time",
    yKey: "count",
  }}
/>;
```

Filters from `dynamic-filter` are auto-merged into `params` based on `id`.

---

## Step 4 — ChartWidget Options

`ChartWidget` is the dashboard-facing facade for ECharts. Keep chart-library concerns inside `ChartWidget` + `EChartWrapper`; callers only provide widget config and data.

```tsx
<ChartWidget
  chartType="bar"
  data={data}
  options={{
    orientation: "vertical", // 'vertical' | 'horizontal'
    stacked: false,
    multiSeries: false,
    xKey: "label",
    yKey: "value",
    seriesKey: "category", // for multiSeries
    colors: ["var(--chart-1)", "var(--chart-2)"], // semantic chart tokens; omit to use the theme palette
  }}
/>
```

| chartType | Extra options                                   |
| --------- | ----------------------------------------------- |
| `'bar'`   | `orientation`, `stacked`, `multiSeries`         |
| `'line'`  | `multiSeries`, `smooth`                         |
| `'pie'`   | `donut`, `showLegend`                           |
| `'gauge'` | `min`, `max`, `thresholds` (for severity label) |
| `'area'`  | `multiSeries`, `smooth`                         |

---

## Step 5 — StatWidget Options

```tsx
// layout: 'single'
<StatWidget value={44468} label="News" layout="single" />

// layout: 'proportion'
<StatWidget
  value={44590}
  label="Total Data"
  layout="proportion"
  breakdown={[
    { label: 'Positive', value: 18360, percentage: 41, color: '#22c55e' },
    { label: 'Neutral',  value: 16630, percentage: 37, color: '#94a3b8' },
    { label: 'Negative', value: 9600,  percentage: 22, color: '#ef4444' },
  ]}
/>
```

---

## Step 6 — ListWidget Options

```tsx
// listType: 'progress'
<ListWidget
  listType="progress"
  items={[
    { label: 'Toksisitas & Paparan', value: 48, max: 100, meta: 'Diatas 23%' },
    { label: 'Kuantitas Pelepasan',  value: 30, max: 100 },
  ]}
/>

// listType: 'alert'
<ListWidget
  listType="alert"
  items={[
    { severity: 'high',   text: 'Siapkan antidot...', source: 'Chlorine' },
    { severity: 'medium', text: 'Monitor konsentrasi...', source: 'General' },
  ]}
/>

// listType: 'checklist'
<ListWidget
  listType="checklist"
  items={[
    { severity: 'medium', text: 'Aktifkan sirine dan notifikasi publik', checked: false },
  ]}
  onCheck={(index, checked) => { /* handler */ }}
/>
```

---

## Step 7 — Widget as Filter Emitter (inter-widget filter)

A widget that filters another widget when the user interacts with it.

```tsx
import { useFilterEmitter } from "@/modules/dynamic-filter";
import { dashboardFilterMap } from "./config/dashboard.filter-map";

function TopInfluencerWidget({ data }: { data: Influencer[] }) {
  const { emit, clear } = useFilterEmitter({
    emitterId: "top-influencer",
    scope: dashboardFilterMap["top-influencer"].scope,
    targets: dashboardFilterMap["top-influencer"].targets,
  });

  return (
    <WidgetShell title="Top Influencer" source="Mainstream Media">
      {data.map((item) => (
        <TableRow key={item.id} onClick={() => emit("influencerId", item.id)} />
      ))}
    </WidgetShell>
  );
}
```

Receiver widget using `DynamicWidget` — filters are injected automatically via `id`:

```tsx
<DynamicWidget
  id="statement-cards"
  widgetType="card-grid"
  title="Influencer Statements"
  dataSource={{ type: "api", endpoint: "/statements", adapter: "default" }}
  options={{ template: "statement", cols: 2 }}
/>
```

---

## Adapter Layer

| Adapter         | Use when                                                         |
| --------------- | ---------------------------------------------------------------- |
| `'default'`     | Response shape matches widget input — just extract via `dataKey` |
| `'chart'`       | Response needs transform to `{ labels[], datasets[] }`           |
| `'stat'`        | Response needs transform to `{ value, breakdown[] }`             |
| `'table'`       | Response needs transform to `{ rows[], total }`                  |
| `(raw) => data` | Fully custom shape — pass a transform function                   |

Custom adapter: add a new file in `src/modules/dynamic-widget/adapters/` — never transform inside the component.

---

## Hooks API Summary

```ts
// Auto-fetch with filter subscription (used internally by DynamicWidget)
useWidgetData(widgetId, dataSource)
  → { data, loading, error, refetch }

// Read resolved filters for a widget (from dynamic-filter module)
useResolvedFilterParams(widgetId)   // → Record<string, unknown>
useResolvedFilters(widgetId)        // → FilterState[]
```

---

## Quick Rules

| Rule                  | Value                                                                    |
| --------------------- | ------------------------------------------------------------------------ |
| Widget container      | Always `WidgetShell` — never build a custom frame                        |
| Chart implementation  | Always `ChartWidget` → `EChartWrapper` (ECharts only)                    |
| New chart variant     | Add `chartType` case in `ChartWidget` — never new file                   |
| New list variant      | Add `listType` case in `ListWidget` — never new file                     |
| Non-standard response | Add adapter in `adapters/` — never transform inside component            |
| Data fetching         | Only in `use-widget-data` or parent hook — never inside widget component |
| Filter listening      | Register widgetId in `setFilterMap` at page level                        |
| widget-map.ts path    | `src/pages/{page}/config/{page}.widget-map.ts`                           |

> Full rules & checklist: [references/widget-rules.md](references/widget-rules.md)
> Type specs: [references/widget-types.md](references/widget-types.md)
> Filter ↔ Widget integration: [references/filter-widget-integration.md](references/filter-widget-integration.md)
