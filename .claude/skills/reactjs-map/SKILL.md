---
name: reactjs-map
description: Implementation guide for any Mapbox GL JS map analytics interface. Covers TWO patterns — (1) MapPlugin module for config-driven ERP-migrated maps (src/modules/map-plugin/), and (2) the generic MapBridge pattern for custom domain maps. Covers env contract, layer system (all types + hover/click/legend), marker system, store architecture, LayerPanel, style switcher, geo search, and floating widgets. Nothing map-related exists in the boilerplate yet (only the mapbox-gl dependency and VITE_MAPBOX_TOKEN in src/config/env.ts) — this skill includes the recipe to create the MapboxWrapper. For layout shell, read .claude/skills/reactjs-app-layout/SKILL.md.
---

# Skill — Interactive Map (Generic)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns the map engine, layers, markers, stores, slot layout and the
> map container contract.

Read `references/map-rules.md` before writing any map code.

> Domain-specific overrides: `.claude/skills/reactjs-tactical-map/SKILL.md` (only when the task or the
> active `design/` theme is tactical).

### Map UI chrome — visual contract

The BEM class names in the snippets below (`map-layer-panel__*`, `map-geo-search__*`, `map-float-widget`…)
mark structure and behavior. Build the chrome from shadcn primitives and semantic tokens:

| Map piece | Build it with |
|---|---|
| Floating panel (layer panel, legend, widget, side slot) | `rounded-xl border border-border bg-card text-card-foreground shadow-md`; header `text-sm font-semibold`, meta `text-xs text-muted-foreground` |
| Overlay buttons on the canvas (layer toggle, zoom, collapse) | `<Button size="icon" variant="outline" className="shadow-md" aria-label="…">` (or primary for the active state) + `Tooltip` |
| Layer on/off | shadcn `Checkbox` or `Switch` — never a native checkbox |
| Style switcher | `ToggleGroup` (or `DropdownMenu` when there are many styles) |
| Geo search | `Input` with `ph-magnifying-glass`, results in `Popover` + `Command` |
| Feature detail on click | `Sheet` (side panel) or `Dialog`; data as a definition list |
| Hover popup / tooltip | small `rounded-lg border border-border bg-popover text-popover-foreground shadow-md` box, `text-xs` |
| Loading / empty / error in widgets | `Skeleton` / `EmptyState` / `Alert variant="destructive"` + Retry |

Markers, heatmaps and data-driven layer colors are data visualization — they may use layer-config
colors; UI chrome may not. Light and dark mode come from the tokens.

---

## Status in this boilerplate (read first)

| Piece | State | Where to create it |
|---|---|---|
| `mapbox-gl` (^3) | installed (`apps/web/package.json`) | — |
| `VITE_MAPBOX_TOKEN` | already in the env schema → `env.map.mapboxToken` (`src/config/env.ts`) and `apps/web/env/.env.example` (empty) | set it in your local `apps/web/env/.env` |
| `MapboxWrapper` | **not present** | create it at `src/components/wrappers/MapboxWrapper.tsx` (recipe below) |
| `src/config/map/*` (marker styles, layer paint, map styles) | **not present** | create on demand (Pattern B) |
| shared map types (`MapStyleKey`, `TMapHoverState`, …) | **not present** | create `src/types/map.d.ts` (types only); runtime guards such as `isMvtSource` go in `src/utils/map.ts` |
| `src/modules/map-plugin/` | **not present** | create on demand (Pattern A) |
| `EChartWrapper`, `src/modules/dynamic-widget` | **not present** | see `.claude/skills/reactjs-chart/SKILL.md` / `.claude/skills/reactjs-dynamic-widget/SKILL.md` |
| Backend `/map/*` tile router, `/widget/get-data` | **not part of this backend** | see the domain skills `.claude/skills/fastapi-render-map/SKILL.md` |

Paths in this skill follow `.claude/skills/reactjs-architecture/SKILL.md`: map UI pieces of
a domain live in `src/features/{domain}/{feature}/components/` (not in `src/pages/`).

### Recipe — `src/components/wrappers/MapboxWrapper.tsx` (create it)

```tsx
import 'mapbox-gl/dist/mapbox-gl.css'

import mapboxgl from 'mapbox-gl'
import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'

import env from '@/config/env'
import { cn } from '@/utils/cn'

export interface MapboxWrapperRef {
  getMap: () => mapboxgl.Map | null
}

export interface MapboxWrapperProps {
  mapStyle: string
  center?: [number, number]
  zoom?: number
  width?: number | string
  height?: number | string
  className?: string
  onLoad?: (map: mapboxgl.Map) => void
}

/** The only place that reads the Mapbox token and creates/destroys the map. */
export const MapboxWrapper = forwardRef<MapboxWrapperRef, MapboxWrapperProps>(function MapboxWrapper(
  { mapStyle, center = [106.8456, -6.2088], zoom = 9, width = '100%', height = '100%', className, onLoad },
  ref,
) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<mapboxgl.Map | null>(null)

  useImperativeHandle(ref, () => ({ getMap: () => mapRef.current }), [])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return undefined
    if (!env.map.mapboxToken) console.warn('VITE_MAPBOX_TOKEN is not set — the map will not load')
    const map = new mapboxgl.Map({ container, accessToken: env.map.mapboxToken, style: mapStyle, center, zoom })
    mapRef.current = map
    map.on('load', () => onLoad?.(map))
    const observer = new ResizeObserver(() => map.resize())   // keep the canvas = frame size
    observer.observe(container)
    return () => {
      observer.disconnect()
      map.remove()
      mapRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- create once per mount
  }, [])

  useEffect(() => {
    mapRef.current?.setStyle(mapStyle)
  }, [mapStyle])

  return <div ref={containerRef} className={cn('relative min-h-0', className)} style={{ width, height }} />
})
```


---

## Which pattern to use?

| Scenario | Pattern |
|---|---|
| Widget from ERP dashboard export (`visualization_type === "mapPlugin"`) | **MapPlugin Module** — Section 12 |
| Custom domain map built from scratch (not from ERP export) | **MapBridge pattern** — Sections 1–11 |

Both patterns share the same Mapbox GL JS rules (`references/map-rules.md`) and env token.

---

## Access Token Contract

For any map-related env setup, use this canonical public token:

```bash
VITE_MAPBOX_TOKEN=pk.YOUR_MAPBOX_PUBLIC_TOKEN
```

Rules:

1. Read the token via `env.map.mapboxToken` from `src/config/env.ts` (validated `VITE_MAPBOX_TOKEN`); never read `import.meta.env` directly.
2. Keep token reads inside `MapboxWrapper` or map-specific helpers only.
3. Reuse the same `VITE_MAPBOX_TOKEN` for geocoding/search calls. Do not introduce alternate names like `MAPBOX_ACCESS_TOKEN` or `MAPBOX_TOKEN`.
4. **Always set `VITE_MAPBOX_TOKEN` in your local env file** — create `apps/web/env/.env` from `apps/web/env/.env.example` (the key exists there, empty) — without it Mapbox falls back to a deprecated demo token and the map canvas renders blank/white with no error in the console.

> **Symptom of missing token:** Map container renders but canvas is pure white — the Mapbox style
> request fails silently. Confirm by checking the Network tab for a failed request to
> `api.mapbox.com/styles/...` with a 401 or 403 response.

---

## Layout — Map must fill its host container / frame

The Mapbox canvas must **match the allocated layout region**: same width **and** height as the card, panel, dashboard slot, or `main` area that is supposed to hold the map. A shorter map inside a taller frame is a **layout bug**.

**Rules (see `references/map-rules.md` § Container & frame contract for detail):**

1. **Establish height on the chain** — Flex parents along the path to the map must allow the child to consume remaining space: use `flex-1 min-h-0` (and `overflow-hidden` or `overflow-auto` on scroll siblings as appropriate). Without `min-h-0`, flex children often refuse to shrink and the map gets an implicit height smaller than the visual frame.
2. **Map slot wrapper** — Wrap `MapboxWrapper` / map root in a box that fills that slot: e.g. `relative min-h-0 flex-1` on the flex child, with an inner `h-full w-full min-h-0` **or** `absolute inset-0` inside a `relative` parent whose height is fully defined.
3. **Do not** rely on Mapbox’s internal default sizing alone when the parent is a flex/grid cell — always tie the map container to `100%` / `size-full` of the bounded parent.
4. **After layout changes** (sidebar collapse, tabs, split pane resize), call `map.resize()` once the container dimensions have updated so the canvas matches the frame.

Verify in DevTools: the map container element’s **computed height** should equal the frame’s content box height (no large empty band below the canvas inside the same bordered region).

---

## File Reference

### Pattern A — MapPlugin Module (ERP-migrated `mapPlugin` widget)

```
src/
├── modules/
│   └── map-plugin/                       ← REUSABLE ENGINE — never domain-specific
│       ├── types/
│       │   └── index.ts                  ← MapPluginConfig, MapLayerConfig, TooltipConfig,
│       │                                    LayerType, SourceType, VisualChannel, SizeChannel,
│       │                                    LabelChannel, IconChannel, ThresholdChannel
│       ├── store/
│       │   └── useMapPluginStore.ts      ← global store keyed by maps_id
│       │                                    state per instance: layerVisibility, clickedFeature, tooltipPosition
│       ├── helpers/
│       │   ├── data-driven.ts            ← renderColorStyle, renderColorAndOpacity,
│       │   │                                generateColorRange, generateIconRange, rendersizeRange
│       │   ├── color-scale.ts            ← d3 replacement: scaleLinear, scaleOrdinal,
│       │   │                                generateRangeStep (pure math, no external deps)
│       │   ├── mapbox-utils.ts           ← layersUpper, getFieldsVisualChannels,
│       │   │                                MAP_STYLE_URLS: Record<defaultStyle, mapboxStyleUrl>
│       │   └── render-layer/
│       │       ├── polygon-layer.ts      ← renderPolygonV2 (fill + outline)
│       │       ├── point-layer.ts        ← renderPointV2 (circle + symbol label, pulse alert)
│       │       ├── line-layer.ts         ← renderLine, renderLineRelation
│       │       ├── heatmap-layer.ts      ← renderHeatmap
│       │       ├── icon-layer.ts         ← renderIconV2
│       │       ├── cluster-layer.ts      ← renderCluster
│       │       └── index.ts             ← LAYER_RENDERERS: Record<LayerType, RenderFn>
│       ├── hooks/
│       │   └── useMapLayers.ts           ← iterates config.layers → renderLayersMvt per layer
│       │                                    inferLayerType(layer) when layer.type is absent
│       ├── components/
│       │   ├── MapPluginShell.tsx        ← Mapbox init + layout orchestrator; layer toggle button top:10 left:10
│       │   ├── MapLayerPanel.tsx         ← groups (empty→"Default") + color swatch + eye-toggle per group + show-all
│       │   │                               see references/map-layer-panel.md for full source
│       │   ├── MapTooltip.tsx            ← click event → TooltipTemplate | TooltipAutoFields
│       │   ├── tooltip/
│       │   │   ├── TooltipTemplate.tsx   ← developer.html parsed to React nodes (no innerHTML)
│       │   │   │                            handles {{data.field}}, {{thousandFormat data.field ...}}
│       │   │   └── TooltipAutoFields.tsx ← auto rows from fields[] + fieldsAlias[]
│       │   └── MapPluginWidget.tsx       ← entry: lookup config by referenceId, guard null
│       └── index.ts                      ← barrel: MapPluginWidget, useMapPluginStore, types
│
└── features/dashboard/{map-page}/        ← DOMAIN DATA — one folder per page
    ├── data/
    │   └── maps.json                     ← copy of dashboard-migrator/maps_*.json
    ├── config/
    │   └── map-plugin.config.ts          ← MAP_PLUGIN_CONFIGS: Record<mapsId, MapPluginConfig>
    │                                        + inferLayerType applied per layer
    └── components/
        └── {PageName}Page.tsx            ← imports MapPluginWidget + MAP_PLUGIN_CONFIGS
```

### Pattern B — MapBridge (custom domain map, not from ERP export)

```
src/
├── config/map/
│   ├── marker-styles.config.ts           ← MARKER_STYLES keyed by MarkerStatus
│   ├── layer-paint.config.ts             ← LAYER_PAINT presets per layerType
│   └── map-styles.config.ts              ← MAP_STYLE_OPTIONS (style key → URL)
└── features/{domain}/
    ├── index.ts                          ← barrel export
    ├── config/
    │   ├── layers.config.ts              ← MAP_LAYERS, BY_GROUP, DEFAULT_VISIBILITY
    │   ├── markers.config.ts             ← MARKER_CONFIGS [if using custom markers]
    │   └── widgets.config.ts             ← FLOATING_WIDGETS [if using floating widgets]
    ├── stores/
    │   ├── useMapStore.ts                ← map interaction state (hover, modal, style, search, zoom)
    │   ├── useLayerStore.ts              ← layer visibility + filters
    │   └── useEntityStore.ts             ← entities/markers + selectedId [optional]
    ├── sources/
    │   ├── rest.source.ts
    │   ├── websocket.source.ts
    │   ├── mvt.source.ts
    │   └── index.ts
    ├── hooks/
    │   └── useMapDataSources.ts          ← orchestrator
    └── types/
        └── {domain}.types.ts
```

---

## 1. Layer System

### Layer Config Schema

Every layer in `MAP_LAYERS` must declare this shape:

```ts
// layers.config.ts
export type TMapLayerConfig = {
  id: string                  // app-level unique key
  label: string               // display label in LayerPanel
  group: string               // group key
  icon?: string               // Phosphor icon name (for LayerPanel)
  defaultVisible: boolean
  mapLayerId: string          // globally unique Mapbox GL layer ID
  mapSourceId?: string        // defaults to mapLayerId if omitted
  layerType: TMapLayerType    // see below
  sourceType: 'geojson' | 'vector' | 'raster'
  paint?: object              // from LAYER_PAINT[preset] — never inline
  layout?: object             // Mapbox layout properties (symbol, text, etc.)
  hover?: TLayerHoverConfig   // optional — declare to enable hover popup
  click?: TLayerClickConfig   // optional — declare to enable click modal
  legend?: TLayerLegend       // optional — shown in LayerPanel
  dataSource?: TLayerDataSource
}

export type TMapLayerType = 'fill' | 'circle' | 'line' | 'symbol' | 'heatmap' | 'fill-extrusion' | 'raster'
```

### All Layer Types with Examples

**fill — polygon area**
```ts
{
  id: 'ZONE_FILL',
  label: 'Zone Area',
  group: 'ZONES',
  icon: 'polygon',
  defaultVisible: true,
  mapLayerId: 'layer-zone-fill',
  layerType: 'fill',
  sourceType: 'geojson',
  paint: LAYER_PAINT.zoneFill.paint,
  hover: { enabled: true, popupFields: ['name', 'area_km2'] },
  click: { enabled: true, action: 'modal' },
  legend: { type: 'exact', items: [{ color: 'var(--color-warning)', label: 'Restricted' }] },
},
```

**circle — point data**
```ts
{
  id: 'POINT_CIRCLE',
  label: 'Data Points',
  group: 'POINTS',
  icon: 'circle',
  defaultVisible: true,
  mapLayerId: 'layer-point-circle',
  layerType: 'circle',
  sourceType: 'geojson',
  paint: LAYER_PAINT.dataPoint.paint,
  hover: { enabled: true, popupFields: ['id', 'value', 'status'] },
},
```

**line — route / boundary**
```ts
{
  id: 'ROUTE_LINE',
  label: 'Routes',
  group: 'ROUTES',
  icon: 'path',
  defaultVisible: true,
  mapLayerId: 'layer-route-line',
  layerType: 'line',
  sourceType: 'geojson',
  paint: LAYER_PAINT.routeLine.paint,
  legend: { type: 'exact', items: [{ color: 'var(--color-info)', label: 'Active Route' }] },
},
```

**symbol — icon/text label**
```ts
{
  id: 'LABEL_SYMBOL',
  label: 'Labels',
  group: 'LABELS',
  icon: 'text-t',
  defaultVisible: false,
  mapLayerId: 'layer-label-symbol',
  layerType: 'symbol',
  sourceType: 'geojson',
  layout: {
    'text-field': ['get', 'name'],
    'text-size': 12,
    'icon-image': ['get', 'icon'],
    'icon-size': 0.8,
  },
  // Mapbox paint cannot read CSS variables — resolve tokens first, e.g.
  // getComputedStyle(document.documentElement).getPropertyValue('--color-foreground'), and re-apply on theme change
  paint: { 'text-color': resolved.foreground, 'text-halo-color': resolved.background, 'text-halo-width': 1 },
},
```

**heatmap**
```ts
{
  id: 'DENSITY_HEATMAP',
  label: 'Density Heat',
  group: 'ANALYTICS',
  icon: 'fire',
  defaultVisible: false,
  mapLayerId: 'layer-density-heatmap',
  layerType: 'heatmap',
  sourceType: 'geojson',
  paint: LAYER_PAINT.densityHeat.paint,
  legend: {
    type: 'range',
    min: 0,
    max: 100,
    colorStops: [
      { value: 0, color: 'rgba(0,0,255,0)' },
      { value: 0.5, color: 'rgba(255,165,0,0.8)' },
      { value: 1, color: 'rgba(255,0,0,1)' },
    ],
  },
},
```

**fill-extrusion — 3D buildings / volumes**
```ts
{
  id: 'BUILDING_3D',
  label: '3D Buildings',
  group: 'INFRASTRUCTURE',
  icon: 'buildings',
  defaultVisible: false,
  mapLayerId: 'layer-building-3d',
  layerType: 'fill-extrusion',
  sourceType: 'vector',
  paint: LAYER_PAINT.building3d.paint,
},
```

### Hover Config

```ts
export type TLayerHoverConfig = {
  enabled: boolean
  popupFields?: string[]    // feature.properties keys to render in hover tooltip
  popupComponent?: string   // custom component name if fields not enough
}
```

MapBridge wires hover automatically when `layer.hover?.enabled === true`.  
Hover state stored in `useMapStore.hoveredFeature` — `HoverPopup` component renders it.

### Click Config

```ts
export type TLayerClickConfig = {
  enabled: boolean
  action: 'modal' | 'flyTo' | 'custom'
  modalComponent?: string   // component name registered in MAP_MODAL_REGISTRY
}
```

Click state stored in `useMapStore.clickedFeature` — `MapModal` reads and renders it.

### Legend Config

```ts
export type TLayerLegend =
  | {
      type: 'exact'
      items: { color: string; label: string; icon?: string }[]
    }
  | {
      type: 'range'
      min: number
      max: number
      unit?: string
      colorStops: { value: number; color: string }[]  // value 0–1 normalized
    }
```

Legend renders at the bottom of each layer item in `LayerPanel`.

---

## 2. Marker System

Markers are for custom HTML/icon elements positioned by coordinate — distinct from GeoJSON layers.

### Marker Config Schema

```ts
// markers.config.ts
export type TMarkerConfig = {
  id: string
  lngLat: [number, number]
  iconName: string               // Phosphor icon name
  status?: MarkerStatus          // drives color from MARKER_STYLES
  customStyle?: Partial<TMarkerStyle>
  hover?: { enabled: boolean; popupFields?: string[] }
  click?: { enabled: boolean; action: 'modal' | 'flyTo' | 'custom' }
  data?: Record<string, unknown>
}
```

### Rendering Markers in MapBridge

```tsx
// one useEffect per concern — see MapBridge section
useEffect(() => {
  const map = mapRef.current?.getMap()
  if (!map) return

  markersRef.current.forEach((m) => m.remove())
  markersRef.current = []

  entities.forEach((entity) => {
    const style = MARKER_STYLES[entity.status ?? 'normal']
    const el = document.createElement('div')
    const root = createRoot(el)

    root.render(
      <div
        className={`map-marker map-marker--${entity.status}`}
        style={{ color: style.color, width: style.size, height: style.size }}
      >
        <i className={`ph-fill ph-${entity.iconName}`} />
        {style.pulse && <span className="map-marker__pulse" />}
      </div>
    )

    const marker = new mapboxgl.Marker({ element: el })
      .setLngLat(entity.lngLat)
      .addTo(map)

    // Hover
    if (entity.hover?.enabled) {
      el.addEventListener('mouseenter', () =>
        setHoveredFeature({ type: 'marker', id: entity.id, lngLat: entity.lngLat, data: entity.data ?? {} })
      )
      el.addEventListener('mouseleave', () => setHoveredFeature(null))
    }

    // Click
    if (entity.click?.enabled) {
      el.addEventListener('click', () =>
        openModal({ type: 'marker', id: entity.id, data: entity.data ?? {} })
      )
    }

    markersRef.current.push(marker)
  })

  return () => { markersRef.current.forEach((m) => m.remove()) }
}, [entities])
```

---

## 3. Store Architecture

### `useMapStore.ts` — central map interaction state

```ts
// src/features/{domain}/stores/useMapStore.ts
import { create } from 'zustand'
// create src/types/map.d.ts first (types only — see "Status in this boilerplate")
import type { MapStyleKey, TMapHoverState, TMapClickState, TGeoSearchResult } from '@/types/map'

type TMapStore = {
  // Map style
  activeStyle: MapStyleKey
  setActiveStyle: (key: MapStyleKey) => void

  // Panel
  layerPanelOpen: boolean
  toggleLayerPanel: () => void

  // Hover popup
  hoveredFeature: TMapHoverState | null
  setHoveredFeature: (state: TMapHoverState | null) => void

  // Click modal
  clickedFeature: TMapClickState | null
  openModal: (state: TMapClickState) => void
  closeModal: () => void

  // Geo search
  searchResult: TGeoSearchResult | null
  setSearchResult: (result: TGeoSearchResult | null) => void

  // Zoom target — set by widgets or external code, consumed by MapBridge
  zoomTarget: { lngLat: [number, number]; zoom?: number } | null
  setZoomTarget: (target: { lngLat: [number, number]; zoom?: number } | null) => void
}

export const useMapStore = create<TMapStore>((set) => ({
  activeStyle: 'dark',
  setActiveStyle: (key) => set({ activeStyle: key }),

  layerPanelOpen: true,
  toggleLayerPanel: () => set((s) => ({ layerPanelOpen: !s.layerPanelOpen })),

  hoveredFeature: null,
  setHoveredFeature: (state) => set({ hoveredFeature: state }),

  clickedFeature: null,
  openModal: (state) => set({ clickedFeature: state }),
  closeModal: () => set({ clickedFeature: null }),

  searchResult: null,
  setSearchResult: (result) => set({ searchResult: result }),

  zoomTarget: null,
  setZoomTarget: (target) => set({ zoomTarget: target }),
}))
```

### `useLayerStore.ts` — visibility + filters

```ts
// src/features/{domain}/stores/useLayerStore.ts
import { create } from 'zustand'
import { DEFAULT_LAYER_VISIBILITY } from '@/features/{domain}'
import type { LayerId } from '@/features/{domain}'

type TLayerStore = {
  layers: Record<LayerId, boolean>
  toggleLayer: (id: LayerId) => void
  setLayer: (id: LayerId, visible: boolean) => void
  toggleGroup: (ids: LayerId[]) => void        // check/uncheck all in group
  resetLayers: () => void
  // For widget → layer filter interaction
  layerFilters: Partial<Record<LayerId, unknown[]>>
  setLayerFilter: (id: LayerId, filter: unknown[] | null) => void
}

export const useLayerStore = create<TLayerStore>((set) => ({
  layers: { ...DEFAULT_LAYER_VISIBILITY },
  layerFilters: {},

  toggleLayer: (id) =>
    set((s) => ({ layers: { ...s.layers, [id]: !s.layers[id] } })),

  setLayer: (id, visible) =>
    set((s) => ({ layers: { ...s.layers, [id]: visible } })),

  toggleGroup: (ids) =>
    set((s) => {
      const anyVisible = ids.some((id) => s.layers[id])
      const next = { ...s.layers }
      ids.forEach((id) => { next[id] = !anyVisible })
      return { layers: next }
    }),

  resetLayers: () =>
    set({ layers: { ...DEFAULT_LAYER_VISIBILITY } }),

  setLayerFilter: (id, filter) =>
    set((s) => ({
      layerFilters: { ...s.layerFilters, [id]: filter ?? undefined },
    })),
}))
```

### `useEntityStore.ts` — entities on map [optional]

```ts
// src/features/{domain}/stores/useEntityStore.ts
import { create } from 'zustand'
import type { TEntity } from '@/features/{domain}'

type TEntityStore = {
  entities: TEntity[]
  selectedId: string | null
  setEntities: (data: TEntity[]) => void
  select: (id: string | null) => void
}

export const useEntityStore = create<TEntityStore>((set) => ({
  entities: [],
  selectedId: null,
  setEntities: (data) => set({ entities: data }),
  select: (id) => set({ selectedId: id }),
}))
```

---

## 4. MapBridge — The Bridge Component

The only component allowed to import both Zustand stores and `mapbox-gl`.

```tsx
// src/features/{domain}/{feature}/components/MapBridge.tsx
import { useRef, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
// recipe imports — create MapboxWrapper, src/config/map/*, src/utils/map.ts first (see "Status in this boilerplate")
import { MapboxWrapper } from '@/components/wrappers/MapboxWrapper'
import type { MapboxWrapperRef } from '@/components/wrappers/MapboxWrapper'
import { MAP_LAYERS } from '@/features/{domain}'
import { MARKER_STYLES } from '@/config/map/marker-styles.config'
import { useLayerStore } from '@/features/{domain}/stores/useLayerStore'
import { useEntityStore } from '@/features/{domain}/stores/useEntityStore'
import { useMapStore } from '@/features/{domain}/stores/useMapStore'
import { useMapDataSources } from '@/features/{domain}/hooks/useMapDataSources'
import { registerMvtSource } from '@/features/{domain}/sources'
import { isMvtSource } from '@/utils/map'
import mapboxgl from 'mapbox-gl'

export function MapBridge() {
  const mapRef = useRef<MapboxWrapperRef>(null)

  const layers = useLayerStore((s) => s.layers)
  const layerFilters = useLayerStore((s) => s.layerFilters)
  const entities = useEntityStore((s) => s.entities)
  const selectedId = useEntityStore((s) => s.selectedId)
  const select = useEntityStore((s) => s.select)
  const { activeStyle, setHoveredFeature, openModal, zoomTarget, setZoomTarget } = useMapStore()
  const markersRef = useRef<mapboxgl.Marker[]>([])

  useMapDataSources(mapRef)

  // ── Layer visibility ───────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map?.isStyleLoaded()) return
    MAP_LAYERS.forEach(({ mapLayerId }) => {
      map.setLayoutProperty(mapLayerId, 'visibility', layers[mapLayerId as keyof typeof layers] !== false ? 'visible' : 'none')
    })
  }, [layers])

  // ── Layer filters (from widgets) ───────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map?.isStyleLoaded()) return
    Object.entries(layerFilters).forEach(([layerId, filter]) => {
      if (map.getLayer(layerId)) {
        map.setFilter(layerId, filter ?? null)
      }
    })
  }, [layerFilters])

  // ── Map style change ───────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map) return
    const styleConfig = MAP_STYLE_OPTIONS[activeStyle]
    map.setStyle(styleConfig.url)
    map.once('style.load', () => {
      if (styleConfig.show3dBuildings && map.getLayer('building')) {
        map.setPaintProperty('building', 'fill-extrusion-height', ['get', 'height'])
        map.setPaintProperty('building', 'fill-extrusion-base', ['get', 'min_height'])
        map.setPaintProperty('building', 'fill-extrusion-opacity', 0.7)
      }
    })
  }, [activeStyle])

  // ── Entity markers ─────────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map) return
    markersRef.current.forEach((m) => m.remove())
    markersRef.current = []
    entities.forEach((entity) => {
      const style = MARKER_STYLES[entity.status ?? 'normal']
      const el = document.createElement('div')
      const root = createRoot(el)
      root.render(
        <div className={`map-marker map-marker--${entity.status}`} style={{ color: style.color, width: style.size, height: style.size }}>
          <i className={`ph-fill ph-${entity.iconName ?? 'map-pin'}`} />
          {style.pulse && <span className="map-marker__pulse" />}
        </div>
      )
      const marker = new mapboxgl.Marker({ element: el }).setLngLat(entity.lngLat).addTo(map)
      if (entity.hover?.enabled) {
        el.addEventListener('mouseenter', () => setHoveredFeature({ type: 'marker', id: entity.id, lngLat: entity.lngLat, data: entity.data ?? {} }))
        el.addEventListener('mouseleave', () => setHoveredFeature(null))
      }
      if (entity.click?.enabled) {
        el.addEventListener('click', () => openModal({ type: 'marker', id: entity.id, data: entity.data ?? {} }))
      } else {
        el.addEventListener('click', () => select(entity.id))
      }
      markersRef.current.push(marker)
    })
    return () => { markersRef.current.forEach((m) => m.remove()) }
  }, [entities])

  // ── Zoom to selected entity ────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current?.getMap()
    const entity = entities.find((e) => e.id === selectedId)
    if (!map || !entity) return
    map.flyTo({ center: entity.lngLat, zoom: 15, duration: 1200 })
  }, [selectedId, entities])

  // ── Zoom target from widgets ───────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!map || !zoomTarget) return
    map.flyTo({ center: zoomTarget.lngLat, zoom: zoomTarget.zoom ?? 14, duration: 1200 })
    setZoomTarget(null)
  }, [zoomTarget])

  // ── Register layers on map load ────────────────────────────────────────────
  function handleMapLoad(map: mapboxgl.Map) {
    MAP_LAYERS.forEach((layer) => {
      if (layer.sourceType === 'geojson' && layer.dataSource?.type !== 'mvt') {
        if (!map.getSource(layer.mapSourceId ?? layer.mapLayerId)) {
          map.addSource(layer.mapSourceId ?? layer.mapLayerId, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
        }
        if (!map.getLayer(layer.mapLayerId)) {
          map.addLayer({
            id: layer.mapLayerId,
            type: layer.layerType,
            source: layer.mapSourceId ?? layer.mapLayerId,
            paint: (layer.paint ?? {}) as mapboxgl.AnyPaint,
            layout: (layer.layout ?? {}) as mapboxgl.AnyLayout,
          })
        }
      }
      if (layer.dataSource && isMvtSource(layer.dataSource)) {
        registerMvtSource(map, layer.mapLayerId, layer.dataSource, layer.paint ?? {}, layer.layerType)
      }

      // Wire hover
      if (layer.hover?.enabled) {
        map.on('mousemove', layer.mapLayerId, (e) => {
          if (!e.features?.length) return
          const feat = e.features[0]
          const data = layer.hover!.popupFields
            ? Object.fromEntries((layer.hover!.popupFields).map((f) => [f, feat.properties?.[f]]))
            : feat.properties ?? {}
          setHoveredFeature({ type: 'layer', id: layer.id, lngLat: [e.lngLat.lng, e.lngLat.lat], data })
          map.getCanvas().style.cursor = 'pointer'
        })
        map.on('mouseleave', layer.mapLayerId, () => {
          setHoveredFeature(null)
          map.getCanvas().style.cursor = ''
        })
      }

      // Wire click
      if (layer.click?.enabled) {
        map.on('click', layer.mapLayerId, (e) => {
          if (!e.features?.length) return
          const feat = e.features[0]
          openModal({
            type: 'layer',
            id: layer.id,
            layerId: layer.mapLayerId,
            modalComponent: layer.click!.modalComponent,
            data: feat.properties ?? {},
            lngLat: [e.lngLat.lng, e.lngLat.lat],
          })
        })
      }
    })
  }

  return (
    <MapboxWrapper
      ref={mapRef}
      mapStyle={MAP_STYLE_OPTIONS[activeStyle].url}
      height="100%"
      width="100%"
      onLoad={handleMapLoad}
    />
  )
}
```

---

## 5. LayerPanel [optional]

Floating panel — top-left by default.

```tsx
// src/features/{domain}/{feature}/components/LayerPanel.tsx
import { MAP_LAYERS_BY_GROUP } from '@/features/{domain}'
import type { LayerGroup } from '@/features/{domain}'
import { useLayerStore } from '@/features/{domain}/stores/useLayerStore'
import { useMapStore } from '@/features/{domain}/stores/useMapStore'
import { LayerLegend } from './LayerLegend'

const GROUP_ORDER: LayerGroup[] = ['GROUP_A', 'GROUP_B']  // define per domain

export function LayerPanel() {
  const layerPanelOpen = useMapStore((s) => s.layerPanelOpen)
  const toggleLayerPanel = useMapStore((s) => s.toggleLayerPanel)
  const layers = useLayerStore((s) => s.layers)
  const { toggleLayer, toggleGroup } = useLayerStore()

  return (
    <div className="map-layer-panel">
      {/* Toggle button — always visible */}
      <button className="map-layer-panel__toggle" onClick={toggleLayerPanel} aria-label="Toggle layer panel">
        <i className={`ph ph-${layerPanelOpen ? 'caret-left' : 'stack'}`} />
      </button>

      {layerPanelOpen && (
        <div className="map-layer-panel__body">
          {GROUP_ORDER.map((group) => {
            const items = MAP_LAYERS_BY_GROUP[group]
            if (!items?.length) return null
            const groupIds = items.map((l) => l.id as LayerId)
            const allVisible = groupIds.every((id) => layers[id] !== false)
            const groupConfig = MAP_GROUP_CONFIG[group]

            return (
              <section key={group} className="map-layer-panel__group">
                {/* Group header — icon, label, group toggle */}
                <div className="map-layer-panel__group-header">
                  {groupConfig?.icon && <i className={`ph ph-${groupConfig.icon}`} />}
                  <span className="map-layer-panel__group-label">{groupConfig?.label ?? group}</span>
                  <input
                    type="checkbox"
                    checked={allVisible}
                    onChange={() => toggleGroup(groupIds)}
                    aria-label={`Toggle all ${group} layers`}
                  />
                </div>

                {/* Layer items */}
                {items.map((layer) => (
                  <div key={layer.id} className="map-layer-panel__item">
                    <label className="map-layer-panel__row">
                      <input
                        type="checkbox"
                        checked={layers[layer.id as LayerId] !== false}
                        onChange={() => toggleLayer(layer.id as LayerId)}
                      />
                      {layer.icon && <i className={`ph ph-${layer.icon}`} aria-hidden="true" />}
                      <span>{layer.label}</span>
                    </label>
                    {/* Legend */}
                    {layer.legend && layers[layer.id as LayerId] !== false && (
                      <LayerLegend legend={layer.legend} />
                    )}
                  </div>
                ))}
              </section>
            )
          })}
        </div>
      )}
    </div>
  )
}
```

### LayerLegend — exact vs range

```tsx
// src/features/{domain}/{feature}/components/LayerLegend.tsx
import type { TLayerLegend } from '@/features/{domain}'

export function LayerLegend({ legend }: { legend: TLayerLegend }) {
  if (legend.type === 'exact') {
    return (
      <ul className="map-legend map-legend--exact">
        {legend.items.map((item) => (
          <li key={item.label} className="map-legend__item">
            {item.icon
              ? <i className={`ph ph-${item.icon}`} style={{ color: item.color }} />
              : <span className="map-legend__dot" style={{ background: item.color }} />
            }
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
    )
  }

  // range — gradient bar
  const gradient = legend.colorStops
    .map((s) => `${s.color} ${s.value * 100}%`)
    .join(', ')
  return (
    <div className="map-legend map-legend--range">
      <div className="map-legend__bar" style={{ background: `linear-gradient(to right, ${gradient})` }} />
      <div className="map-legend__labels">
        <span>{legend.min}{legend.unit}</span>
        <span>{legend.max}{legend.unit}</span>
      </div>
    </div>
  )
}
```

---

## 6. HoverPopup [optional]

Renders when `useMapStore.hoveredFeature` is non-null. Positioned at cursor.

```tsx
// src/features/{domain}/{feature}/components/HoverPopup.tsx
import { useMapStore } from '@/features/{domain}/stores/useMapStore'
import { useEffect, useRef } from 'react'

export function HoverPopup() {
  const hovered = useMapStore((s) => s.hoveredFeature)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!hovered || !ref.current) return
    const onMove = (e: MouseEvent) => {
      if (!ref.current) return
      ref.current.style.left = `${e.clientX + 12}px`
      ref.current.style.top = `${e.clientY + 12}px`
    }
    window.addEventListener('mousemove', onMove)
    return () => window.removeEventListener('mousemove', onMove)
  }, [hovered])

  if (!hovered) return null

  return (
    <div ref={ref} className="map-hover-popup" style={{ position: 'fixed', pointerEvents: 'none', zIndex: 1000 }}>
      {Object.entries(hovered.data).map(([key, val]) => (
        <div key={key} className="map-hover-popup__row">
          <span className="map-hover-popup__key">{key}</span>
          <span className="map-hover-popup__val">{String(val)}</span>
        </div>
      ))}
    </div>
  )
}
```

---

## 7. MapModal [optional]

Renders when `useMapStore.clickedFeature` is non-null. Uses the shadcn `Sheet` (side panel keeps the map
visible) — swap for `Dialog` when the content is a short confirmation. Never a hand-built overlay.

```tsx
// src/features/{domain}/{feature}/components/MapModal.tsx
import { Fragment } from 'react'

import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { useMapStore } from '@/features/{domain}/stores/useMapStore'
import { MAP_MODAL_REGISTRY } from '@/features/{domain}/config/modal-registry'

export function MapModal() {
  const clicked = useMapStore((s) => s.clickedFeature)
  const closeModal = useMapStore((s) => s.closeModal)

  const ModalContent = clicked?.modalComponent ? MAP_MODAL_REGISTRY[clicked.modalComponent] : null

  return (
    <Sheet open={!!clicked} onOpenChange={(open) => !open && closeModal()}>
      <SheetContent side="right" className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{clicked?.title ?? 'Feature details'}</SheetTitle>
          <SheetDescription>Selected on the map</SheetDescription>
        </SheetHeader>
        {clicked && (ModalContent
          ? <ModalContent data={clicked.data} lngLat={clicked.lngLat} />
          : (
            <dl className="grid grid-cols-[max-content_1fr] gap-x-8 gap-y-3 px-4 text-sm">
              {Object.entries(clicked.data).map(([k, v]) => (
                <Fragment key={k}>
                  <dt className="text-muted-foreground">{k}</dt>
                  <dd className="text-foreground tabular-nums">{String(v)}</dd>
                </Fragment>
              ))}
            </dl>
          ))}
      </SheetContent>
    </Sheet>
  )
}
```

`MAP_MODAL_REGISTRY` maps component name strings to React components — registered once per domain.

---

## 8. MapStyleSwitcher [optional]

```tsx
// src/features/{domain}/{feature}/components/MapStyleSwitcher.tsx
// create src/config/map/map-styles.config.ts first (Pattern B recipe)
import { MAP_STYLE_OPTIONS } from '@/config/map/map-styles.config'
import { useMapStore } from '@/features/{domain}/stores/useMapStore'
import type { MapStyleKey } from '@/config/map/map-styles.config'

export function MapStyleSwitcher() {
  const activeStyle = useMapStore((s) => s.activeStyle)
  const setActiveStyle = useMapStore((s) => s.setActiveStyle)

  // shadcn ToggleGroup (`npx shadcn@latest add toggle-group` if missing) inside a floating card
  return (
    <div className="rounded-xl border border-border bg-card p-1 shadow-md">
      <ToggleGroup
        type="single"
        value={activeStyle}
        onValueChange={(value) => value && setActiveStyle(value as MapStyleKey)}
        aria-label="Map style"
      >
        {(Object.values(MAP_STYLE_OPTIONS) as TMapStyleOption[]).map((style) => (
          <ToggleGroupItem key={style.id} value={style.id} aria-label={style.label} title={style.label}>
            <i className={`ph ${style.icon}`} aria-hidden="true" />
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  )
}
```

`map-styles.config.ts`:

```ts
export type MapStyleKey = 'satellite' | 'satellite3d' | 'dark' | 'tactical' | 'navigation' | 'topo'

export type TMapStyleOption = {
  id: MapStyleKey
  label: string
  icon: string          // Phosphor icon name
  url: string
  show3dBuildings: boolean
}

export const MAP_STYLE_OPTIONS: Record<MapStyleKey, TMapStyleOption> = {
  satellite: {
    id: 'satellite',
    label: 'Satellite',
    icon: 'ph-planet',
    url: 'mapbox://styles/mapbox/satellite-streets-v12',
    show3dBuildings: false,
  },
  satellite3d: {
    id: 'satellite3d',
    label: '3D Satellite',
    icon: 'ph-buildings',
    url: 'mapbox://styles/mapbox/satellite-streets-v12',
    show3dBuildings: true,
  },
  dark: {
    id: 'dark',
    label: 'Dark',
    icon: 'ph-moon',
    url: 'mapbox://styles/mapbox/dark-v11',
    show3dBuildings: false,
  },
  tactical: {
    id: 'tactical',
    label: 'Tactical',
    icon: 'ph-crosshair',
    url: 'mapbox://styles/mapbox-i2/cmmn8lx0o000c01s9089yfbrj',
    show3dBuildings: false,
  },
  navigation: {
    id: 'navigation',
    label: 'Navigation',
    icon: 'ph-compass',
    url: 'mapbox://styles/mapbox/navigation-night-v1',
    show3dBuildings: false,
  },
  topo: {
    id: 'topo',
    label: 'Topo',
    icon: 'ph-mountains',
    url: 'mapbox://styles/mapbox-i2/cmmi55ltt00as01qucz65bkxa',
    show3dBuildings: false,
  },
}
```

---

## 9. GeoSearch [optional]

```tsx
// src/features/{domain}/{feature}/components/GeoSearch.tsx
import { useState } from 'react'
import { useMapStore } from '@/features/{domain}/stores/useMapStore'

export function GeoSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<TGeoSearchResult[]>([])
  const setSearchResult = useMapStore((s) => s.setSearchResult)
  const setZoomTarget = useMapStore((s) => s.setZoomTarget)
  const MAPBOX_TOKEN = env.map.mapboxToken   // import env from '@/config/env'

  if (!MAPBOX_TOKEN) {
    throw new Error('Missing VITE_MAPBOX_TOKEN')
  }

  async function search(q: string) {
    if (!q.trim()) return
    const res = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(q)}.json?access_token=${MAPBOX_TOKEN}&limit=5`
    )
    const json = await res.json()
    setResults((json.features as Array<{ id: string; place_name: string; geometry: { coordinates: [number, number] } }>).map((f) => ({
      id: f.id,
      label: f.place_name,
      lngLat: f.geometry.coordinates as [number, number],
    })))
  }

  function select(result: TGeoSearchResult) {
    setSearchResult(result)
    setZoomTarget({ lngLat: result.lngLat, zoom: 14 })
    setResults([])
    setQuery(result.label)
  }

  // Structure only — build it as shadcn Input + Popover + Command (see "Map UI chrome" above):
  // the results list must be keyboard-navigable (Command), not clickable <li>s.
  return (
    <div className="relative w-72">
      <i className="ph ph-magnifying-glass pointer-events-none absolute top-5 left-3 size-4 -translate-y-1/2 text-base leading-none text-muted-foreground" aria-hidden="true" />
      <Input
        value={query}
        onChange={(e) => { setQuery(e.target.value); search(e.target.value) }}
        placeholder="Search location…"
        aria-label="Search location"
        className="h-10 bg-card pl-9 shadow-md"
      />
      {results.length > 0 && (
        <Command className="mt-1 rounded-xl border border-border bg-popover shadow-md">
          <CommandList>
            {results.map((r) => (
              <CommandItem key={r.id} value={r.label} onSelect={() => select(r)}>
                <i className="ph ph-map-pin text-muted-foreground" aria-hidden="true" />
                {r.label}
              </CommandItem>
            ))}
          </CommandList>
        </Command>
      )}
    </div>
  )
}
```

---

## 10. Floating Widgets [optional]

Floating widgets use the existing `dynamic-widget` skill components. They are positioned freely over the map.

### Widget Config

```ts
// widgets.config.ts
export type TFloatingWidgetConfig = {
  id: string
  position: { top?: string; bottom?: string; left?: string; right?: string }
  layout: 'flat' | 'tabs'   // flat = stacked list, tabs = grouped tabs
  widgets: TDynamicWidgetConfig[]  // same schema as dynamic-widget skill
}

export const FLOATING_WIDGETS: TFloatingWidgetConfig[] = [
  {
    id: 'top-stats',
    position: { top: '16px', right: '16px' },
    layout: 'flat',
    widgets: [
      { id: 'total-count', type: 'stat', title: 'Total', ... },
      { id: 'status-list', type: 'list', title: 'Status', ... },
    ],
  },
]
```

### FloatingWidgetContainer

```tsx
// src/features/{domain}/{feature}/components/FloatingWidgetContainer.tsx
import { FLOATING_WIDGETS } from '@/features/{domain}/config/widgets.config'
// not present yet — build src/modules/dynamic-widget via .claude/skills/reactjs-dynamic-widget/SKILL.md
import { DynamicWidget } from '@/modules/dynamic-widget'

export function FloatingWidgetContainer() {
  return (
    <>
      {FLOATING_WIDGETS.map((container) => (
        <div
          key={container.id}
          className="map-float-widget"
          style={{ position: 'absolute', ...container.position, zIndex: 10, pointerEvents: 'auto' }}
        >
          {container.layout === 'tabs' ? (
            <FloatingTabsWidget config={container} />
          ) : (
            <div className="map-float-widget__flat">
              {container.widgets.map((w) => (
                <DynamicWidget key={w.id} config={w} />
              ))}
            </div>
          )}
        </div>
      ))}
    </>
  )
}
```

### Running Text Ticker [optional]

```tsx
// src/features/{domain}/{feature}/components/MapTicker.tsx
type TTickerProps = {
  items: string[]
  position?: 'top' | 'bottom'
  speed?: number  // px/s, default 60
}

export function MapTicker({ items, position = 'bottom', speed = 60 }: TTickerProps) {
  return (
    <div className={`map-ticker map-ticker--${position}`}>
      <div
        className="map-ticker__track"
        style={{ '--ticker-speed': `${speed}px` } as React.CSSProperties}
      >
        {[...items, ...items].map((item, i) => (
          <span key={i} className="map-ticker__item">{item}</span>
        ))}
      </div>
    </div>
  )
}
```

### Widget → Layer Filter Interaction

Widget emits a filter value → `useLayerStore.setLayerFilter` → MapBridge applies `map.setFilter()`.

```tsx
// Inside a widget component
const setLayerFilter = useLayerStore((s) => s.setLayerFilter)

function onFilterChange(value: string) {
  // Mapbox filter expression
  setLayerFilter('ZONE_FILL', ['==', ['get', 'status'], value])
}
```

### Layer → Widget Filter Interaction

User clicks a map feature → `useMapStore.clickedFeature` → widget reads and filters its data.

```tsx
// Inside a widget component
const clicked = useMapStore((s) => s.clickedFeature)

const filteredData = useMemo(
  () => clicked ? data.filter((d) => d.zoneId === clicked.data.id) : data,
  [data, clicked]
)
```

### Zoom to Location from Widget

```tsx
// Inside a widget component
const setZoomTarget = useMapStore((s) => s.setZoomTarget)

function onRowClick(lngLat: [number, number]) {
  setZoomTarget({ lngLat, zoom: 15 })
}
```

MapBridge `useEffect([zoomTarget])` picks this up and calls `map.flyTo()`.

---

## 11. Data Sources

### REST — one-shot or polling

```ts
dataSource: {
  type: 'rest',
  url: '/api/zones/geojson',
  pollingInterval: 30_000,     // omit for one-shot
  transform: (raw) => raw as GeoJSON.FeatureCollection,
},
```

### WebSocket — real-time

```ts
dataSource: {
  type: 'websocket',
  url: 'wss://api.example.com/ws/positions',
  updateStrategy: 'upsert',    // 'replace' | 'append' | 'upsert'
  reconnect: 'exponential',
  maxFeatures: 500,            // required when updateStrategy is 'append'
  transform: (raw) => { /* raw → GeoJSON.Feature */ },
},
```

### MVT — vector tiles

```ts
dataSource: {
  type: 'mvt',
  tiles: ['https://tiles.example.com/data/{z}/{x}/{y}.pbf'],
  sourceLayer: 'data',
  minzoom: 8,
  maxzoom: 18,
},
```

---

## Definition of Done

- [ ] All layers registered in `MAP_LAYERS` with explicit `layerType` and `sourceType`
- [ ] `paint` references `LAYER_PAINT[preset]` — no inline paint objects
- [ ] Hover and click config declared in layer entry — not wired manually in component
- [ ] Legend declared in layer entry for any layer with color meaning
- [ ] `useMapStore` created with all required fields
- [ ] `useLayerStore` includes `toggleGroup` and `setLayerFilter`
- [ ] `MapBridge` has one `useEffect` per concern
- [ ] `LayerPanel` reads only `MAP_LAYERS_BY_GROUP` and `useLayerStore` + `useMapStore.layerPanelOpen`
- [ ] `HoverPopup` imports zero `mapbox-gl` — reads `useMapStore.hoveredFeature` only
- [ ] `MapModal` imports zero `mapbox-gl` — reads `useMapStore.clickedFeature` only
- [ ] Floating widgets use `DynamicWidget` — no custom widget components unless necessary
- [ ] Widget→layer filter goes through `useLayerStore.setLayerFilter`
- [ ] Layer→widget interaction goes through `useMapStore.clickedFeature`
- [ ] Zoom-to-location goes through `useMapStore.setZoomTarget`
- [ ] No `mapbox-gl` imports outside `MapBridge`
- [ ] All markers cleaned up in `useEffect` return

> Layout shell: `.claude/skills/reactjs-app-layout/SKILL.md`
> Dynamic widgets: `.claude/skills/reactjs-dynamic-widget/SKILL.md`
> Detailed rules: [references/map-rules.md](references/map-rules.md)
> Tactical domain override: [../reactjs-tactical-map/SKILL.md](../reactjs-tactical-map/SKILL.md)

---

## 12. MapPlugin Module — Config-driven Map from ERP Export

Use this section when `visualization_type === "mapPlugin"` in a migrated ERP dashboard widget.
(The `erp-dashboard-migrator` skill that originally carried the full migration pattern is not
installed in this repo.) `src/modules/map-plugin/` does not exist yet — create it on demand from
this section, which is the reference.

> **UI styling contract** — before touching any file in `src/modules/map-plugin/components/`, read
> [`references/map-plugin-ui-contract.md`](references/map-plugin-ui-contract.md) first. It defines
> the Tailwind-vs-inline rule, light-theme design tokens for panel chrome, z-index stack, dark
> overlay pattern for map-surface buttons, ResizeObserver pattern, and the full slot code contracts
> for `MapPluginShell`, `MapSideSlot`, `MapBottomSlot`, `MapStickySlot`, `MapTooltip`.

### Overview

`MapPluginWidget` is a **config-driven** Mapbox map. Instead of a static `MAP_LAYERS` array
built by a developer, it reads layer definitions at runtime from `maps_*.json` exported from the ERP.

**All overlay widgets (top / side / sticky / bottom positions) are scaffolded as static React
components — not rendered via a generic engine or Handlebars.** Each `widgetId` maps to a
hand-crafted React component registered in `MAP_WIDGET_REGISTRY` (domain-level).

### Module location

```
src/modules/map-plugin/        ← reusable engine, never domain-specific
```

Full scaffolding → the file structure below (create on demand).

### Separation of concerns

```
src/modules/map-plugin/        ← engine (create on demand): helpers, renderers, store, slot containers, widget-host, types
src/features/dashboard/{page}/ ← domain data: maps.json, config parser, widgets/, page component
```

The module **never** imports from `src/features/`. The domain **always** imports from the module via barrel:

```ts
import { MapPluginWidget, useMapPluginStore } from '@/modules/map-plugin'
```

### Full file structure

```
src/modules/map-plugin/              ← create on demand
├── types/
│   └── index.ts                     ← MapPluginConfig, MapLayerConfig, TooltipConfig,
│                                       LayerType, SourceType, VisualChannel, SizeChannel,
│                                       LabelChannel, IconChannel, ThresholdChannel,
│                                       MapWidgetPosition ('top'|'side'|'sticky'|'bottom')
├── store/
│   └── useMapPluginStore.ts         ← global store keyed by maps_id
│                                       InstanceState: layerVisibility, clickedFeature,
│                                       tooltipPosition, sortConfig, dateFilter
│                                       actions: setLayerVisibility, setClickedFeature,
│                                       clearClickedFeature, setSortConfig, setDateFilter
├── helpers/
│   ├── data-driven.ts               ← renderColorStyle, renderColorAndOpacity,
│   │                                   generateColorRange, generateIconRange, rendersizeRange
│   ├── color-scale.ts               ← d3 replacement: scaleLinear, scaleOrdinal,
│   │                                   generateRangeStep (pure math, no external deps)
│   ├── mapbox-utils.ts              ← layersUpper, getFieldsVisualChannels,
│   │                                   MAP_STYLE_URLS: Record<defaultStyle, mapboxStyleUrl>
│   └── render-layer/
│       ├── polygon-layer.ts         ← renderPolygonV2
│       ├── point-layer.ts           ← renderPointV2
│       ├── line-layer.ts            ← renderLine, renderLineRelation
│       ├── heatmap-layer.ts         ← renderHeatmap
│       ├── icon-layer.ts            ← renderIconV2
│       ├── cluster-layer.ts         ← renderCluster
│       └── index.ts                 ← LAYER_RENDERERS: Record<LayerType, RenderFn>
├── hooks/
│   └── useMapLayers.ts              ← iterates config.layers → renderLayersMvt per layer
├── components/
│   ├── MapPluginShell.tsx           ← Mapbox init + layout orchestrator
│   ├── MapLayerPanel.tsx            ← layer show/hide panel (groups + legend)
│   ├── MapTooltip.tsx               ← click tooltip dispatcher
│   ├── tooltip/
│   │   ├── TooltipTemplate.tsx      ← developer.html → React nodes (no innerHTML)
│   │   └── TooltipAutoFields.tsx    ← auto rows from fields[] + fieldsAlias[]
│   ├── MapPluginWidget.tsx          ← entry point: props referenceId + configs + widgetRegistry
│   │
│   ├── slots/                       ← layout slot containers, position-specific wrappers
│   │   ├── MapTopSlot.tsx           ← absolute top-left over canvas
│   │   ├── MapSideSlot.tsx          ← absolute right, supports floating/inside mode + tabs/scroll
│   │   ├── MapStickySlot.tsx        ← absolute bottom-center over canvas
│   │   └── MapBottomSlot.tsx        ← static below map row, collapsible with animation
│   │
│   └── widget-host/
│       └── MapWidgetHost.tsx        ← lookup widgetId in registry → render component
└── index.ts                         ← barrel: MapPluginWidget, useMapPluginStore, types

src/features/dashboard/{page}/
├── data/
│   └── maps.json                    ← copy of dashboard-migrator/maps.json
├── config/
│   └── map-plugin.config.ts         ← MAP_PLUGIN_CONFIGS: Record<mapsId, MapPluginConfig>
├── widgets/                         ← ALL map overlay widgets as static React components
│   ├── index.ts                     ← barrel + MAP_WIDGET_REGISTRY
│   ├── sorting/
│   │   └── {WidgetName}Sorting.tsx  ← type=sorting → local sort state + store dispatch
│   ├── top/
│   │   └── {WidgetName}Widget.tsx
│   ├── side/
│   │   └── {WidgetName}Widget.tsx
│   ├── sticky/
│   │   └── {WidgetName}Widget.tsx
│   └── bottom/
│       └── {WidgetName}Widget.tsx
└── components/
    └── {PageName}Page.tsx
```

### Entry point

```tsx
// src/features/dashboard/{page}/components/{PageName}Page.tsx
import { MapPluginWidget } from '@/modules/map-plugin'
import { MAP_PLUGIN_CONFIGS } from '../config/map-plugin.config'
import { MAP_WIDGET_REGISTRY } from '../widgets'

// Inside widget switch / devtools-map:
case 'mapPlugin':
  return (
    <MapPluginWidget
      referenceId={widget._extra?.referenceId}
      configs={MAP_PLUGIN_CONFIGS}
      widgetRegistry={MAP_WIDGET_REGISTRY}
      className="h-full w-full"
    />
  )
```

### Config parser per domain

```ts
// src/features/dashboard/{page}/config/map-plugin.config.ts
import rawMaps from '../data/maps.json'
import type { MapPluginConfig } from '@/modules/map-plugin'

export const MAP_PLUGIN_CONFIGS: Record<string, MapPluginConfig> =
  Object.fromEntries(
    (rawMaps as any[])
      .filter((m) => m.maps_id || m.id)
      .map((m) => [m.maps_id ?? m.id, applyInferredTypes(m)])
  )

function applyInferredTypes(m: any): MapPluginConfig {
  return {
    ...m,
    layers: m.layers.map((l: any) => ({
      ...l,
      type: l.type || inferLayerType(l.config?.columnType),
      sourceType: l.sourceType || 'mvt',
    })),
  }
}

function inferLayerType(columnType?: string): string {
  if (columnType === 'latlon') return 'point'
  if (columnType === 'geojson') return 'polygon'
  return 'point'
}
```

### MAP_WIDGET_REGISTRY — widget resolver

```ts
// src/features/dashboard/{page}/widgets/index.ts
import type { FC } from 'react'
import { RevenueChartWidget } from './bottom/RevenueChartWidget'
import { StatusSummaryWidget } from './side/StatusSummaryWidget'
import { RegionSortingWidget } from './sorting/RegionSortingWidget'

export const MAP_WIDGET_REGISTRY: Record<string, FC<{ mapsId: string }>> = {
  'widget-id-abc123': RevenueChartWidget,
  'widget-id-def456': StatusSummaryWidget,
  'widget-id-ghi789': RegionSortingWidget,
}
```

Key = `widgetId` from `maps.json` widgets array. One entry per overlay widget. Missing IDs log a
`console.warn` in dev and render `null`.

### MapWidgetHost — resolver component

```tsx
// src/modules/map-plugin/components/widget-host/MapWidgetHost.tsx
import type { FC } from 'react'

type Props = {
  widgetId: string
  mapsId: string
  registry: Record<string, FC<{ mapsId: string }>>
}

export function MapWidgetHost({ widgetId, mapsId, registry }: Props) {
  const Widget = registry[widgetId]
  if (!Widget) {
    if (env.app.isDev) console.warn(`[MapWidgetHost] no component for widgetId: ${widgetId}`)
    return null
  }
  return <Widget mapsId={mapsId} />
}
```

The module never knows what the widget renders — that is the domain's responsibility.

### Slot containers

#### MapPluginShell — layout orchestrator

```tsx
// src/modules/map-plugin/components/MapPluginShell.tsx
// Layout:
<div className="relative h-full w-full flex flex-col">
  {/* Map canvas area + all absolute-positioned slots */}
  <div className="relative flex-1 min-h-0">
    <MapboxGL ... />                         {/* canvas */}

    {/* Layer panel — top-left, absolute */}
    <div className="absolute top-4 left-4 z-10 flex flex-col items-start gap-2">
      <Button size="icon" variant="outline" className="shadow-md" aria-label="Toggle layers" onClick={toggleLayerPanel}>
        <i className="ph ph-stack" aria-hidden="true" />
      </Button>
      {layerPanelOpen && <MapLayerPanel mapsId={mapsId} config={config} />}
    </div>

    {/* Top slot — top-left below layer toggle, absolute */}
    {topWidgets.length > 0 && (
      <MapTopSlot mapsId={mapsId} widgets={topWidgets} registry={widgetRegistry} />
    )}

    {/* Side slot — right edge, absolute (floating or inside mode) */}
    {sideWidgets.length > 0 && (
      <MapSideSlot
        mapsId={mapsId}
        widgets={sideWidgets}
        sortingWidgets={sortingWidgets}
        registry={widgetRegistry}
        mode={config.mapStyle?.rightWidgetLayout ?? 'floating'}
        scrollSide={config.mapStyle?.widgets?.scrollSide}
        scrollSideTabs={config.mapStyle?.widgets?.scrollSideTabs}
        hideSideTitle={config.mapStyle?.widgets?.hideSideTitle}
        width={config.mapStyle?.widthInsideDetail}
        hasDateFilter={!!config.mapStyle?.showdateFilter}
      />
    )}

    {/* Sticky slot — bottom center, absolute */}
    {stickyWidgets.length > 0 && (
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 z-10">
        <MapStickySlot mapsId={mapsId} widgets={stickyWidgets} registry={widgetRegistry} />
      </div>
    )}
  </div>

  {/* Bottom slot — static flow, below canvas */}
  {bottomWidgets.length > 0 && (
    <MapBottomSlot
      mapsId={mapsId}
      widgets={bottomWidgets}
      registry={widgetRegistry}
      defaultCollapsed={config.mapStyle?.widgets?.defaultCollapsed}
      containerWidth={config.mapStyle?.WidgetBottomWidth ?? '83vw'}
      justifyContent={config.mapStyle?.JustifyContent ?? 'justify-content-center'}
      collapseHeight={config.mapStyle?.WidgetBottomCollapseHeight ?? '0px'}
    />
  )}
</div>
```

Widget arrays derived by filtering `config.widgets` by `position` field before passing to slots.

#### MapSideSlot — two render modes

```
MapSideSlot
├── toggle button (chevron, absolute) — right offset = widgetWidth when open
├── mode="floating"  → absolute right, overlays canvas, does not shrink map
└── mode="inside"    → flex sibling panel, shrinks map canvas when open

Both modes render:
  ├── sorting widgets FIRST (above tabs/scroll, no Tab wrapper)
  └── regular widgets:
      ├── scrollSide: true  → stacked vertically, overflow-y-auto
      └── scrollSide: false → Tab.Container per widget (key = widget.name)
          └── scrollSideTabs: true → tab nav scrollable horizontally
```

#### MapBottomSlot — collapsible with animation

```
MapBottomSlot
├── chevron toggle button
├── defaultCollapsed: true  → collapsed by default, expand on click
├── defaultCollapsed: false → expanded by default, collapse on click
└── widget row: flex, justify from config, width from config
    └── MapWidgetHost per widget (width/height from dataMaps.widgets[].width/height)
```

Animation: `max-height` transition `0.5s cubic-bezier(0.4, 0, 0.2, 1)` between `collapseHeight` and `1000px`.

### Widget scaffold rules — all positions

**Every overlay widget becomes a dedicated React component.** No generic engine, no Handlebars, no `ChartComponent` wrapper.

```tsx
// src/features/dashboard/{page}/widgets/bottom/RevenueChartWidget.tsx
// EChartWrapper is not present yet — create it via .claude/skills/reactjs-chart/SKILL.md
import { EChartWrapper } from '@/components/wrappers/EChartWrapper'
import { useResolvedTheme } from '@/hooks/use-resolved-theme'

import { useRevenueData } from '../hooks/useRevenueData'

export function RevenueChartWidget({ widgetId, mapsId }: { widgetId: string; mapsId: string }) {
  const mode = useResolvedTheme()
  const { data, isPending } = useRevenueData(widgetId, mapsId)
  if (isPending) return <div className="map-widget-loading" />
  return <EChartWrapper option={buildBarOption(data)} mode={mode} height={240} />
}
```

Data hook reads filters from store — no prop drilling. **Overlay widgets are still page widgets**
(the widget backend + `src/services/widget.service.ts` are not part of this boilerplate — create the
service with `apiRequests` from `src/services/api-factory.service.ts` against your widget API):
they fetch through the same `POST /widget/get-data` endpoint as every non-map widget (via
`widgetService.getData` / `use-widget-data`), keyed by the overlay's `widgetId`. Never give a map
overlay widget its own bespoke fetch service — that duplicates the standard widget data contract.

```ts
// src/features/dashboard/{page}/widgets/hooks/useRevenueData.ts
// create src/services/widget.service.ts first (not present in the boilerplate)
import { widgetService } from '@/services/widget.service'

function useRevenueData(widgetId: string, mapsId: string) {
  const dateFilter = useMapPluginStore((s) => s.instances[mapsId]?.dateFilter)
  const sortConfig  = useMapPluginStore((s) => s.instances[mapsId]?.sortConfig)

  return useQuery({
    queryKey: ['revenue', widgetId, mapsId, dateFilter, sortConfig],
    queryFn: () => widgetService.getData(widgetId, { dateFilter, sortConfig }),
  })
}
```

### Sorting widget scaffold

`type === 'sorting'` widgets control sort order for sibling widgets. Rendered above the tab/scroll
list in `MapSideSlot` (not inside a Tab.Pane).

```tsx
// src/features/dashboard/{page}/widgets/sorting/RegionSortingWidget.tsx
import { useMapPluginStore } from '@/modules/map-plugin'

const SORT_OPTIONS = [
  { label: 'Nama A–Z',       value: { field: 'name',  order: 'asc'  } },
  { label: 'Nilai Tertinggi', value: { field: 'value', order: 'desc' } },
]

export function RegionSortingWidget({ mapsId }: { mapsId: string }) {
  const setSortConfig = useMapPluginStore((s) => s.setSortConfig)
  const sortConfig    = useMapPluginStore((s) => s.instances[mapsId]?.sortConfig)

  return (
    <div className="map-sorting-widget">
      {SORT_OPTIONS.map((opt) => (
        <button
          key={opt.value.field + opt.value.order}
          className={sortConfig?.field === opt.value.field ? 'active' : ''}
          onClick={() => setSortConfig(mapsId, opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
```

Sibling widget hooks read `useMapPluginStore((s) => s.instances[mapsId]?.sortConfig)` and include
it in their `queryKey` — no prop or event bus needed.

### Store — global, keyed by maps_id

```ts
// useMapPluginStore.ts shape
interface InstanceState {
  layerVisibility:  Record<string, boolean>
  clickedFeature:   { layerId: string; properties: Record<string, any> } | null
  tooltipPosition:  { x: number; y: number } | null
  sortConfig:       { field: string; order: 'asc' | 'desc' } | null   // driven by sorting widget
  dateFilter:       { type: string; start?: string; end?: string } | null  // driven by date controls
}

interface MapPluginState {
  instances: Record<string, InstanceState>   // key = maps_id
  setLayerVisibility: (mapsId: string, layerId: string, visible: boolean) => void
  setClickedFeature:  (mapsId: string, feature: InstanceState['clickedFeature'], pos: { x: number; y: number }) => void
  clearClickedFeature:(mapsId: string) => void
  setSortConfig:      (mapsId: string, config: InstanceState['sortConfig']) => void
  setDateFilter:      (mapsId: string, filter: InstanceState['dateFilter']) => void
}
```

One store instance, all map instances isolated by `mapsId` key. Multiple `MapPluginWidget` on the
same page coexist without collision.

### Helpers — color-scale (d3 replacement)

`src/modules/map-plugin/helpers/color-scale.ts` (create it with the module) provides the same interface as d3 without the dependency:

| d3 equivalent | local helper |
|---|---|
| `d3.scaleQuantile().domain(data).range(colors)` | `scaleQuantile(data, colors)` |
| `d3.scaleOrdinal().domain(data).range(colors)` | `scaleOrdinal(data, colors)` |
| `d3.scaleLinear().domain([min,max]).range(sizeRange)` | `scaleLinear([min,max], sizeRange)` |
| `d3.min(arr)` / `d3.max(arr)` | `arrayMin(arr)` / `arrayMax(arr)` |
| `d3.color(hex).formatHex()` | `hexToHex(hex)` (passthrough) |
| `d3.color(hex).formatRgb()` | `hexToRgb(hex)` |

### Expression style — MVT caveat

For MVT layers, `features[]` are unavailable at init. `generateColorRange` will receive an empty
array. In this case the helper falls back to the solid color (`fillColor.color`). Data-driven
expressions activate automatically on subsequent tile loads when features become available.

**Do not** try to fetch features before `map.addLayer()` for MVT — Mapbox manages tile loading.

### Tooltip — React component, not innerHTML

`TooltipTemplate` and `TooltipAutoFields` are reusable across domains:

```tsx
// If developer.html present → parsed to React nodes
<TooltipTemplate html={tooltipConfig.developer.html} css={tooltipConfig.developer.css} data={feature.properties} title={tooltipConfig.title} />

// If no developer.html → auto field list
<TooltipAutoFields fields={tooltipConfig.fields} fieldsAlias={tooltipConfig.fieldsAlias} data={feature.properties} title={tooltipConfig.title} />
```

`TooltipTemplate` tokenizer handles:
- `{{data.fieldName}}` → `String(data[fieldName] ?? '')`
- `{{thousandFormat data.field maxFractionDigits=N}}` → `Intl.NumberFormat` with fraction digits
- `{{thousandFormat data.field locale="id-ID"}}` → locale-aware number format
- Static HTML segments → rendered as plain text nodes inside React fragment

### MVT tile URL

A `map.service.ts` helper `layerTileUrl(layerId)` builds the tile source URL (create
`src/services/map.service.ts`; the `/map` tile router is not in this backend — see
`.claude/skills/fastapi-render-map/SKILL.md`). The web reaches the backend through
`env.api.baseUrl` (default `/api/v1/apps`, proxied to the backend with the prefix stripped).

```ts
// map.service.ts — correct implementation
layerTileUrl: (layerId: string): string => {
  // env from '@/config/env'; Mapbox needs an absolute tile URL
  const base = env.api.baseUrl.startsWith('/') ? `${window.location.origin}${env.api.baseUrl}` : env.api.baseUrl
  return `${base}/map/${layerId}/{z}/{x}/{y}.pbf`   // ← /map/ only, never /api/map/
},
```

> **Common mistake:** adding another `/api` segment (`${base}/api/map/...`) — the backend
> serves the router at `/map/...` and the proxy already strips `/api/v1/apps`.

If tiles come from a different host, add `VITE_MAP_TILE_URL` to the zod schema in
`src/config/env.ts` (+ `env/.env.example`) and read it through `env` — never `import.meta.env`.

### Layer types supported

`polygon` · `point` · `icon` · `lineString` · `arc` · `lineRelation` · `line` · `heatmap` · `cluster`

Types `grid` / `hex` / `pie` → log warning, skip render.

### `enableAlert` — pulse animation on point layers

When `config.visConfig.enableAlert === true`, `renderPointV2` adds a pulsing ring behind the circle layer. Color and size derive from `visualChannels.fillColor` and `visualChannels.radiusSize`.

**Pattern (Mapbox `StyleImageInterface` with `onAdd` canvas):**

```ts
// CORRECT: canvas created inside onAdd, not in constructor
const pulseMarker = {
  width: SIZE, height: SIZE,
  data: new Uint8Array(SIZE * SIZE * 4),

  onAdd(this: { context: CanvasRenderingContext2D }) {
    const canvas = document.createElement('canvas')
    canvas.width = SIZE; canvas.height = SIZE
    this.context = canvas.getContext('2d')!
  },

  render(this: { context: CanvasRenderingContext2D; data: Uint8Array }): boolean {
    const ctx = this.context
    if (!ctx) return false
    const DURATION = 2200
    const t1 = (performance.now() % DURATION) / DURATION
    const t2 = ((performance.now() + DURATION * 0.5) % DURATION) / DURATION
    const cx = SIZE / 2; const maxR = cx * 0.9
    ctx.clearRect(0, 0, SIZE, SIZE)
    // Ring 1 — primary
    ctx.beginPath(); ctx.arc(cx, cx, maxR * t1, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(${r},${g},${b},${(1 - t1) * 0.85})`
    ctx.lineWidth = 3; ctx.stroke()
    // Ring 2 — offset phase
    ctx.beginPath(); ctx.arc(cx, cx, maxR * t2, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(${r},${g},${b},${(1 - t2) * 0.5})`
    ctx.lineWidth = 2; ctx.stroke()
    this.data = ctx.getImageData(0, 0, SIZE, SIZE).data as unknown as Uint8Array
    map.triggerRepaint()
    return true
  },
}
map.addImage(imageId, pulseMarker as never, { pixelRatio: 2 })
```

**Rules:**
- Canvas MUST be created in `onAdd()` — creating it in the constructor prevents Mapbox from uploading new texture data on each frame → the image renders as a static disc.
- Exactly **2 rings** with `t` and `t + 0.5*DURATION` phase offset — never use `setInterval` + accumulating ring array (causes visual noise with many rings stacking).
- Animation is time-based (`performance.now() % DURATION`) — frame-rate independent.
- Canvas `SIZE = 120`, `pixelRatio: 2` → rendered as 60×60 CSS px at `icon-size: 1`.
- Pulse layer inserted **before** the circle layer (`map.addLayer({...}, circleLayerId)`) so the circle renders on top.
- `extractSolidColor(channel)` reads `channel.color ?? colorRange.colors[0]` for a single hex.
- `getLayerIds` for point layers must include `${layersId}-pulse` so visibility toggle also hides the pulse.

### Container contract

`MapPluginShell` wraps the Mapbox canvas in `h-full w-full relative`.
The **caller** must supply a bounded-height ancestor — same `min-h-0` flex chain rule as all maps.
See `references/map-rules.md` § Container & frame contract.

### MapPlugin Definition of Done

- [ ] `src/modules/map-plugin/` (create on demand) contains engine only — no domain-specific imports
- [ ] `MAP_WIDGET_REGISTRY` defined in `src/features/dashboard/{page}/widgets/index.ts`
- [ ] Every overlay widgetId in `maps.json` has a corresponding entry in `MAP_WIDGET_REGISTRY`
- [ ] `MapPluginWidget` receives `widgetRegistry` prop and passes it to `MapPluginShell`
- [ ] `MapWidgetHost` renders `null` + `console.warn` for missing registry entries (dev only)
- [ ] Widget components import `useMapPluginStore` for filter/sort state — no prop drilling
- [ ] Sorting widgets (`type === 'sorting'`) rendered above tab/scroll list in `MapSideSlot`
- [ ] `MapSideSlot` supports both `mode="floating"` and `mode="inside"` from `mapStyle.rightWidgetLayout`
- [ ] `MapSideSlot` supports `scrollSide` (scroll list) and tab modes
- [ ] `MapBottomSlot` collapse/expand animated via `max-height` transition
- [ ] `useMapPluginStore` instance state includes `sortConfig` and `dateFilter`
- [ ] Layer visibility toggle goes through `useMapPluginStore.setLayerVisibility`
- [ ] No `ChartComponent`, `WidgetProvider`, or Handlebars engine in any map widget
- [ ] No `dangerouslySetInnerHTML` outside `TooltipTemplate` tokenizer
- [ ] Widget data hooks read filters from `useMapPluginStore` — not from props
