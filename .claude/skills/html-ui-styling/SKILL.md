---
name: html-ui-styling
description: Static HTML mockup skill — generates standalone HTML mockup pages (Tailwind CDN + design tokens) under mockup/{web,mobile}-html/. Use ONLY when the user explicitly asks for an HTML mockup / static HTML ("buat desain html", "design html web", "design html mobile", "html mockup", "slice this to html") or the repo has no React app target. In a repo with apps/web, "build ui", "buatkan ui", "buat halaman", "design this screen" mean the React app — use reactjs-ui-design instead. "design html web" → output to mockup/web-html/. "design html mobile" → output to mockup/mobile-html/.
---

# HTML Mockup Skill

---

## 0 — Constraints (read before anything else)

⛔ **HTML mockups only.** This skill writes static `.html` files under `mockup/`. If the repo has `apps/web` and the
user did not explicitly say "HTML"/"mockup", the request is React UI work → load
`.claude/skills/reactjs-ui-design/SKILL.md` (and `.claude/rules/web/ui-design.md`) instead and stop here.

🎨 **Default look = the app UI spec.** When no `design/` theme exists (or it does not say otherwise), mockups follow the
same modern, minimal, slightly rounded direction as the React app: `.claude/rules/web/ui-design.md` and
`.claude/skills/reactjs-ui-design/SKILL.md` §1–§2, §5–§7 (neutral-first surfaces with one accent; `rounded-md` controls,
`rounded-xl` surfaces; 1px quiet borders + `shadow-xs`, real shadows only on floating layers; one title + one primary
action per screen; designed loading/empty/error states). A selected `design/` theme may override radius/shadow/palette
only where its DESIGN.md explicitly says so (e.g. a square-cornered command-center theme chosen by the brief).

⛔ **Never read or explore files inside `mockup/`** unless the user explicitly points to a specific file. They are output artifacts, not inputs.

⛔ **Never read `tailwind.css`, `variable.css`, or `variable_dark.css`** inside `design/`. These are generated artifacts. The only allowed design reference is `DESIGN.md`.

---

## 1 — Initialize Todo Checklist

At the very start of every slicing task, call `TodoWrite` to register all steps. Mark each item `in_progress` when you begin it, and `completed` immediately when done — never batch updates.

```
TodoWrite([
  { id: "read-design-system",  content: "Read design/design-system.md + DESIGN.md", status: "pending" },
  { id: "load-references",     content: "Load required reference files",             status: "pending" },
  { id: "detect-mode",         content: "Detect slicing mode (single / multi / modular) — announce selected mode", status: "pending" },
  { id: "scaffold",            content: "Confirm output path & scaffold structure",  status: "pending" },
  { id: "write-page",          content: "Write HTML page(s)",                        status: "pending" },
  { id: "finishing",           content: "Finishing {filename}.html",                 status: "pending" },
])
```

For multi-page tasks add one extra todo per page: `{ id: "page-{name}", content: "Write {name}.html", status: "pending" }`.

---

## 2 — Read the Design System

> Skip this step if `design/design-system.md` and `DESIGN.md` have already been read in the current session — the token context is already in the conversation window.

> **No `design/` folder?** Do not invent a theme. Either run `design-system-builder` first (it defaults to the
> modern-minimal spec), or reuse the app tokens: `design-apply` / copy `apps/web/src/styles/variable.css` +
> `tailwind.css` into `mockup/{stack}-html/css/`. Visual rules then come from `.claude/rules/web/ui-design.md`.

If not yet loaded:

**Call 1 — resolve active platform & theme:**
```
Read("design/design-system.md")
```
Extract `platform` and `theme`. Override with task context if an explicit stack is mentioned. Use the **Platform Reference Map** table for exact paths — never hardcode.

**Call 2 — load design tokens (parallel with call 1 if possible):**
```
Read("design/{platform}/{theme}/DESIGN.md")
```

> ⛔ Both reads are BLOCKING — do not proceed until complete.

**Confirm aloud after reading:**
- Announce design system: e.g. `"Design system: web / {theme}"` (or `"Design system: app default (ui-design.md)"`)
- Default mode (`dark` or `light`) from the `**Theme:**` field in DESIGN.md
- Typography font family
- At least 3 semantic color token examples

**Load additional references based on what the task needs:**

| Condition | Read |
|---|---|
| Always | `references/coding-rules.md` |
| New page | + `references/template-shell.md` |
| Adding components | + `references/data-ui-mapping.md` |
| Charts present | + `references/echarts.md` |
| Scroll containers | + `references/scrollbar.md` |
| Map present | + `references/mapbox.md` |
| Component modular mode | + `references/component-modular.md` |

---

## 3 — Detect Slicing Mode

| Mode | Trigger keywords | Output strategy |
|------|-----------------|-----------------|
| **Single page** | "buat halaman", "slice this", "buatkan UI" (1 page) | One self-contained `.html` file |
| **Multi-page** | "multi page", "beberapa halaman", "buat 3 halaman", explicit list of pages | One `.html` file per page, shared CSS |
| **Component modular** | "component", "modular", "pakai loader", "pisahkan komponen" | Separate component files + `js/loader.js` |

If ambiguous, **default to Single page**.

**After detecting mode, announce it aloud:** e.g. `"Slicing mode: Single page"` / `"Slicing mode: Multi-page"` / `"Slicing mode: Component modular"`.

---

## 4 — Scaffold Output Location

**All HTML output MUST be saved under `mockup/{stack}-html/` — never anywhere else.**

```
mockup/{stack}-html/{stack}-{page_name}.html
```

- `{stack}` = `web` or `mobile`. Default to `web` if not specified.
- Multiple pages → one file per page, same folder.

```
❌ dashboard.html                             → WRONG (project root)
❌ design/web/financial-metrics.html          → WRONG (old path)
✅ mockup/web-html/web-financial-metrics.html
✅ mockup/mobile-html/mobile-dashboard.html
```

For **Component modular** mode, see `references/component-modular.md` for loader and shadow DOM conventions.

---

## 5 — Write the Page

For new pages: use the shell from `references/template-shell.md`.

For fixes / additions: edit the existing file directly.

> ⛔ **FINISHING** — Before saving, verify `<head>` contains both:
> ```html
> <link rel="stylesheet" href="css/variable.css" />
> <link rel="stylesheet" href="css/styles.css" />
> ```
> If `styles.css` is missing, add it immediately after `variable.css`.

Follow all rules in:
- `references/coding-rules.md` — Tailwind, visual direction, typography, icons, charts, scrollbars, maps
- `references/data-ui-mapping.md` — every structural element needs `data-ui`

---

## Special — DESIGN.md Generation

When asked to generate or update a `DESIGN.md`:
- Re-read active design system files (Step 1).
- Write a concise summary: active theme, semantic color palette, typography scale, layout contract, component quick-reference.
- Do NOT copy full token tables — summarize only tokens that components actually use.
- Output path: `{project}/DESIGN.md`.

---

## References

- `references/template-shell.md` — HTML boilerplate, dark/light toggle, download button
- `references/coding-rules.md` — Tailwind, visual direction, typography, icons, charts, scrollbars, maps
- `references/data-ui-mapping.md` — `data-ui` → shadcn mapping + extra `data-*` props
- `.claude/rules/web/ui-design.md` + `.claude/skills/reactjs-ui-design/SKILL.md` — default visual direction
- `references/component-modular.md` — Component Modular mode: loader.js, shadow DOM, naming
- `references/echarts.md` — ECharts config patterns, theming with CSS variables
- `references/mapbox.md` — Mapbox GL JS setup, marker system, panel overlay pattern
- `references/scrollbar.md` — Perfect Scrollbar CDN, init pattern, theme-aware CSS overrides
- [Tailwind CSS v4 Docs](https://tailwindcss.com/docs)
