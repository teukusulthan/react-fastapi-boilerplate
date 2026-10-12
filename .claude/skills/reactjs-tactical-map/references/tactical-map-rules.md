# Tactical Map — Rules (Domain Override)

**Base rules:** `skills/map/references/map-rules.md` — all general map rules apply here. This file documents tactical-specific terminology, naming conventions, and overrides only.

---

# Tactical Map — Rules

## 1. Two-Layer Architecture — Primitives vs Domain

Tactical map config is split into two mandatory layers. Never merge them.

| Layer | Location | Contains | Reusable |
|-------|----------|----------|----------|
| **Map Primitives** | `src/config/map/` | Marker shapes, paint properties, base styles | ✅ Any page |
| **Domain Registry** | `src/features/tactical/config/` | Layer list, incident types, tactical-specific mapping | ❌ Tactical only |

### Primitive files

```
src/config/map/
├── marker-styles.config.ts   ← MARKER_STYLES keyed by MarkerSeverity
├── layer-paint.config.ts     ← LAYER_PAINT presets (fill, circle, line, heatmap)
└── map-styles.config.ts      ← base Mapbox style URL presets
```

### Domain registry files

```
src/features/tactical/config/
├── layers.config.ts          ← TACTICAL_LAYERS, TACTICAL_LAYERS_BY_GROUP, DEFAULT_LAYER_VISIBILITY
├── incident-types.config.ts  ← INCIDENT_TYPES keyed by IncidentType
└── index.ts                  ← barrel export
```

---

## 2. Layer Registry Rules

### ✅ Mandatory

| Rule | Reason |
|------|--------|
| Every layer MUST have an entry in `TACTICAL_LAYERS` | Single source of truth — LayerPanel and TacticalMap both loop this array |
| `mapLayerId` must be globally unique across the entire map instance | Duplicate IDs cause Mapbox GL runtime errors |
| `group` must be one of the `LayerGroup` union values | Controls how LayerPanel renders sections |
| `defaultVisible` must be explicitly declared | Never assume visibility — store init reads this |
| `markerStyle` references `MARKER_STYLES[severity]` — never inline object | Keeps visual consistency across all markers |
| `paint` references `LAYER_PAINT[preset]` — never inline object | Reuses defined presets, easy to retheme |
| `isGeoJson: true` for polygon/line layers | Signals TacticalMap to add GeoJSON source, not marker |

### ❌ Forbidden

| Pattern | Reason |
|---------|--------|
| ❌ Adding a layer directly in `TacticalMap.tsx` without registry entry | Breaks LayerPanel sync — user can't toggle it |
| ❌ Hardcoding `mapLayerId` string anywhere except `layers.config.ts` | String drift causes silent bugs |
| ❌ Inline paint object in component code | Duplicates config, inconsistent theming |
| ❌ Using `TACTICAL_LAYERS` outside `@/features/tactical` barrel | Always import from barrel, not internal paths |

---

## 3. Marker System Rules

### ✅ Mandatory

| Rule | Reason |
|------|--------|
| All marker colors use CSS variables from status tokens — `var(--color-destructive)`, `var(--color-warning)`… | Theme swap (light/dark, Tactical theme) works automatically |
| `pulse: true` only for `critical` and `alert` severity | Visual hierarchy — not everything should blink |
| Marker size follows severity scale: critical(32) > alert(28) > normal(24) > info(20) > offline(20) | Clear visual priority at a glance |
| Custom marker HTML rendered via `createRoot` — never `innerHTML` direct manipulation | React-managed lifecycle, no memory leaks |
| Markers cleaned up in `useEffect` return when incidents change | Prevents stale markers on map |

### ❌ Forbidden

| Pattern | Reason |
|---------|--------|
| ❌ `new mapboxgl.Marker({ color: '#ff0000' })` with hardcoded hex | Must use `MARKER_STYLES[severity].color` |
| ❌ `marker.setPopup(new mapboxgl.Popup().setHTML(rawUserContent))` | XSS risk — sanitize or use React portal |
| ❌ Calling `marker.addTo(map)` outside `useEffect` | Race condition with map load state |
| ❌ Storing raw `mapboxgl.Marker[]` in Zustand | DOM objects in store cause serialization errors |

---

## 4. Panel Store Contract Rules

Panels are pure UI components — they read from stores and write to stores. They never control the map directly.

### ✅ Mandatory

| Rule | Reason |
|------|--------|
| Panel open/closed state lives in `useLayerStore` or a dedicated `usePanelStore` — not local `useState` | Multiple components can toggle a panel |
| `LayerPanel` reads only `TACTICAL_LAYERS_BY_GROUP` and `useLayerStore` — no other imports | Panel must not know about incidents or sensors |
| `LiveFeedPanel` reads only `useSensorStore` and `useIncidentStore.selectedId` — no map imports | Panel must not directly control the map |
| `IncidentPopup` reads only `useIncidentStore.selectedId` and `INCIDENT_TYPES` | Popup must not fetch data — it reads from store |

### ❌ Forbidden

| Pattern | Reason |
|---------|--------|
| ❌ Panel components calling `mapRef.current?.flyTo()` directly | Map control belongs to `TacticalMap` only |
| ❌ Panel components importing from `mapbox-gl` | Panels are pure UI — map concerns stay in wrappers |
| ❌ Cross-panel imports (LayerPanel importing from LiveFeedPanel) | Panels are independent — communicate via store |

> For layout rules (positioning, z-index, shell) → read `.claude/skills/reactjs-app-layout/SKILL.md` and
> `.claude/skills/reactjs-map/references/map-rules.md` § Container & frame contract

---

## 5. Store Contract Rules

Three stores, strict scope boundaries:

### `useLayerStore`

```
Owns: layer visibility state
Reads by: LayerPanel, TacticalMap
Writes by: LayerPanel (user toggle)
Does NOT own: incident data, sensor data, panel state
```

### `useIncidentStore`

```
Owns: incidents[], selectedId
Reads by: TacticalMap (marker rendering), IncidentPopup, LiveFeedPanel (highlight)
Writes by: TacticalMap (map click → select), LiveFeedPanel (row click → select)
Does NOT own: sensor readings, layer visibility
```

### `useSensorStore`

```
Owns: readings[], feed[], overallStatus
Reads by: LiveFeedPanel, TacticalMap (sensor markers)
Writes by: data source hook (WebSocket / mock interval)
Does NOT own: selected incident, layer state
```

### ✅ Mandatory

| Rule | Reason |
|------|--------|
| Each store owns exactly its declared scope above | Prevents cross-store coupling |
| `selectedId` is a `string | null` in `useIncidentStore` — the one source of "what is focused" | All panels sync to this single value |
| `overallStatus` in `useSensorStore` is derived from `readings[]` — never set manually | Computed, not managed state |
| Store selectors are granular — `useIncidentStore((s) => s.selectedId)` not `useIncidentStore()` | Prevents unnecessary re-renders |

### ❌ Forbidden

| Pattern | Reason |
|---------|--------|
| ❌ Storing `mapboxgl.Map` instance in any Zustand store | DOM objects break store serialization |
| ❌ Fetching data inside a store action | Data fetching belongs in hooks, not stores |
| ❌ One store importing another store | Creates circular dependency — use composition in components |
| ❌ Server response data stored directly in Zustand | Use React Query for server state; Zustand for UI state only |

---

## 6. Data Source Rules

Three source types exist. Each has a distinct contract — never mix their patterns.

### Source Type Contracts

| Type | Who fetches | Data flows through | Registered in |
|------|-------------|-------------------|---------------|
| `rest` | React (`useRestSource`) | `map.getSource().setData()` | `useTacticalDataSources` hook |
| `websocket` | React (`useWebSocketSource`) | `map.getSource().setData()` (incremental) | `useTacticalDataSources` hook |
| `mvt` | **Mapbox GL JS directly** | **Never touches React or Zustand** | `TacticalMap onLoad()` only |

### ✅ Mandatory

| Rule | Reason |
|------|--------|
| Every layer with external data declares `dataSource` in `layers.config.ts` | Single config entry drives all adapter wiring automatically |
| `useTacticalDataSources(mapRef)` called once in `TacticalMap` | Orchestrator reads the registry — no per-layer wiring in components |
| `registerMvtSource()` called only inside `onLoad` callback | Mapbox vector source must be added while style is loading |
| REST polling uses `AbortController` — aborted on cleanup | Prevents stale response applying after unmount |
| WebSocket cleanup sets `ws.onclose = null` before `ws.close()` | Prevents reconnect loop on intentional unmount |
| WebSocket `updateStrategy: 'append'` always sets `maxFeatures` | Unbounded append causes DOM memory growth |
| `updateStrategy: 'upsert'` requires features to have stable `feature.id` | Upsert deduplicates by id — missing id causes duplicates |
| MVT layers never write to Zustand | Mapbox owns MVT data — no parallel state needed |

### ❌ Forbidden

| Pattern | Reason |
|---------|--------|
| ❌ `fetch()` or `new WebSocket()` inside a component directly | Use adapters — `useRestSource` / `useWebSocketSource` |
| ❌ Opening WebSocket inside a store action | Store actions are synchronous — async belongs in hooks |
| ❌ Writing MVT tile data to Zustand | Mapbox owns the lifecycle — never duplicate it in React |
| ❌ `registerMvtSource()` called outside `onLoad` | Map style not ready — silent failure |
| ❌ `setInterval` without cleanup return | Memory leak on unmount |
| ❌ REST fetch without `AbortController` | Stale responses apply to wrong map state |
| ❌ WebSocket without reconnect strategy declaration | Explicit `reconnect: 'none'` if reconnect is intentionally off |
| ❌ Calling `useTacticalDataSources` more than once | One orchestrator per map instance |

### File Locations

```
src/features/tactical/
├── sources/
│   ├── rest.source.ts          ← useRestSource adapter
│   ├── websocket.source.ts     ← useWebSocketSource adapter
│   ├── mvt.source.ts           ← registerMvtSource (pure function, not a hook)
│   └── index.ts
└── hooks/
    └── useTacticalDataSources.ts  ← orchestrator — reads TACTICAL_LAYERS, wires adapters
```

---

## 7. TacticalMap — The Bridge Rules

`TacticalMap.tsx` is the only component allowed to have both store access and Mapbox GL imperative calls.

### ✅ Mandatory

| Rule | Reason |
|------|--------|
| One `useEffect` per concern — layer sync, marker sync, selection flyTo are separate effects | Prevents side effect entanglement |
| Layer visibility sync: `useEffect([layers])` → `map.setLayoutProperty()` | Reactive to store, declarative |
| Marker sync: `useEffect([incidents])` → remove old markers, add new | Full replace on every change |
| Selection sync: `useEffect([selectedId])` → `map.flyTo()` | Smooth transition on selection change |
| All Mapbox layer registration happens inside `onLoad` callback | Map must be ready before adding layers |
| Layers registered in `TACTICAL_LAYERS` order — iterate the registry, never hardcode | Adding new layer = add to config only |

### ❌ Forbidden

| Pattern | Reason |
|---------|--------|
| ❌ `map.addLayer()` called outside `onLoad` | Map not ready — silent failure or crash |
| ❌ Business logic inside `onLoad` callback | `onLoad` only registers layers — logic belongs in hooks |
| ❌ Calling `map.setLayoutProperty()` for a layer not in registry | Registry is the source of truth |
| ❌ `TacticalMap` importing from `LayerPanel` or `LiveFeedPanel` | One-way data flow only — stores mediate everything |

---

## 8. Design System Rules for Tactical UI

> Visual rules: `.claude/skills/reactjs-ui-design/SKILL.md`. Tactical panels use the same primitives and
> semantic classes as the rest of the app; a Tactical `design/` theme (if one is active) only changes the
> token values.

### ✅ Mandatory

| Rule | Reason |
|------|--------|
| Panel chrome: shadcn primitives + `bg-card border-border rounded-xl shadow-md` (floating) | One visual language across the app |
| Severity colors from status tokens — `var(--color-destructive)`, `var(--color-warning)`, `var(--color-success)`, `var(--color-info)`; badges via `StatusBadge` | Consistent across markers, badges, feed entries |
| Monospace (`font-mono tabular-nums`) for sensor readings and coordinates | Readability of rapidly-changing numeric values |
| UI chrome uses the token font-family (Inter) — `font-mono` only for readings | Follows design system contract |
| Only when the active `design/` theme is Tactical: its DESIGN.md token values (dark-first) are applied in `variable.css` | Theme lives in tokens, not in component classes |

### ❌ Forbidden

| Pattern | Reason |
|---------|--------|
| ❌ Hardcoded hex colors in any tactical component | Defeats theming |
| ❌ Glassmorphism / semi-transparent blurred panels (unless the active Tactical DESIGN.md specifies them) | Not part of the visual direction; hurts legibility |
| ❌ Text below `text-muted-foreground` contrast in panels | Readability requirement for operational use |

---

## Quick Forbidden Summary

| Violation | Rule |
|-----------|------|
| Layer added to map without `TACTICAL_LAYERS` entry | Layer registry is mandatory |
| Marker with hardcoded hex color | Use `MARKER_STYLES[severity].color` |
| Panel calling `mapRef.flyTo()` directly | Only `TacticalMap` controls the map |
| Panel importing from `mapbox-gl` | Panels are pure UI |
| Cross-panel imports | Panels communicate only via store |
| Store containing `mapboxgl.Map` instance | DOM objects not allowed in store |
| `overallStatus` set manually instead of derived | Must be computed from `readings[]` |
| `setInterval` without `useEffect` cleanup | Memory leak |
| Feed array growing without cap | Unbounded DOM growth |
| `map.addLayer()` outside `onLoad` | Map not ready |
| Tactical component using raw hex / Tailwind palette colors | Use semantic + status tokens |
| `fetch()` / `new WebSocket()` inside a component | Use source adapters |
| MVT data written to Zustand | Mapbox owns MVT lifecycle |
| `registerMvtSource()` outside `onLoad` | Map not ready |
| `useTacticalDataSources` called more than once per map | One orchestrator per instance |

---

## Pre-Implementation Checklist

Before writing any tactical component:

- [ ] If a Tactical theme is wanted: `design/web/tactical/` exists and its tokens are applied to `src/styles/variable.css`; otherwise use the default tokens
- [ ] `src/features/tactical/types/tactical.types.ts` is complete
- [ ] `src/config/map/marker-styles.config.ts` defines all severity styles
- [ ] `src/config/map/layer-paint.config.ts` defines all needed paint presets
- [ ] `src/features/tactical/config/layers.config.ts` has all layers registered
- [ ] `src/features/tactical/config/incident-types.config.ts` has all incident types
- [ ] Three stores (`useLayerStore`, `useIncidentStore`, `useSensorStore`) are created with correct scope
- [ ] Each layer with external data has `dataSource` declared in `layers.config.ts`
- [ ] `useTacticalDataSources(mapRef)` called once in `TacticalMap`
- [ ] MVT layers use `registerMvtSource()` inside `onLoad` only
- [ ] Route `/command` is registered with a menu entry — for layout setup read `.claude/skills/reactjs-app-layout/SKILL.md`
