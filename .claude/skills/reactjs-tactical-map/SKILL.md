---
name: reactjs-tactical-map
description: Tactical command center map — domain override on top of the generic map skill. Covers tactical-specific layer groups, incident types, sensor stores, and the TacticalMap bridge. Use ONLY for an explicitly tactical/command-center domain. Read `skills/reactjs-map/SKILL.md` first for the base pattern.
---

# Skill — Tactical Map (Domain Override)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns the tactical domain model (layer groups, incident types,
> sensor stores, the `TacticalMap` bridge). It applies **only** when the task is a tactical /
> command-center map — never use it as a style reference for ordinary pages.

**Base skill:** `skills/reactjs-map/SKILL.md` — read this first. This file only documents what is different for the tactical domain.

**Layout:** Tactical maps follow the same **container / frame** rules as the generic map skill — the map canvas must fill the hosting panel (flex `min-h-0` chain, full-size wrapper). See `skills/reactjs-map/SKILL.md` § Layout and `references/map-rules.md` § Container & frame contract.

**Access token:** Tactical maps inherit the same env contract as `skills/reactjs-map/SKILL.md` —
`VITE_MAPBOX_TOKEN` in `apps/web/env/.env`, read as `env.map.mapboxToken` from `src/config/env.ts`.
Never hardcode a token in code or docs.

---

## Tactical Domain Terminology Mapping

| Generic term          | Tactical name                                                        |
| --------------------- | -------------------------------------------------------------------- |
| `{domain}`            | `tactical`                                                           |
| `{Entity}`            | `Incident`                                                           |
| `{Feed}`              | `SensorReading`                                                      |
| `MAP_LAYERS`          | `TACTICAL_LAYERS`                                                    |
| `ENTITY_TYPES`        | `INCIDENT_TYPES`                                                     |
| `MapBridge`           | `TacticalMap`                                                        |
| `useEntityStore`      | `useIncidentStore`                                                   |
| `useFeedStore`        | `useSensorStore`                                                     |
| `LayerGroup` values   | `'INSIDEN' \| 'ANALISIS' \| 'RESPONS' \| 'INFRASTRUKTUR' \| 'COMMS'` |
| `MarkerStatus` values | `'critical' \| 'alert' \| 'normal' \| 'info' \| 'offline'`           |

---

## File Reference (Tactical)

```
src/
├── types/map.d.ts
├── config/map/
│   ├── marker-styles.config.ts
│   └── layer-paint.config.ts
└── features/tactical/
    ├── index.ts
    ├── config/
    │   ├── layers.config.ts           ← TACTICAL_LAYERS, BY_GROUP, DEFAULT_VISIBILITY
    │   └── incident-types.config.ts   ← INCIDENT_TYPES
    └── types/
        └── tactical.types.ts
```

---

## Tactical-Specific: Layer Groups

```ts
// tactical.types.ts
export type LayerGroup =
  | "INSIDEN"
  | "ANALISIS"
  | "RESPONS"
  | "INFRASTRUKTUR"
  | "COMMS";
```

Panel render order:

```ts
const GROUP_ORDER: LayerGroup[] = [
  "INSIDEN",
  "ANALISIS",
  "RESPONS",
  "INFRASTRUKTUR",
  "COMMS",
];
```

---

## Tactical-Specific: Adding a Layer

Follow the generic pattern in `skills/reactjs-map/SKILL.md` §1, substituting tactical names.

Example for a radiation zone layer:

```ts
// layer-paint.config.ts
// Mapbox paint cannot read CSS variables — resolve the status token (`--color-destructive`) with
// getComputedStyle at map load and re-apply on theme change
radiationZone: {
  type: 'fill' as const,
  paint: {
    'fill-color': resolved.destructive,
    'fill-opacity': 0.18,
    'fill-outline-color': resolved.destructive,
  },
},
```

```ts
// layers.config.ts — inside TACTICAL_LAYERS array
{
  id: 'RADIATION_ZONE',
  label: 'Zona Radiasi',
  group: 'ANALISIS' as LayerGroup,
  icon: 'radioactive',
  defaultVisible: false,
  mapLayerId: 'layer-radiation-zone',
  paint: LAYER_PAINT.radiationZone.paint,
  isGeoJson: true,
},
```

```ts
// tactical.types.ts
export type LayerId =
  | "INCIDENT_MARKERS"
  | "RADIATION_ZONE" // ← add here
  | (string & {});
```

---

## Tactical-Specific: Adding an Incident Type

Follow the generic pattern in `skills/reactjs-map/SKILL.md` §2, substituting tactical names.

```ts
// tactical.types.ts
export type IncidentType = "CHEMICAL_LEAK" | "FLOOD_CONTAMINATION"; // ← add here
```

```ts
// incident-types.config.ts
FLOOD_CONTAMINATION: {
  label: 'Kontaminasi Banjir',
  markerStyle: MARKER_STYLES.alert,
  severity: 'alert',
  icon: 'drop-half-fill',
},
```

---

## Tactical-Specific: Store Names

Apply the generic store patterns from `skills/reactjs-map/SKILL.md` §3 with these names:

- `useEntityStore` → `useIncidentStore` — owns `incidents[]` and `selectedId`
- `useFeedStore` → `useSensorStore` — owns `readings[]`, `feed[]`, `overallStatus`
- `useLayerStore` — unchanged

`useSensorStore` sensor classification:

```ts
function deriveStatus(readings: TSensorReading[]): SensorStatus {
  if (readings.some((r) => r.status === "CRITICAL")) return "CRITICAL";
  if (readings.some((r) => r.status === "ALERT")) return "ALERT";
  if (readings.every((r) => r.status === "OFFLINE")) return "OFFLINE";
  return "NORMAL";
}
```

---

## Tactical-Specific: Design Tokens

**Default (no `design/web/tactical/` theme in the repo):** tactical panels use the same chrome as every
other map panel — shadcn primitives, semantic tokens (`bg-card`, `border-border`, `text-muted-foreground`),
`rounded-xl` floating surfaces with `shadow-md`, light **and** dark mode (see `reactjs-ui-design` and the
"Map UI chrome" table in `reactjs-map`). Severity colors map to status tokens:

```
critical → var(--color-destructive)   / text-destructive, bg-destructive/10
alert    → var(--color-warning)       / text-warning,     bg-warning/10
normal   → var(--color-success)       / text-success
info     → var(--color-info)          / text-info
offline  → var(--color-muted-foreground)
```

**Only when the active `design/` theme is Tactical** (`design/web/tactical/DESIGN.md` exists and is
selected in `design/design-system.md`): apply that theme's token values via `variable.css` (dark-first);
component classes stay the semantic ones. Panels stay opaque `bg-card` (no glassmorphism) unless that
DESIGN.md explicitly specifies an overlay surface token.

Rules (all themes):

- Monospace (`font-mono tabular-nums`) for sensor readings and coordinates
- Status colors only for status; neutral chrome everywhere else
- Panel text never below `text-muted-foreground` contrast

---

## Tactical TacticalMap — Bridge Component

Named `TacticalMap.tsx` in this domain. Follows all `MapBridge` rules from `skills/reactjs-map/references/map-rules.md` §7.

Additional tactical rule: the data source orchestrator is named `useTacticalDataSources` (not `useMapDataSources`).

```tsx
import { useTacticalDataSources, registerMvtSource } from "@/features/tactical";
// ...same pattern as MapBridge in skills/reactjs-map/SKILL.md §8
```

---

## Definition of Done

Same checklist as `skills/reactjs-map/SKILL.md`, plus:

- [ ] `TacticalMap` named component exported from the correct page parts folder
- [ ] `useTacticalDataSources(mapRef)` called once in `TacticalMap`
- [ ] All incident types in `INCIDENT_TYPES` config
- [ ] `useSensorStore.overallStatus` derived via `deriveStatus()` — never set manually
- [ ] Feed capped at 100 entries in `appendFeed`
- [ ] Chrome built from shadcn primitives + semantic tokens; severity → status tokens
- [ ] Reviewed with `npm run ui:snapshot -- --route <path>` (`reactjs-ui-design` §8)

> Detailed rules: [references/tactical-map-rules.md](references/tactical-map-rules.md)
> Base pattern: [../reactjs-map/SKILL.md](../reactjs-map/SKILL.md)
