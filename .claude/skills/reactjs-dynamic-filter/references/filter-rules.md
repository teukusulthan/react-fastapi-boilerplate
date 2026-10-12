---
name: filter-rules-reference
description: Mandatory rules, anti-patterns, and decision checklist for the dynamic filter system.
---

# Dynamic Filter — Rules Reference

> The module is not present in the boilerplate yet — this is the target structure to create at
> `src/modules/dynamic-filter/` (see `../SKILL.md` § Status).

## File Structure (create it at)

```
src/modules/dynamic-filter/
├── types/
│   ├── filter.types.ts
│   └── index.ts
├── store/
│   └── filter.store.ts
├── hooks/
│   ├── use-url-filters.ts
│   ├── use-resolved-filters.ts
│   └── use-filter-emitter.ts
├── hoc/
│   └── withFilterSupport.tsx
├── utils/
│   ├── filter.merge.ts
│   ├── filter.scope.ts
│   └── filter.url.ts
├── components/
│   ├── Filter.tsx
│   ├── DependentFilter.tsx
│   ├── TextDebounce.tsx
│   ├── TagInput.tsx
│   ├── Radio.tsx
│   ├── SelectAsync.tsx
│   ├── TreeSelect.tsx
│   ├── Checkbox.tsx
│   ├── MultiSelectStatic.tsx
│   ├── MultiSelectAsync.tsx
│   ├── Toggle.tsx
│   ├── NumberInput.tsx
│   ├── BetweenNumber.tsx
│   ├── Slider.tsx
│   ├── SliderRange.tsx
│   ├── DatePicker.tsx
│   ├── DateRange.tsx
│   ├── RelativeDate.tsx
│   └── index.ts
└── index.ts

src/pages/{page}/
├── config/
│   └── {page}.filter-map.ts   ← scope & targets declaration per widget
└── {page}.tsx
```

---

## Mandatory Rules

### filter-map.ts

- ✅ Every page that uses filters **MUST** have a `config/{page}.filter-map.ts`
- ✅ All widgets that emit filters **MUST** be registered in the filter-map
- ✅ `targets[]` is required when `scope: "partial"` or `scope: "exclude-self"`
- ✅ Register the filter-map in the page with `useEffect` + cleanup:
  ```ts
  useEffect(() => {
    setFilterMap(dashboardFilterMap)
    return () => setFilterMap({})  // cleanup on page unmount
  }, [setFilterMap])
  ```
- ❌ Do not hardcode scope/targets directly in the component — always read from the filter-map

### Filter Components

- ✅ Import from `@/modules/dynamic-filter/components`
- ✅ Use `Filter` for standalone filters (global/partial single select)
- ✅ Use `DependentFilter` for filters that depend on another filter's value
- ✅ Always pass `config={filterMap['widget-id']}` to every filter component
- ❌ Do not use `useState` to store filter values in the component — everything goes through the store
- ❌ Do not add a `label` prop to filter components — titles are handled by the parent layout

**Adding a new filter component (optional):**
- ✅ **Prioritize the 18 available components** — check the full list in `SKILL.md` before creating a new one
- ✅ If the UI requirement is not covered by any existing component, a new one may be added
- ✅ New components go in `src/modules/dynamic-filter/components/`
- ✅ New components must use `useFilterEmitter` — they may not manage filter state themselves
- ✅ Register the export in `src/modules/dynamic-filter/components/index.ts`
- ✅ Update the component list in `SKILL.md` after adding a new component

### Connect to Other Filter (dependsOnKey)

- ✅ Read parent value directly from `globalFilters`/`urlFilters` — **never** via `resolve()`
- ✅ Always reset the child filter when the parent changes (`clearFilterKey(filterKey)` in `useEffect`)
- ✅ Every option in `DependentFilter` must have a `dependsOnValue` that matches the parent value
- ✅ Chains longer than 2 levels are allowed when there is a clear data hierarchy (e.g. Province → District → Sub-district)
- ✅ For non-`DependentFilter` components (e.g. `MultiSelectAsync`), read the parent value from the store at the page level and pass it to `fetchOptions`
- ❌ Do not use long chains for data without a clear hierarchy — use multi-select or independent filters instead
- ❌ Do not reset filters that do not depend on the changed filter

### Use as Filter Widget

- ✅ Implement toggle: clicking the same row/element again → `clearFilterKey(key)`
- ✅ Read `activeId` directly from `globalFilters` (not from local state)
- ✅ Use `scope: "partial"` + `targets[]` for specific targets, `scope: "exclude-self"` for all except self
- ❌ Do not store selected state in `useState` — it will go out of sync with the store when the filter is cleared externally

### Filter Receiver Widgets

- ✅ Backend list endpoints receive filters as `FindDTO.filters` (`FilterItem[]`) on whitelisted fields — convert with `toFilterItems()` (SKILL.md § Bridging to the backend)

- ✅ Use `useResolvedFilterParams(widgetId)` to get filters as a plain object
- ✅ Use `useResolvedFilters(widgetId)` if you need the full `FilterState[]`
- ✅ Use the `withFilterSupport(Component)` HOC to inject `resolvedFilters` via props
- ❌ Do not read `globalFilters` or `widgetFilters` directly from the store in receiver widgets — always use `resolve()`

### URL Filter

- ✅ Call `useUrlFilters()` once at the page level (not inside individual widgets)
- ✅ URL filters always have `scope: "all"` — they cannot be scoped to specific widgets
- ❌ Do not call `setUrlFilters` manually — only `useUrlFilters()` should do this

---

## Decision Tree — Choose a Filter Component

```
Need a new filter input?
│
├── Single select from a static list?
│   ├── Does not depend on another filter → Filter
│   └── Options depend on another filter → DependentFilter
│
├── Single select fetched from API (with search) → SelectAsync
│
├── Hierarchical / tree data → TreeSelect
│
├── Single select via radio buttons → Radio
│
├── Multi select?
│   ├── Static options → Checkbox or MultiSelectStatic
│   └── Options from API → MultiSelectAsync
│
├── Text input?
│   ├── Single text with debounce → TextDebounce
│   └── Multiple tags (Enter/comma) → TagInput
│
├── Boolean on/off → Toggle
│
├── Number?
│   ├── Single value input → NumberInput
│   ├── Min–Max input → BetweenNumber
│   ├── Single slider → Slider
│   └── Range slider → SliderRange
│
└── Date?
    ├── Single date → DatePicker
    ├── Date range (from–to) → DateRange
    └── Relative presets (Today, Last 7 days, etc.) → RelativeDate
```

If none of the 18 components fits the requirement, a new component may be created — see the **Adding a new filter component** rule above.

## Decision Tree — Choose a Filter Type (scope)

```
Need a new filter?
│
├── Filter comes from the URL on page load?
│   └── → Type 1: useUrlFilters() in the page, no extra config needed
│
├── Filter affects ALL widgets?
│   └── → Type 2: scope: "all" in filter-map
│
├── Filter affects SPECIFIC widgets only?
│   └── → Type 3: scope: "partial" + targets: [...] in filter-map
│
├── Filter options depend on the value of another filter?
│   └── → Type 4: DependentFilter + dependsOnKey (connect to other filter)
│       └── Should this filter also be partial?
│           ├── Yes → scope: "partial" + targets
│           └── No  → scope: "all"
│
├── A widget (chart/table/map) that filters other widgets when clicked?
│   └── → Type 5: useAsFilter: true + useFilterEmitter inside the widget
│       └── Specific targets? → scope: "partial" + targets
│           All except self?  → scope: "exclude-self"
│
└── Combination of multiple types?
    └── Register each in the filter-map with its own config
```

---

## Anti-Patterns

| ❌ Anti-Pattern | ✅ Correct Approach |
|---|---|
| `useState` for filter values in a component | All filter values live in the Zustand store |
| `resolve(emitterId)` to read a parent filter value | Read directly from `globalFilters.find(key)` |
| Missing `return () => setFilterMap({})` in useEffect | Always cleanup the filter-map on page unmount |
| `scope: "partial"` without `targets[]` | `targets[]` is required |
| Dispatch `filters: []` to clear | Use `clearFilterKey(key)` or `reset()` |
| Local filter state per widget | One store, all widgets subscribe |
| Long filter chains without a clear data hierarchy | Redesign as multi-select or step wizard |
| `label` prop on a filter component | Titles are handled by the parent layout (FilterSection, Card, etc.) |
| Importing filter internals from a feature folder | Import from the module's public `index.ts` (`@/modules/dynamic-filter` once created) |
| Filter strip as its own gray/boxed card | Filters live in the table card's `DataTableToolbar` or a plain toolbar row under `PageHeader` (see SKILL.md → Visual Conventions) |
| Flat always-visible checkbox/radio option list in a filter panel | Collapsed trigger → dropdown popover via one shared select component |
| Re-implementing a select dropdown per page | Reuse one shared dropdown-select component app-wide |
| Second/third filter trigger added next to the main one | Fold the new field into the single panel instead |

---

## Implementation Checklist

### When creating a new page with filters:
- [ ] Create `{page}/config/{page}.filter-map.ts` with all involved widgets
- [ ] Call `useUrlFilters()` at the page level
- [ ] Register the filter-map with `setFilterMap` + cleanup in `useEffect`
- [ ] Each receiver widget: `useResolvedFilterParams(widgetId)`
- [ ] Each filter component: pass `config={filterMap['id']}`

### When adding a new filter:
- [ ] Determine the filter type (1–6) using the scope decision tree
- [ ] Choose a filter component from the 18 available — check `SKILL.md` first
- [ ] If none fits, create a new component in `modules/dynamic-filter/components/` using `useFilterEmitter`
- [ ] Add an entry in `{page}/config/{page}.filter-map.ts`
- [ ] Verify `scope` and `targets` are correct
- [ ] Test: select a value → target widgets update, non-target widgets do not

### When adding a "use as filter" widget:
- [ ] Add `useAsFilter: true` in the filter-map
- [ ] Implement `useFilterEmitter` inside the widget
- [ ] Implement toggle (click again → clear)
- [ ] Read `activeId` from the store, not local state
- [ ] Add a visual indicator (highlight the active row/element)
