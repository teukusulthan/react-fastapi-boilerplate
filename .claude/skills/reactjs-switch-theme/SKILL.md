---
name: reactjs-switch-theme
description: Step-by-step guide to switch apps/web to a design system theme from a design/[platform]/[theme]/ folder (only when such a theme exists and is selected). Covers importing the theme's variables into the semantic shadcn variables, adapting tailwind.css, default mode, font, and verifying with the screenshot review loop — while preserving the reactjs-ui-design radius/shadow/component rules unless the selected theme explicitly overrides them. Light/dark toggling is useThemeStore, not this skill.
---

# Switch Theme Skill (React / TypeScript)

> **Visual rules:** [`reactjs-ui-design`](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns **importing a `design/` theme** into the token files.
> A theme switch changes **values** (palette, font, radius, default mode) behind the semantic variables —
> it never changes component code, component priority, states or the review loop. The playbook's
> radius/shadow rules (controls `rounded-md`, surfaces `rounded-xl`, `shadow-xs` resting) stay in force
> unless the selected `design/` theme's `DESIGN.md` explicitly specifies otherwise.

> Apply any design system theme to a React app by replacing `variable.css` and `tailwind.css`
> with the canonical files from `design/[platform]/[theme]/`.
> Works for any design system that follows the `design/` structure. This repo ships **no** `design/`
> folder; without one, there is nothing to switch — re-brand via `reactjs-design-system` Step 1 instead.
>
> **In this repo (`apps/web`):** tokens live in `src/styles/variable.css`, the Tailwind v4 `@theme inline` mapping in `src/styles/tailwind.css`, component/scrollbar styles in `src/styles/components.css`; `src/index.css` imports all three after `@import 'tailwindcss'`. Dark mode is the `.dark` class on `<html>`, managed by `src/stores/useThemeStore.ts` (`@custom-variant dark` in `index.css`).

---

## When to Use This Skill

- Switching the active design system theme for a React app
- Regenerating CSS after the design contract or CSS variables are updated
- Onboarding a new React app that needs its theme variables populated

**With this skill, also load:** `.claude/skills/reactjs-ui-design/SKILL.md` (visual rules that survive the switch), `.claude/skills/reactjs-design-system/SKILL.md` (token chain), `.claude/skills/reactjs-app-layout/SKILL.md` (shell regions) and, if the theme changes sidebar width, `.claude/skills/reactjs-sidebar/SKILL.md`. The command `.claude/commands/switch-design-system.md` encodes the full read order.

Not this skill: the user-facing light/dark/system toggle (`ThemeToggle` + `src/stores/useThemeStore.ts`).

---

## Step 0 — Resolve the Active Theme

Read `design/design-system.md` to confirm:

- `platform` — e.g. `web`, `mobile`
- `theme` — the active theme name (e.g. `tactical`, `fusion`, `carbon`, `material`)

All subsequent paths derive from these two values:

```
design/
└── [platform]/
    └── [theme]/
        ├── DESIGN.md         ← READ THIS FIRST — decision rules, token map, font, dark mode behavior
        ├── variable.css      ← CSS custom properties (:root + .dark)  ← COPY THIS
        └── tailwind.css      ← Tailwind v4 @theme mapping              ← ADAPT THIS
```

**Read `design/[platform]/[theme]/DESIGN.md` before doing anything else.**
It defines: font family, default mode (dark or light), semantic variable names, forbidden patterns,
and the Tailwind class reference for that specific theme.

> **Theme switching is applied by the AI in the IDE** — read the canonical files from `design/[platform]/[theme]/`
> and apply them directly. In Cursor, use the **`/switch-design-system`** command (`.claude/commands/switch-design-system.md`) as the standard entry point.

---

## Step 1 — Import the theme into `variable.css`

Bring the values of `design/[platform]/[theme]/variable.css` into `apps/web/src/styles/variable.css`.
A straight copy is fine **only** if the canonical file keeps the shadcn semantic variables
(`--background`, `--card`, `--primary`, `--muted`, `--border`, `--ring`, `--sidebar-*`, `--chart-*`) and
their `.dark` overrides; otherwise merge so that every semantic variable still exists and points at the
new palette. Components only know the semantic classes — never rename them to theme-specific names.

**Radius/shadow:** keep `--radius` so that `rounded-md` ≈ 8px and `rounded-xl` ≈ 12px, and keep the
subtle `--shadow-xs`/`--shadow-md`/`--shadow-lg` scale — **unless** the theme's `DESIGN.md` explicitly
specifies a different radius/shadow policy. Record such an override in `changelog/web.md`.

**Keep all content as-is from the canonical file:**

- All `--base-*` palette values in `:root` (light/default-mode values)
- All semantic tokens (`--bg-*`, `--font-*`, `--border-*`, `--state-*`, brand scales, etc.)
- The complete `.dark {}` block (overrides `--base-*` to dark-mode values)
- `--radius-*`, `--shadow-*`, typography scale variables
- All shadcn/ui wiring variables (`--background`, `--foreground`, `--card`, `--sidebar`, etc.)

**Adapt if needed:**

- Spacing values: if the canonical file uses `px` units (`--spacing-1: 4px`) and the app needs `rem`,
  convert: 4px → 0.25rem, 8px → 0.5rem, etc. OR rely on Tailwind v4's `--spacing: 0.25rem` in `tailwind.css`
- Radius values: similarly convert `px` → `rem` if the boilerplate requires it

**Verify the result has all sections:**

```css
:root {
  /* --base-* palette (neutral, primary, secondary, tertiary, ...) */
  /* --base-* state colors (warning, error, success, info, ...) */
  /* Semantic tokens (--bg-*, --font-*, --border-*, --state-*, brand scales) */
  /* shadcn/ui wiring (--background, --foreground, --card, --sidebar, ...) */
  /* --radius-*, --shadow-*, typography scale */
}

.dark {
  /* ALL --base-* overridden to dark-mode values */
  /* shadcn/ui overrides for dark mode */
}
```

---

## Step 2 — Adapt `tailwind.css`

Base the new `tailwind.css` on `design/[platform]/[theme]/tailwind.css` with these adaptations:

1. **Remove** the `@import "tailwindcss";` line (already in `index.css`)
2. **Add** `--spacing: 0.25rem;` as the first entry in `@theme inline {}` (Tailwind v4 base spacing unit)
3. **Preserve** any project-specific animations from the previous `tailwind.css`
4. **Keep** every existing palette group and semantic variable (rule: additive only). If the new theme's
   `DESIGN.md` has no values for a brand scale (`secondary-*` … `quinary-*`, data-viz only), map it to
   the closest new values instead of deleting it — charts and legacy code still reference them

The result must include all color palette aliases (direct `--color-{palette}-{shade}` entries) plus
all semantic aliases that DESIGN.md defines as Tailwind classes:

```css
@theme inline {
  --spacing: 0.25rem;
  --font-sans: "..."; /* from DESIGN.md */

  /* Full base palette: --color-neutral-*, --color-primary-*, etc. */
  /* Semantic aliases: whatever DESIGN.md lists as Tailwind classes */
  /* shadcn/ui: --color-background, --color-foreground, --color-card, ... */
  /* --radius-*, --shadow-*, --text-* scale */
}
```

---

## Step 3 — Update Font in `index.html`

Read the font requirement from `design/[platform]/[theme]/DESIGN.md`.
Replace or add the Google Fonts `<link>` in `<head>`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family={FontName}:wght@400;500;600;700&display=swap"
  rel="stylesheet"
/>
```

Also verify `tailwind.css` has the matching `--font-sans` value.

---

## Step 4 — Set the Default Mode on `<html>`

Read the **primary mode** from `design/[platform]/[theme]/DESIGN.md`:

| Primary mode | Action                                         |
| ------------ | ---------------------------------------------- |
| **Dark**     | Set `class="dark"` on `<html>` in `index.html` |
| Light        | Remove `class="dark"` from `<html>`            |

```html
<!-- Dark-first theme -->
<html lang="en" class="dark">
  <!-- Light-first theme -->
  <html lang="en"></html>
</html>
```

> **Why this matters:** `:root {}` in `variable.css` holds the default-mode values.
> The `.dark {}` block holds the alternate-mode overrides.
> Without the correct class on `<html>`, the app renders in the wrong mode.

---

## Step 5 — Verify the Result

### Visual check (screenshot review loop)

```bash
cd apps/web
npm run ui:snapshot -- --route /ui-kit --route / --route /administrator/user   # light + dark, desktop + mobile
```

Open every PNG and run the playbook §8 checklist. Also:

- Background color matches the theme's primary mode (dark theme → dark surface; light theme → light surface)
- Primary accent color matches the theme (check `DESIGN.md` for the expected primary color)
- Body text is readable on all surfaces

### Font check

- DevTools → Elements → Computed → `font-family` on `<body>` matches the expected font

### Dark mode check

- Toggle dark mode by adding/removing `class="dark"` on `<html>` in DevTools
- All surfaces switch correctly
- No invisible text, no transparent panels

### Palette cleanup

- Components should only use semantic classes; if any still use a brand scale (`secondary-*` … `quinary-*`)
  outside data-viz, migrate them to semantic classes rather than deleting the scale
- Check `DESIGN.md` of the **new** theme for the available palette list

### tailwind.css audit

- Every semantic class name listed in `DESIGN.md`'s "Decision Rules" table has a corresponding `--color-*` entry in `tailwind.css`
- No entry references a CSS variable that doesn't exist in `variable.css`

---

## Step 6 — Token Chain Integrity Check

```
DESIGN.md  →  design/variable.css  →  apps/web/src/styles/variable.css  →  tailwind.css  →  component
```

Each layer must be complete. Verify:

| Layer                             | Check                                                                       |
| --------------------------------- | --------------------------------------------------------------------------- |
| `design/[platform]/[theme]/DESIGN.md` | Defines the active visual contract, semantic names, and composition rules |
| `apps/*/src/styles/variable.css` | All `--base-*` match the canonical `variable.css` values                    |
| `apps/*/src/styles/tailwind.css`  | All semantic classes in `DESIGN.md` are registered                          |
| Components                        | No raw hex, no arbitrary Tailwind, no direct `var(--base-*)` in `className` |

---

## Step 7 — Primitive & composition check (CRITICAL)

> Theme switching is NOT complete until the primitives render correctly with the new values.

**`src/components/ui/`:** review each primitive on `/ui-kit` in light and dark. Because primitives use
semantic classes (`bg-card`, `border-border`, `rounded-xl`, `ring-ring`), a correct variable import
usually needs **no component edits**. Edit a primitive's `cva` variants only when:

- a color doesn't switch → the variable is missing in `:root` or `.dark` (fix the CSS, not the component);
- the theme defines a structural constant that differs (e.g. `SIDEBAR_WIDTH` in `sidebar.tsx`, header height);
- the theme's `DESIGN.md` explicitly mandates a radius/shadow policy the variables can't express.

Composition stays as the playbook defines it (`PageHeader` → content surfaces, `DataTable` in a card,
`StatCard` rows, designed states). Do not rewrite pages to theme-specific class names; legacy aliases
(`bg-background-primary`, `text-font-*`, `border-border-primary`) are only for older code.

Do NOT declare the theme switch complete until `/ui-kit` and two real pages look right in both modes.

---

## Appendix — Known Design System Specifics

> These are examples. Any design system that follows the `design/[platform]/[theme]/` structure works.

### Tactical (only when the active `design/` theme is Tactical)

Tactical is a dark-first command-center theme that explicitly overrides the playbook's radius/shadow
policy. Apply these values **only** when `design/design-system.md` selects it; express them through the
variables (`--radius: 0`, flat shadows), not by writing `rounded-none` into components.

| Property                  | Value                                                                              |
| ------------------------- | ---------------------------------------------------------------------------------- |
| Primary mode              | **Dark** — set `class="dark"` on `<html>`                                          |
| Font                      | Montserrat                                                                         |
| Primary color             | Cyan / Sky Blue                                                                    |
| Neutral scale             | **Inverted in dark mode** — `neutral-50` = near-black in `.dark`, white in `:root` |
| Extra palette             | `orange` (high-risk state)                                                         |
| Missing                   | No `quaternary`, no `quinary`                                                      |
| Semantic font vars        | `--font-primary`, `--font-secondary`, `--font-placeholder`, `--font-on-accent`     |
| Tailwind text classes     | `text-font-primary`, `text-font-secondary`, `text-font-placeholder`                |
| Tailwind bg classes       | `bg-background-primary`, `bg-background-secondary`                                 |
| Radius / shadow           | Square, flat — via `--radius` / `--shadow-*` variables, not component classes      |

### Fusion

| Property              | Value                                                                        |
| --------------------- | ---------------------------------------------------------------------------- |
| Primary mode          | Light — no `class="dark"` on `<html>`                                        |
| Font                  | Inter                                                                        |
| Primary color         | Blue (navy)                                                                  |
| Neutral scale         | Standard (50=lightest, 900=darkest), same in light and dark                  |
| Extra palettes        | `quaternary` (pink/red), `quinary` (purple)                                  |
| Missing               | No `orange` state palette                                                    |
| Semantic font vars    | `--text-color-primary`, `--text-color-secondary`, `--text-color-placeholder` |
| Tailwind text classes | `text-foreground`, `text-muted-foreground` (shadcn defaults)                 |
| Tailwind bg classes   | `bg-background`, `bg-secondary` (shadcn defaults)                            |

---

> Detailed rules and validation checklist: [references/switch-theme-rules.md](references/switch-theme-rules.md)
