---
name: uiux
description: Design-token pipeline — creating or importing a design/ theme (from a brief or Figma) and syncing its tokens into apps/web/src/styles or a Flutter theme. Use when the user mentions design tokens, a Figma file, a brand palette/typography to import, or a design/ folder. For building or restyling React UI (pages, components, dashboards, forms, tables) load reactjs-ui-design first — it is the visual playbook (shadcn-first, semantic tokens, review loop); this skill only feeds it values.
---

# Skill: UI/UX Design System

> **Visual rules:** [`reactjs-ui-design`](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns the **token pipeline** (brief/Figma → `design/` → app styles).
>
> **Building UI in `apps/web`?** Start with `reactjs-ui-design`: component priority (shadcn
> `components/ui` → install with `npx shadcn@latest add` → `components/common` patterns +
> `modules/data-table` → static markup), shadcn semantic classes only (`bg-card`,
> `text-muted-foreground`, `border-border`, `bg-primary`), designed states, and the screenshot review loop
> (`npm run ui:snapshot`). No `design/` folder is needed for that — the app's own tokens in
> `apps/web/src/styles/variable.css` are the default modern-minimal theme.

## Position in the Argus pipeline

This skill runs **after** [`brief-builder`](../brief-builder/SKILL.md) and **before** [`bootstrap-project`](../../commands/bootstrap-project.md):

1. Read the brief at `<cwd>/brief/00_OVERVIEW.md` + per-feature `<cwd>/brief/NN_*.md`. Extract information architecture, screens, personas, data shapes.
2. Produce design tokens under `<cwd>/design/`. Token files are what scaffolded apps consume.
3. When design is satisfied, hand off to [`bootstrap-project`](../../commands/bootstrap-project.md) — the project scaffold reads `<cwd>/design/` to drive PoC frontend code; tokens flow into `apps/web/src/styles/` after scaffold.

If `<cwd>/brief/` does not exist yet, redirect to `brief-builder` first — never run the token pipeline against an unwritten brief. (Ordinary UI work in an existing app does not need a brief — use `reactjs-ui-design`.)

---

## Design System Structure

When a project has a `<cwd>/design/` folder, it is the source of the token **values**. Start by reading the active config:

```
<cwd>/design/
├── design-system.md          ← READ FIRST — active platform + theme config
└── web/
    └── {theme}/
        ├── DESIGN.md         ← visual guidelines, semantic token reference, component rules
        ├── variable.css      ← CSS custom properties (actual color/spacing/typography values)
        └── tailwind.css      ← Tailwind v4 @theme mapping from variable.css
```

> `design-token.json` exists in the folder but **DO NOT LOAD** — already compiled into `variable.css` and `tailwind.css`.

### Resolution steps (mandatory — always in this order)

**Step 1** — Read `design/design-system.md`:
- Check `Active Config` → get `platform` and `theme`
- Resolve path: `design/{platform}/{theme}/`

**Step 2** — Load 3 files from the active theme folder:

| File | Load when |
|------|-----------|
| `DESIGN.md` | Always — visual guidelines, semantic token reference, component rules |
| `variable.css` | Always — actual values for all CSS variables |
| `tailwind.css` | Always — Tailwind v4 mapping from variable.css |

**Step 3** — Apply to code (see Apply sections below)

---

## Resolution Process (Before Generating Any UI)

### Level 1 — Token already exists

1. Read `design/design-system.md` → resolve `platform` + `theme`
2. Load `design/{platform}/{theme}/DESIGN.md`, `variable.css`, `tailwind.css`
3. Extract semantic tokens from `DESIGN.md` (colors, typography, spacing, radius)
4. Use Tailwind classes from `tailwind.css` and CSS vars from `variable.css`
5. Apply to code per the Apply sections below

### Level 2 — Extract from Figma

If the theme folder does not exist or tokens are empty/incomplete:

1. Check Figma link in brief or ask user to provide one
2. Read the Figma file/page title → convert to **kebab-case** → use as the theme name
   - Examples: "Tactical Design System" → `tactical`, "Fusion UI Kit" → `fusion`, "Dark Navy Pro" → `dark-navy-pro`
3. Determine platform: **web** or **mobile**
4. Create folder `design/{platform}/{theme}/` if it does not exist
5. Extract from Figma: color styles, text styles, spacing, component specs
6. Output directly to 3 files in that folder:
   - `design/{platform}/{theme}/DESIGN.md` — visual guidelines + semantic token table
   - `design/{platform}/{theme}/variable.css` — CSS custom properties with actual values from Figma
   - `design/{platform}/{theme}/tailwind.css` — Tailwind v4 `@theme inline { }` mapping from variable.css
7. Update `design/design-system.md`:
   - Add row to **Available Themes** if new theme
   - Update **Active Config** if this theme is being used immediately
8. **Do not overwrite existing files** — append/update only the relevant sections

> **Naming rule:** theme name = Figma title in kebab-case, derived from the file or main page name. Never use an arbitrary name — always derive from Figma.

### Level 3 — No `design/` theme and no Figma (the default in this boilerplate)

- Do **not** block UI work. Use the app's existing semantic tokens (`apps/web/src/styles/variable.css`)
  and the `reactjs-ui-design` playbook — modern, minimal, neutral-first, slightly rounded.
- Never invent arbitrary colors/fonts in components. If the user wants a brand, re-brand via the semantic
  variables (`--primary`, `--ring`, `--radius`, chart colors — `reactjs-design-system` Step 1) or create a
  theme with `design-system-builder`.

---

## Web — Apply Token

After loading 3 files from the active theme folder, apply to the project in this order:

### 1. CSS Variables → `apps/web/src/styles/variable.css`

Import the values from `design/web/{theme}/variable.css` into the project's **semantic shadcn variables** (`--background`, `--card`, `--primary`, `--muted`, `--border`, `--ring`, `--sidebar-*`, `--chart-*`) in `:root` and `.dark`. Keep the semantic names — components never learn theme-specific class names. Details: `reactjs-switch-theme`.

```css
/* Example values imported from a design/ theme */
:root {
  --base-neutral-50: #FFFFFF;
  --base-neutral-900: #080C14;
  --base-primary-500: #4FC3E8;
  /* ... all CSS vars from design/web/{theme}/variable.css */
}
```

### 2. Tailwind Config → `apps/web/src/styles/tailwind.css` or `globals.css`

Copy or sync from `design/web/{theme}/tailwind.css`. Maps CSS vars to Tailwind utility classes via Tailwind v4 `@theme inline`.

```css
/* Example from a design/ theme's tailwind.css */
@import "tailwindcss";

@theme inline {
  --color-neutral-50: var(--base-neutral-50);
  --color-primary-500: var(--base-primary-500);
  /* ... all mappings from design/web/{theme}/tailwind.css */
}
```

### 3. Components — follow the playbook

Component composition, radius (controls `rounded-md` ≈ 8px, surfaces `rounded-xl` ≈ 12px), shadows
(`shadow-xs` resting, `shadow-md/lg` floating) and states come from `reactjs-ui-design`. A theme's
`DESIGN.md` may override radius/shadow **only if it states so explicitly** — apply that through the
variables (`--radius`, `--shadow-*`), never by writing per-component classes. Read its **Components**
section for brand-specific details (e.g. button weight, input height) and map them onto the primitives'
variants in `src/components/ui/`.

> **Always use semantic classes** (`bg-primary`, `bg-card`, `border-border`) — never hardcode hex values
> from `variable.css` into components.

After applying: `cd apps/web && npm run ui:snapshot -- --route /ui-kit` and review light + dark.

---

## Figma Extraction → Output to 3 Files

When extracting from Figma, produce 3 files (not JSON):

### `DESIGN.md`

```markdown
# {Theme Name} — Style Reference

> {One-sentence visual system description}

## Tokens — Colors

### Semantic / Brand Tokens

#### Background
| Role | Token | Source |
|------|-------|--------|
| Primary | `background.primary` | neutral.50 |
| Secondary | `background.secondary` | neutral.100 |

...

## Tokens — Typography
...

## Components
...
```

### `variable.css`

```css
/* ============================================
  {THEME} DESIGN SYSTEM - Design Tokens
  Source: design/web/{theme}/variable.css
============================================ */

:root {
  /* BASE COLOR PALETTE */
  --base-neutral-50: {hex from Figma};
  --base-neutral-100: {hex from Figma};
  ...

  /* SEMANTIC TOKENS */
  --color-background-primary: var(--base-neutral-50);
  --color-text-primary: var(--base-neutral-900);
  ...

  /* SHADCN SEMANTIC VARIABLES (required — apps/web components use only these) */
  --background: var(--base-neutral-50);
  --card: var(--base-neutral-50);
  --primary: var(--base-primary-500);
  --muted: var(--base-neutral-100);
  --border: var(--base-neutral-200);
  --ring: var(--base-primary-300);
  ...
  --radius: 0.5rem; /* playbook default: controls 8px, surfaces 12px — change only if Figma says so */
}
```

### `tailwind.css`

```css
/* ============================================================
  {Theme} Design System — Tailwind v4 Theme Mapping
  Maps CSS variables from variable.css → Tailwind utility classes
============================================================ */

@import "tailwindcss";

@theme inline {
  /* Neutral Palette */
  --color-neutral-50: var(--base-neutral-50);
  --color-neutral-100: var(--base-neutral-100);
  ...

  /* Semantic */
  --color-background-primary: var(--color-background-primary);
  --color-text-primary: var(--color-text-primary);
  ...
}
```

---

## Mobile — Apply Token

Same structure — resolve from `design/design-system.md` then load 3 files:

```
design/mobile/{theme}/
├── DESIGN.md
├── variable.css
└── tailwind.css
```

For Flutter, extract values from `variable.css` and map to `app_theme.dart`:

```dart
// Derived from design/mobile/{theme}/variable.css
static const Color backgroundPrimary = Color(0xFF...); // --color-background-primary
static const Color textPrimary = Color(0xFF...);       // --color-text-primary
static const Color primaryBase = Color(0xFF...);       // --color-primary-base

static const double spacing1 = 4.0;
static const double spacing2 = 8.0;
static const double spacing4 = 16.0;
```

---

## Rules

- **UI work in `apps/web`:** load `reactjs-ui-design` first; this skill only supplies token values
- **If a `design/` folder exists:** read `design/design-system.md` first, then load `DESIGN.md` + `variable.css` + `tailwind.css`
- **NEVER** load `design-token.json` — not needed, already compiled into CSS
- **NEVER** hardcode hex values directly into components — use semantic tokens
- **NEVER** generate UI without resolved tokens — the app's `src/styles/variable.css` always provides them
- Generated themes default to the playbook direction (neutral-first, radius 8/12px, subtle shadows) unless the brief/Figma says otherwise
- **Figma extraction → output directly to `design/`**:
  - Folder: `design/{platform}/{theme}/` — create if it does not exist
  - Platform: `web` or `mobile` — determine from context
  - Theme name: derive from **Figma file/page title**, convert to **kebab-case**
  - Output: 3 files (`DESIGN.md`, `variable.css`, `tailwind.css`) — not JSON
- Append-only updates when files already exist — never overwrite entirely
