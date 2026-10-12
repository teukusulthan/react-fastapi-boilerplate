---
name: reactjs-dynamic-filter
description: Build recipe for a dynamic filter system on dashboard pages (module not present in the boilerplate yet — created at src/modules/dynamic-filter/). Covers all 6 filter types — URL filter, global-all, global-partial, nested/dependent, use-as-filter (widget-to-widget), exclude-self — and how resolved filters become backend FindDTO filters. Use when adding any filter widget, making a widget emit filters to others, or wiring a page to the filter store.
---

# Dynamic Filter Skill

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md` win over any markup here. This skill owns filter state (store, scopes, URL sync, FindDTO mapping) and filter interaction patterns. Every filter control is built from shadcn primitives (`Popover`, `Command`, `Select`, `RadioGroup`, `Checkbox`, `Switch`, `Slider`, `Calendar`, `Tooltip`, `Badge`) — never native `<select>`/checkbox or hand-built dropdowns.

> **Status: not present in the boilerplate yet.** `src/modules/dynamic-filter/` does not exist in
> `apps/web`. The first page that needs cross-widget filtering creates it at `src/modules/dynamic-filter/`
> following this recipe (structure below + `references/`). Until then, simple list pages keep their
> search/filter state in a feature hook that builds a memoized `FindDTO` (see
> `src/features/administrator/user/hooks/useUserListQuery.ts`) — don't build this module for one table.

Once created, every dashboard filter flows through one centralized Zustand store (zustand 5, `create<State>()(…)`,
not persisted — URL params are the shareable state). Read this skill completely before writing filter code.

> Detailed type specs → [references/filter-types.md](references/filter-types.md)
> Rules & anti-patterns → [references/filter-rules.md](references/filter-rules.md)

---

## Visual Conventions (filter appearance) — recommended baseline

These conventions come from a real production migration and are the default filter UX. Radius,
color and spacing come from `reactjs-ui-design`; a selected `design/` theme may only change token values.

### 1. Filter strip is part of the surface it filters, not its own box

On a list page the filters live in the `DataTableToolbar` at the top of the table card. On a dashboard
they sit in a toolbar row directly under the `PageHeader` on the page background. Either way: no extra
gray/boxed strip, a hairline border only where it separates content.

```tsx
// ✅ Dashboard filter row — page background, no box
<div className="flex flex-wrap items-center gap-2">{/* filter trigger + chips */}</div>

// ✅ Inside a table card — DataTable renders the toolbar row (with its border-b) for you
<DataTable
  …
  toolbar={<DataTableToolbar searchValue={search} onSearchChange={setSearch} filters={/* filter trigger + chips */} actions={/* reset */} />}
/>

// ❌ Avoid — filter strip as a gray card competing with the content (or a card inside the card)
<div className="rounded-xl border border-border bg-muted p-4"> … </div>
```

### 2. Option filters: collapsed trigger → dropdown, not a flat always-open list

A filter that picks from a list of options should render as a compact, collapsed trigger (e.g.
"All" / "N selected") that reveals its options in a popover on click. Avoid an always-visible flat
checkbox/radio list sitting open in the panel — it doesn't scale past a handful of options and clutters
the panel.

- Build (or reuse) one shared dropdown-select component for this across the app (shadcn `Popover` +
  `Command`) — do not reinvent a bespoke select per page.
- For long option lists (dozens+ of values — place names, usernames, categories), add type-to-search
  inside the popover, ideally auto-enabled past a threshold count rather than hand-rolled per instance.
- If an upstream config explicitly requests an inline radio/checkbox style for a specific filter,
  that's a legitimate override — honor it as an exception, not the default.
- **Selected options should DROP OUT of the list, not stay visible with a checkmark toggle.** This
  matches `react-select`'s default `hideSelectedOptions` for `isMulti` (the usual reference dropdown):
  once a value is picked it becomes a chip in the trigger and disappears from the option list
  entirely. A shadcn Command/Combobox-style "keep it visible, toggle a checkmark" pattern is a
  common default that reads as a visible fidelity gap next to such a reference — filter the
  rendered options by `!selected.includes(value)` rather than rendering a check icon.

### 2b. Date-range filters: collapsed box → nested two-level popover, never open text inputs

A date-range field should not render as two always-editable `Input type="text"` boxes with a
separate row of preset buttons below — that's noticeably "not quite matching" a typical BI-dashboard
reference even when every value works correctly. The reference shape:

- One collapsed, clickable box (`Button variant="outline"`): a `ph-calendar-blank` icon + the
  formatted range (or a placeholder like "Select dates") — never hand-typed.
- Clicking it opens a **first-level popover**: a single row of SHORT-CODE preset buttons —
  `T | W | M | Q | Y | ADV` — each with a hover tooltip spelling out the full name (Today, This
  Week, This Month, This Quarter, This Year, Advanced). Picking a non-`ADV` preset applies
  immediately and closes the popover.
- Picking `ADV` opens a **second, nested popover**: a left column of relative-date presets (Custom
  Date, Last 24 Hours, Last N days/months) + a right side with a (dual-month, for ranges) calendar,
  a time input per month, and Cancel/Apply Filter buttons. Use the shadcn `Calendar` (react-day-picker)
  inside a `Popover`; install it with the CLI if missing.

```tsx
// ✅ collapsed box → first popover (short codes + tooltip) → nested calendar popover on ADV
<Popover open={open} onOpenChange={setOpen}>
  <PopoverTrigger asChild>
    <Button variant="outline" className="justify-start font-normal">
      <i className="ph ph-calendar-blank text-muted-foreground" aria-hidden="true" />
      {formattedRangeOrPlaceholder}
    </Button>
  </PopoverTrigger>
  <PopoverContent align="start" className="flex w-auto gap-1 p-1">
    {presets.map((p) => (
      <Tooltip key={p.code}>
        <TooltipTrigger asChild><Button variant="ghost" size="sm" onClick={() => apply(p)}>{p.code}</Button></TooltipTrigger>
        <TooltipContent>{p.fullName}</TooltipContent>
      </Tooltip>
    ))}
    {/* ADV button opens a nested Popover here instead of applying directly */}
  </PopoverContent>
</Popover>

// ❌ Avoid — always-editable inputs, no collapsed/staged interaction
<Input value={dateFrom} onChange={...} /> <span>to</span> <Input value={dateTo} onChange={...} />
<div>{presets.map((p) => <Button onClick={() => apply(p)}>{p.fullName}</Button>)}</div>
```

### 3. Group all filters for a page into ONE panel behind a single trigger

Prefer a single `[ Filter {n} ⌄ ]` trigger that opens one staged panel containing every filterable
field for the page (date range, dimensions, etc.), with a shared Reset / Apply footer — over scattering
each field as its own always-visible control or a row of separate trigger buttons. This keeps the
toolbar compact and gives the user one predictable place to adjust all filtering.

- A store-driven generic filter bar naturally satisfies this if every field is registered with it.
- A page with a hand-built filter (no shared store) should still funnel all its fields into one
  trigger + panel, rather than exposing a second/third trigger alongside it — if a new field doesn't
  fit, add it to the panel instead of adding another toolbar control.
- **Don't hand-roll this from scratch if a reusable implementation already exists in the
  project.** Check `src/modules/` first (e.g. a filter-pill bar / filter-panel module created by an
  earlier page) and reuse/extend it instead of building a second implementation of the same pattern.
  Nothing like this exists in the boilerplate today — the first page builds it, generically, in
  `src/modules/`.
- The trigger's badge count should reflect the number of active field *groups*, not raw filter values.

### 4. Committed filters should show as chips beside the trigger, not just a count badge

A count badge on the trigger tells the user *how many* filters are active but not *what* they are.
Render one chip per committed filter next to the trigger so the current filter state is visible
without opening anything.

```tsx
// ✅ trigger + a chip per applied filter
<Button variant="outline" size="sm">
  <i className="ph ph-funnel-simple" aria-hidden="true" />Filter
  {n > 0 && <Badge variant="secondary" className="rounded-full px-1.5 tabular-nums">{n}</Badge>}
  <i className="ph ph-caret-down text-muted-foreground" aria-hidden="true" />
</Button>
{activeFilters.map((f) => (
  <Badge key={f.key} variant="outline" title={`${f.label}: ${f.value}`} className="gap-1 font-normal">
    <span className="text-muted-foreground">{f.label}:</span> {f.value}
  </Badge>
))}

// ❌ Avoid — only a count badge, no visibility into what's applied
<Button variant="outline">Filter <span>{activeCount}</span></Button>
```

- Chips must reflect **committed** filter state, never staged/in-progress panel state — they update
  only after Apply, not on every keystroke/click inside the panel.
- **Two legitimate chip philosophies — pick one deliberately, don't mix them:**
  - **App-UX default (this section's baseline):** chips are clickable (reopen the panel or, if you
    add it, remove that one field directly) and a categorical chip with multiple values can spell
    them out (`Platform: facebook, instagram`).
  - **Strict source-fidelity migration (matching an existing dashboard):** chips are **read-only info, not
    interactive** — no click handler, no remove ("×") affordance at all; clearing a field happens
    only by reopening the panel (or full Reset). A categorical ("is one of") chip never spells out
    the values — it's always `{field label} {circular count badge}`, even at exactly 1 selected
    value (don't collapse to `label: value` for a single selection). Give each chip an icon keyed
    by field kind (clock for dates, a text-glyph icon for free-text/keyword fields) instead of
    relying on label text alone. A field the source system treats as its own picker (e.g. a
    Topic/Account selector) gets its own trigger, never a duplicate entry in the generic chip row.
  - Whichever philosophy you pick, apply it consistently across every chip on the page — don't mix
    removable and read-only chips in the same bar.
- **The badge count is not always `chips.length`.** If a hidden field carries a permanent/default
  value with no UI control at all (a pinned tenant filter, an always-on exclude list), and the
  source system's own "how many filters are active" semantics count it too, the trigger badge can
  legitimately read higher than the number of chips actually rendered — verify what the count is
  *supposed* to mean (visible fields only, vs. every filter with a real value) before assuming a
  mismatch is a bug.

### 5. A text field's `style` is a two-way switch — check it per field, not once for the page

If an upstream filter config carries a `style` hint on a free-text field, it's picking between
**two editors**, not just occasionally flagging a special case: `style: "text-input"` (default) →
single-line `<Input>`; `style: "text-area"` + `rows: N` → an actual multi-line `<Textarea
rows={N}>`. A page can legitimately mix both — e.g. single-line category fields alongside a
multi-line free-text Query field — so read `style`/`rows` per field, don't assume one style covers
every text filter on the page.

---

## Stack (files you create)

| Layer | Library / File |
|-------|---------------|
| State | Zustand — create `src/modules/dynamic-filter/store/filter.store.ts` |
| Types | create `src/modules/dynamic-filter/types/filter.types.ts` |
| Hooks | `useResolvedFilterParams`, `useFilterEmitter`, `useUrlFilters` |
| HOC | `withFilterSupport` — create `src/modules/dynamic-filter/hoc/withFilterSupport.tsx` |
| Components | create `src/modules/dynamic-filter/components/` — 18 filter components, each a thin wrapper over a shadcn primitive (`Select`, `Popover`+`Command`, `RadioGroup`, `Checkbox`, `Switch`, `Slider`, `Calendar`, `Input`, `Textarea`) |
| Config | `{page}/config/{page}.filter-map.ts` per page |

---

## Module Structure

Not present in the boilerplate yet — create it at:

```
src/modules/dynamic-filter/
├── types/
│   ├── filter.types.ts         ← FilterState, FilterEvent, WidgetFilterConfig, WidgetFilterMap
│   └── index.ts
├── store/
│   └── filter.store.ts         ← Zustand: dispatch, resolve, clearFilterKey, reset, setFilterMap
├── hooks/
│   ├── use-url-filters.ts      ← sync URL → store on page load
│   ├── use-resolved-filters.ts ← useResolvedFilters, useResolvedFilterParams
│   └── use-filter-emitter.ts   ← useFilterEmitter: emit, emitMultiple, clear
├── hoc/
│   └── withFilterSupport.tsx   ← HOC: inject resolvedFilters into any widget
├── utils/
│   ├── filter.merge.ts         ← mergeFilters() — pure function
│   ├── filter.scope.ts         ← isApplicable() — pure function
│   └── filter.url.ts           ← parseUrlParams(), serializeToUrl()
├── components/
│   ├── Filter.tsx              ← Single select (global/partial)
│   ├── DependentFilter.tsx     ← Select whose options depend on another filter's value
│   ├── TextDebounce.tsx        ← Text input with debounce
│   ├── TagInput.tsx            ← Multi-tag input (Enter/comma)
│   ├── Radio.tsx               ← RadioGroup single select
│   ├── SelectAsync.tsx         ← Select with async fetch
│   ├── TreeSelect.tsx          ← Hierarchical tree select
│   ├── Checkbox.tsx            ← Multi-select via checkboxes
│   ├── MultiSelectStatic.tsx   ← Multi-select popover (static options)
│   ├── MultiSelectAsync.tsx    ← Multi-select popover (async fetch)
│   ├── Toggle.tsx              ← Boolean toggle (Switch)
│   ├── NumberInput.tsx         ← Single number input
│   ├── BetweenNumber.tsx       ← Min–Max number input pair
│   ├── Slider.tsx              ← Single value slider
│   ├── SliderRange.tsx         ← Range slider (min–max)
│   ├── DatePicker.tsx          ← Single date picker
│   ├── DateRange.tsx           ← Date range picker (from–to)
│   ├── RelativeDate.tsx        ← Relative date preset buttons (Today, Last 7 days, etc.)
│   └── index.ts                ← exports all components
└── index.ts                    ← public API: hooks, store, hoc, types
```

---

## 18 Filter Components — Quick Reference

| Component | Props Key | Emitted Value | Type |
|-----------|-----------|--------------|------|
| `Filter` | `filterKey` | `string` | Single select |
| `DependentFilter` | `filterKey`, `dependsOnKey` | `string` | Connected select |
| `TextDebounce` | `filterKey` | `string` | Text debounce |
| `TagInput` | `filterKey` | `string[]` | Multi-tag input |
| `Radio` | `filterKey` | `string` | RadioGroup |
| `SelectAsync` | `filterKey`, `fetchOptions` | `string` | Async select |
| `TreeSelect` | `filterKey`, `nodes` | `string` | Tree select |
| `Checkbox` | `filterKey` | `string[]` | Multi checkbox |
| `MultiSelectStatic` | `filterKey`, `options` | `string[]` | Multi select |
| `MultiSelectAsync` | `filterKey`, `fetchOptions` | `string[]` | Multi async |
| `Toggle` | `filterKey`, `valueOn`, `valueOff` | `boolean\|any` | Switch |
| `NumberInput` | `filterKey` | `number` | Number input |
| `BetweenNumber` | `filterKeyMin`, `filterKeyMax` | `number, number` | Min–Max input |
| `Slider` | `filterKey` | `number` | Single slider |
| `SliderRange` | `filterKeyMin`, `filterKeyMax` | `number, number` | Range slider |
| `DatePicker` | `filterKey` | `string (yyyy-MM-dd)` | Date picker |
| `DateRange` | `filterKeyFrom`, `filterKeyTo` | `string, string` | Date range |
| `RelativeDate` | `filterKeyFrom`, `filterKeyTo` | `string, string` | Preset date |

All components accept `config?: WidgetFilterConfig` prop for scope/targets.

If none of the 18 components fits the UI requirement, a new component may be added — see rules in [references/filter-rules.md](references/filter-rules.md).

---

## 6 Filter Types — Quick Reference

| # | Name | Component | scope | Target |
|---|------|-----------|-------|--------|
| 1 | URL Filter | `useUrlFilters()` | `all` | All widgets |
| 2 | Global → All | `Filter` | `all` | All widgets |
| 3 | Global → Partial | `Filter` | `partial` | Widgets in `targets[]` |
| 4 | Connect to Other Filter | `DependentFilter` + any component | `all`/`partial` | Per config |
| 5 | Use as Filter | `useFilterEmitter` inside widget | `partial` | Widgets in `targets[]` |
| 6 | Use as Filter (exclude self) | `useFilterEmitter` inside widget | `exclude-self` | All minus emitter |

---

## Step 1 — Create filter-map.ts

Every page that uses filters must have a `config/{page}.filter-map.ts`.

```ts
// src/pages/dashboard/config/dashboard.filter-map.ts
import { WidgetFilterMap } from '@/modules/dynamic-filter'

export const dashboardFilterMap: WidgetFilterMap = {

  // Type 2 — Global → All
  'filter-period': {
    scope: 'all',
  },

  // Type 3 — Global → Partial (specific widgets only)
  'filter-category': {
    scope: 'partial',
    targets: ['chart-revenue', 'table-orders'],
  },

  // Type 4 — Connected (options depend on filter-category)
  'filter-product': {
    scope: 'all',
  },

  // Type 5 — Use as Filter (table filters other charts)
  'table-orders': {
    useAsFilter: true,
    scope: 'partial',
    targets: ['chart-revenue', 'chart-trend'],
  },

  // Type 6 — Use as Filter (exclude self)
  'chart-region': {
    useAsFilter: true,
    scope: 'exclude-self',
    targets: ['chart-revenue', 'table-orders', 'chart-trend'],
  },
}
```

---

## Step 2 — Page Setup

```tsx
// src/pages/dashboard/DashboardPage.tsx
import { useEffect } from 'react'
import { useFilterStore, useUrlFilters } from '@/modules/dynamic-filter'
import { dashboardFilterMap } from './config/dashboard.filter-map'

export default function DashboardPage() {
  useUrlFilters()  // Type 1: sync URL params → store

  const setFilterMap = useFilterStore((s) => s.setFilterMap)
  useEffect(() => {
    setFilterMap(dashboardFilterMap)
    return () => setFilterMap({})  // cleanup on unmount
  }, [setFilterMap])

  return (/* ... */)
}
```

---

## Step 3 — Type 2 & 3: Filter (Global / Partial)

```tsx
// components you create in src/modules/dynamic-filter/components/ (recipe)
import { Filter } from '@/modules/dynamic-filter/components'

// Type 2 — scope: "all" → all widgets
<Filter
  id="filter-period"
  filterKey="period"
  options={[
    { label: 'January 2026', value: '2026-01' },
    { label: 'February 2026', value: '2026-02' },
  ]}
  config={dashboardFilterMap['filter-period']}
/>

// Type 3 — scope: "partial" → targets only
<Filter
  id="filter-category"
  filterKey="category"
  options={[
    { label: 'All', value: 'all' },
    { label: 'Electronics', value: 'electronics' },
    { label: 'Fashion', value: 'fashion' },
  ]}
  config={dashboardFilterMap['filter-category']}
/>
```

---

## Step 4 — Type 4: Connect to Other Filter (dependsOnKey)

One filter is "connected" to another — its value depends on and auto-resets when the referenced filter changes. This works with **any filter component**, not just `DependentFilter`.

**Example — 3-level chain (Province → District → Sub-district):**

```tsx
import { Filter, DependentFilter } from '@/modules/dynamic-filter/components'

// Provider — does not depend on anything
<Filter
  id="filter-province"
  filterKey="province"
  options={PROVINCE_OPTIONS}
  config={dashboardFilterMap['filter-province']}
/>

// Consumer of province, provider for sub-district
<DependentFilter
  id="filter-district"
  filterKey="district"
  dependsOnKey="province"           // connected to filter-province
  options={DISTRICT_OPTIONS}        // each option has dependsOnValue
  config={dashboardFilterMap['filter-district']}
/>

// Consumer of district
<DependentFilter
  id="filter-subdistrict"
  filterKey="subdistrict"
  dependsOnKey="district"           // connected to filter-district
  options={SUBDISTRICT_OPTIONS}
  config={dashboardFilterMap['filter-subdistrict']}
/>
```

**Auto-reset cascade:** Province changes → District resets → Sub-district resets automatically.

> Chains longer than 2 levels are allowed when there is a clear data hierarchy.
> For non-`DependentFilter` components, read the parent value from the store and pass it into `fetchOptions`.

---

## Step 5 — Type 5 & 6: Use as Filter (inside a widget)

Non-filter widgets (charts, tables, maps) that emit filters when the user interacts with them.

```tsx
import { useFilterStore, useFilterEmitter } from '@/modules/dynamic-filter'
import { dashboardFilterMap } from './config/dashboard.filter-map'

function TableOrdersWidget() {
  const activeOrderId = useFilterStore((s) =>
    s.globalFilters.find((f) => f.key === 'orderId')?.value as string | undefined
  )
  const clearFilterKey = useFilterStore((s) => s.clearFilterKey)

  const { emit } = useFilterEmitter({
    emitterId: 'table-orders',
    scope: dashboardFilterMap['table-orders'].scope,
    targets: dashboardFilterMap['table-orders'].targets,
  })

  function handleRowClick(orderId: string) {
    if (activeOrderId === orderId) clearFilterKey('orderId')
    else emit('orderId', orderId)
  }

  return (
    <div>
      {MOCK_ORDERS.map((order) => (
        <button
          key={order.id}
          type="button"
          aria-pressed={activeOrderId === order.id}
          onClick={() => handleRowClick(order.id)}
          className="flex w-full rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-muted/50 aria-pressed:bg-accent aria-pressed:text-accent-foreground"
        >
          {order.id} — {order.customer}
        </button>
      ))}
    </div>
  )
}
```

---

## Step 6 — Filter Receiver Widget

```tsx
import { useResolvedFilterParams } from '@/modules/dynamic-filter'

function ChartRevenueWidget() {
  const filters = useResolvedFilterParams('chart-revenue')
  // filters = { period: "2026-01", category: "electronics", orderId: "ORD-001" }

  // useQuery({ queryKey: ['revenue', filters], queryFn: () => revenueService.get(filters) })
  // For a POST /x/get-all endpoint, convert to FindDTO filters first — see "Bridging to the backend".

  return <div>chart with {JSON.stringify(filters)}</div>
}
```

**With HOC (optional):**

```tsx
import { withFilterSupport, WithFilterSupportProps } from '@/modules/dynamic-filter'

interface ChartProps extends WithFilterSupportProps {
  title: string
}

function ChartRevenue({ title, resolvedFilters }: ChartProps) {
  return <div>{title} — {JSON.stringify(resolvedFilters)}</div>
}

export const FilteredChartRevenue = withFilterSupport(ChartRevenue)

// Usage:
<FilteredChartRevenue widgetId="chart-revenue" title="Revenue" />
```

---

## Full Scenario Matrix

| Scenario | Emitter | Store | Receiver | Clear by |
|----------|---------|-------|----------|----------|
| URL load | `useUrlFilters()` | `urlFilters` | All widgets | Navigate away |
| Select Period | `Filter` scope `all` | `globalFilters` | All widgets | Select new value |
| Select Category | `Filter` scope `partial` | `globalFilters` | chart-revenue, table-orders | Select new value |
| Select Product | `DependentFilter` scope `all` | `globalFilters` | All widgets | Category changes → auto |
| Click Orders row | `useFilterEmitter` scope `partial` | `globalFilters` | chart-revenue, chart-trend | Click row again |
| Click Map region | `useFilterEmitter` scope `exclude-self` | `globalFilters` | All except map | Click region again |

---

## Bridging to the backend (FindDTO filters)

Resolved filter params are UI state. Backend list endpoints (`POST /<module>/get-all`) only accept the
`FindDTO` contract from `src/types/api.d.ts` (see `.claude/skills/reactjs-api-design/SKILL.md` §5): `filters`
is a list of `FilterItem { field, operator, value?: { is?, isOneOf?, gte?, lte? }, operatorType? }` with the
legacy operator vocabulary, on **backend-whitelisted camelCase fields only** (unknown field → 422).

Create the converter next to the store, keeping the mapping explicit per page (filter key → API field + operator):

```ts
// src/modules/dynamic-filter/utils/filter.to-find-dto.ts  (new file, part of this recipe)
import type { FilterItem, FilterOperator, FilterScalar } from '@/types/api'

export interface FilterFieldMapping {
  field: string                 // backend API field (camelCase, filterable whitelist)
  operator: FilterOperator      // 'is' | 'is one of' | 'is between' | 'is contains' | …
}

export function toFilterItems(params: Record<string, unknown>, mapping: Record<string, FilterFieldMapping>): FilterItem[] {
  const items: FilterItem[] = []
  for (const [key, raw] of Object.entries(params)) {
    const map = mapping[key]
    if (!map || raw === undefined || raw === null || raw === '') continue
    switch (map.operator) {
      case 'is one of':
      case 'is not one of':
      case 'all':
        items.push({ field: map.field, operator: map.operator, value: { isOneOf: ([] as FilterScalar[]).concat(raw as FilterScalar) } })
        break
      case 'is between':
      case 'is not between': {
        const [gte, lte] = raw as [FilterScalar, FilterScalar]
        items.push({ field: map.field, operator: map.operator, value: { gte, lte } })
        break
      }
      case 'greater than equals':
        items.push({ field: map.field, operator: map.operator, value: { gte: raw as FilterScalar } })
        break
      case 'less than equals':
        items.push({ field: map.field, operator: map.operator, value: { lte: raw as FilterScalar } })
        break
      case 'is exist':
      case 'is not exist':
        items.push({ field: map.field, operator: map.operator })
        break
      default: // is, is not, is contains, is not contains
        items.push({ field: map.field, operator: map.operator, value: { is: raw as FilterScalar } })
    }
  }
  return items
}
```

Receiver usage: `const query = useMemo<FindDTO>(() => ({ page, size, filters: toFilterItems(params, MAP) }), [page, size, params])`
→ `useQuery({ queryKey: KEYS.list(query), queryFn: () => service.getAll(query) })`. Dates go as ISO-8601 UTC
strings; values must be scalars or lists of scalars (objects are rejected).

---

## Hooks API Summary

```ts
// Consume filters in receiver widgets
useResolvedFilters(widgetId)        // → FilterState[]
useResolvedFilterParams(widgetId)   // → Record<string, unknown>

// Emit filters from a widget
useFilterEmitter({ emitterId, scope, targets })
  → { emit(key, value), emitMultiple(values), clear() }

// Sync URL → store (call at page level only)
useUrlFilters()

// Direct store actions
useFilterStore((s) => s.clearFilterKey(key))  // remove 1 key from all sources
useFilterStore((s) => s.reset(widgetId?))     // reset all or per widget
useFilterStore((s) => s.resolve(widgetId))    // same as useResolvedFilters
```

---

## Quick Rules

| Rule | Value |
|------|-------|
| Filter state | Zustand store — never `useState` |
| Read parent value | Directly from `globalFilters.find(key)` — never via `resolve()` |
| filter-map path | `src/pages/{page}/config/{page}.filter-map.ts` |
| filter-map register | Required in page component, cleanup on unmount |
| `scope: "partial"` | Must include `targets[]` |
| Toggle/deselect | Use `clearFilterKey(key)` — never dispatch empty |
| Active state (use-as-filter) | Read from store, not local state |
| URL filter | `useUrlFilters()` at page level only |
| Receiver widget | Always use `useResolvedFilterParams(widgetId)` |

> Full type specs: [references/filter-types.md](references/filter-types.md)
> Rules & checklist: [references/filter-rules.md](references/filter-rules.md)
