---
name: reactjs-slicing-ui
description: Workflow for translating a Figma design, screenshot or HTML mockup into React components in apps/web — mapping each block to shadcn primitives, components/common patterns and modules/data-table, mapping colors/sizes to semantic tokens (token-chain discipline, gap resolution), placing files in the right folder (components/ui, components/common, components/layouts, components/wrappers, modules, features, pages), and resolving token/composition conflicts. Look & feel, component priority and the screenshot review loop come from reactjs-ui-design (load it first).
---

## Skill: Slicing UI (Figma / mockup → React)

> **Visual rules:** [`reactjs-ui-design`](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns the **translation workflow**: block → component mapping,
> value → token mapping, token-gap resolution, file placement and conflict resolution.

### Overview

Slicing UI means converting a design source (Figma frame, screenshot, HTML mockup from `mockup/`) into
React + Tailwind code in `apps/web` that:

1. is built from **shadcn primitives + `components/common` patterns + `modules/data-table`** (playbook §3–§4),
2. uses **only semantic token classes** (playbook §2), and
3. passes the **screenshot review loop** (`npm run ui:snapshot`, playbook §8).

A design source is the *content and layout intent*, not a pixel spec to copy literally: when a mockup's
radius, shadow, color or spacing disagrees with the playbook, the playbook wins (map to the nearest
token), unless the project has a `design/` theme that explicitly specifies otherwise — and then that
theme is imported into the variables, not into components (see `reactjs-design-system`).

### Token chain

```
(optional) design/[platform]/[theme]/DESIGN.md   ← only if a design/ theme exists; imported into ↓
    ↓
apps/web/src/styles/variable.css                 ← :root + .dark semantic variables (--primary, --card, --border, --radius …)
    ↓
apps/web/src/styles/tailwind.css                 ← Tailwind v4 @theme inline mapping (--color-*, --radius-*, --shadow-*)
    ↓
Semantic utility classes                         ← bg-card, text-muted-foreground, border-border, bg-primary, rounded-xl …
    ↓
React component JSX                              ← className="…" (via primitives' variants first)
```

Every visual value in a component must trace back to a semantic token. Raw hex/rgb, Tailwind palette
colors (`blue-500`) and arbitrary values (`text-[13px]`, `rounded-[14px]`) are never acceptable — if no
token covers a case, resolve the gap in the styles (Step 1b), not in the component.

### Folder hierarchy (current architecture)

| Level | Folder | Examples |
|---|---|---|
| UI primitives (shadcn, themed) | `src/components/ui/` | `button`, `input`, `select`, `dialog`, `dropdown-menu`, `table`, `card`, `badge`, `tooltip`, `sidebar` |
| Generic page patterns | `src/components/common/` | `PageHeader`, `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`, `ConfirmDialog`, `LoadingState`, `ErrorFallback` |
| App shell | `src/components/layouts/` | `AppLayout`, `AppHeader`, `AppSidebar`, `AuthLayout` |
| 3rd-party adapters | `src/components/wrappers/` | `PerfectScrollArea`, `AppProviders`, chart/map wrappers |
| Generic reusable modules (2+ features) | `src/modules/<name>/` | `data-table/` (`DataTable`, `DataTableToolbar`, `DataTablePagination`, …) |
| Domain UI | `src/features/<domain>/<feature>/components/` | `UserListView`, `ProjectStatsRow` |
| Single-page parts | `src/pages/<page>/parts/` | rarely needed; prefer features |
| Route files (thin) | `src/pages/<area>/<Name>Page.tsx` | default export rendering a feature view |

**Import direction (one-way):** `pages → features → modules → components/common → components/ui`
(`components/layouts` and `components/wrappers` may be used by any level above `ui`). Never place
domain components in `src/components/` (see `.claude/rules/architecture.md`).

---

### When to Use

| Situation | Action |
|---|---|
| Implementing a screen from Figma / screenshot / mockup | Step 0 → Step 8 below, then the playbook review loop |
| Building UI with no design source | Use `reactjs-ui-design` recipes directly; this skill only for placement/token questions |
| A color/spacing in the design has no token | Map to the nearest semantic token; if truly missing, Step 1b |
| A shadcn primitive is needed but not installed | Install it (Step 1c) + post-install checklist (playbook §3) |
| A primitive renders with wrong color/radius | Fix token wiring or the primitive's variants (Step 1d) — not the call site |
| Choosing where to place a new component | Folder table above |
| Dark mode | Never fork styles — rely on `.dark {}` in `variable.css` |

---

### How to Use

#### Step 0 — Build a block map (CRITICAL)

Before writing JSX, split the design into blocks and map each one to an existing building block:

| Design block | Map to |
|---|---|
| Page title / subtitle / top-right buttons | `PageHeader` (`title`, `description`, `actions`) |
| KPI / metric tiles | `StatCard` in `grid gap-4 sm:grid-cols-2 xl:grid-cols-4` |
| Any table or list with columns | `DataTable` (`src/modules/data-table/`) — it is the card itself: `toolbar={<DataTableToolbar … />}`, built-in pagination footer |
| Titled panel / settings group | `SectionCard` (or `Card` + `CardHeader`/`CardContent`) |
| Status pill / chip | `StatusBadge` (tone) or `Badge` (variant) |
| Dropdown, select, date picker, tabs, dialog, drawer, tooltip, toast | the shadcn primitive (`DropdownMenu`, `Select`, `Popover`+`Calendar`, `Tabs`, `Dialog`, `Sheet`, `Tooltip`, `sonner`) |
| Delete / destructive confirm | `ConfirmDialog` |
| "No data" area | `EmptyState` |
| Chart | ECharts via `EChartWrapper` (`reactjs-chart`) inside a `Card` |

Only blocks that map to nothing get new markup — and if they are generic, they become a new
`components/common/` pattern (with an entry on `/ui-kit`), not an inline one-off.

#### Step 1 — Map design values to semantic tokens

Read `src/styles/variable.css` + `src/styles/tailwind.css` (and, *if a `design/` theme exists*, its
`DESIGN.md`). Then map what you see:

| Design value | Class |
|---|---|
| Page canvas | `bg-background` |
| Card / panel / dialog surface | `bg-card text-card-foreground` (via `Card`/`Dialog`) |
| Subtle fill, hover row, skeleton | `bg-muted`, `bg-muted/50`, `bg-accent` |
| Main text / secondary text | `text-foreground` / `text-muted-foreground` |
| Border / input border / focus | `border-border` / `border-input` / `ring-ring` |
| Brand fill | `bg-primary text-primary-foreground` (use `<Button>`) |
| Error / success / warning / info | `destructive` variants; tints `bg-success/10 text-success`, `bg-warning/10 text-warning`, `bg-info/10 text-info` |
| Chart series | `chart-1` … `chart-5` |
| 12/14/16/24px text | `text-xs` / `text-sm` / `text-base` / `text-2xl` (titles `font-semibold tracking-tight`) |
| 4/8/16/24/32px spacing | `1` / `2` / `4` / `6` / `8` on the spacing scale |
| Control corners (≈6–8px) | `rounded-md` |
| Surface corners (≈10–16px) | `rounded-xl` |
| Square corners / 0 radius in the mockup | still `rounded-md` / `rounded-xl` — unless a selected `design/` theme mandates square |
| Big soft/colored shadows | `shadow-xs` on resting surfaces; `shadow-md/lg` only on floating layers |

Never invent class names. If a class you want isn't defined, it's a gap (Step 1b).

#### Step 1b — Token gap resolution

If you truly need a token that doesn't exist (rare — check `muted`, `accent`, status first):

1. Add it to `src/styles/variable.css` in **both** `:root` and `.dark`:

```css
:root { --your-new-token: var(--base-neutral-200); }
.dark { --your-new-token: var(--base-neutral-700); }
```

2. Alias it in `src/styles/tailwind.css` `@theme inline`: `--color-your-new-token: var(--your-new-token);`
3. Use it via the Tailwind class only — never `var()` in JSX.

Additive only — never remove or rename existing variables. Verify the name really exists in the served
CSS (silent `var()` failure — see `reactjs-design-system` § *Token-name reality*).

#### Step 1c — shadcn primitive strategy

Follow the playbook's component priority (§3):

```
Does src/components/ui/<name>.tsx exist?
├─ YES → use it with its variants/props; extend via a new cva variant if truly needed
└─ NO  → Does shadcn have it? (https://ui.shadcn.com/docs/components)
          ├─ YES → cd apps/web && npx shadcn@latest add <name>
          │        then the post-install checklist (playbook §3): lucide → Phosphor,
          │        React.forwardRef for React 18, semantic tokens + radius/shadow, @/utils/cn
          └─ NO  → compose from existing primitives; generic → components/common/
```

- Never hand-build: dropdown, select, combobox, dialog, alert dialog, sheet, popover, tooltip, tabs,
  accordion, checkbox, radio, switch, toggle group, date picker, command palette, toast.
- Never use native `<select>`, `<input type="checkbox">`, `alert()`, `confirm()`.
- Run the CLI inside `apps/web`, never at repo root. Never leave `lucide-react` imports (see `reactjs-icon`).
- Preserve behavior props: `asChild`, refs, `aria-*`, `data-*`, controlled values, focus rings, portals.

#### Step 1d — Editing primitive variants

You may edit `src/components/ui/*.tsx` `cva` variants/base classes so a primitive matches the playbook
(e.g. it renders square, uses a raw color, lacks the focus ring). Rules:

- Change presentation only; keep Radix behavior, refs, `asChild`, `data-*`, a11y.
- Edit in place; don't fork primitives into duplicates.
- One fix in the base string fixes every usage — that is the point. Never patch the same look at call sites.
- After a `design/` theme switch, layout constants (e.g. `SIDEBAR_WIDTH` in `sidebar.tsx`) may need to
  match that theme.

---

#### Step 2 — UI primitives (`components/ui/`)

Primitives map to one shadcn/Radix primitive, are named in kebab-case as the CLI creates them
(`button.tsx`, `dropdown-menu.tsx`), use named exports, forward `className` via `cn()` (last), use
`React.forwardRef` for DOM-rendering parts, and contain no business logic, API calls or domain imports.
Do not import from `components/common/`, `modules/` or `features/`.

#### Step 3 — Common patterns (`components/common/`)

Domain-agnostic page patterns composed from primitives (`PageHeader`, `StatCard`, `EmptyState`,
`SectionCard`, `StatusBadge`, `ConfirmDialog`, …). Check them before writing layout markup; add a new one
only when a pattern is generic, and add it to the `/ui-kit` page. Each pattern's props are the exported
`…Props` interface in its file (summary table: `reactjs-ui-design` §4).

```tsx
// usage — never re-implement these inline
<PageHeader
  title="Products"
  description="Manage your product catalogue."
  actions={<Button><i className="ph ph-plus" aria-hidden="true" />Add product</Button>}
/>
<StatusBadge tone="warning">Low stock</StatusBadge>
```

#### Step 4 — Domain components (`features/<domain>/<feature>/components/`)

Feature components compose primitives, common patterns and modules, and get data from the feature's
TanStack Query hooks (never fetch in components). Example of a sliced card:

```tsx
// src/features/catalog/product/components/ProductCard.tsx
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { StatusBadge } from '@/components/common/StatusBadge'
import { cn } from '@/utils/cn'
import type { ProductCardProps } from '../types/product.types'
import { formatPrice } from '../utils/format-price'

export function ProductCard({ name, price, stock, imageUrl, onAddToCart, className }: ProductCardProps) {
  const isOutOfStock = stock === 0
  return (
    <Card className={cn('overflow-hidden', className)}>
      <img src={imageUrl} alt={name} className="aspect-square w-full object-cover" />
      <CardContent className="flex flex-col gap-1 p-4">
        <p className="line-clamp-2 text-sm font-medium text-foreground">{name}</p>
        <p className="text-base font-semibold tabular-nums">{formatPrice(price)}</p>
        {stock > 0 && stock <= 5 && <StatusBadge tone="warning">Only {stock} left</StatusBadge>}
        {isOutOfStock && <StatusBadge tone="destructive">Out of stock</StatusBadge>}
      </CardContent>
      <CardFooter className="p-4 pt-0">
        <Button className="w-full" disabled={isOutOfStock} onClick={onAddToCart}>Add to cart</Button>
      </CardFooter>
    </Card>
  )
}
```

Generic code reused by 2+ features goes to `src/modules/<name>/` (`reactjs-modules`); lists always use
`src/modules/data-table/`.

#### Step 5 — Layout shell

Do **not** create new shells for a slice. Pages render inside the existing `AppLayout` (header +
config-driven `AppSidebar` + main in `PerfectScrollArea`), which owns page padding. If the design shows a
different shell, change `src/components/layouts/*` per `reactjs-app-layout` and keep the non-overlap
contract in `.claude/rules/architecture.md`. Every bounded scroll region uses **`PerfectScrollArea`**
(`reactjs-responsive` § *Scrollable regions*).

#### Step 6 — Page

Pages are thin route files that render a feature view; the view starts with `PageHeader`:

```tsx
// src/pages/catalog/ProductListPage.tsx
import { ProductListView } from '@/features/catalog/product'
export default function ProductListPage() { return <ProductListView /> }

// src/features/catalog/product/components/ProductListView.tsx
export function ProductListView() {
  const { data, isPending, isError, refetch } = useProductList()
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Products" description="Manage your product catalogue." actions={/* primary action */} />
      {/* loading → skeleton grid · error → Alert + Retry · empty → EmptyState · data → grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">{/* ProductCard … */}</div>
    </div>
  )
}
```

Add the route **and** the menu entry (`src/config/menu/*`) in the same change.

#### Step 7 — Token conflict resolution

Replace any divergent value with its semantic token:

```tsx
// ❌
className="bg-[#0d5eba] p-[18px] text-[15px] rounded-[8px] text-gray-500 border-gray-200"
style={{ color: '#5b5d63' }}

// ✅
className="bg-primary p-4 text-sm rounded-md text-muted-foreground border-border"
```

| What you found | Replace with |
|---|---|
| Brand hex | `bg-primary` / `text-primary` (via `<Button>` where it's an action) |
| Page/surface/hover greys | `bg-background` / `bg-card` / `bg-muted` |
| Text greys | `text-foreground` / `text-muted-foreground` |
| Border greys | `border-border` / `border-input` |
| Red / green / amber / blue status | `destructive` / `success` / `warning` / `info` (tinted `/10` for badges, alerts) |
| `text-[12px]`/`[14px]`/`[16px]` | `text-xs` / `text-sm` / `text-base` |
| `p-[16px]`, `gap-[8px]`, `gap-[24px]` | `p-4`, `gap-2`, `gap-6` |
| `rounded-[4–8px]` on controls | `rounded-md` |
| `rounded-[10–16px]` on surfaces | `rounded-xl` |
| Legacy aliases (`bg-background-primary`, `text-font-*`, `border-border-primary`) | shadcn semantic class |

#### Step 8 — Composition conflict resolution (CRITICAL)

Composition conflict = valid tokens, wrong structure. Common examples: cards inside cards; a table
without the card wrapper/toolbar/pagination; a page without `PageHeader`; borders around every element;
a hand-built dropdown; a status rendered as colored text instead of `StatusBadge`; no loading/empty/error
state. Resolve by re-mapping the block to the building block from Step 0 and the matching playbook
recipe (§5). Keep shadcn behavior untouched.

Do not mark slicing complete until composition conflicts are resolved **and** the playbook review loop
has been run:

```bash
cd apps/web && npm run ui:snapshot -- --route <path>   # then open every PNG and run the playbook §8 checklist
```

---

## Styling workflow

```
Need to style something?
  ├─ Is there a primitive / common pattern / variant for it? ── YES → use it (no extra classes)
  ├─ Can Tailwind semantic classes handle it? ───────────────── YES → className via cn()
  ├─ Complex/dynamic CSS-only (keyframes, clip-path, mask)? ─── YES → styled-components (rare)
  └─ Inline style for visuals? ───────────────────────────────── NEVER
```

- Conditional classes always via `cn()` from `@/utils/cn` — never template-literal concatenation.
- Responsive: mobile-first (`grid-cols-1 md:grid-cols-2 xl:grid-cols-4`); verify 390 / 768 / 1440px.
- Dark mode: tokens switch automatically through `.dark {}` in `variable.css`; don't add per-component
  `dark:` overrides that the tokens already handle.

```tsx
<div className="rounded-xl border bg-card text-card-foreground shadow-xs">…</div>
<p className="text-sm text-muted-foreground">…</p>
```

### styled-components (rare)

`styled-components` is installed but not wired. Use it **only** when Tailwind cannot express the style
(custom `@keyframes`, `clip-path`/`mask`/`filter` with dynamic values, dynamic pseudo-element content,
third-party overrides needing specificity), and only with CSS variables (`var(--border)`), never raw
colors. Place it co-located (`ComponentName.styles.ts`). Charts always render through `EChartWrapper`
(`reactjs-chart`) — no Recharts/Chart.js/ApexCharts/Nivo/custom SVG chart stacks.

---

## shadcn Button

Use the variants (`default`, `secondary`, `outline`, `ghost`, `destructive`, `link`) and sizes defined in
`src/components/ui/button.tsx` (check the file for the current list; typically `sm`, `default`, `lg`,
`icon`). One primary (`default`) button per view; secondary actions `outline`/`ghost`; icon-only buttons
use `size="icon"` + `aria-label` + `Tooltip`.

> Pre-execution validator, full rules and verification checklist: [references/slicing-ui-rules.md](references/slicing-ui-rules.md)

> Quality gate: run **`reactjs-anti-slop`** alongside this skill, and the **`reactjs-ui-design`** review
> loop (§8) before marking any slice complete.

---

## Appendix — Projects with a `design/` theme

Only if `design/design-system.md` exists: resolve the active `design/[platform]/[theme]/DESIGN.md`,
import its palette/font/radius into the semantic variables per `reactjs-design-system` Step 4, and keep
slicing with the semantic classes above. Theme-specific class names from a `DESIGN.md` (e.g.
`bg-background-secondary`, `text-font-*`) are legacy aliases — prefer the shadcn semantic equivalents in
new code. A theme that mandates square corners or no shadows changes the variables, never the
component code.
