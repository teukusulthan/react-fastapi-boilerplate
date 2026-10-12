# /html-ui-slicing

Static HTML from the design system: **mockup packages** (`mockup/`) or **workspace spec PoC** (single file under `<cwd>/design/`).

Choose Mode A vs Mode B (Step 0 below). Note: the `html-ui-slicing` skill body (`SKILL.md`) is **not
bundled** in this repo — only [`references/workspace-spec-poc.md`](../skills/html-ui-slicing/references/workspace-spec-poc.md)
exists. For Mode A (mockup pages) use the [`html-ui-styling`](../skills/html-ui-styling/SKILL.md) skill
(+ `design-apply` for CSS assets).

> Use this **only** when the user explicitly asks for an HTML mockup / static HTML. "Build a UI/page/screen"
> in this repo means the React app in `apps/web` → `/generate-ui` + `reactjs-ui-design`. Without a
> `design/` theme, mockups follow the same modern-minimal, slightly rounded look as
> `.claude/rules/web/ui-design.md`.

## Usage

```
/html-ui-slicing
/html-ui-slicing slice dashboard ke mockup web-html
/html-ui-slicing Mode B: HTML satu file dari spec di <cwd>/sprint
```

## Action

1. **Step 0** — pick the mode:
   - **Mode A** — mockup under `mockup/{web|mobile}-html/` via `html-ui-styling`: copy `css/`, Tailwind v4 browser CDN, `data-ui` rules.
   - **Mode B** — read `.claude/skills/html-ui-slicing/references/workspace-spec-poc.md` in full; spec/brief → one inlined HTML under `<cwd>/design/{slug}.html`, mock data only.

For Mode B, design references are **only** `<cwd>/design/**/{DESIGN.md,tailwind.css,variable.css}` (or `varaible.css`) — do not use `design-token.json` as a visual source.

## Next step

After HTML is ready, continue with `/bootstrap-project` or `/sprint-builder` as needed, or port into `apps/web*` per web stack rules.
