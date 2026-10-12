# Switch Theme — Rules & Validation Checklist

> These rules apply to **any** `design/` theme, and only when one exists and is selected.
> Visual rules from [`reactjs-ui-design`](../../reactjs-ui-design/SKILL.md) (component priority, states,
> radius `rounded-md`/`rounded-xl`, subtle shadows, review loop) survive every theme switch unless the
> selected theme's `DESIGN.md` explicitly overrides radius/shadow. Per-theme notes are in the Appendix.

---

## Core Rules

**Rule 1 — Source of truth is `design/[platform]/[theme]/`**

- Always read `design/[platform]/[theme]/DESIGN.md` first — it defines the font, primary mode (dark/light), semantic variable names, available palettes, and Tailwind class conventions for that theme.
- Never invent semantic variable names — copy them exactly from the canonical `variable.css`.
- Never modify `design/` files — they are Figma export artifacts. Treat them as read-only.

**Rule 2 — Both `variable.css` AND `tailwind.css` must be updated together**

- `variable.css` provides the raw `--base-*` palette and semantic CSS variables.
- `tailwind.css` maps them to Tailwind utility classes via `@theme inline {}`.
- Updating only one causes a broken token chain — some Tailwind classes will produce no color.

**Rule 3 — `DESIGN.md` supplies values; the playbook supplies composition**

- `DESIGN.md` defines the font, mode, palettes and (optionally) a radius/shadow policy. Import those into
  the semantic variables.
- Composition (page anatomy, building blocks, states) stays as defined by `reactjs-ui-design`.
- Do not invent token names outside `DESIGN.md` / `variable.css`.

**Rule 4 — `@theme inline` must include `--spacing: 0.25rem`**

- Tailwind v4 requires this as the first entry in `@theme inline {}`.
- Without it, all spacing utilities (`p-4`, `m-2`, `gap-3`) break.

**Rule 5 — Set `<html class>` to match the primary mode**

- Read the primary mode from `DESIGN.md` (dark-first or light-first).
- Dark-first themes: `<html lang="en" class="dark">`
- Light-first themes: `<html lang="en">` (no class)
- **Never hardcode this** — always derive from `DESIGN.md` for the active theme.

**Rule 6 — Neutral scale direction depends on the theme**

- Some themes (e.g. Tactical) invert the neutral scale in dark mode: `neutral-50` = near-black, `neutral-900` = near-white.
- Some themes (e.g. Fusion) use a standard scale: `neutral-50` = lightest, `neutral-900` = darkest.
- Always check `DESIGN.md` and the `.dark {}` block in `variable.css` to confirm the direction.
- This directly affects `bg-neutral-50`, `text-neutral-900`, etc. in components.

**Rule 7 — Only use palettes that exist in the active theme**

- Each theme defines its own palette list (primary, secondary, tertiary, etc.) in `DESIGN.md`.
- Do not reference `bg-quaternary-*` or `text-quinary-*` if the active theme doesn't include those palettes.
- Never delete a palette group or variable that code still references (see the additive-only rule below); remap its values to the new theme instead. Brand scales are for data visualization only.

**Rule 8 — No raw hex or `var(--base-*)` in component `className`**

- Components must only use shadcn semantic classes (`bg-background`, `bg-card`, `text-foreground`, `text-muted-foreground`, `border-border`, …)
- Allowed only in `variable.css` and `tailwind.css` — never in component JSX.

**Rule 9 — Preserve project-specific animations in `tailwind.css`**

- `tailwind.css` may contain project-specific `--animate-*` or `@keyframes` definitions.
- Keep these when adapting the canonical `tailwind.css` — the canonical file won't have them.

**Rule 10 — Additive-only: DESIGN.md is the primary guide**

- If `DESIGN.md` defines a semantic token that is NOT in the canonical `variable.css` or the app's `variable.css` → **add it**, do not skip it.
- When adding a new CSS variable: add to both `:root` AND `.dark {}` (with correct light/dark values), then register a Tailwind alias in `tailwind.css`.
- NEVER remove or reduce existing CSS variables from `variable.css` or entries from `tailwind.css` — only additive changes are allowed.
- Template files (`variable.css`, `tailwind.css`) are starting points. `DESIGN.md` is the authority.

**Rule 11 — Wire shadcn/ui variables in `variable.css`**

- shadcn/ui components use internal CSS variables (`--background`, `--foreground`, `--card`, `--popover`, `--border`, `--muted`, `--accent`, etc.)
- These MUST be mapped to the active theme's semantic tokens inside `variable.css` — both in `:root {}` and `.dark {}`.
- Do NOT override shadcn variables in component files or JSX.
- After switching themes, verify shadcn components (Button, Card, Dialog, Popover) render with correct theme colors.

---

**Rule 12 — Preserve radius/shadow rules unless the theme overrides them**

- Keep `--radius` so controls (`rounded-md`) ≈ 8px and surfaces (`rounded-xl`) ≈ 12px, and keep the subtle
  shadow scale (`shadow-xs` resting, `shadow-md/lg` floating).
- Only a selected theme whose `DESIGN.md` explicitly specifies a different policy (e.g. square, flat
  Tactical) changes them — through the variables, never by writing `rounded-none`/`shadow-none` into
  components. Note the override in `changelog/web.md`.

**Rule 13 — Primitives render correctly (release blocker)**

- Review every primitive on `/ui-kit` in light and dark after the switch; fix missing variables in CSS first,
  primitive `cva` variants second, call sites never.
- Sidebar and card surfaces are the visual anchors: if either looks wrong (transparent, wrong width, colors
  not switching), the switch has FAILED.

**Rule 14 — Layout contract parity**

- If `DESIGN.md` defines shell constraints (header height, sidebar width), apply them in
  `src/components/layouts/*` / `sidebar.tsx` constants while keeping the non-overlap contract in
  `.claude/rules/architecture.md`.

---

## Validation Checklist

After switching, verify each item:

### Visual

- [ ] Background surface matches the theme's primary mode (dark → dark surface, light → light surface)
- [ ] Primary accent color visible and matches DESIGN.md spec
- [ ] Body text is readable with sufficient contrast
- [ ] Toggle dark class on `<html>` — all surfaces switch cleanly

### Font

- [ ] Google Fonts link in `<head>` matches the font defined in DESIGN.md
- [ ] DevTools Computed → `font-family` on `<body>` shows the correct font
- [ ] `--font-sans` in `tailwind.css` matches the font name exactly

### Token Chain

- [ ] `variable.css` has complete `:root {}` (all `--base-*` + all semantic tokens)
- [ ] `variable.css` has complete `.dark {}` (all dark overrides)
- [ ] `tailwind.css` `@theme inline` includes `--spacing: 0.25rem`
- [ ] Every semantic class in DESIGN.md's Tailwind reference is present in `tailwind.css`
- [ ] No `--color-*` entry in `tailwind.css` references a missing `--variable` in `variable.css`

### Component cleanup

- [ ] No palette group or variable was deleted while still referenced; brand scales are used only for data-viz
- [ ] No raw hex colors in `className`
- [ ] No `var(--base-*)` direct usage in component JSX

### Primitive & composition check (CRITICAL)

- [ ] `/ui-kit` reviewed in light and dark: every primitive and `components/common` pattern renders with the new values
- [ ] Radius/shadow match the playbook (or the theme's explicit override, applied via variables only)
- [ ] Sidebar and card surfaces correct (width, active state, surfaces switch in dark)
- [ ] Shell layout constraints from `DESIGN.md` applied without overlap
- [ ] `npm run ui:snapshot -- --route /ui-kit --route / --route /administrator/user` PNGs reviewed against playbook §8

---

## How to Add a New Design System

Any new design system is supported immediately if it follows the folder convention:

```
design/
└── [platform]/
    └── [theme-name]/
        ├── DESIGN.md         ← Required: font, mode, token map, Tailwind classes, palettes
        ├── variable.css      ← Required: :root + .dark CSS custom properties
        └── tailwind.css      ← Required: Tailwind v4 @theme inline block
```

The agent will:

1. Read `DESIGN.md` to understand the theme's conventions
2. Import `variable.css` values into `apps/web/src/styles/variable.css`, keeping every shadcn semantic variable
3. Adapt `tailwind.css` to `apps/*/src/styles/tailwind.css`
4. Set the font and `<html>` class from `DESIGN.md`

No changes to the skill are required.

---

## Appendix — Per-Theme Migration Notes

### Tactical → Fusion (only relevant when a Tactical `design/` theme was active)

| Property            | Tactical (dark-first)   | Fusion (light-first)    |
| ------------------- | ----------------------- | ----------------------- |
| `<html>` class      | `class="dark"`          | _(remove class)_        |
| Font                | Montserrat              | Inter                   |
| Semantic text var   | `--font-primary`        | `--text-color-primary`  |
| Legacy alias text   | `text-font-primary`     | `text-foreground`       |
| Legacy alias bg     | `bg-background-primary` | `bg-background`         |
| Radius policy       | square (variable override) | playbook default (`rounded-md`/`rounded-xl`) |
| Extra palettes      | `orange`                | `quaternary`, `quinary` |
| Neutral 50 in dark  | near-black (inverted)   | lightest (standard)     |

### Fusion → Tactical

Reverse of the table above.

### Any New Theme

Read `DESIGN.md` for that theme. Its decision rules table and Tailwind class reference replace any per-theme table here.
