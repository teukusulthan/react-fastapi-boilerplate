---
name: html-to-react
description: Convert an HTML mockup file (from mockup/web-html/ or mockup/mobile-html/) into a fully structured React feature. Extracts HTML content, custom CSS classes, interactive JS functions, static mock data, third-party dependencies, ECharts configs, Mapbox configs and GeoJSON layers, CSS keyframe animations, marker/popup factories, and data-ui attribute mappings — then hands off to reactjs-ui-design (visual rules, shadcn-first) and reactjs-slicing-ui for the final React/TypeScript implementation. Use when asked to "convert HTML to React", "implement from mockup", "slice HTML ke React", or "buatkan feature dari HTML".
---

# Skill — HTML to React Converter

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over the mockup's markup and CSS. This skill owns the extraction inventory only. The mockup tells
> you *what* is on the screen; the React build uses shadcn primitives, `components/common` patterns,
> `modules/data-table` and semantic tokens — it does not copy the mockup's hand-rolled widgets.

Analyses an HTML mockup and extracts all artefacts needed before implementation. After extraction, hand
off to **`reactjs-ui-design`** + **`reactjs-slicing-ui`** (and sub-skills as needed) to build the final
React/TypeScript feature.

---

## Step 1 — Read the HTML file

Read the full HTML file the user points to (e.g. `mockup/web-html/*.html`).

---

## Step 2 — Extract Artefacts

Run through each extraction category below and produce a structured summary. Skip categories not present in the file.

### 2.1 HTML Content (layout-stripped)
- Strip the outer layout shell: `<header data-ui="header">`, `<aside data-ui="sidebar">`, and any global wrapper already provided by `AppLayout`
- Keep only the **inner page/feature content** — the region that will live inside `{Name}Feature.tsx`
- Note every `id` attribute that JS or ECharts references

### 2.2 Custom CSS Classes → shadcn primitives / Tailwind semantic utilities
For every class defined in `<style>` (and every inline `style=""`), decide in this order:

1. **Is it a widget shadcn ships** (dropdown, select, tabs, dialog, tooltip, toggle, table…)? → use the
   primitive from `src/components/ui/` (install it if missing) and drop the class.
2. **Is it a page pattern** (page header, KPI tile, empty state, section card, status pill)? → use the
   `src/components/common/` component (`PageHeader`, `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`).
3. **Otherwise** → Tailwind utilities with the shadcn semantic tokens (`bg-card`, `text-muted-foreground`,
   `border-border`, `rounded-md`/`rounded-xl`) per `reactjs-ui-design` §2. Map the mockup's raw colors,
   radii and shadows to tokens; don't carry over its values.
4. **Only** CSS that utilities can't express (complex keyframes, pseudo-element art, map marker skins) may
   go into a named block in `src/styles/components.css` using `var(--token)` values.

For each class note: name, properties, the chosen target (1–4), and whether it depends on JS state
(→ conditional `cn(...)` classes or `data-[state]` variants). Never carry over raw `style={{}}` props.

### 2.3 Interactive JS Functions → React State/Hooks
List every JavaScript function and `setInterval` / `addEventListener`. Map each to a React pattern:

| HTML pattern | React equivalent |
|---|---|
| `function toggleX()` modifying classList | `useState` + conditional className |
| `setInterval(...)` | `useEffect` with cleanup |
| `function filterType()` iterating DOM | `useState` filter value + derived list |
| `function focusVessel(name)` calling map API | callback prop or zustand action |
| `function pbControl()` playback timer | `useRef` timer + `useState` slider value |
| `function toggleLayer()` + `map.setLayoutProperty` | Mapbox store action (see `reactjs-map`) |
| `function updatePlayback(v)` | controlled `<input type="range">` onChange |

### 2.4 Static Mock Data → TypeScript Types + Data File
Identify every hardcoded data array / config object. For each:
- Define a TypeScript interface
- Extract to `features/{domain}/{feature}/mocks/mock-{entity}.ts` (POC scope only — see `apps/web/AI_GUIDE.md` §6)
- Infer field names and value types from the data

### 2.5 Third-party Dependencies
Map each CDN library to its npm package:

| CDN | npm package | Notes |
|---|---|---|
| `mapbox-gl@3.3.0` | `mapbox-gl` | load `reactjs-map` |
| `echarts@5` | `echarts` | load `reactjs-chart` |
| `@phosphor-icons/web` | already in project | `<i class="ph ...">` — no change |
| `perfect-scrollbar` | use `react-perfect-scrollbar` (already in project) | `<PerfectScrollArea>` from `@/components/wrappers/PerfectScrollArea` |

Flag any library not already in `apps/web/package.json` as **needs install**.

### 2.6 ECharts Chart Configs → Custom Hooks
For each `echarts.init(...)` block:
- Identify chart id and chart type (pie, gauge, scatter, line, etc.)
- Extract full `setOption({...})` config
- Map to `use{ChartName}Chart.ts` hook inside `features/{name}/hooks/`
- Note CSS vars resolved via `resolveColor()` — become `useChartTheme(mode)` inputs (`chart-1…5` tokens)
- Load `reactjs-chart` skill when implementing

### 2.7 Mapbox Config + GeoJSON Layer Definitions
If a Mapbox map is present:
- Extract: `center`, `zoom`, `pitchWithRotate`, map style URLs (dark/light)
- Extract every `addSource` + `addLayer` block → `config/layers.config.ts`
- Extract vessel/marker data → `config/markers.config.ts`
- `createVesselMarker()` → React component rendered to DOM node for custom marker
- `popupHTML()` → `renderToStaticMarkup(<VesselPopup vessel={v} />)` pattern
- Access token → `VITE_MAPBOX_TOKEN` (`env.map.mapboxToken` from `src/config/env.ts`)
- Load `reactjs-map` skill when implementing

### 2.8 CSS Keyframe Animations
Prefer the primitives' built-in `data-[state]` animations and Tailwind `transition-colors`/`animate-*`
utilities. A genuinely custom `@keyframes` goes into `src/styles/components.css` (next to the existing
dialog keyframes) or `@theme` in `src/styles/tailwind.css` — never into `index.css`, never inline. Respect
`prefers-reduced-motion`.

### 2.9 `data-ui` Attribute Mapping → shadcn/ui Components
Map every `data-ui="..."` to its shadcn primitive:

| `data-ui` value | shadcn component |
|---|---|
| `button` | `Button` from `@/components/ui/button` |
| `badge` | `Badge` from `@/components/ui/badge` |
| `card` | `Card`, `CardContent` from `@/components/ui/card` |
| `input` | `Input` from `@/components/ui/input` |
| `select` / `dropdown` / `tabs` / `dialog` / `tooltip` | the matching shadcn primitive (`npx shadcn@latest add <name>` if missing) |
| `table` | `DataTable` from `@/modules/data-table` |
| `stat` / `kpi` | `StatCard` from `@/components/common/StatCard` |
| `empty` | `EmptyState` from `@/components/common/EmptyState` |
| `sidebar` | Existing `AppSidebar` — do NOT create new sidebar |
| `header` | Existing `AppHeader` — do NOT recreate |

---

## Step 3 — Hand-off to reactjs-ui-design + reactjs-slicing-ui

After extraction is complete:

1. Load `reactjs-ui-design` (visual rules, component priority, review loop) and `reactjs-slicing-ui`
2. Load sub-skills as needed:
   - Map present → `reactjs-map`
   - Charts present → `reactjs-chart`
   - New feature → `reactjs-features`
3. Implement, then run the review loop: `npm run ui:snapshot -- --route <path>` and check the PNGs
   (`reactjs-ui-design` §8)

**Constraints carried forward from extraction:**
- Every §2.2 class is resolved to a primitive, a common pattern or token utilities — no raw `style={{}}` props
- All mock data from §2.4 goes into the feature's `mocks/` — never inline in component
- All ECharts option builders from §2.6 go into `config/` (pure builders) + `hooks/` — never inline in JSX
- All Mapbox layer definitions from §2.7 go into `config/` — never inline in component
- Keyframe animations from §2.8 live in `src/styles/` — never `index.css`, never inline

---

## Output Format

Present extraction results as a markdown report with one section per category **before writing any code**. Get user confirmation if any section is unclear, especially around mock data types and component split.
