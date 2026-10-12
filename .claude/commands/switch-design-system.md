# Command: /switch-design-system

Apply the **active** design system from the workspace `design/` folder into a target app under `apps/`. Do **not** invent a new theme name — derive everything from `design/design-system.md`.

## Trigger

`/switch-design-system [app-folder]`

- If `[app-folder]` is omitted, infer the primary web app (e.g. `apps/web`) from context or ask once which app under `apps/` to update.

## Mandatory first reads

The active theme's **`DESIGN.md`** supplies the brand values (palette, fonts, primary mode, any explicit radius/shadow choices). They are applied by **mapping onto the shadcn semantic variables** in `src/styles/variable.css` (`--background`, `--card`, `--primary`, `--muted-foreground`, `--border`, `--ring`, `--radius`, `--chart-*`, `--sidebar-*`), not by restyling components one by one. Everything `DESIGN.md` does not explicitly override stays on the defaults in **`.claude/rules/web/ui-design.md`** (modern-minimal, `rounded-md` controls / `rounded-xl` surfaces, quiet shadows, shadcn-first). Skills below explain *how* to apply it in code.

### `components/ui/` — base primitives (non-negotiable)

Everything under **`apps/<target>/src/components/ui/`** is the **base component layer** (shadcn/Radix primitives, already themed through semantic tokens). After a design-system switch, audit every file in this folder: semantic colors, rings and radii must come from the token chain (no hardcoded values left from an old theme). Change primitive classes only where the new `DESIGN.md` **explicitly** differs from the `ui-design.md` defaults (e.g. a brief-driven square/flat theme); otherwise keep the primitives as they are. Leaving a primitive with hardcoded old-theme values breaks downstream pages that compose from `ui/`.

### A — Workspace routing & contract file

1. **`design/design-system.md`** — read the **Active Config** table for `platform` and `theme`. All canonical paths use these two values only.
2. **`design/[platform]/[theme]/DESIGN.md`** — read **before** editing any app file. This file defines palette usage, semantic Tailwind classes, forbidden patterns, card/sidebar/table/dialog recipes, typography scale, and how each surface should be composed after a switch.

### B — Skills (load every run; order matters)

3. **`.claude/skills/reactjs-switch-theme/SKILL.md`** — mechanical pipeline: copy/adapt `variable.css`, `tailwind.css`, fonts, `<html>` default mode, verification, Step 7 composition audit (Steps 0–7). Entry point for *files on disk*.

4. **`.claude/skills/reactjs-design-system/SKILL.md`** — token wiring and re-branding through the semantic variables; when (rarely) a variant/class override is justified by the active `DESIGN.md`.

5. **`.claude/skills/reactjs-slicing-ui/SKILL.md`** — token chain discipline (`design-system.md` → `DESIGN.md` → CSS → Tailwind → components) when porting a mockup or Figma; look & feel defers to `reactjs-ui-design`.

6. **`.claude/skills/reactjs-sidebar/SKILL.md`** — when the app shell uses shadcn Sidebar: layout offsets, `SIDEBAR_WIDTH`, menu/active/hover classes — all must follow the **sidebar rules in active `DESIGN.md`** (often requires edits to `sidebar.tsx` + layout).

7. **`.claude/skills/reactjs-app-layout/SKILL.md`** — **shell + regions**: `AppLayout`, `AppHeader`, topbar vs sidebar vs main — no overlapping regions; offsets when Sidebar is `fixed`; route/`Outlet` wiring; **active `DESIGN.md` shell contract** (header height, sidebar width, canvas/surface tokens). Required whenever the theme switch touches layout files.

### C — Always

- **`.claude/rules/web/ui-design.md`** + **`.claude/skills/reactjs-ui-design/SKILL.md`** — the default visual rules and the review loop. After the switch run `npm run ui:snapshot -- --route / --route /ui-kit` (from `apps/web`) and review the PNGs in light and dark.

### D — Optional context

- **`.claude/skills/uiux/SKILL.md`** — only if you need broader `./design/` resolution or Figma alignment; the active `DESIGN.md` wins for brand values, `ui-design.md` for anything it does not specify.

Canonical sources (replace `[platform]` and `[theme]` from Active Config):

| Asset | Path |
| ----- | ---- |
| Contract + class map | `design/[platform]/[theme]/DESIGN.md` |
| CSS variables | `design/[platform]/[theme]/variable.css` |
| Tailwind `@theme` | `design/[platform]/[theme]/tailwind.css` |

## Execution steps (summary — details live in the skill)

1. **Step 0** — Resolve active `platform` + `theme` from `design/design-system.md`. Read `DESIGN.md` for that theme before editing files.

2. **Step 1** — Copy `design/[platform]/[theme]/variable.css` → `apps/<target>/src/styles/variable.css` (preserve any project-specific CSS suffix rules described in the skill).

3. **Step 2** — Adapt app theme file from canonical `tailwind.css` (this repo often uses `src/styles/tailwind.css` or `theme.css`): merge with existing `@theme inline`, keep `@import "tailwindcss"` only in `index.css`, preserve project animations.

4. **Step 3** — Update Google Fonts (or equivalent) in `index.html` per **active** `DESIGN.md`.

5. **Step 4** — Set default mode on `<html>` (`class="dark"` or not) per **primary mode** in **active** `DESIGN.md`.

6. **Step 5** — Verify visually: `npm run ui:snapshot -- --route / --route /ui-kit` (light + dark), open the PNGs (surfaces, font, dark mode, palette cleanup, radius/shadow consistency).

7. **Step 6** — Token chain integrity: `DESIGN.md` → canonical CSS → app CSS → components.

8. **Step 7 — CRITICAL** — Composition alignment: (a) **audit every file under `components/ui/`** for hardcoded values and for differences the **active** `DESIGN.md` explicitly requires (otherwise keep the `ui-design.md` defaults); (b) audit **app shell** (`components/layouts/*`, `AppLayout`, regions per **app-layout** skill); (c) audit composed surfaces (cards, tables, dialogs, etc.). Adjust primitives and layouts where defaults still reflect the old theme — **preserve Radix/shadcn behavior and a11y**, change presentation only.

## Output

- List every file created or modified with a one-line reason.
- Do not mark complete until Step 7 composition checks pass for the **active** theme.

## References

- Theme files & verification: `.claude/skills/reactjs-switch-theme/SKILL.md`
- Composition & shadcn vs `DESIGN.md`: `.claude/skills/reactjs-design-system/SKILL.md`
- Token chain & UI primitives: `.claude/skills/reactjs-slicing-ui/SKILL.md`
- Sidebar shell: `.claude/skills/reactjs-sidebar/SKILL.md`
- App shell (layout regions, header/sidebar/main): `.claude/skills/reactjs-app-layout/SKILL.md`
- Optional checklist: `.claude/skills/reactjs-switch-theme/references/switch-theme-rules.md`
