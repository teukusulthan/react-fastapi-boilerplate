# /design-system-setup

Copy design token CSS and generate `loader.js` into a mockup output folder (`mockup/{web,mobile}-html/css/`).

Trigger the [`design-system-setup`](../skills/design-system-setup/SKILL.md) skill.

## Usage

```
/design-system-setup
/design-system-setup init mockup web-html
```

## Action

1. Open `.claude/skills/design-system-setup/SKILL.md`.
2. Read `design/design-system.md` → resolve `platform` + `theme`.
3. Copy `variable.css` (+ merge `variable_dark.css` when present) and `tailwind.css` into `mockup/{platform}-html/css/` only if files do not already exist.
4. Generate `styles.css` and `js/loader.js` per the skill.

Usually invoked automatically by **html-ui-slicing** when scaffolding a new page; run standalone when the mockup folder is missing CSS assets.
