---
name: reactjs-design-system
description: Token wiring and re-branding for apps/web — how the semantic CSS variables in src/styles/variable.css (--primary, --ring, --radius, chart colors, sidebar, status) map to Tailwind/shadcn classes in src/styles/tailwind.css, how to re-brand without touching components, how to add a token, how to verify a var() actually resolves, and how to import an optional design/ theme. Use when wiring tokens, re-branding, fixing visual drift caused by missing/wrong variables, broken dark mode, or editing shadcn variants' token usage. For how UI should look (radius, shadow, spacing, typography, component priority), load reactjs-ui-design first.
---

# Design System Skill — Token Wiring & Re-branding (`apps/web`)

> **Visual rules:** [`reactjs-ui-design`](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns the **token chain**: CSS variables → Tailwind theme →
> shadcn semantic classes, re-branding, dark mode completeness, and importing an optional `design/` theme.

The look of the app (modern, minimal, neutral-first, slightly rounded: controls `rounded-md` 8px,
surfaces `rounded-xl` 12px, `shadow-xs` on resting surfaces) is defined by the playbook. This skill makes
sure the tokens behind those classes exist, resolve, and switch correctly between light and dark.

---

## shadcn/ui contract — primitives are the baseline

- shadcn primitives in `src/components/ui/` are **already re-themed** to our tokens. Their styling *is* the
  baseline: use them as-is, with their variants (`variant`, `size`), instead of re-styling per screen.
- If a primitive looks wrong, the fix is **token wiring** (a missing/wrong variable) or the primitive's
  own `cva` variants in `src/components/ui/<name>.tsx` — never a one-off override at the call site and
  never a hand-rolled replacement.
- Keep behavior props intact (`asChild`, `aria-*`, `data-*`, controlled values, refs, portals, focus rings).
- Component priority (use `ui/` → install from shadcn → compose `components/common` /
  `modules/data-table` → hand-write static markup) is defined in the playbook §3.

| Need | Use |
|---|---|
| Button, Input, Select, Dialog, Popover, Dropdown, Tooltip, Form, Sidebar, Card, Table, Badge… | shadcn primitive from `src/components/ui/` (install it if missing) |
| Page title, KPI tile, empty state, settings section, status pill, confirm dialog | `src/components/common/` patterns (`PageHeader`, `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`, `ConfirmDialog`) |
| Any list / table | `src/modules/data-table/` (`DataTable` + toolbar/pagination) |
| Bounded scroll (sidebar body, main, panels, feeds) | **`PerfectScrollArea`** — not Radix `ScrollArea` for new work (see `reactjs-responsive` § *Scrollable regions*) |
| A primitive renders with the wrong color/radius | Fix the variable or the primitive's variant — not the call site |

---

## Step 0 — Where tokens live

| File | Role |
|---|---|
| `src/styles/variable.css` | `:root` + `.dark`: base palettes (`--base-*`), **semantic shadcn variables** (`--background`, `--foreground`, `--card`, `--popover`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--input`, `--ring`, `--sidebar-*`, `--chart-1…5`, status `--success-*`/`--warning-*`/`--info-*` exposed as `bg-success`, `text-warning`, `bg-info/10` …), `--radius*`, `--shadow-*`, `--font-sans` |
| `src/styles/tailwind.css` | `@theme inline`: maps variables to Tailwind utilities (`--color-*`, `--radius-*`, `--shadow-*`, `--text-*`) |
| `src/styles/components.css` | Global component CSS (e.g. `.ps__*` scrollbar theming from tokens) |
| `index.html` | Font `<link>` (Inter) |

**Optional `design/` theme.** This repo has no `design/` folder by default. *If a `design/` theme exists*
(`design/design-system.md` → `design/[platform]/[theme]/DESIGN.md`), read its `DESIGN.md` and import its
**values** into the semantic variables above (Step 4). Its brand colors, font and radius replace ours;
the component priority, states and review loop from the playbook still apply. Without a `design/`
theme, the playbook is the visual contract and `variable.css` is the source of truth.

---

## Step 1 — Re-brand by changing semantic variables only

To change the look of the whole app, edit **only** `src/styles/variable.css` (both `:root` and `.dark`):

| Want | Change |
|---|---|
| Brand / accent color | `--primary`, `--primary-foreground`, `--ring` (and `--sidebar-primary`, `--sidebar-ring`) |
| Corner radius | `--radius` (the base; `--radius-sm/md/lg/xl` derive from it). Keep the playbook mapping: controls `rounded-md` ≈ 8px, surfaces `rounded-xl` ≈ 12px |
| Neutral temperature | `--background`, `--card`, `--muted`, `--accent`, `--border`, `--input` |
| Chart palette | `--chart-1` … `--chart-5` |
| Status colors | the status variables behind `--color-success` / `--color-warning` / `--color-info` and `--destructive` |
| Font | `--font-sans` + the `<link>` in `index.html` |

Never restyle per component, never add raw colors in components, never re-brand by editing call sites.
After re-branding, check light **and** dark with `npm run ui:snapshot -- --route /ui-kit`.

---

## Step 2 — Verify the font is loaded

`index.html` loads **Inter** via Google Fonts (`preconnect` + stylesheet). `--font-sans` must reference it.
If a `design/` theme specifies another font, swap both the `<link>` and `--font-sans` — nothing else.
Never set `font-family` inline in components.

---

## Step 3 — Verify CSS variables are complete

Every variable used by a utility must exist in **both** `:root` and `.dark`.

| Component group | Variables required |
|---|---|
| shadcn base | `--background`, `--foreground`, `--card`, `--card-foreground`, `--popover`, `--popover-foreground`, `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--muted`, `--muted-foreground`, `--accent`, `--accent-foreground`, `--destructive`, `--border`, `--input`, `--ring` |
| Sidebar (shadcn) | `--sidebar`, `--sidebar-foreground`, `--sidebar-primary`, `--sidebar-primary-foreground`, `--sidebar-accent`, `--sidebar-accent-foreground`, `--sidebar-border`, `--sidebar-ring` |
| Status | the variables behind `--color-success`, `--color-warning`, `--color-info` (grep `tailwind.css` for the current names) |
| Charts | `--chart-1` … `--chart-5` |
| Radius / shadow | `--radius` (+ derived `--radius-*`), `--shadow-xs`, `--shadow-md`, `--shadow-lg` |

Then open `src/styles/tailwind.css`: the `@theme inline` block needs a `--color-*` alias for every color
variable used as a class. A semantic variable without an alias = a class that silently does nothing.

### ⚠️ Token-name reality — silent `var()` failures

A wrong token name fails silently — CSS drops an undefined `var()` with no error. `rounded-(--r-md)` or
`text-(--font-primary)` compiles to valid CSS that produces *nothing* (square corners / default color),
passes build and typecheck, and looks broken. `DESIGN.md` files (if a `design/` theme exists) often use
spec-level names that are **not** the compiled variable names.

Rule: **before using any `var(--x)` / `bg-(--x)` / `rounded-(--x)`, confirm `--x` is defined in the
served CSS.** Better: use the semantic utility (`bg-card`, `rounded-xl`) and don't reference variables
directly at all.

- Grep real names: `grep -roE -- "--[a-z0-9-]+:" src/styles/*.css | sort -u`.
- After building, confirm the class resolved **and** the variable exists:
  `grep -oE "border-radius:var\(--radius-xl\)" build/**/*.css` and `grep -oE -- "--radius-xl:[^;}]+" build/**/*.css`.

### Primitive radius sanity check

Every primitive must carry the playbook radius in its own base classes: controls (`button`, `input`,
`select` trigger, `badge`, `toggle`) `rounded-md`; surfaces (`card`, `dialog`, `popover`, `sheet`,
dropdown content, table wrapper) `rounded-xl`; `rounded-full` only for avatar/switch/dots. If a newly
installed shadcn component renders square, fix its `cva` base string — fixing the base fixes every usage.

---

## Step 4 — Importing a `design/` theme (only if one exists)

1. Read `design/design-system.md` → active `platform`/`theme` → `design/[platform]/[theme]/DESIGN.md`.
2. Map the theme's palette onto our **semantic** variables (`--primary`, `--background`, `--card`,
   `--border`, `--ring`, `--sidebar-*`, `--chart-*`, status). Keep the semantic names — components never
   learn theme-specific class names.
3. Map its radius onto `--radius`. Only if the theme explicitly specifies square corners or no shadows
   (e.g. a "Tactical" command-center theme) do you change radius/shadow — and then only via variables,
   documented in `changelog/web.md`.
4. Snapshot `/ui-kit` and two real pages in light + dark.

Legacy alias classes (`bg-background-primary`, `text-font-*`, `border-border-primary`) still resolve for
older code, but new code uses the shadcn semantic classes.

---

## Step 5 — Replace hardcoded values

| Found | Replace with |
|---|---|
| `#hex`, `rgb()`, `hsl()` in className/style | Semantic class (`bg-card`, `text-muted-foreground`, `border-border`, `bg-primary`) |
| Tailwind palette (`blue-500`, `gray-200`, `red-400`) | Semantic class; status → `text-success`, `bg-warning/10`, `text-destructive` |
| Arbitrary values (`text-[13px]`, `p-[18px]`, `rounded-[14px]`) | Tailwind scale (`text-sm`, `p-4`, `rounded-xl`) |
| Brand palettes (`secondary-*`, `tertiary-*` scales) in chrome | Neutral/semantic classes — those scales are for data viz only |
| Inline `style` for visuals | Classes |

Typography uses Tailwind's default scale per the playbook (`text-sm` body, `text-2xl font-semibold
tracking-tight` page title, `text-base font-semibold` section title, `text-xs` caption).

---

## Step 6 — Dark mode verification

Toggle dark (`.dark` on `<html>`, or the theme toggle). Verify no transparent/invisible surfaces,
borders visible but quiet, text contrast sufficient, sidebar/card/popover/dialog have dark surfaces.
Then `npm run ui:snapshot -- --route <path>` and look at the dark PNGs.

---

## Common fixes

| Symptom | Fix |
|---|---|
| Sidebar transparent | Missing `--sidebar-*` in `variable.css` or alias in `tailwind.css` |
| Wrong font | Missing Inter `<link>` / `--font-sans` |
| Color mismatch | Raw palette class → semantic class |
| Dark mode broken | Variable defined in `:root` but not `.dark` |
| Component square / unrounded | Primitive's `cva` base lacks `rounded-md`/`rounded-xl`, or a `rounded-(--x)` with an undefined variable |
| Header and sidebar overlap | Structural shell bug — see `reactjs-app-layout` and the shell contract in `.claude/rules/architecture.md` (root `flex h-svh flex-col overflow-hidden`, header `h-12`, body `flex min-h-0 flex-1`, sidebar offset `top-12 h-[calc(100svh-3rem)]` with its gap reserving `--sidebar-width`, main `SidebarInset` with `PerfectScrollArea`) |

---

## Adding a new token

1. Confirm no existing semantic variable fits (most needs are covered by `muted`, `accent`, status).
2. Add it to `src/styles/variable.css` in **both** `:root` and `.dark`.
3. Alias it in `src/styles/tailwind.css` `@theme inline` (`--color-<name>: var(--<name>)`).
4. Add a swatch/usage to the `/ui-kit` page section that shows tokens (if present).

Never declare CSS variables inside component files.

---

## Pre-submission checklist

- [ ] Visual decisions follow `reactjs-ui-design` (radius, shadow, spacing, typography, component priority)
- [ ] Re-branding done only via semantic variables in `variable.css`
- [ ] Every referenced variable exists in `:root` **and** `.dark`, and has a `tailwind.css` alias
- [ ] Zero raw hex/rgb, zero Tailwind palette colors, zero arbitrary values in components
- [ ] Inter (or the `design/` theme font) loaded in `index.html`; no inline `font-family`
- [ ] Primitives keep behavior/accessibility; their base classes carry the playbook radius
- [ ] If a `design/` theme exists, its values are imported into the semantic variables (not into components)
- [ ] `npm run ui:snapshot` reviewed in light + dark
