# Workspace spec PoC (single HTML under `<cwd>/design/`)

This document is **normative** when [`html-ui-slicing`](../../../commands/html-ui-slicing.md) **Step 0** selects **Mode B — Workspace spec PoC**. It replaces the retired standalone **`design-html`** skill: brief/spec-driven static HTML with mock data only, design pack anchored under `<cwd>/design/**`.

**Do not** read `design/design-system.md` for this mode — discovery uses only the three approved files under `<cwd>/design/` (see [Design System Contract](#design-system-contract)).

## Lifecycle

Usually runs **after** `spec-builder`, or directly from a brief when the user wants HTML before a formal spec exists. Does **not** replace `design-system`, `uiux`, or scaffolded app code.

## Markup contract (shared with Mode A)

Use the same **`data-ui` + semantic Tailwind** rules as the [`html-ui-styling`](../../html-ui-styling/SKILL.md) skill (the `html-ui-slicing` skill body is not bundled) (§ Semantic Component Classes, § Step 4 — Coding Rules). Never ship bare `data-ui` without utilities.

## Input Contract

Primary input (pick the best available source in this order):

- `<cwd>/sprint/00-app-spec.md`
- one or more relevant files under `<cwd>/brief/`
- another user-provided brief/spec file for the same app

When reading from `<cwd>/brief/`, prefer the smallest relevant subset, for example:

- `<cwd>/brief/00_OVERVIEW.md`
- `<cwd>/brief/NN_FEATURE.md`
- any other brief markdown files that define pages, features, flows, or UI expectations

Optional supporting input:

- `<cwd>/brief/00_OVERVIEW.md` only for naming, terminology, and copy tone
- the selected design pack under `<cwd>/design/`

If `<cwd>/sprint/00-app-spec.md` exists, use it as the structural source of truth.

If no app spec exists but the user explicitly asks for direct HTML from a brief, derive the page/section model from the relevant brief files instead of stopping.

Only redirect to `spec-builder` first when:

- there is no usable spec
- the brief is too ambiguous to infer a believable page structure
- and the user did **not** explicitly ask for a direct brief-to-HTML pass

## Design System Contract

Before writing HTML, inspect `<cwd>/design/` and choose the most relevant design pack.

The design pack must be anchored to these three files:

- `DESIGN.md`
- `tailwind.css`
- `variable.css`

If the repository uses the misspelled filename `varaible.css`, treat it as the token source in place of `variable.css`.

Only these files may be read or loaded as design references for **this mode**. Do **not** read, load, or use any other design-pack file as reference material, including but not limited to `design-token.json`, draft notes, screenshots, auxiliary markdown files, or generated artifacts.

Platform selection rules:

1. Default to **web** when the request is ambiguous.
2. Switch to **mobile** only when the request, source document, or folder structure clearly indicates a mobile screen/app direction.
3. If both web and mobile packs exist, choose the one that best matches the requested deliverable.
4. If no design pack matches perfectly, use the closest pack and state that assumption.

How to use the three files:

- `DESIGN.md` → source of truth for visual principles, semantic token usage, component rules, density, spacing, typography, iconography, and responsive behavior
- `tailwind.css` → source of truth for token-to-utility/theme mapping; mirror its naming and token intent when using Tailwind CDN
- `variable.css` / `varaible.css` → source of truth for canonical CSS variables/tokens; inline the relevant variables into the generated HTML instead of inventing a new palette

Hard rules:

- Do **not** invent an unrelated design language when a relevant design pack exists in `<cwd>/design/`
- Do **not** hardcode arbitrary colors if semantic tokens already exist in the chosen design pack
- Do **not** read or load any design-pack reference file besides `DESIGN.md`, `tailwind.css`, and `variable.css` / `varaible.css`
- Do **not** use `design-token.json` as a reference source for **this mode**, even if it exists beside the approved files
- Because the output must stay single-file HTML, translate the needed parts of the chosen design pack into inline `<style>` variables, minimal utility aliases, or a small `tailwind.config` block inside the HTML

## Output Contract

Write exactly **one file** under `<cwd>/design/` (unless the user requests another path inside the repo).

### Output path & filename

The **basename** follows user input or project naming — do **not** assume a fixed `poc.html`.

1. **User gave a path or filename** → use it; if only a basename, write `<cwd>/design/{basename}` (ensure `.html`).
2. **User gave a project / product / app name** → kebab-case slug → `<cwd>/design/{slug}.html`.
3. **No name given** → slug from `00-app-spec.md` title, or `<cwd>/brief/00_OVERVIEW.md`, or brief filename stem → `<cwd>/design/{slug}.html`; append `-poc` if colliding with unrelated files.
4. **Scoped revision** → overwrite the same file the user indicates.

State the **final relative path** in the response.

Rules:

1. Output must be a **single `.html` file**.
2. Keep all CSS and JavaScript inline in that file.
3. Use **mock/dummy data only**. No real API calls, no backend dependency, no auth flow, no database wiring.
4. Treat the result as a **PoC visual prototype**, not production frontend code.
5. If the spec contains multiple pages, simulate them inside the same HTML file with section switching, tabs, or a tiny router. Do not split into multiple HTML files.

## Source-Locked Improvisation Contract

Improvisation is allowed, but only **inside** the UI direction already defined by the source prompt/spec/brief. The skill must treat the source as the authority for **what the UI is**, and improvisation only as a tool for deciding **how that same UI is presented more convincingly**.

Rules:

1. Preserve the source-defined **page composition**:
   - page count
   - route model
   - widget inventory
   - primary zone composition
   - relative emphasis between areas
2. Preserve the source-defined **feature intent**:
   - a map stays the main map if the source says it is central
   - a left asset panel stays an asset panel if the source says it is left
   - an analytics panel stays analytics, not a different module
   - an event console stays an event/log surface, not a chat, feed, or generic table unless the source supports that
3. Improvisation may refine:
   - visual hierarchy
   - spacing rhythm
   - panel chrome
   - typography treatment
   - motion and microinteraction
   - chart framing
   - map overlays
   - icon usage
   - density and clarity
4. Improvisation must **not** change the source-defined composition by:
   - introducing new major widgets that were not implied by the source
   - removing required widgets
   - swapping the role of major zones
   - turning a multi-zone command UI into a generic landing page, analytics SaaS, or unrelated dashboard pattern
   - over-stylizing one section until it dominates the screen in a way the source did not ask for
5. When the source is sparse, fill gaps in the **same direction** as the source instead of inventing a new concept.
6. If the source explicitly describes layout composition, that composition wins over personal visual preference.

Interpretation examples:

- Source says: central tactical map + left asset panel + right analytics + bottom event console + top nav
  -> you may improve density, framing, glow, scanlines, overlays, badges, and chart styling
  -> you may **not** relocate the main emphasis away from the map or collapse the layout into a generic card grid unless the source supports it
- Source says: auth page with server status indicator
  -> you may improve atmosphere and terminal feel
  -> you may **not** turn it into a marketing login, onboarding wizard, or multi-step auth flow unless requested

## Scoped Revision Contract

When the user is **not** asking for a fresh brief/spec-to-HTML generation, but instead asks to adjust an existing PoC HTML in a narrow area (for example: "chart saja", "header only", "sidebar doang", "rapikan map widget", "tombolnya aja"), treat the task as a **scoped revision**.

Rules for scoped revisions:

1. Preserve the previously selected source of truth:
   - `<cwd>/sprint/00-app-spec.md` remains the structural source when it exists
   - the chosen brief file(s) remain the content/tone reference
   - the chosen design pack under `<cwd>/design/` remains the visual source
2. Change **only** the user-requested surface unless the user explicitly approves broader changes.
3. Do **not** reinterpret a scoped revision as permission to redesign the full page.
4. Do **not** add, remove, rename, or reshuffle pages/widgets/routes unless the requested scoped change truly requires it and the source supports it.
5. Keep the same data contract for the targeted widget/section unless the user explicitly asks to change the data itself.
6. "Improve", "improvise", or "make it better" inside one named area means:
   - improve presentation, framing, motion, hierarchy, chart treatment, or local component composition
   - while preserving the original feature intent from the source document
7. If a requested local improvement would conflict with the source, favor the source and explain the limitation briefly.

Examples:

- "Improvisasi chartnya doang" -> adjust only chart presentation and chart-adjacent framing in the analytics area; keep page structure, map area, sidebars, event feed, and source-derived metrics intact
- "Rapikan top bar" -> adjust only top navigation visuals/copy hierarchy; do not rewrite dashboard layout
- "Bikin map lebih tactical" -> adjust only the map widget and its local overlays; do not silently redesign unrelated panels

## Library Rules

Use CDN assets only when needed:

- Tailwind CSS: `https://cdn.tailwindcss.com`
- **Perfect Scrollbar (ALWAYS required):**
  - CSS: `https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/css/perfect-scrollbar.css`
  - JS: `https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/dist/perfect-scrollbar.min.js`
- ECharts for all chart widgets: `https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js`
- Mapbox GL JS for all map cases:
  - CSS: `https://api.mapbox.com/mapbox-gl-js/v3.4.0/mapbox-gl.css`
  - JS: `https://api.mapbox.com/mapbox-gl-js/v3.4.0/mapbox-gl.js`

Mapbox token for this skill:

```js
const MAPBOX_ACCESS_TOKEN = "pk.YOUR_MAPBOX_PUBLIC_TOKEN";
```

Hard rules:

- **Every scrollable container MUST use Perfect Scrollbar.** Never use native browser scrollbars (`overflow-y: auto/scroll`, `scrollbar-width`, `::-webkit-scrollbar`).
- For each scrollable element: set `overflow: hidden; position: relative;` in CSS, then call `new PerfectScrollbar('#id', { suppressScrollX: true })` in JS after content is rendered.
- Call `ps.update()` on the relevant instance whenever the container's content changes dynamically (e.g. after re-rendering a list or injecting new rows).
- Override PS thumb styles to match the active design pack tokens (no rounded thumbs when the design system uses `border-radius: 0`).
- All chart widgets must use **ECharts via CDN** as the rendering base.
- Chart styling may be freely improvised through ECharts options plus surrounding HTML/CSS chrome, as long as the result still reads clearly and stays aligned with the source-defined widget purpose.
- You may art-direct the chart container, HUD framing, legends, annotations, glow, gradients, labels, tooltips, markers, and overlays around the ECharts canvas, but the chart itself must still be rendered by ECharts.
- All map widgets must use **Mapbox GL JS via CDN**.
- Do not use npm packages, bundlers, or framework bootstrapping.
- Do not include chart/map CDN scripts if the spec does not need them.

## Workflow

### 1. Read and normalize the spec

First resolve the source document and design pack.

Extract from the chosen input:

- page list
- route per page
- persona per page
- widget list per page
- navigation relationships
- notable layout signals: dashboard, detail, list, form, auth, map-heavy, analytics-heavy
- explicit composition signals: central focus area, side panels, top/bottom bars, panel priority, dominant widget, fixed zones, or shell structure

Also extract from the chosen design pack:

- platform (`web` by default, `mobile` when clearly requested)
- semantic color tokens
- typography families/scales
- spacing and radius rules
- component style constraints
- responsive behavior expectations

Translate the input from markdown into a compact internal model before writing HTML.

If the task is a **scoped revision** of an existing PoC:

- first identify the exact requested surface to change
- map that surface back to the source widget/page definition
- keep a short list of **protected surfaces** that must remain untouched
- perform the smallest believable edit that satisfies the request
- after editing, verify that non-targeted sections still match the original source interpretation

### 2. Decide the single-file navigation model

Use one of these patterns:

- **Sidebar + page sections** for dashboard/admin specs
- **Top tabs + page sections** for small multi-page specs
- **Single long-scroll landing sections** only when the spec is essentially one route

For multi-page specs, prefer:

- one shell layout
- one navigation component
- one content mount area
- section switching with `data-page`, hash fragments, or tiny in-file state

Do not create separate documents for `/dashboard`, `/reports`, `/settings`, etc.

### 3. Convert widgets into reusable component families

Before coding, group widgets into reusable families:

- stat / KPI cards
- chart panels
- table panels
- list / timeline panels
- filter bars
- alert / status banners
- map panels
- form blocks
- detail summary blocks

Do not hand-code each widget as a unique snowflake if several share the same visual pattern.

### 4. Build mock data from the spec

All content must be fake but plausible.

Use the widget names and feature context to derive:

- KPI values
- chart series
- table rows
- map markers
- activity entries
- notifications
- filters

Rules for mock data:

- Keep naming aligned with the domain in the spec
- Keep counts realistic enough for demos
- Prefer a small but varied dataset
- Never call `fetch()`
- Never depend on external JSON files

### 5. Write one-file HTML architecture

Recommended structure:

```html
<!doctype html>
<html lang="id">
  <head>
    <!-- meta -->
    <!-- Tailwind CDN -->
    <!-- optional tiny tailwind.config derived from selected design pack -->
    <!-- Perfect Scrollbar CSS (always) -->
    <link href="https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/css/perfect-scrollbar.css" rel="stylesheet">
    <!-- conditional Mapbox CSS -->
    <style>
      /* inline CSS variables copied/adapted from selected variable.css */
      /* Perfect Scrollbar theme override ΓÇö match design pack tokens */
      .ps__rail-y, .ps__rail-x { background: transparent !important; opacity: 1 !important; }
      .ps__thumb-y { background: var(--border-hi) !important; border-radius: 0 !important; }
      .ps__thumb-x { background: var(--border-hi) !important; border-radius: 0 !important; }
      /* scrollable containers must be: overflow:hidden; position:relative */
      /* tiny custom CSS only for things awkward in utilities */
    </style>
  </head>
  <body>
    <div id="app"></div>

    <!-- Perfect Scrollbar JS (always) -->
    <script src="https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/dist/perfect-scrollbar.min.js"></script>
    <!-- conditional ECharts CDN when any chart uses ECharts -->
    <!-- conditional Mapbox JS CDN -->
    <script>
      const MAPBOX_ACCESS_TOKEN = "...";
      const designSystem = { /* selected pack + platform + token summaries */ };
      const specModel = { /* normalized pages */ };
      const mockData = { /* all fake data */ };
      const classes = { /* repeated Tailwind strings */ };
      const ui = {
        shell(){},
        navItem(){},
        panel(){},
        statCard(){},
        chartPanel(){},
        tablePanel(){},
        listPanel(){},
        mapPanel(){},
      };
      // render
      // init charts
      // init maps

      // Perfect Scrollbar ΓÇö init AFTER all content is rendered
      // const psX = new PerfectScrollbar('#scrollable-id', { suppressScrollX: true });
      // call psX.update() whenever content inside changes
    </script>
  </body>
</html>
```

## Reusability Rules

Efficiency is mandatory. Repetition should be absorbed into helpers, not duplicated in markup.

Minimum expectations:

- Define shared class groups, e.g. `panel`, `panelTitle`, `chip`, `metricValue`, `tableCell`
- Use reusable render helpers for repeated surfaces
- Keep one source of truth for spacing, radius, panel chrome, and typography rhythm
- Prefer data-driven rendering (`array.map`) over copied blocks
- Keep charts/maps initialized from configuration arrays when possible

Good pattern:

```js
const cls = {
  panel: "rounded-2xl border border-slate-200 bg-white shadow-sm",
  panelBody: "p-5",
  title: "text-sm font-semibold text-slate-900",
};

function panel(title, body) {
  return `
    <section class="${cls.panel}">
      <div class="${cls.panelBody}">
        <h3 class="${cls.title}">${title}</h3>
        ${body}
      </div>
    </section>
  `;
}
```

Bad pattern:

- Copy-pasting 8 nearly identical cards with only title and value changed
- Repeating long Tailwind strings in every section
- Writing separate imperative blocks for each simple chart when a small config loop would do

## Chart Rules

All chart widgets must use **ECharts** as the rendering engine. The goal is not to use ECharts in its most default-looking form; the goal is to produce a chart that still reads as the source-defined widget while visually fitting the surrounding UI.

Default-looking chart output is considered **insufficient** when the surrounding page is clearly art-directed. If the panel shell, map, sidebar, and overall interface already feel designed, but the chart still resembles a stock ECharts example with minimal framing, generic spacing, and untouched default treatment, the task is not done yet.

### What may be improvised

Freely improvise the **styling layer** around ECharts, for example:

- chart container framing
- gridline intensity
- palette tuning from the active design tokens
- line/bar/area glow treatment
- gradients and opacity balance
- axis label density
- legend treatment
- tooltip styling
- annotation badges
- target lock / tactical overlay chrome
- status chips and supporting labels around the chart
- chart-stage paneling (inner frame, corner brackets, stage borders, HUD strips)
- background series or threshold guides that improve readability
- emphasis markers (latest-point pulse, threshold line, acquisition window, alert band)
- glow, scanline, or tactical grid overlays **behind** the chart geometry
- value callouts, delta chips, and operator-facing chart footnotes

### Chart art-direction contract

For every chart widget, think in **two layers**:

1. **ECharts geometry layer**  
   The actual data visualization: line, bar, area, gauge, scatter, etc.
2. **Chart presentation layer**  
   The surrounding shell that makes the chart feel native to the selected design pack: panel chrome, tactical frame, HUD labels, metadata strip, annotations, and supporting status language.

In practice, the agent should assume a good chart panel usually needs:

- a titled chart shell, not only a naked chart canvas
- at least one supporting visual cue around the chart (badge, delta, threshold, mini metadata row, or callout)
- non-default tooltip styling
- token-aware gridline/axis treatment
- controlled use of gradient or glow when it improves hierarchy

The chart should feel like a **designed instrument panel**, not a library demo dropped into a box.

### What must stay locked to the source

Do not improvise away the source-defined chart role:

- keep the same metric purpose
- keep the same panel role inside the layout
- keep the same surrounding context in the page composition
- keep the same source-driven story (for example: risk trend, battery trend, mission probability, anomaly count)
- do not replace a real chart with a purely decorative widget unless the source itself asked for a non-chart telemetry treatment

### Balance rule

Aim for a middle ground:

- more polished than default ECharts demo styling
- more controlled than a flashy concept shot
- strong enough to feel designed
- restrained enough to keep data legible and credible

If forced to choose, prefer:

- clearer metric communication over decorative effects
- better panel hierarchy over louder color
- stronger tactical framing over adding extra chart types
- a few deliberate visual decisions over many random effects

### Implementation rules

- Before non-trivial ECharts `option` trees, read **[echarts.md](../../html-ui-styling/references/echarts.md)** (in `html-ui-styling`) for `getComputedStyle`, `resolveColor` / oklch, series order, and resize handling.
- When the user requests chart-only refinement, keep the same chart purpose, metric, and surrounding widget role from the source; improve the treatment, not the underlying feature definition
- Create chart containers with stable IDs
- Store ECharts option builders in reusable functions
- Initialize ECharts after the DOM is rendered
- Handle ECharts resize with a shared listener
- Reuse shared chart styling tokens/helpers where possible so multiple charts feel like one system
- Use demo-friendly, readable palettes that still follow the selected design pack tokens
- Supporting HTML/CSS chrome may enhance the chart, but the data geometry must remain readable
- Chart styling must not overpower panel hierarchy or break the intended composition of the overall UI
- Derive chart color/gradient decisions from the active design pack semantics first (`primary`, `warning`, `error`, `success`, etc.), not ad-hoc hex choices
- Prefer custom ECharts option treatment over untouched defaults: explicitly set tooltip, grid, axis, splitLine, series styling, and emphasis behavior
- Treat the chart container as a reusable component family (`chart shell`, `chart stage`, `chart meta strip`, `chart footnote`) instead of a one-off `<div>`
- Where appropriate, add one or two tactical readability aids using ECharts itself: `markLine`, `markPoint`, `effectScatter`, background bars, band thresholds, gauge ticks, or confidence zones
- Improve gauge and line/bar charts differently; do not apply one identical visual recipe to every chart type
- Use gradients, shadows, and glow as **hierarchy tools**, not as decoration sprayed everywhere
- If the rest of the interface is dense and cinematic, the charts must receive matching treatment before the task can be considered complete

### Strong recommendations by chart type

These are recommendations, not rigid requirements, but the agent should prefer them when they fit the source:

- **Line / area charts**
  - use softened curves only when the metric story still reads correctly
  - combine tuned gridlines + gradient area + one emphasis point or threshold marker
  - avoid raw default line-only styling unless the source explicitly calls for austere minimalism
- **Bar charts**
  - consider background tracks, threshold lines, or color-banded severity treatment
  - make label placement intentional; do not accept awkward stock placement
- **Gauge charts**
  - art-direct the whole instrument: ring, ticks, pointer, anchor, detail typography, and supporting labels
  - avoid the impression of a default circular gauge dropped into the panel
- **Radar / polar / special telemetry charts**
  - treat the frame, labels, and glow carefully so the geometry remains readable
  - never let tactical effects overpower the underlying metric comparison

### Failure mode to avoid

The following is a common failure and must be avoided:

- The agent adds ECharts correctly, but leaves the output looking like:
  - a plain chart canvas
  - minimal or generic axis styling
  - stock tooltip
  - no panel-specific chrome or metadata
  - no relationship to the surrounding design system beyond color choice

That outcome technically satisfies the library requirement, but **fails** the design-quality requirement of this skill.

Do not:

- use Chart.js, ApexCharts, Recharts, Nivo, or any other third-party charting library besides ECharts
- replace a source-defined chart with a fully custom non-ECharts rendering
- leave charts in raw default-demo styling when the surrounding UI is heavily art-directed
- over-style charts until labels, trends, comparison, or metric meaning become harder to read
- hardcode a completely unique implementation for every chart unless the widget is truly unique
- assume that \"using ECharts\" alone is enough; the styling layer is part of the deliverable
- dump a chart directly into a panel without surrounding chrome when the page language is tactical / cinematic / enterprise-dense
- use gradients, shadows, glows, or overlays that reduce contrast or make the series harder to parse

## Map Rules

Use **Mapbox GL JS via CDN** only when the spec includes a map widget.

Implementation rules:

- Set `mapboxgl.accessToken = MAPBOX_ACCESS_TOKEN`
- Use a bounded container height
- Add a small set of mock markers, popups, or one light overlay if useful
- Keep the map visually supportive of the page, not overengineered
- If the spec only says "peta sebaran" or similar, use a straightforward marker distribution with demo labels

Do not:

- call backend geocoding services
- create real-time sockets
- build a complex production layer system

## Styling Rules

Use Tailwind CDN for the main styling layer, but make the chosen design pack the visual source of truth.

Styling priority:

1. Follow `DESIGN.md`
2. Reuse token intent from `variable.css` / `varaible.css`
3. Mirror utility/theme naming from `tailwind.css`
4. Only then add a tiny amount of local CSS for PoC-only behavior

Prefer:

- semantic visual rhythm
- one shell style
- one panel style family
- one button system
- one badge system
- design-token-driven colors and typography
- responsive behavior that matches the selected pack's platform expectations

Use a tiny inline `<style>` block only for:

- scrollbar polish
- glass/blur edge cases
- chart or map container sizing
- animation details that are awkward in utilities
- inlined variables copied from the chosen design pack

Do not move styles into external CSS files.
Do not ignore the design tokens from `<cwd>/design/`.

## UX Rules for a PoC

The HTML should feel interactive enough for review, even though it is static.

Include lightweight demo behaviors when useful:

- page switching
- open/close sidebar on mobile
- filter chips that visually toggle
- tab switching
- modal or drawer previews
- fake notifications or activity pulses

Keep behavior local and simple. Avoid turning the PoC into a framework.

## Validation Checklist

Before finishing:

- [ ] A usable source document was chosen (`<cwd>/sprint/00-app-spec.md`, relevant file(s) under `<cwd>/brief/`, or equivalent)
- [ ] A relevant design pack under `<cwd>/design/` was selected
- [ ] `DESIGN.md`, `tailwind.css`, and `variable.css` / `varaible.css` were consulted before implementation
- [ ] No other design-pack files were read or loaded as design references
- [ ] Platform choice was resolved correctly (`web` by default, `mobile` when clearly requested)
- [ ] If this was a scoped revision, the requested surface was identified explicitly before editing
- [ ] If this was a scoped revision, non-targeted sections/pages/widgets were not broadened or silently redesigned
- [ ] If this was a scoped revision, the source-derived widget purpose/data contract remained intact
- [ ] Output is exactly one HTML file
- [ ] Output uses mock data only
- [ ] No external CSS or JS files were created
- [ ] Tailwind is loaded from CDN
- [ ] **Perfect Scrollbar CSS + JS CDN is always included**
- [ ] Every scrollable container has `overflow: hidden; position: relative` and is instantiated with `new PerfectScrollbar(...)`
- [ ] `ps.update()` is called after any dynamic content change inside a scrollable container
- [ ] PS thumb styles are overridden to match the active design pack (radius, color)
- [ ] Every chart widget uses ECharts as the rendering base
- [ ] Chart styling is improved beyond default ECharts demo appearance while still staying legible and source-aligned
- [ ] Mapbox CDN is included only if there are map widgets
- [ ] Mapbox token is set to the provided public token when maps are used
- [ ] Repeated panels/cards are implemented via reusable helpers
- [ ] Multi-page spec is simulated inside one HTML document
- [ ] No API calls or real backend logic exist
- [ ] Visual choices remain consistent with the selected design pack instead of ad-hoc styling
- [ ] Improvisation stayed within the source-defined UI composition and did not reshape the page structure without support from the source

## Anti-Patterns

- Do not start from the brief when a spec is available
- Do not ignore `<cwd>/design/` when a matching design pack exists
- Do not output multiple HTML files
- Do not generate separate `styles.css` or `app.js`
- Do not use React, Vue, Vite, Next, or any bundler
- Do not use real services or fetch live data
- Do not read or load `design-token.json` or any other non-approved design-pack file as a design reference
- Do not use non-ECharts chart libraries
- Do not replace chart widgets with custom-drawn chart systems that bypass ECharts
- Do not use non-Mapbox map libraries when a map is required
- Do not overfit every widget as a one-off layout if a shared panel pattern works
- Do not invent a fresh palette, spacing scale, or component language when `DESIGN.md` + token CSS already define one
- Do not broaden a local revision request into a full-page redesign without explicit user approval
- Do not change source-derived widget/page structure when the user only asked for a local visual improvement
- Do not treat "improve one section" as permission to replace the chosen source interpretation
- **Do not use native browser scrollbars** (`overflow-y: auto/scroll`, `scrollbar-width`, `::-webkit-scrollbar`) ΓÇö use Perfect Scrollbar on every scrollable container without exception

## Response Pattern

When using this skill, communicate briefly:

1. Confirm whether you are translating from a spec or directly from a brief
2. Confirm whether the task is a fresh generation or a scoped revision of an existing HTML PoC
3. Mention which design pack/platform was selected from `<cwd>/design/`
4. Mention whether chart and/or map CDN integrations are needed, with charts staying `ECharts only`
5. If scoped, state which surfaces are being changed and which are intentionally left untouched
6. Write the HTML file
7. Report the output path and the major demo sections included
