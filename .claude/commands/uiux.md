# /uiux

Establish the project's design tokens under `<cwd>/design/`. Reads the brief at `<cwd>/brief/` and resolves the active design system from `<cwd>/design/design-system.md`.

Trigger the [`uiux`](../skills/uiux/SKILL.md) skill.

> This command is about **tokens / re-branding** (optional). To *build or restyle* UI in `apps/web`, use
> `/generate-ui` and the [`reactjs-ui-design`](../skills/reactjs-ui-design/SKILL.md) playbook. Without a
> `design/` theme, the default look in `.claude/rules/web/ui-design.md` applies, and any theme you create
> keeps its radius/shadow rules (8px controls, 12px surfaces, quiet shadows) unless the brief says
> otherwise.

## Usage

```
/uiux
/uiux use tactical theme, prioritise situational dashboard
/uiux extract from Figma https://figma.com/...
```

## Pre-condition

`<cwd>/brief/00_OVERVIEW.md` exists. If not, redirect the user to `/brief-builder` first.

## Action

Open `.claude/skills/uiux/SKILL.md` and follow the resolution process:

1. Read `<cwd>/design/design-system.md` → resolve active `platform` + `theme`
2. Load 3 files from `<cwd>/design/{platform}/{theme}/`:
   - `DESIGN.md` — visual guidelines + semantic token reference
   - `variable.css` — CSS custom properties (actual values)
   - `tailwind.css` — Tailwind v4 @theme mapping
3. If tokens do not exist → extract from Figma:
   - Theme name: derive from **Figma file/page title** → convert to **kebab-case**
   - Output directly to `<cwd>/design/{platform}/{theme}/` (3 files above)
   - Update `design-system.md` (Available Themes + Active Config)
4. Apply tokens to project (`apps/web/src/styles/`) by mapping them onto the shadcn semantic variables (`--background`, `--card`, `--primary`, `--muted-foreground`, `--border`, `--ring`, `--radius`, `--chart-*`) — see `/switch-design-system`

> No JSON output — all tokens go directly to the 3 CSS/MD files in the theme folder.

## Next step

When design is satisfied, user invokes `/bootstrap-project`.
