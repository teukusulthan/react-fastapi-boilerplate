# Coding Rules

## Visual Direction (default)

Unless the active `design/` theme's DESIGN.md explicitly says otherwise, mockups use the same look as the React app —
see `.claude/rules/web/ui-design.md` and `.claude/skills/reactjs-ui-design/SKILL.md`:

- **Neutral first, one accent.** Surfaces `bg-background` / `bg-card` / `bg-muted`; text `text-foreground` /
  `text-muted-foreground`; `bg-primary text-primary-foreground` only for the primary action, active nav and focus.
  Status colors only for status (tinted: `bg-success/10 text-success`). Brand palettes 2–5 are for charts only.
- **Slightly rounded.** Controls (button, input, select, badge) `rounded-md`; surfaces (card, table wrapper, dialog,
  popover, sheet) `rounded-xl`; `rounded-full` only for avatars, status dots and switches. No square boxes, no pills.
- **Quiet depth.** 1px `border-border` + at most `shadow-xs` on resting surfaces; `shadow-md`/`shadow-lg` only on
  floating layers (dropdown, popover, dialog, toast). No glows, colored shadows, glassmorphism or gradient blobs.
- **Hierarchy.** One page title + one-line description + one primary action, top-left. No cards inside cards.
- **States.** Show loading (skeleton rows/cards), empty (icon tile + title + hint + action) and error (inline alert with
  retry) variants for every data surface the mockup represents.
- Hover = background shift (`hover:bg-muted/50`), focus = visible ring (`focus-visible:ring-[3px] ring-ring/50`).

## Tailwind Classes

- Use **only** semantic Tailwind classes from the token set — never raw hex, never default Tailwind palette (`bg-blue-500`, `text-gray-900`), never arbitrary values like `bg-[#fff]`.
- Prefer the **shadcn semantic classes** (`bg-background`, `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`, `border-border`, `border-input`, `ring-ring`, `bg-primary`, `text-primary-foreground`, `bg-destructive`) — they map 1:1 to the React app, so `html-to-react` needs no class translation. Legacy aliases (`bg-background-primary`, `text-font-*`, `border-border-primary`) still resolve but don't use them in new pages.
- Never use numeric scale classes (`primary-500`, `primary-300`) — only alias names defined in `@theme` (e.g. `primary-base`, `primary-soft`, `primary-bold`), and only where no semantic class fits (charts, data accents).
- Opacity modifiers on semantic tokens are fine for tints and hover (`bg-success/10`, `hover:bg-muted/50`).
- Token chain: `variable.css` base tokens → semantic tokens → `tailwind.css @theme` → Tailwind classes.
- Follow DESIGN.md component contracts (card, sidebar, table, form, button, panel) when a `design/` theme is active.

## Layout

- Dashboard shell: `h-12` (or `h-14`) topbar · `w-[220px]` sidebar · `p-6` main content. Shell regions never overlap.
- Page anatomy: header (title, description, actions) → optional toolbar/tabs → content surfaces, separated with `gap-6`.
- Forms: single column `max-w-2xl`, label above input, helper/error below, actions bottom-right.
- Responsive: flex/grid only, no fixed full-page widths. Stack to single column on mobile (check 390px).

## Typography

- Body text `text-sm` (14px); page title `text-2xl font-semibold tracking-tight`; section title `text-base font-semibold`; helper text `text-sm text-muted-foreground`; captions `text-xs`. Weights 400/500/600 only. Numbers `tabular-nums`.
- If the active DESIGN.md defines its own scale (`text-body-*`, `text-label-*`, `text-h1`…`text-h6`), use that scale consistently instead — never mix the two.
- No arbitrary sizes (`text-[13px]`), no ALL-CAPS paragraphs, sentence case for labels and buttons.
- Sensor/coordinate values: `font-mono tabular-nums`.

## Icons

> ⛔ **MANDATORY**: All icons MUST use Phosphor Icons — no other library permitted.

- Always: `<i class="ph ph-{icon-name}"></i>`
- Script required on every page: `<script src="https://unpkg.com/@phosphor-icons/web"></script>`
- Size: `text-base` (16px) in controls and table rows · `text-xl` (20px) in page headers / empty-state tiles.
- Color: `text-muted-foreground` (default) · `text-primary` (active) · `opacity-50` on disabled controls.
- Icon-only buttons need `aria-label` + a tooltip.
- Weight variants when needed: `<i class="ph-bold ph-{icon-name}"></i>`

## Charts (ECharts)

> ⛔ **MANDATORY**: Any chart feature MUST use ECharts — no placeholders, no CSS fakes, no other library.

- Uncomment ECharts CDN whenever any chart is needed.
- Read `references/echarts.md` before writing any chart config — do NOT invent from memory.
- Initialize inside `DOMContentLoaded` using `getComputedStyle` to read CSS variable colors — never hardcode hex.
- Always add `window.addEventListener('resize', () => chart.resize())` per chart instance.
- Do NOT use ECharts on metric cards, status panels, or tables.
- **Always use `containLabel: true`** in `grid` config — `containLabel: false` causes axis labels to render outside the container and overflow the page.
- **Scatter / bubble charts**: always set `xAxis.max` slightly above the largest data value (e.g. `max: dataMax + 10`), add `clip: true` on series, and `overflow: hidden` on the chart div — bubble radius extends beyond the plot point and will overflow without these guards.
- **Multi-column grid with charts**: never use `%` columns alongside `gap` — use `fr` units (`3fr 2fr` not `60% 40%`). Percentage columns + CSS gap = total > 100% → right overflow.

## Scrollbars (Perfect Scrollbar)

> ⛔ **MANDATORY**: Any styled scrollable container MUST use Perfect Scrollbar — no `:-webkit-scrollbar` hacks.

- Container requirements: `position: relative` + `overflow-hidden` + explicit height.
- Uncomment Perfect Scrollbar CDN (CSS + JS) when any scrollable container is present.
- Inject theme override CSS block (uses `var(--color-*)` tokens) inside inline `<style>`.
- Call `ps.update()` after any dynamic content change inside a PS container.
- See `references/scrollbar.md` for full setup.

## Maps (Mapbox)

- Include Mapbox GL JS **only** when the feature explicitly needs a geographic map.
- Always use the project Mapbox public token (see `references/mapbox.md`).
- Map container must have explicit height: e.g., `style="height: 480px"`.
- See `references/mapbox.md` for full integration pattern.
