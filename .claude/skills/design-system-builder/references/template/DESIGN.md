# {THEME_NAME} — Style Reference
> {ONE_LINE_DESIGN_PHILOSOPHY} — {CORE_PRINCIPLES_3_TO_5_WORDS_EACH}.

**Theme:** {light | dark | system}

{NARRATIVE_PARAGRAPH: 4–6 sentences. Describe the design character. Cover: surface stack depth, radius philosophy, how hierarchy is expressed (type vs color vs spacing), primary color discipline, and the emotion/function the system targets. Be declarative — every sentence should constrain AI generation choices. Default direction is modern, minimal, slightly rounded (see .claude/rules/web/ui-design.md); deviate only where the brief explicitly asks.}

> **Example (default — modern minimal):** A calm, information-dense workspace in the spirit of Linear, Vercel and Stripe dashboards. About 90% of every screen is neutral: a `bg-background` canvas, `bg-card` surfaces with a 1px `border-border` and at most `shadow-xs`. Corners are slightly rounded — controls `rounded-md` (8px), cards, tables and dialogs `rounded-xl` (12px). Hierarchy comes from type size, weight and `text-muted-foreground`, not from boxes or color. `primary` appears only on the primary action, active navigation and focus; status colors only on status.
>
> **Example (brief-driven alternative — only when the brief asks for it, e.g. a military command center):** "Tactical" — square corners, flat surfaces, depth via two background steps. Such a theme must state its radius/shadow overrides explicitly in Do's and Don'ts and in `--radius*` / `--shadow*` tokens; otherwise the default applies.

---

## Colors

> Hex values listed for reference only. Never hardcode in implementation — always use the Tailwind token.

> Foreground pairs follow the shadcn convention: `bg-<token>` → `text-<token>-foreground` (e.g. `bg-primary text-primary-foreground`, `bg-card text-card-foreground`, `bg-destructive text-destructive-foreground`). Status colors are used as tints: `bg-success/10 text-success`.

### Surface

{INSTRUCTION: Define 6 surface tokens using the shadcn semantic classes: canvas (bg-background), card surface (bg-card), subtle fill (bg-muted), sidebar (bg-sidebar), border (border-border) and input border / focus ring (border-input / ring-ring). Neutral-first: all surfaces come from the neutral ramp, never from brand colors.}

| Name | Hex (info) | Tailwind Token | Role |
|------|-----------|----------------|------|
| {NAME} | `#{HEX}` | `bg-background` | Page canvas — the base all surfaces sit on |
| {NAME} | `#{HEX}` | `bg-card` | Cards, table wrappers, dialogs, popovers |
| {NAME} | `#{HEX}` | `bg-muted` | Subtle fill — hover rows, secondary buttons, skeletons, inline code |
| {NAME} | `#{HEX}` | `bg-sidebar` | Sidebar nav container |
| {NAME} | `#{HEX}` | `border-border` | All borders and dividers — one quiet 1px tone |
| {NAME} | — | `border-input` / `ring-ring` | Input borders and focus ring |

### Brand

> Each brand ramp has five stops: `light` → `soft` → `base` → `bold` → `deep`.

{INSTRUCTION: Define 5 brand colors. Brand 1 = primary (the single accent for primary actions, active nav, focus). Brands 2–5 = chart series and categorical data accents only — never buttons, cards, nav or page chrome. Assign a short evocative name and a role for each. Use the 5-stop ramp pattern for all.}

| Brand | Name | Base Hex (info) | Token Prefix | Role |
|-------|------|----------------|--------------|------|
| Primary | {NAME} | `#{HEX}` | `primary-*` | Primary action, active navigation, focus — the system's sole accent |
| Secondary | {NAME} | `#{HEX}` | `secondary-*` | Chart series 2, categorical data labels |
| Tertiary | {NAME} | `#{HEX}` | `tertiary-*` | Chart series 3, categorical data labels |
| Quaternary | {NAME} | `#{HEX}` | `quaternary-*` | Chart series 4, heat indicators |
| Quinary | {NAME} | `#{HEX}` | `quinary-*` | Chart series 5, categorical grouping |

Token usage pattern: `bg-<brand>-<stop>` / `text-<brand>-<stop>` / `border-<brand>-<stop>` — data visualization and categorical labels only.

Note: `bg-secondary` (no stop) is the shadcn **secondary button fill** and maps to a neutral tone; the brand ramp is `secondary-light … secondary-deep`.

Example: `bg-primary text-primary-foreground`, `bg-secondary-light text-secondary-bold` (category chip), `stroke: var(--chart-3)`

#### Neutral Colors

`bg-neutral-light / soft / base / bold / deep` — the source ramp for every surface, border and text token.

### State Colors (bg / text / border)

{INSTRUCTION: Keep the 4 semantic states. Adjust hex values in variable.css to fit the theme's palette. The role descriptions below are fixed — do not change them.}

| State | Grades |
|-------|--------|
| success | `*-success-light / soft / base / bold / deep` |
| error | `*-error-light / soft / base / bold / deep` (shadcn: `destructive`) |
| warning | `*-warning-light / soft / base / bold / deep` |
| info | `*-info-light / soft / base / bold / deep` |

| State | Role |
|-------|------|
| `success-*` | Positive trend indicators, completed status, success toasts |
| `error-*` / `destructive` | Danger/destructive actions, critical alerts, error badges, form validation |
| `warning-*` | Caution states, elevated thresholds, degraded performance indicators |
| `info-*` | Informational states, neutral data callouts, help text emphasis |

Default usage is a subtle tint: `bg-success/10 text-success`, `bg-destructive/10 text-destructive`. Solid fills only for one-off emphasis.

### Text

{INSTRUCTION: 5 text roles are required. Keep names and roles fixed — adjust hex values in variable.css only.}

| Use (shadcn class) | Legacy alias (still resolves) | Role |
|--------------------|-------------------------------|------|
| `text-foreground` | `text-font-primary` | Default text — body, headings, table data |
| `text-muted-foreground` | `text-font-secondary` | Muted copy, captions, table headers, helper labels |
| `placeholder:text-muted-foreground` | `text-font-placeholder` | Input placeholder text |
| `disabled:opacity-50` | `text-font-disabled` | Disabled input and control labels |
| `text-primary-foreground` | `text-font-on-accent` | Text on filled `primary` / `destructive` backgrounds |

### shadcn Semantic Variables (what React components consume)

`variable.css` must define these in `:root` **and** `.dark`; shadcn primitives in `apps/web/src/components/ui/` read only these, so re-branding never requires per-component edits.

| CSS variable | Tailwind class | Default mapping |
|--------------|----------------|-----------------|
| `--background` / `--foreground` | `bg-background` / `text-foreground` | neutral canvas / neutral deep |
| `--card` / `--popover` (+ `-foreground`) | `bg-card` / `bg-popover` | neutral surface, one step from canvas |
| `--primary` / `--primary-foreground` | `bg-primary` / `text-primary-foreground` | brand primary base / on-accent |
| `--secondary` / `--muted` / `--accent` | `bg-secondary` / `bg-muted` / `bg-accent` | neutral subtle fills (accent may be a light primary tint) |
| `--muted-foreground` | `text-muted-foreground` | neutral, ≥ 4.5:1 on `--background` |
| `--destructive` | `bg-destructive` / `text-destructive` | error base |
| `--border` / `--input` / `--ring` | `border-border` / `border-input` / `ring-ring` | quiet neutral / neutral / primary |
| `--sidebar*` | `bg-sidebar`, `text-sidebar-foreground`, `bg-sidebar-accent` … | neutral |
| `--chart-1 … --chart-5` | `chart-1 … chart-5` | brand ramps 1–5 (data only) |
| `--radius` (+ `--radius-sm … -3xl`) | `rounded-md` / `rounded-lg` / `rounded-xl` | 8px / 10px / 12px |
| `--shadow-xs / -md / -lg` | `shadow-xs` / `shadow-md` / `shadow-lg` | resting surface / dropdown / dialog |

---

## Typography

### {FONT_FAMILY} — {ONE_SENTENCE_TYPEFACE_RATIONALE}

{INSTRUCTION: One typeface only. Explain in 2–3 sentences why this family was chosen and how its weight range drives hierarchy without family-switching.}

- **Substitute:** {GOOGLE_FONTS_OR_SYSTEM_FALLBACK}
- **Weights:** `font-regular` (400), `font-medium` (500), `font-semibold` (600) for UI; `font-bold` (700) only for display numerals
- **Base size:** `text-body-lg` ({PX}px)
- **Line height:** {leading-* at display sizes}, {leading-* at body sizes}
- **Letter spacing:** `tracking-tight` on page titles and display sizes, `tracking-normal` elsewhere

### Font Family Tokens

| Token | Font | Digunakan untuk |
|-------|------|-----------------|
| `font-sans` | {BODY_FONT_NAME} | Body, UI copy, labels, inputs |
| `font-serif` | {HEADING_FONT_NAME} | Display, h1–h4, stat numbers |
| `font-mono` | {MONO_FONT_NAME} | Code, data values, timestamps |

### Type Scale

{INSTRUCTION: 9 roles minimum. Keep the token names (text-label-sm through text-display). Adjust sizes and weights to reflect the theme's density. Compact = smaller gaps; Airy = larger. In the React app these roles map to the Tailwind default scale: body text-sm, page title text-2xl font-semibold, section title text-base font-semibold, caption text-xs.}

| Role | Size Token | Size | Weight Token | Line Height Token |
|------|-----------|------|--------------|-------------------|
| Caption / badge | `text-label-sm` | {PX}px | `font-regular` | `leading-snug` |
| Label | `text-label-md` | {PX}px | `font-medium` | `leading-snug` |
| Body small | `text-body-sm` | {PX}px | `font-regular` | `leading-normal` |
| Body | `text-body-lg` | {PX}px | `font-regular` | `leading-relaxed` |
| Subheading | `text-h6` | {PX}px | `font-semibold` | `leading-snug` |
| Heading small | `text-h5` | {PX}px | `font-semibold` | `leading-tight` |
| Heading | `text-h4` | {PX}px | `font-semibold` | `leading-tight` |
| Metric | `text-h2` | {PX}px | `font-semibold` | `leading-tight` |
| Display | `text-display` | {PX}px | `font-bold` | `leading-none` |

---

## Spacing & Layout

**Base unit:** `spacing-1` (4px grid)

**Density:** {compact | comfortable | airy}

{INSTRUCTION: Fill in spacing values to match the chosen density. Compact = tighter padding. Keep the list of properties fixed. Default card padding is p-6 (compact p-4).}

- **Page width:** conditional — full width for map/canvas pages; `max-w-{SIZE} mx-auto` for all other pages
- **Section gap:** `gap-{N}`
- **Card padding:** none on container — padding lives on card header (`px-{N} py-{N}`) and card body (`px-{N} py-{N}`)
- **Element gap:** `gap-{N}`
- **Sidebar width:** {PX}px expanded / {PX}px collapsed

---

## Components

{INSTRUCTION: Define all components below. For each: preserve the Role line, keep the base Tailwind class string (semantic tokens, rounded-md controls, rounded-xl surfaces), add hover/focus/active state classes, and add a 1–2 sentence behavioral note. Do NOT invent new component names — add variants inside the existing ones. In the React app these are shadcn primitives (Button, Card, Table, Badge, Input, Alert, Tabs, Sidebar) already themed through the variables above.}

### Primary Button
**Role:** Main CTA — Save, Confirm, Apply filter, Export

`bg-primary text-primary-foreground font-sans text-body-sm font-medium rounded-md shadow-xs px-{N} py-{N}`

Hover → `hover:bg-primary-bold`. {ADDITIONAL_NOTES}

### Border Button
**Role:** Secondary actions, cancel, adjacent controls

`bg-background border border-input text-foreground rounded-md shadow-xs hover:bg-accent px-{N} py-{N}`

{BEHAVIORAL_NOTE}

### Destructive Button
**Role:** Delete, remove, terminate operations

`bg-destructive text-destructive-foreground rounded-md shadow-xs px-{N} py-{N}`

Hover → `hover:bg-destructive/90`. Use only for irreversible actions, always behind a confirmation dialog.

### Ghost Button
**Role:** Inline tertiary actions, icon-only controls

`text-foreground rounded-md hover:bg-accent hover:text-accent-foreground` — no background or border at rest. {BEHAVIORAL_NOTE}

### Segmented Button / Timeframe Toggle
**Role:** Mutually exclusive filter or timeframe selection — a group of inline buttons where exactly one is active at a time

Container: `inline-flex items-center gap-0.5 rounded-lg bg-muted p-0.5`

Base (inactive): `px-{N} py-{N} text-label-sm font-medium rounded-md text-muted-foreground hover:text-foreground`

Active: `px-{N} py-{N} text-label-sm font-medium rounded-md bg-background text-foreground shadow-xs`

{RADIUS_NOTE}. In React use the shadcn `ToggleGroup` / `Tabs` primitive.

### Panel Card
**Role:** Stat blocks, data tables, form sections, widget containers

Container: `bg-card text-card-foreground border border-border rounded-xl shadow-xs` — no padding on the container itself; tables inside use `overflow-hidden`.

Card header: `px-{N} py-{N}` — no border-b by default; add `border-b border-border` only when explicit separation from the body is needed.
Card body: `px-{N} py-{N}`
Card footer: `px-{N} py-{N} border-t border-border`

{SHADOW_NOTE}

### Metric Block
**Role:** Key KPI callouts — counts, percentages, status numerics

Large numeral: `text-h2 font-semibold tabular-nums text-foreground`. Label above: `text-label-md font-medium text-muted-foreground`. Optional trend indicator (arrow icon + delta value) at `text-label-md`: `text-success` (positive) or `text-destructive` (negative). Sits inside a Panel Card.

### Data Table
**Role:** Structured tabular data — the primary information display organism

- Wrapper: Panel Card with `overflow-hidden` (table never floats on the canvas)
- Header row: `bg-muted/50 text-label-sm font-medium text-muted-foreground`
- Body rows: `h-12 text-body-md font-regular text-foreground`
- Row dividers: `border-b border-border`
- Row hover: `hover:bg-muted/50`
- Selected row: `bg-muted`

{ALTERNATING_ROW_NOTE}

### Sidebar / Nav
**Role:** Primary navigation container

`bg-sidebar border-r border-sidebar-border` — fixed width {PX}px (collapsed: {PX}px icon-only).

- Nav links inactive: `rounded-md text-body-md font-medium text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground`
- Nav links active: `rounded-md bg-sidebar-accent text-sidebar-accent-foreground font-medium`

### Badge / Status Chip
**Role:** Inline state labels — semantic states and categorical labels

Base classes applied to every badge regardless of variant: `inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-label-sm font-medium`. Status badges carry a `size-1.5 rounded-full bg-current` dot.

**Tinted** (default — in-table and inline states):

| Variant | Classes |
|---------|---------|
| Neutral | `bg-muted text-muted-foreground` |
| Primary / active | `bg-primary/10 text-primary` |
| Success | `bg-success/10 text-success` |
| Error | `bg-destructive/10 text-destructive` |
| Warning | `bg-warning/10 text-warning` |
| Info | `bg-info/10 text-info` |
| Category (data only) | `bg-secondary-light text-secondary-bold` (same for tertiary / quaternary / quinary) |

**Solid** (rare — one prominent standalone badge per view):

| Variant | Classes |
|---------|---------|
| Primary | `bg-primary text-primary-foreground` |
| Destructive | `bg-destructive text-destructive-foreground` |

### Input Field
**Role:** All form inputs, search fields, filter controls

`bg-transparent border border-input rounded-md shadow-xs px-{N} py-{N} font-sans text-body-md font-regular text-foreground placeholder:text-muted-foreground`

- Focus: `focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50` — never remove the ring
- Invalid: `aria-invalid:border-destructive aria-invalid:ring-destructive/20`
- Optional left icon at 16px, `text-muted-foreground`

### Alert / Toast
**Role:** System feedback — success, warning, error, info notifications

Base: `rounded-lg border px-4 py-3` (toasts additionally `shadow-lg`).

| Variant | Classes |
|---------|---------|
| Default | `bg-card border-border text-foreground` |
| Success | `bg-success/10 border-success/30 text-success` |
| Error | `bg-destructive/10 border-destructive/30 text-destructive` |
| Warning | `bg-warning/10 border-warning/30 text-warning` |
| Info | `bg-info/10 border-info/30 text-info` |

Title: `text-body-md font-medium`. Body: `text-body-sm font-regular text-muted-foreground`. Semantic icon at 16px, inline left.

### Tab Bar
**Role:** In-panel content switching — Overview / Details / History

- Segmented (default, shadcn Tabs): list `rounded-lg bg-muted p-0.5`; active trigger `rounded-md bg-background text-foreground shadow-xs font-medium`; inactive `text-muted-foreground font-medium`
- Underline (page-level tabs): active `border-b-2 border-primary text-foreground font-medium`; inactive `text-muted-foreground`

{TAB_STYLE_NOTE: segmented or underline}. Spacing: `py-{N} gap-{N}`.

### Header / Top Bar
**Role:** Global page-level nav strip

`bg-background border-b border-border h-{N}`

- Left: wordmark or breadcrumb — `text-body-md font-semibold text-foreground`
- Center: optional search input
- Right: icon actions (`text-muted-foreground`, ghost icon buttons with tooltips) + user menu

---

## Do's and Don'ts

{INSTRUCTION: Keep the structural rules below. Replace the example-specific content in each bullet with constraints derived from the chosen theme. Each Do must be a positive constraint; each Don't must name a specific forbidden pattern. Default radius rule: controls rounded-md 8px, surfaces rounded-xl 12px, rounded-full only for avatars/dots/switches. Only a brief that explicitly asks for square corners may say otherwise.}

### Do
- Use `bg-card` for all card and panel surfaces, `bg-sidebar` for sidebar/nav containers — semantic aliases express intent.
- Apply `primary` exclusively to primary actions, active states, and focus.
- {TYPOGRAPHY_HIERARCHY_RULE}
- {RADIUS_RULE — default: controls rounded-md (8px), surfaces rounded-xl (12px)}
- {ICON_USAGE_RULE}
- {SURFACE_STACK_RULE — max N background tones per view}
- Use `text-muted-foreground` for all secondary text — captions, table headers, helper copy, placeholders.
- Design loading (skeleton), empty (icon + title + hint + action) and error (inline alert + retry) states for every data surface.

### Don't
- Don't use `primary` as a card background, decoration, or repeated highlight — scarcity is its power.
- {RADIUS_DONT — matching the radius rule above}
- {TYPEFACE_DONT}
- {SHADOW_DONT}
- Don't use color for decorative purposes — every color must encode a semantic or functional state. No gradients, glows, colored shadows or glassmorphism.
- Don't nest cards inside cards or put a border around every element — space separates groups.
- Don't place body text at `text-label-sm` or below — compact density is achieved through spacing and weight hierarchy.
- **Never use raw palette colors or arbitrary values** (`bg-blue-500`, `text-[13px]`, `#hex`). Opacity modifiers on semantic tokens are fine for tints and hover (`bg-success/10`, `hover:bg-muted/50`, `ring-ring/50`); if a needed tone does not exist, add a semantic token to `variable.css` first.

---

## Elevation

{INSTRUCTION: Default depth model is quiet: 1px borders plus at most shadow-xs on resting surfaces; real shadows only on floating layers. A brief that explicitly asks for a flat system may set shadow tokens to none and say so here. Keep this table structure.}

Depth comes from a quiet border plus a minimal shadow on resting surfaces, and real shadows only on layers that float above the page.

| Level | Tailwind Classes | Notes |
|-------|-----------------|-------|
| Canvas | `bg-background` | Absolute base, never a card background |
| Card | `bg-card border border-border rounded-xl shadow-xs` | Cards, stat blocks, table wrappers, panel containers |
| Sidebar | `bg-sidebar border-r border-sidebar-border` | Sidebar nav; header uses `bg-background border-b border-border` |
| Row hover | `hover:bg-muted/50` | Ephemeral state on table rows and nav links |
| Active nav | `bg-sidebar-accent text-sidebar-accent-foreground rounded-md` | Persistent active-link surface |
| Input focus | `focus-visible:ring-[3px] ring-ring/50 border-ring` | Visible ring, never removed |
| Dropdown / popover | `bg-popover border border-border rounded-xl shadow-md` | Floating menus, comboboxes, date pickers |
| Dialog / sheet / toast | `bg-background border border-border rounded-xl shadow-lg` | Overlay layers |
| Modal overlay | `bg-black/50` | Backdrop behind dialogs |

---

## Surfaces

| Surface | Token | Notes |
|---------|-------|-------|
| Canvas | `bg-background` | Page background — main area may use `bg-muted/40` for subtle layering |
| Card | `bg-card` | Cards, stat blocks, widget containers, dialogs |
| Sidebar | `bg-sidebar` | Sidebar nav container |
| Muted / hover | `bg-muted` | Table header, row hover, skeletons, secondary buttons |
| Active nav fill | `bg-sidebar-accent` | Behind active sidebar nav items |

---

## Layout

{INSTRUCTION: Write one dense paragraph (5–8 sentences) covering: canvas approach, sidebar dimensions, header height, primary grid strategy (12-col or auto-fit), gap values, card padding convention, table width, metric card column count, chart placement. Every page starts with a header block: title, one-line description, one primary action. Then define the page width rule for full-width vs max-width pages.}

{LAYOUT_PARAGRAPH}

**Page width rule:**
- **Full width** — pages with large map canvas (Mapbox, geospatial, fullscreen chart). No max-width on `<main>` or content wrapper.
- **Max-width** — all other pages (dashboard, analytics, report, metrics, alerts, tables). Wrap main content with `max-w-{SIZE} mx-auto w-full` inside `<main>`; header remains full-width.

---

## Chart & Data Visualization Colors

{INSTRUCTION: Map the 5 brand ramps to chart series 1–5 in order. Always use base stop for active line/bar, -soft for area fills. Grid and axis styling is fixed.}

The five brand ramps serve as the categorical color sequence for charts and data series. Always use the base stop for the active data line/bar, `-soft` for area fills and backgrounds.

| Series | Token | Alias | Role |
|--------|-------|-------|------|
| Series 1 | `primary` | `chart-1` | Primary metric line/bar — the dominant data series |
| Series 2 | `secondary-base` | `chart-2` | Comparison or secondary metric |
| Series 3 | `tertiary-base` | `chart-3` | Tertiary data series |
| Series 4 | `quaternary-base` | `chart-4` | Fourth data series or heat indicator |
| Series 5 | `quinary-base` | `chart-5` | Fifth series or categorical grouping |

Area fill under a line: use `-soft` stop at 15–20% opacity (e.g. `bg-primary-soft/20`).
Grid lines and axis labels: `border-border` / `text-muted-foreground`.
Tooltip container: `bg-popover border border-border rounded-lg shadow-md`.

---

## Similar Brands

{INSTRUCTION: List 4–5 real products whose visual language overlaps with this design system. One sentence each — focus on the specific shared trait (surface approach, type weight discipline, color vocabulary, density). This section helps AI calibrate the intended aesthetic register.}

- **{PRODUCT}** — {SHARED_TRAIT}
- **{PRODUCT}** — {SHARED_TRAIT}
- **{PRODUCT}** — {SHARED_TRAIT}
- **{PRODUCT}** — {SHARED_TRAIT}
- **{PRODUCT}** — {SHARED_TRAIT}

---

<!--
GENERATION CHECKLIST — remove this block after generation is complete

Theme identity:
[ ] THEME_NAME and tagline filled
[ ] Theme (light/dark/system) set
[ ] Narrative paragraph written — constrains AI choices (default modern-minimal unless the brief says otherwise)

Colors:
[ ] 6 surface tokens defined (canvas, card, muted, sidebar, border, input/ring) — all neutral
[ ] 5 brand colors chosen with hex + role (brands 2–5 data-only)
[ ] State colors acknowledged (hex in variable.css, roles unchanged)
[ ] 5 text roles acknowledged (hex in variable.css, roles unchanged)
[ ] shadcn semantic variables present in :root and .dark (incl. --radius, --border)

Typography:
[ ] Single typeface chosen + rationale written
[ ] All 9 type scale rows filled (px sizes + weights)

Spacing:
[ ] Density level set (compact / comfortable / airy)
[ ] All 5 spacing properties filled

Components:
[ ] All components filled with Tailwind classes (rounded-md controls, rounded-xl surfaces)
[ ] Hover/focus states specified
[ ] Behavioral notes added where marked

Rules:
[ ] Do: 8 rules filled
[ ] Don't: 8 rules filled (raw-value / opacity rule preserved verbatim)

Elevation & Surfaces: unchanged unless the brief explicitly asks for a flat system

Layout:
[ ] Layout paragraph written
[ ] Page width rule filled

Charts: unchanged — tokens reference brand palette above

Similar brands: 4–5 products listed with shared traits
-->
