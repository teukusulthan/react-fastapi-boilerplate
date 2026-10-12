---
name: design-apply
description: Set up design system assets (CSS tokens, Tailwind stylesheet, loader.js) into a target folder. Use when asked to "setup design system", "init design system", "copy CSS assets", "init mockup folder", or before slicing a new UI page when the target folder doesn't yet have variable.css / tailwind.css. Also called internally by html-ui-styling when scaffolding a new page.
---

# Design System Setup

Thin wrapper — resolves active platform/theme, then delegates to `/design-apply`.

> **No `design/` folder?** There is nothing to apply. For mockups, copy the app tokens
> (`apps/web/src/styles/variable.css` + `tailwind.css`) into `{TARGET}/css/` and generate `styles.css` / `script.js` /
> `loader.js` per Step 3A of the command; the visual direction is `.claude/rules/web/ui-design.md`. For the app, do
> nothing — it already ships the default modern-minimal tokens. Create a theme first with `design-system-builder` if
> the brief needs a different brand.
>
> **App targets (`apps/*`):** applying a theme means swapping token *values* (palette, `--radius*`, shadows, fonts)
> behind the shadcn semantic variables. It never restyles components one by one — see Step 4 of
> `.claude/commands/design-apply.md` and the visual rules in `.claude/skills/reactjs-ui-design/SKILL.md`.

## Step 1 — Resolve Platform & Theme

Read `design/design-system.md`.

| Variable | How to resolve |
|---|---|
| `PLATFORM` | From task context: `web` or `mobile`. **Default: `web`** if not stated. |
| `THEME` | From `design-system.md` — find the active theme row for the resolved `PLATFORM`. |
| `TARGET` | From task context. Default: `mockup/{PLATFORM}-html` (e.g. `mockup/web-html`, `mockup/mobile-html`) for mockup tasks, or the explicit `apps/*` path for app tasks. |

After resolving, output a short progress update:

```
Active design : {THEME} ({PLATFORM})
Default theme : dark | light   ← from design-system.md active row
Brand primary : {list each primary color name + hex from DESIGN.md}
```

## Step 2 — Invoke Command

Run `/design-apply` with resolved values:

```
/design-apply --source={THEME} --platform={PLATFORM} --target={TARGET} [--skip-ui]
```

Pass `--skip-ui` only if explicitly requested. Default behavior (no flag) runs the full flow including UI component update.

Examples after resolution (`{theme}` = the active theme slug in `design/design-system.md`):
```
/design-apply --source={theme} --platform=web --target=mockup/web-html
/design-apply --source={theme} --platform=mobile --target=mockup/mobile-html
/design-apply --source={theme} --platform=web --target=apps/web
/design-apply --source={theme} --platform=web --target=apps/web --skip-ui
```

Follow the full execution logic in `.claude/commands/design-apply.md`.
