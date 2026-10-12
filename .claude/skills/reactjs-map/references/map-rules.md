# Interactive Map — Rules

## 0. Container & frame contract (layout)

The map viewport **must fill the hosting UI frame** (dashboard card, split pane, full-bleed panel, embed inside `main`). The bordered or token-styled “map frame” and the actual Mapbox canvas must share the **same rectangular extent** — no unused empty strip inside that frame where the map stops short vertically or horizontally.

### Mandatory

| Rule                                                                                                                                                                 | Reason                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Bounded height exists all the way from page shell → map wrapper                                                                                                      | Mapbox needs a definite container size; ambiguous flex height yields a canvas shorter than the visible frame  |
| Every flex ancestor in the vertical chain uses `min-h-0` where the map should grow (`flex-1` child path)                                                             | Default `min-height: auto` blocks flex children from shrinking to fit; classic cause of “map not tall enough” |
| Map host wrapper uses `h-full w-full` or `size-full` plus `min-h-0` inside its flex parent, **or** `absolute inset-0` inside a `relative` parent whose height is set | Guarantees the GL canvas stretches to the allocated slot                                                      |
| Card/panel around map uses `flex flex-col min-h-0 overflow-hidden` (or explicit `h-*`) when the map is the primary content                                           | Prevents the inner map from collapsing while the outer chrome stays tall                                      |
| After container size changes (sidebar toggle, tab switch, `ResizeObserver`), trigger `map.resize()` when appropriate                                                 | Mapbox does not always pick up CSS-only layout changes                                                        |

### Forbidden

| Pattern                                                                                       | Reason                                                             |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Map wrapper only `w-full` with no height inheritance while parent frame is taller             | Map renders shorter than the frame                                 |
| Deep flex column without `min-h-0` on scroll/grow segments leading to map                     | Middle sections clip growth of map child                           |
| Fixed `h-[300px]` (or similar) on inner map while outer layout expects flex-fill              | Breaks responsive/dashboard layouts and diverges from design frame |
| Padding/margin on inner map container that steals height without matching outer visual bounds | Visual mismatch between chrome and canvas                          |

---

## 0.5 Access token contract

Use this canonical public token for map-related env setup:

```bash
VITE_MAPBOX_TOKEN=pk.YOUR_MAPBOX_PUBLIC_TOKEN
```

### Mandatory

| Rule                                                                 | Reason                                                                                |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Read the token via `env.map.mapboxToken` (`src/config/env.ts`, validated `VITE_MAPBOX_TOKEN`) | Vite only exposes `VITE_*` vars; `import.meta.env` is read only in `config/env.ts` |
| Reuse `VITE_MAPBOX_TOKEN` for geocoding/search requests              | Avoid duplicate token naming like `MAPBOX_TOKEN` or `MAPBOX_ACCESS_TOKEN`             |
| Keep token reads inside `MapboxWrapper` or map-specific helpers only | Prevents token scattering across feature components                                   |

### Forbidden

| Pattern                                                               | Reason                                                  |
| --------------------------------------------------------------------- | ------------------------------------------------------- |
| Hardcoding `pk.eyJ...` inside a component or page                     | Breaks the env contract and duplicates configuration    |
| Node-style env access or `NEXT_PUBLIC_MAPBOX_TOKEN` / `import.meta.env` outside `config/env.ts` | Only `VITE_*` vars exist in Vite builds, and they are read once in `src/config/env.ts` |

---

## 0.6 Vector tile URL contract (Mapbox GL v3)

Mapbox GL **v3** loads vector tiles inside a **Web Worker**, where `new Request(url)` has no document base URL. A **relative** tile URL (`/api/map/...`) therefore throws `Failed to construct 'Request': Failed to parse URL` and the data layer stays blank — **while the basemap still renders** (its tiles use absolute `https://` URLs). `curl` of the same relative path succeeds, so this hides from server-side checks.

### Mandatory

| Rule | Reason |
| ---- | ------ |
| Build vector source `tiles` as an **absolute** URL: `` `${window.location.origin}/api/map/${layersId}/{z}/{x}/{y}.pbf` `` | v3 workers cannot parse relative URLs; absolute still routes through the Vite `/api` proxy |
| Pin `mapbox-gl` in `package.json` to the major you actually install | A `^2` pin with v3 in `node_modules` silently changes worker tile-loading behavior |
| When "basemap shows but data layers are blank + red console error", suspect a **relative tile URL** first | Most common v3 map-data failure once the BFF tile endpoint is verified working |

---

## 1. Architecture — Two-Layer Config Split

Map config is split into two mandatory layers. Never merge them.

| Layer               | Location                        | Contains                                     | Reusable            |
| ------------------- | ------------------------------- | -------------------------------------------- | ------------------- |
| **Map Primitives**  | `src/config/map/` (create on demand) | Marker styles, paint presets, map style URLs | ✅ Any domain       |
| **Domain Registry** | `src/features/{domain}/config/` | Layer list, entity types, widget config      | ❌ That domain only |

### Primitive files (not present yet — create them at these paths)

```
src/config/map/
├── marker-styles.config.ts   ← MARKER_STYLES keyed by MarkerStatus
├── layer-paint.config.ts     ← LAYER_PAINT presets per layerType
└── map-styles.config.ts      ← MAP_STYLE_OPTIONS: MapStyleKey → Mapbox URL
```

### Domain config files

```
src/features/{domain}/config/
├── layers.config.ts          ← MAP_LAYERS, MAP_LAYERS_BY_GROUP, DEFAULT_LAYER_VISIBILITY
├── markers.config.ts         ← MARKER_CONFIGS [if using custom markers]
├── widgets.config.ts         ← FLOATING_WIDGETS [if using floating widgets]
├── modal-registry.ts         ← MAP_MODAL_REGISTRY [if using click modals]
└── index.ts                  ← barrel export
```

---

## 2. Layer Registry Rules

### ✅ Mandatory

| Rule                                                                                                                       | Reason                                                                      |
| -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Every rendered layer MUST have an entry in `MAP_LAYERS`                                                                    | Single source of truth — LayerPanel and MapBridge both loop this array      |
| `mapLayerId` must be globally unique across the entire map instance                                                        | Duplicate IDs cause Mapbox GL runtime errors                                |
| `layerType` must be explicitly declared — one of `fill \| circle \| line \| symbol \| heatmap \| fill-extrusion \| raster` | MapBridge uses this to call `map.addLayer()` with correct type              |
| `sourceType` must be `'geojson' \| 'vector' \| 'raster'`                                                                   | Determines which source registration path MapBridge takes                   |
| `defaultVisible` must be explicitly declared                                                                               | Never assume visibility — store init reads this                             |
| `paint` references `LAYER_PAINT[preset]` — never an inline object                                                          | Centralized, themeable                                                      |
| `hover` and `click` configs declared in layer entry — never wired manually in component                                    | MapBridge auto-wires from registry; manual wiring creates unsync'd behavior |
| `legend` declared for any layer where color carries meaning                                                                | LayerPanel renders it automatically                                         |

### ❌ Forbidden

| Pattern                                                                                   | Reason                                          |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------- |
| ❌ `map.addLayer()` with hardcoded type in MapBridge body (not from registry `layerType`) | Config is the single source of layer type truth |
| ❌ Inline paint object anywhere outside `layer-paint.config.ts`                           | Duplicates config, breaks theming               |
| ❌ `map.on('mousemove', ...)` or `map.on('click', ...)` wired outside `onLoad` loop       | Events must be registered after layer exists    |
| ❌ Wiring hover/click for a layer outside `handleMapLoad`                                 | Registration order must follow layer add order  |
| ❌ Using `MAP_LAYERS` outside the domain barrel import                                    | Always import from barrel, not internal paths   |

---

## 3. Layer Type — Paint Config Rules

Each `layerType` has a matching paint namespace in `LAYER_PAINT`. Never mix paint across types.

| layerType        | Paint interface                   | Config key pattern            |
| ---------------- | --------------------------------- | ----------------------------- |
| `fill`           | `mapboxgl.FillPaint`              | `LAYER_PAINT.{name}Fill`      |
| `circle`         | `mapboxgl.CirclePaint`            | `LAYER_PAINT.{name}Circle`    |
| `line`           | `mapboxgl.LinePaint`              | `LAYER_PAINT.{name}Line`      |
| `symbol`         | `mapboxgl.SymbolPaint` + `layout` | `LAYER_PAINT.{name}Symbol`    |
| `heatmap`        | `mapboxgl.HeatmapPaint`           | `LAYER_PAINT.{name}Heat`      |
| `fill-extrusion` | `mapboxgl.FillExtrusionPaint`     | `LAYER_PAINT.{name}Extrusion` |
| `raster`         | `mapboxgl.RasterPaint`            | `LAYER_PAINT.{name}Raster`    |

### ✅ Mandatory

| Rule                                                                        | Reason                                           |
| --------------------------------------------------------------------------- | ------------------------------------------------ |
| All color values in paint presets use CSS variables — `var(--color-*)`      | Theme-aware — dark/light works automatically     |
| `symbol` layers declare `layout` in the layer config entry (not in `paint`) | Mapbox separates symbol icons/text into `layout` |

### ❌ Forbidden

| Pattern                                               | Reason                             |
| ----------------------------------------------------- | ---------------------------------- |
| ❌ Hardcoded hex color in any paint preset            | Defeats theming                    |
| ❌ `FillPaint` applied to `circle` layer (wrong type) | Runtime error — Mapbox will reject |

---

## 4. Hover & Click Event Rules

### ✅ Mandatory

| Rule                                                                                            | Reason                                                                   |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Hover state stored in `useMapStore.hoveredFeature` — never in component state                   | HoverPopup reads from store; component state would cause stale closure   |
| Click state stored in `useMapStore.clickedFeature` — never in component state                   | MapModal reads from store                                                |
| `HoverPopup` uses CSS `position: fixed` + follows `mousemove` on `window`                       | Avoids overflow clip from map container                                  |
| `HoverPopup` has `pointer-events: none`                                                         | Never blocks map interaction                                             |
| Layer hover cursor set via `map.getCanvas().style.cursor = 'pointer'` and reset on `mouseleave` | Required UX feedback                                                     |
| Click modal renders `MAP_MODAL_REGISTRY[component]` if `modalComponent` declared                | Decoupled rendering — MapModal doesn't import domain components directly |

### ❌ Forbidden

| Pattern                                                        | Reason                                     |
| -------------------------------------------------------------- | ------------------------------------------ |
| ❌ `marker.setPopup(new mapboxgl.Popup().setHTML(rawContent))` | XSS risk — use React portal (`HoverPopup`) |
| ❌ `HoverPopup` importing from `mapbox-gl`                     | Pure UI — no map deps                      |
| ❌ `MapModal` importing from `mapbox-gl`                       | Pure UI — no map deps                      |
| ❌ Hover popup with `pointer-events` other than `none`         | Must not block map clicks                  |
| ❌ `MAP_MODAL_REGISTRY` components importing `mapboxgl`        | Modal content is pure UI                   |

---

## 5. Marker System Rules

### ✅ Mandatory

| Rule                                                                             | Reason                                   |
| -------------------------------------------------------------------------------- | ---------------------------------------- |
| Marker element rendered via `createRoot` — never `innerHTML` direct manipulation | React-managed lifecycle, no memory leaks |
| All marker colors from `MARKER_STYLES[status].color` — CSS variable              | No hardcoded hex                         |
| `pulse: true` only for `critical` and `alert` status                             | Visual hierarchy                         |
| Markers replaced fully on every entity change (`useEffect([entities])`)          | Prevents stale markers                   |
| Markers cleaned up in `useEffect` return                                         | No leaked DOM nodes                      |
| Hover and click wired on the `el` element inside the same `useEffect`            | Same lifecycle as marker creation        |

### ❌ Forbidden

| Pattern                                                           | Reason                                          |
| ----------------------------------------------------------------- | ----------------------------------------------- |
| ❌ Hardcoded color in `new mapboxgl.Marker({ color: '#...' })`    | Must use `MARKER_STYLES[status].color`          |
| ❌ `marker.addTo(map)` outside `useEffect`                        | Race condition with map load                    |
| ❌ Storing `mapboxgl.Marker[]` in Zustand                         | DOM objects break serialization                 |
| ❌ `useRef<mapboxgl.Marker[]>` shared between multiple components | One owner (MapBridge) — never share marker refs |

---

## 6. Store Contract Rules

Four stores, strict scope boundaries:

### `useMapStore`

```
Owns: activeStyle, layerPanelOpen, hoveredFeature, clickedFeature, searchResult, zoomTarget
Reads by: MapBridge, HoverPopup, MapModal, MapStyleSwitcher, GeoSearch, FloatingWidgets (zoom)
Writes by: MapBridge (hover/click events), UI components (style switch, search, panel toggle)
Does NOT own: layer visibility, entity data, feed data
```

### `useLayerStore`

```
Owns: layers (visibility), layerFilters
Reads by: LayerPanel, MapBridge
Writes by: LayerPanel (user toggle), FloatingWidgets (filter emission)
Does NOT own: entity data, map style, hover/click state
```

### `useEntityStore`

```
Owns: entities[], selectedId
Reads by: MapBridge (marker rendering), EntityPopup / MapModal
Writes by: MapBridge (click → select), FeedPanel or Widget (row click → select)
Does NOT own: layer visibility, map style
```

### ✅ Mandatory

| Rule                                                                          | Reason                                              |
| ----------------------------------------------------------------------------- | --------------------------------------------------- |
| `selectedId` is `string \| null` — the one source of "what entity is focused" | All panels/widgets sync to this single value        |
| `zoomTarget` in `useMapStore` — set by widgets, consumed by MapBridge         | Decouples widget from map imperative API            |
| `layerFilters` in `useLayerStore` — set by widgets, consumed by MapBridge     | Decouples widget filter from map `setFilter()` call |
| Store selectors are granular — `useMapStore((s) => s.hoveredFeature)`         | Prevents unnecessary re-renders                     |

### ❌ Forbidden

| Pattern                                              | Reason                                                |
| ---------------------------------------------------- | ----------------------------------------------------- |
| ❌ `mapboxgl.Map` instance in any Zustand store      | DOM objects break serialization                       |
| ❌ Data fetching inside a store action               | Belongs in hooks                                      |
| ❌ One store importing another store                 | Circular dependency — compose in components           |
| ❌ Widget calling `mapRef.current?.flyTo()` directly | Only MapBridge controls the map — use `setZoomTarget` |
| ❌ Widget calling `map.setFilter()` directly         | Only MapBridge applies filters — use `setLayerFilter` |

---

## 7. MapBridge — The Bridge Rules

`MapBridge.tsx` is the **only** component allowed to import both Zustand stores and `mapbox-gl`.

### ✅ Mandatory

| Rule                                                                                                       | Reason                                                      |
| ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| One `useEffect` per concern — layers, filters, style, markers, selectedId, zoomTarget are separate effects | No side effect entanglement                                 |
| All layer registration, hover, and click wiring inside `handleMapLoad` (the `onLoad` callback)             | Map must be ready before any `map.addLayer()` or `map.on()` |
| Layers registered in `MAP_LAYERS` order — iterate registry, never hardcode                                 | Adding a new layer = update config only                     |
| `map.setStyle()` triggered by `useEffect([activeStyle])`                                                   | Reactive to store, not imperative call from switcher        |
| `map.setFilter()` triggered by `useEffect([layerFilters])`                                                 | Reactive to store, not direct from widget                   |
| `map.flyTo()` triggered by `useEffect([zoomTarget])` + `setZoomTarget(null)` after                         | Consume-and-clear prevents repeated fly                     |

### ❌ Forbidden

| Pattern                                                                  | Reason                                          |
| ------------------------------------------------------------------------ | ----------------------------------------------- |
| ❌ `map.addLayer()` outside `onLoad`                                     | Map style not ready                             |
| ❌ Business logic inside `handleMapLoad`                                 | `onLoad` registers layers only — logic in hooks |
| ❌ `MapBridge` importing from panel components                           | One-way data flow — stores mediate everything   |
| ❌ `map.on('click', ...)` or `map.on('mousemove', ...)` outside `onLoad` | Layer doesn't exist yet                         |

---

## 8. LayerPanel Rules

### ✅ Mandatory

| Rule | Reason |
|---|---|
| Panel open/close state lives in `useMapStore.layerPanelOpen` (MapBridge pattern) or local `useState` in `MapPluginShell` (MapPlugin pattern) | Multiple components can toggle it |
| `LayerPanel` reads only layer config + visibility store | Panel knows nothing about entities, hover, or modal |
| Group toggle via eye icon — toggles all layers in that group at once | All-or-nothing per group |
| Show/hide-all eye icon in panel header | One-click convenience |
| Layer visibility toggle uses `useMapPluginStore.setLayerVisibility` / `useLayerStore.toggleLayer` | Store is single source of truth |
| `LayerLegend` / color swatch only rendered when layer is visible | Legend for hidden layer confuses users |

### MapPlugin MapLayerPanel — styling contract

> **Full source:** `references/map-layer-panel.md` — reproduce that file exactly when regenerating `MapLayerPanel.tsx`.


**Row layout (left → right):** `[icon-with-bg] [name + range-bar (flex-col)] [single-dot?] [checkbox]`

- **Icon background**: `28–30px` rounded square, unique color per layer type (see table below). Never a plain icon without background.
- **Layer name**: `12–13px`, `fontWeight 600`, truncated with ellipsis.
- **Single color swatch**: `13–14px` circle dot with subtle border + shadow, inline right of name.
- **Range color bar**: `5px` height `flex: 1` bars, directly below name inside the same flex column (gap `3px`). Never on a separate row outside the flex column.
- **Checkbox**: the shadcn `Checkbox` primitive for layer show/hide — never a native `<input type="checkbox">`.
- **Eye icon (`ph-eye` / `ph-eye-slash`)**: ghost icon `Button` with `aria-label`, in group header and panel header for group-toggle / show-all.
- **Row opacity when hidden**: `0.38` transition `0.18s ease`.
- **Panel**: `w-72` (max viewport − 2rem), floating surface `rounded-xl border border-border bg-card shadow-md` (visual rules: `reactjs-ui-design`).

**Layer type icon colors:**

| type | bg | fg (icon) |
|---|---|---|
| `point` | `#dbeafe` | `#3b82f6` |
| `polygon` | `#d1fae5` | `#10b981` |
| `line` / `lineString` | `#fef3c7` | `#f59e0b` |
| `lineRelation` | `#ede9fe` | `#8b5cf6` |
| `arc` | `#fce7f3` | `#ec4899` |
| `heatmap` | `#fee2e2` | `#ef4444` |
| `cluster` | `#e0f2fe` | `#0ea5e9` |
| `icon` | `#f3e8ff` | `#a855f7` |
| fallback | `#f3f4f6` | `#6b7280` |

**Color extraction mirrors `renderColorStyle` exactly — same 4-case decision tree:**

```
1. !channel.enable || !channel.field  → single = channel.color
2. type === 'solid' || !type          → single = colorRange.colors[0] ?? channel.color
3. colorPalleteCustomRange?.length    → range  = colorPalleteCustomRange.map(e => e.color)
4. category / quantile / quantize     → range  = colorRange.colors
```

**Group header:**
- No background tint (same white as rows).
- Caret (`ph-caret-down` / `ph-caret-right`) + uppercase label (`GENERAL` → `Default`, others → Title Case).
- Eye icon right of label for per-group show/hide.

**Layer panel button in `MapPluginShell`:** anchored `position: absolute, top: 10, left: 10` inside map canvas area. Button and panel share one `flex-col` wrapper — panel renders directly below button with `gap: 6`. This keeps both correctly offset from the top-left edge at all viewport sizes.

### ❌ Forbidden

| Pattern | Reason |
|---|---|
| ❌ `LayerPanel` importing from `mapbox-gl` | Pure UI component |
| ❌ `LayerPanel` reading entity or hover store | Panel scope is layer visibility only |
| ❌ Color swatch hardcoded independent of `renderColorStyle` logic | Swatch must match what is rendered on the map |
| ❌ Range color bar on a separate DOM row outside the name's flex column | Creates visual gap between name and bar |
| ❌ Layer panel button at arbitrary `top` value far from map edge | Button must be `top: 10, left: 10` relative to canvas area |
| ❌ Plain icon without background container for layer type | Icon background is required for visual clarity |

---

## 9. Floating Widget Rules

### ✅ Mandatory

| Rule                                                                                                  | Reason                                                        |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Floating widgets use `DynamicWidget` components from `.claude/skills/reactjs-dynamic-widget`                  | No custom widget components unless the domain is truly unique |
| Widget positions declared in `FLOATING_WIDGETS` config — not inline style in JSX                      | Config drives layout — not component code                     |
| Widget container has `pointer-events: auto` — map container has `pointer-events: none` on overlay div | Widgets receive clicks; map remains interactive underneath    |
| Running text (`MapTicker`) positioned with `position: absolute` — top or bottom of map                | Never overlaps layer panel or other floating widgets          |
| Widget → layer filter uses `useLayerStore.setLayerFilter(layerId, expression)`                        | Only MapBridge applies `map.setFilter()`                      |
| Widget zoom-to-location uses `useMapStore.setZoomTarget({ lngLat, zoom })`                            | Only MapBridge calls `map.flyTo()`                            |

### ❌ Forbidden

| Pattern                                                    | Reason                                           |
| ---------------------------------------------------------- | ------------------------------------------------ |
| ❌ Widget importing from `mapbox-gl`                       | Widgets are pure UI — map is MapBridge's concern |
| ❌ Widget calling `mapRef.flyTo()` directly                | Use `setZoomTarget` — indirect via store         |
| ❌ Widget calling `map.setFilter()` directly               | Use `setLayerFilter` — indirect via store        |
| ❌ Multiple `MapTicker` components rendered simultaneously | Only one ticker per position (top/bottom)        |

---

## 10. GeoSearch Rules

### ✅ Mandatory

| Rule                                                                                   | Reason                                                    |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Search result stored in `useMapStore.searchResult`                                     | Result accessible to other components (e.g., widget list) |
| Zoom to result via `useMapStore.setZoomTarget`                                         | MapBridge handles `flyTo`                                 |
| Geocoding API key must reuse `VITE_MAPBOX_TOKEN` from env — never hardcoded or renamed | One canonical token contract                              |
| Debounce search input — minimum 300ms delay                                            | Avoids excessive API calls                                |

### ❌ Forbidden

| Pattern                                             | Reason                                        |
| --------------------------------------------------- | --------------------------------------------- |
| ❌ `fetch()` geocoding API inside MapBridge         | Search logic belongs in `GeoSearch` component |
| ❌ `map.flyTo()` called directly inside `GeoSearch` | Use `setZoomTarget`                           |

---

## 11. Data Source Rules

| Type        | Who fetches               | Data path                               | Registered in        |
| ----------- | ------------------------- | --------------------------------------- | -------------------- |
| `rest`      | `useRestSource` hook      | `map.getSource().setData()`             | `useMapDataSources`  |
| `websocket` | `useWebSocketSource` hook | `map.getSource().setData()` incremental | `useMapDataSources`  |
| `mvt`       | Mapbox GL JS directly     | Never touches React/Zustand             | `MapBridge onLoad()` |

### ✅ Mandatory

| Rule                                                                 | Reason                                         |
| -------------------------------------------------------------------- | ---------------------------------------------- |
| Every layer with external data declares `dataSource` in `MAP_LAYERS` | Config drives all adapter wiring automatically |
| `useMapDataSources(mapRef)` called once in `MapBridge`               | One orchestrator per map instance              |
| REST uses `AbortController` — aborted on cleanup                     | No stale response after unmount                |
| WebSocket cleanup: `ws.onclose = null` before `ws.close()`           | Prevents reconnect loop on intentional unmount |
| `updateStrategy: 'append'` requires `maxFeatures`                    | Prevents unbounded DOM growth                  |
| `updateStrategy: 'upsert'` requires stable `feature.id`              | Deduplication needs a stable key               |
| `registerMvtSource()` called only inside `onLoad`                    | Map style must be loaded                       |

### ❌ Forbidden

| Pattern                                              | Reason                        |
| ---------------------------------------------------- | ----------------------------- |
| ❌ `fetch()` or `new WebSocket()` inside a component | Use adapters                  |
| ❌ WebSocket inside a store action                   | Store actions are synchronous |
| ❌ MVT data written to Zustand                       | Mapbox owns MVT lifecycle     |
| ❌ `setInterval` without cleanup return              | Memory leak                   |
| ❌ `useMapDataSources` called more than once         | One orchestrator per map      |

---

## 12. MapPlugin UI Contract (Slots, Overlays, Theming)

> Full reference with code patterns: [`map-plugin-ui-contract.md`](map-plugin-ui-contract.md)
> Read that file BEFORE touching any file in `src/modules/map-plugin/components/` (create the module on demand).

### Core rule: Tailwind-first, minimal inline

| What to style | Mechanism |
|---|---|
| Static structure (flex, overflow, radius, fixed px, position type) | Tailwind classes |
| Dynamic/computed values (state-driven width, props-driven top/left, animated maxHeight) | `style={{}}` — only those properties |
| Colors, borders, backgrounds | shadcn semantic token classes (`bg-card`, `border-border`, `text-muted-foreground`, etc.) |
| Overlay buttons floating on the map canvas | `Button` (default/primary variant, `shadow-md`) or `variant="outline"` on `bg-card` with `shadow-md` |

### Z-index hierarchy (inside canvas `relative` wrapper)

| Component | z-index | Tailwind |
|---|---|---|
| Layer panel button | 10 | `z-10` |
| Side panel (`MapSideSlot`) | 20 | `z-20` |
| Date filter + popup | 30 | `z-30` |
| Tooltip | 100 | `z-100` |

> Date filter MUST be `z-30` — its inner popup has `zIndex: 200` only within the date filter's own stacking context. If the container is `< z-20`, the popup renders behind the side panel.

### Theme — semantic tokens inside panels (light and dark)

Visual rules: [`reactjs-ui-design`](../../reactjs-ui-design/SKILL.md). All panel chrome (tab bar, card
surfaces, borders, text) uses the shadcn semantic tokens, so it follows the app's light/dark theme:
- `bg-card text-card-foreground` + `rounded-xl border border-border shadow-md` for floating panels/cards
- `bg-muted` for tab bar backgrounds (or the shadcn `Tabs` primitive)
- `border-border` for all borders
- `text-foreground` / `text-muted-foreground` for text
- Sentiment: `text-success` / `text-destructive` / `text-muted-foreground` for positive/negative/neutral

❌ Never use `rgba(10,20,40,...)`, `#1e293b`, `rgba(255,255,255,...)`, glassmorphism, or Tailwind default palette inside panel chrome.

### Map-overlay buttons exception

Buttons that float **directly on the map canvas** (layer toggle, side collapse strip) need contrast against
the tiles:
- `<Button size="icon" className="shadow-md" aria-label="…">` (primary) — or `variant="outline"` (it sits on `bg-card`)
  with `shadow-md`; both stay `rounded-md`
- Never a borderless, shadowless light button directly on light tiles

### ResizeObserver — mandatory pattern

```tsx
useEffect(() => {
  if (!containerRef.current) return
  const ro = new ResizeObserver(() => { mapRef.current?.resize() })
  ro.observe(containerRef.current)
  return () => ro.disconnect()
}, [])
```

Without this, collapsing the bottom panel or toggling the sidebar leaves the map canvas at the wrong size.

### Panel width

`MapSideSlot` default panel width is **470px** — fixed. Do not read `widget.width` for the panel container.

### `topOffset` for `MapSideSlot`

- Date filter visible: `topOffset = 62` (10px margin + ~44px filter height + 8px gap)
- Date filter hidden: `topOffset = 0`

### `accentColor` props

Always pass CSS var strings, never raw hex:
```tsx
// ✅
accentColor="var(--color-primary)"
accentColor="var(--color-destructive)"

// ❌
accentColor="#3b82f6"
accentColor="#ef4444"
```

### Hover states

Use Tailwind `hover:` classes — never `onMouseEnter`/`onMouseLeave` for color changes:
```tsx
// ✅
className="bg-card hover:bg-muted"   // or a shadcn Button variant, which already has hover states

// ❌
onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}
```

---

## Quick Forbidden Summary

| Violation                                                       | Rule                                                                   |
| --------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Map canvas shorter or narrower than its card/panel frame        | Fill container — flex chain + `min-h-0`, full-size wrapper, `resize()` |
| Layer added to map without `MAP_LAYERS` entry                   | Registry mandatory                                                     |
| `layerType` or `sourceType` missing from layer config           | Explicit typing required                                               |
| Inline paint object in component                                | Must be from `LAYER_PAINT` preset                                      |
| Hover/click wired manually in component outside `handleMapLoad` | Must be in `onLoad` loop                                               |
| Hover popup with `pointer-events` other than `none`             | Blocks map interaction                                                 |
| Marker with hardcoded hex color                                 | Use `MARKER_STYLES[status].color`                                      |
| Panel importing from `mapbox-gl`                                | Panels are pure UI                                                     |
| Widget calling `mapRef.flyTo()` directly                        | Use `setZoomTarget`                                                    |
| Widget calling `map.setFilter()` directly                       | Use `setLayerFilter`                                                   |
| `mapboxgl.Map` in any Zustand store                             | DOM objects not allowed                                                |
| `map.addLayer()` outside `onLoad`                               | Map not ready                                                          |
| `fetch()` / `new WebSocket()` inside a component                | Use source adapters                                                    |
| MVT data written to Zustand                                     | Mapbox owns MVT lifecycle                                              |
| `useMapDataSources` called more than once                       | One orchestrator per map                                               |
| Legend color hardcoded hex                                      | Must use CSS variable                                                  |
| `MapModal` or `HoverPopup` importing `mapbox-gl`                | Pure UI                                                                |

---

## Pre-Implementation Checklist

### MapBridge pattern (custom domain map)

Before writing any map component:

- [ ] Map host fills frame — flex/`min-h-0` chain verified; no gap inside bordered container
- [ ] `VITE_MAPBOX_TOKEN` set in `apps/web/env/.env` (key already in the `src/config/env.ts` schema) before map/geocoding work begins
- [ ] Design tokens for domain are defined
- [ ] `src/config/map/layer-paint.config.ts` created, with presets for all needed layer types
- [ ] `src/config/map/map-styles.config.ts` created, with all style options
- [ ] `MAP_LAYERS` complete — every layer has `layerType`, `sourceType`, `paint`, `defaultVisible`
- [ ] Hover and click configs declared in layer entries (if needed)
- [ ] Legends declared in layer entries (if needed)
- [ ] `useMapStore`, `useLayerStore`, `useEntityStore` (if needed) created with correct scope
- [ ] `FLOATING_WIDGETS` config declared (if using widgets)
- [ ] `MAP_MODAL_REGISTRY` declared (if using click modals)
- [ ] `useMapDataSources(mapRef)` called once in `MapBridge`
- [ ] MVT layers use `registerMvtSource()` inside `onLoad` only
- [ ] Route + menu registered — for layout setup read `.claude/skills/reactjs-app-layout/SKILL.md`

### MapPlugin module (ERP-migrated mapPlugin widget)

Before implementing `visualization_type === "mapPlugin"`:

- [ ] `src/modules/map-plugin/` module exists (create if absent — see `reactjs-map` SKILL.md § 12)
- [ ] `maps_*.json` copied to `src/features/dashboard/{page}/data/maps.json`
- [ ] `map-plugin.config.ts` parses JSON → `MAP_PLUGIN_CONFIGS` with `inferLayerType` applied
- [ ] Tile URL built from `env.api.baseUrl` (`/map/...` under the API prefix), or a `VITE_MAP_TILE_URL` added to the `src/config/env.ts` schema if tiles live elsewhere
- [ ] `VITE_MAPBOX_TOKEN` set (same canonical token as above)
- [ ] `MapPluginWidget` receives `referenceId` + `configs` from page component — not from global DynamicWidget switch
- [ ] `MapPluginShell` caller supplies a bounded-height ancestor (`min-h-0` flex chain)
- [ ] Layer types `grid`/`hex`/`pie` logged as warning + skipped if present in the data

**Before touching any `src/modules/map-plugin/components/` file (create on demand; UI changes, new slots, widget chrome):**

- [ ] Read [`map-plugin-ui-contract.md`](map-plugin-ui-contract.md) first — it is the source of truth
- [ ] Static layout → Tailwind classes only; dynamic/animated values → `style={{}}` only
- [ ] Panel chrome uses shadcn semantic tokens (light + dark) — NOT dark navy / glass-morphism / raw hex; floating panels `rounded-xl border border-border bg-card shadow-md`
- [ ] Buttons overlaid on map canvas are primary or outline `Button`s with `shadow-md` (never borderless light buttons on light tiles)
- [ ] z-index stack respected: layer-btn=10, side-panel=20, date-filter=30, tooltip=100
- [ ] `ResizeObserver` on `containerRef` → `map.resize()` present (do not remove)
- [ ] `topOffset` for `MapSideSlot`: `62` when date filter shown, `0` when hidden
- [ ] `accentColor` props = CSS var strings (`"var(--color-primary)"`), never raw hex
- [ ] Hover states via Tailwind `hover:` classes — no JS `onMouseEnter`/`onMouseLeave` handlers
