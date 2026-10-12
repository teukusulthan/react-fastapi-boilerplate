# MapLayerPanel — Reference Implementation

> Source of truth for `MapLayerPanel.tsx` in `src/modules/map-plugin/components/` (module not present in the
> boilerplate yet — create it at that path when building the MapPlugin module).
> When regenerating this component, reproduce this file's structure and behavior — do not simplify or
> reorganize. Visual classes follow `reactjs-ui-design`.

## Layout contract

```
Panel
├── Header: [stack-icon] [title] [eye-all]
└── Groups (sorted: GENERAL first)
    └── Group
        ├── Header: [caret] [label uppercase] [eye-group]
        └── Rows (animated max-height collapse)
            └── LayerRow: [icon-bg 30×30] [name + range-bar flex-col] [dot?] [Checkbox]
```

## Design system compliance

> Visual rules: [`reactjs-ui-design`](../../reactjs-ui-design/SKILL.md). Floating map panels are surfaces:
> `rounded-xl border border-border bg-card shadow-md` (they float, so `shadow-md` is allowed). Controls are
> shadcn primitives (`Button`, `Checkbox`); light **and** dark mode come from the semantic tokens.

- All UI chrome (layout, borders, backgrounds, text) uses the shadcn semantic token classes
  (`bg-card`, `border-border`, `text-foreground`, `text-muted-foreground`, `bg-accent`…).
- Layer type visualization colors (`LAYER_TYPE_COLOR`, `LAYER_TYPE_ICON_COLOR`) are kept as hex constants
  — they are data-specific, not UI chrome, and must not use design tokens.
- Data-driven color swatches (range bars, single color dot) also stay as inline `style={{ background: c }}`
  since they come from layer config at runtime.
- `EyeBtn` is a ghost icon `Button` (`hover:bg-accent` built in) — no imperative `onMouseEnter/Leave`.
- Layer visibility uses the shadcn `Checkbox` (`src/components/ui/checkbox.tsx`; install with
  `npx shadcn@latest add checkbox` if missing) — never a native `<input type="checkbox">`.

## Full source

```tsx
import { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { useMapPluginStore } from '../store/useMapPluginStore'
import { resolveGroupLabel, inferLayerType } from '../helpers/mapbox-utils'
import type { MapPluginConfig, MapLayerConfig, LayerType, VisualChannel } from '../types'

// ── Layer type icons + visualization colors ───────────────────────────────────
// bg/fg are visualization-specific (not UI chrome) — kept as constants, not tokens

const LAYER_TYPE_ICON: Record<LayerType | string, string> = {
  point:        'ph-radio-button',
  polygon:      'ph-polygon',
  line:         'ph-line-segment',
  lineString:   'ph-line-segment',
  lineRelation: 'ph-git-branch',
  arc:          'ph-path',
  heatmap:      'ph-fire',
  cluster:      'ph-circles-three',
  icon:         'ph-map-pin',
}

const LAYER_TYPE_COLOR: Record<LayerType | string, string> = {
  point:        '#dbeafe',
  polygon:      '#d1fae5',
  line:         '#fef3c7',
  lineString:   '#fef3c7',
  lineRelation: '#ede9fe',
  arc:          '#fce7f3',
  heatmap:      '#fee2e2',
  cluster:      '#e0f2fe',
  icon:         '#f3e8ff',
}

const LAYER_TYPE_ICON_COLOR: Record<LayerType | string, string> = {
  point:        '#3b82f6',
  polygon:      '#10b981',
  line:         '#f59e0b',
  lineString:   '#f59e0b',
  lineRelation: '#8b5cf6',
  arc:          '#ec4899',
  heatmap:      '#ef4444',
  cluster:      '#0ea5e9',
  icon:         '#a855f7',
}

function layerIcon(type: LayerType | string) {
  return {
    icon: LAYER_TYPE_ICON[type]       ?? 'ph-map-trifold',
    bg:   LAYER_TYPE_COLOR[type]      ?? '#f3f4f6',
    fg:   LAYER_TYPE_ICON_COLOR[type] ?? '#6b7280',
  }
}

// ── Color extraction — mirrors renderColorStyle exactly ───────────────────────
// 4-case decision tree: same order as renderColorStyle in data-driven.ts

type TColorInfo = { single: string | null; range: string[] }

function extractColor(channel?: VisualChannel): TColorInfo {
  if (!channel) return { single: null, range: [] }

  if (!channel.enable || !channel.field) {
    return { single: channel.color ?? null, range: [] }
  }

  if (channel.type === 'solid' || !channel.type) {
    const solid = channel.colorRange?.colors?.[0] ?? channel.color ?? null
    return { single: solid, range: [] }
  }

  if (channel.colorPalleteCustomRange?.length) {
    return { single: null, range: channel.colorPalleteCustomRange.map((e) => e.color) }
  }

  const range = channel.colorRange?.colors ?? []
  if (range.length > 1) return { single: null, range }
  if (range.length === 1) return { single: range[0], range: [] }
  return { single: channel.color ?? null, range: [] }
}

// ── Group helpers ─────────────────────────────────────────────────────────────

interface GroupItem { group: string; layers: MapLayerConfig[] }

function buildGroups(layers: MapLayerConfig[]): GroupItem[] {
  const map = new Map<string, MapLayerConfig[]>()
  for (const layer of layers) {
    if (layer.config.hidden) continue
    const g = resolveGroupLabel(layer.group)
    if (!map.has(g)) map.set(g, [])
    map.get(g)!.push(layer)
  }
  return Array.from(map.entries())
    .sort(([a], [b]) => {
      if (a === 'GENERAL') return -1
      if (b === 'GENERAL') return 1
      return 0
    })
    .map(([group, ls]) => ({ group, layers: ls }))
}

function displayGroupLabel(key: string): string {
  if (key === 'GENERAL') return 'Default'
  return key.replace(/\w\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
}

// ── Eye toggle button ─────────────────────────────────────────────────────────

function EyeBtn({
  visible,
  onClick,
  size = 14,
}: {
  visible: boolean
  onClick: (e: React.MouseEvent) => void
  size?: number
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={onClick}
      aria-label={visible ? 'Hide layers' : 'Show layers'}
      title={visible ? 'Hide' : 'Show'}
      className={['size-7 shrink-0', visible ? 'text-muted-foreground' : 'text-muted-foreground/50'].join(' ')}
    >
      <i
        className={`ph ${visible ? 'ph-eye' : 'ph-eye-slash'}`}
        style={{ fontSize: size, lineHeight: 1 }}
        aria-hidden="true"
      />
    </Button>
  )
}

// ── Layer row ─────────────────────────────────────────────────────────────────

interface LayerRowProps {
  layer: MapLayerConfig
  visible: boolean
  onToggle: (layersId: string, visible: boolean) => void
}

function LayerRow({ layer, visible, onToggle }: LayerRowProps) {
  const layerType = inferLayerType(layer)
  const colorInfo = extractColor(layer.config.visualChannels?.fillColor)
  const label     = layer.config.label ?? layer.layers_id
  const hasRange  = colorInfo.range.length > 0
  const { icon, bg, fg } = layerIcon(layerType)

  return (
    <div
      className={[
        'flex items-center gap-2 px-3 py-1.5',
        'border-t border-border',
        'transition-opacity duration-[180ms] ease-in-out',
        visible ? 'opacity-100' : 'opacity-40',
      ].join(' ')}
    >
      {/* Icon with visualization background — bg/fg are data-specific, not tokens */}
      <div
        title={layerType}
        className="flex shrink-0 items-center justify-center rounded-md"
        style={{ width: 30, height: 30, background: bg }}
      >
        <i className={`ph ${icon}`} style={{ fontSize: 15, color: fg, lineHeight: 1 }} />
      </div>

      {/* Name + range bar — stacked flex-col, gap 3px */}
      <div className="flex min-w-0 flex-1 flex-col gap-[3px]">
        <span
          title={label}
          className="truncate text-sm font-medium leading-snug text-foreground"
        >
          {label}
        </span>

        {/* Range bars — data-driven colors stay as inline style */}
        {hasRange && (
          <div className="flex gap-0.5">
            {colorInfo.range.map((c, i) => (
              <span
                key={i}
                title={c}
                className="h-[5px] flex-1 rounded-sm"
                style={{ background: c }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Single color dot — data-driven, inline style for background */}
      {colorInfo.single && (
        <span
          title={colorInfo.single}
          className="size-3 shrink-0 rounded-full border border-border"
          style={{ background: colorInfo.single }}
        />
      )}

      {/* Visibility checkbox — shadcn Checkbox */}
      <Checkbox
        checked={visible}
        onCheckedChange={(checked) => onToggle(layer.layers_id, checked === true)}
        onClick={(e) => e.stopPropagation()}
        aria-label={`Show ${label}`}
        className="shrink-0"
      />
    </div>
  )
}

// ── Collapsible group ─────────────────────────────────────────────────────────

interface GroupProps {
  group: string
  layers: MapLayerConfig[]
  layerVisibility: Record<string, boolean>
  onToggle: (layersId: string, visible: boolean) => void
  onToggleGroup: (layerIds: string[], visible: boolean) => void
}

function LayerGroup({ group, layers, layerVisibility, onToggle, onToggleGroup }: GroupProps) {
  const [open, setOpen] = useState(true)

  const allVisible = layers.every(
    (l) => layerVisibility[l.layers_id] ?? (l.config.isVisible ?? true)
  )

  // Estimate row heights for max-height collapse animation
  const estimatedHeight = layers.reduce((sum, l) => {
    const info = extractColor(l.config.visualChannels?.fillColor)
    return sum + (info.range.length > 0 ? 50 : 44)
  }, 0)

  const layerIds = layers.map((l) => l.layers_id)

  return (
    <div className="border-b border-border last:border-b-0">
      {/* Group header — no background tint */}
      <div className="flex items-center gap-1 px-3 pb-1 pt-1.5">
        <button
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className="flex min-w-0 flex-1 cursor-pointer items-center gap-1 rounded-md border-0 bg-transparent p-0 text-left focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          <i
            className={`ph ph-caret-${open ? 'down' : 'right'} shrink-0 text-muted-foreground`}
            style={{ fontSize: 11 }}
            aria-hidden="true"
          />
          <span className="min-w-0 flex-1 truncate text-xs font-medium text-muted-foreground">
            {displayGroupLabel(group)}
          </span>
        </button>

        <EyeBtn
          visible={allVisible}
          size={13}
          onClick={(e) => { e.stopPropagation(); onToggleGroup(layerIds, !allVisible) }}
        />
      </div>

      {/* Animated layer list */}
      <div
        className="overflow-hidden transition-[max-height] duration-[280ms] ease-[cubic-bezier(0.4,0,0.2,1)]"
        style={{ maxHeight: open ? `${estimatedHeight + 4}px` : '0px' }}
      >
        {layers.map((layer) => (
          <LayerRow
            key={layer.layers_id}
            layer={layer}
            visible={layerVisibility[layer.layers_id] ?? (layer.config.isVisible ?? true)}
            onToggle={onToggle}
          />
        ))}
      </div>
    </div>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────

interface Props {
  config: MapPluginConfig
  mapsId: string
  onToggle: (layersId: string, visible: boolean) => void
}

export function MapLayerPanel({ config, mapsId, onToggle }: Props) {
  const layerVisibility = useMapPluginStore((s) => s.instances[mapsId]?.layerVisibility ?? {})
  const groups          = buildGroups(config.layers)

  const visibleLayers = useMemo(
    () => config.layers.filter((l) => !l.config.hidden),
    [config.layers]
  )

  const allVisible = visibleLayers.every(
    (l) => layerVisibility[l.layers_id] ?? (l.config.isVisible ?? true)
  )

  function handleToggleAll() {
    const next = !allVisible
    for (const l of visibleLayers) onToggle(l.layers_id, next)
  }

  function handleToggleGroup(layerIds: string[], visible: boolean) {
    for (const id of layerIds) onToggle(id, visible)
  }

  return (
    <div className="map-layer-panel flex w-72 max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-xl border border-border bg-card text-card-foreground shadow-md">
      {/* Panel header */}
      <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
        <i className="ph-fill ph-stack size-4 shrink-0 text-base leading-none text-primary" aria-hidden="true" />
        <span className="flex-1 text-sm font-semibold text-foreground">
          Layers
        </span>
        <EyeBtn visible={allVisible} onClick={handleToggleAll} size={15} />
      </div>

      {/* Scrollable group list — bounded region → PerfectScrollArea */}
      <PerfectScrollArea className="max-h-[62svh]">
        {groups.map(({ group, layers }) => (
          <LayerGroup
            key={group}
            group={group}
            layers={layers}
            layerVisibility={layerVisibility}
            onToggle={onToggle}
            onToggleGroup={handleToggleGroup}
          />
        ))}
      </PerfectScrollArea>
    </div>
  )
}
```

## Key constraints

- **`extractColor` must mirror `renderColorStyle` exactly** — same 4-case order. Never infer color independently.
- **Range bar inside flex-col with name** (gap 3px) — never a separate DOM row outside the column.
- **Icon always has background container** (`30×30`, `rounded-md`) — never a plain icon.
- **Row opacity `40` when hidden** — not `display:none`, allows smooth transition.
- **Collapse animation via `maxHeight` estimate** — range rows 50px, plain rows 44px.
- **Group `GENERAL` → label `Default`**; others → Title Case via `replace(/\w\S*/g, ...)`.
- **`EyeBtn`** is a ghost icon `Button` with `aria-label` — no imperative `onMouseEnter/Leave`.
- **Visibility** uses the shadcn `Checkbox` — never a native checkbox.
- **Layer type bg/fg colors** are hex constants — visualization-specific, NOT design tokens.
- **Data-driven swatch colors** (range bars, single dot) stay as `style={{ background: c }}`.
- **All UI chrome** (borders, backgrounds, text, spacing) uses the shadcn semantic token classes; the panel is a
  `rounded-xl` floating surface with `shadow-md` (see `reactjs-ui-design` §2).
