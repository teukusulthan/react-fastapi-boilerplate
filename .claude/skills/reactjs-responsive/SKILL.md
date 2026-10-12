---
name: reactjs-responsive
description: Responsive layout rules for apps/web — mobile-first Tailwind v4 breakpoints, page/feature layout patterns inside the AppLayout shell, the sidebar's mobile sheet (useIsMobile in src/hooks/use-mobile.ts), responsive tables/forms/dialogs, and the mandatory PerfectScrollArea (src/components/wrappers/PerfectScrollArea.tsx, react-perfect-scrollbar themed in src/styles/components.css) for every bounded scroll region. Load when building any screen or fixing layout/scroll issues.
---

# Responsive Layouts (React / TypeScript)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns breakpoints, responsive patterns and scroll regions.

## What the shell already gives you

`AppLayout` (`src/components/layouts/AppLayout.tsx`) renders pages inside (abridged — read the file
for the current classes):

```tsx
<SidebarInset id="main-content" tabIndex={-1} className="min-h-0 outline-none">  {/* <main>; rounded inset panel on md+ */}
  <PerfectScrollArea className="h-full" contentClassName="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
    <Outlet />
  </PerfectScrollArea>
</SidebarInset>
```

So a page/feature view:

- already has outer padding (`px-4 py-6 sm:px-6 lg:px-8 lg:py-8`) and a max width (`max-w-7xl`) — don't add another page-level padding wrapper or another full-page scroller;
- scrolls with the main column — only add an inner `PerfectScrollArea` for a genuinely bounded sub-panel (fixed-height feed, side panel);
- for a full-bleed view (map, canvas) that must fill the viewport height, give the view
  its own bounded height (viewport − `h-12` header − the inset panel's `mb-2` − the main column's vertical padding)
  or restructure with a dedicated layout route; see `.claude/skills/reactjs-map/SKILL.md`.

The sidebar is responsive by itself: below 768px (`useIsMobile()` in
`src/hooks/use-mobile.ts`) it renders as an off-canvas `Sheet` opened by the header's
`SidebarTrigger`; on desktop it collapses to icons (`collapsible="icon"`).

## Step 1 — Pick the pattern

| Feature type | Pattern |
|---|---|
| List / table | `PageHeader` + `DataTable` (`@/modules/data-table`) in one card; toolbar wraps on mobile; table scrolls horizontally inside its card |
| Form | 1 column → `sm:grid-cols-2`, `max-w-2xl` (see `.claude/skills/reactjs-form/SKILL.md`) |
| Dashboard | `StatCard` row `grid gap-4 sm:grid-cols-2 xl:grid-cols-4` → `grid gap-6 xl:grid-cols-3` (chart `xl:col-span-2` + list) |
| Detail page | `PageHeader` + `Tabs` + `SectionCard`s, content constrained (`max-w-3xl`/`max-w-5xl`) |
| Auth/public card | Centered by `AuthLayout`; card `w-full max-w-sm` |

## Step 2 — Mobile-first classes

```tsx
<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">            {/* grid */}
<div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"> {/* header row */}
<div className="hidden md:block">…</div>  <div className="md:hidden">…</div>        {/* show/hide */}
<h1 className="text-2xl font-semibold tracking-tight">Title</h1>                    {/* use PageHeader */}
```

Typography and color: Tailwind's default type scale (`text-sm` body, `text-2xl` page title,
`text-base` section title, `text-xs` captions) and the shadcn semantic classes (`text-foreground`,
`text-muted-foreground`, `bg-background`, `bg-card`, `bg-muted`, `border-border`) — see
`reactjs-ui-design` §2. Legacy `text-h*`/`text-body-*`, `text-font-*`, `bg-background-primary` and
`border-border-primary` utilities still resolve but are not used in new code.

## Step 3 — Tables on small screens

`src/components/ui/table.tsx` already wraps `<table>` in a horizontal-overflow container —
wide tables scroll sideways on phones. For dense data either hide low-priority columns
(`className: 'hidden md:table-cell'` in the column meta/cell) or render a card list below
`md` and the table from `md` up. Keep the `DataTablePagination` footer usable at 390px.

## Step 4 — Dialogs and sheets

```tsx
<DialogContent className="flex max-h-[85svh] w-full max-w-md flex-col overflow-hidden">
  <DialogHeader>…</DialogHeader>
  <PerfectScrollArea className="min-h-0 flex-1" contentClassName="flex flex-col gap-4 py-2">…body…</PerfectScrollArea>
  <DialogFooter>…</DialogFooter>
</DialogContent>
```

Header/footer stay pinned; only the body scrolls.

## Scrollable regions — `PerfectScrollArea` (mandatory)

Every bounded in-app scroll region (main column, sidebar body, drawer/sheet/dialog body,
panels, feeds, fixed-height lists) uses the wrapper — not raw `overflow-auto` or
`scrollbar-thin`.

```tsx
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'

<div className="relative flex min-h-0 flex-1 flex-col">              {/* bounded parent */}
  <PerfectScrollArea className="h-full" contentClassName="flex flex-col gap-2 p-3">
    {items.map((item) => <FeedItem key={item.id} item={item} />)}
  </PerfectScrollArea>
</div>
```

Wrapper facts (`src/components/wrappers/PerfectScrollArea.tsx`):

- Props: everything from `react-perfect-scrollbar`'s `ScrollBarProps` + `contentClassName`
  (classes for the inner content div — put padding/flex there, not on the scroller).
- Defaults `options.wheelPropagation = false`.
- A `ResizeObserver` on the content and its parent calls `updateScroll()` automatically —
  no manual refresh needed after sidebar toggles or data changes.
- Adds the `perfect-scroll-area` class (`position: relative; min-height: 0`).
- Library CSS is imported once in `src/index.css`; rail/thumb theming lives in
  `src/styles/components.css` (`.ps__rail-*`, `.ps__thumb-*`, token colors such as
  `--color-primary-base`). Never import the library CSS elsewhere.

Height chain: the scroller only scrolls when an ancestor has a finite height
(`h-full` under a bounded parent, `flex-1 min-h-0` in a flex column, or `absolute inset-0`
inside a `relative` bounded box). Without it, it silently grows and never scrolls.

Exceptions (native overflow OK): document/body scroll, native controls (`<textarea>`,
`<select>`), the horizontal table container in `components/ui/table.tsx`, third-party
embeds (map canvas, PDF viewer), and containers whose markup is injected by a third party.

## Rules

- MUST write mobile-first; every screen usable at 390px (and 375px) with no horizontal page scroll.
- MUST use Tailwind breakpoints (`sm` 640, `md` 768, `lg` 1024, `xl` 1280, `2xl` 1536); JS
  breakpoint checks only via `useIsMobile()`.
- MUST use `PerfectScrollArea` for bounded scroll regions; one scroll container per region
  (no nested scrollers fighting the main column).
- MUST keep `min-w-0` / `min-h-0` on flex children that contain scrollers, tables or charts.
- MUST keep touch targets ≥ 44px on mobile for primary actions (pick a `Button` size from
  `components/ui/button.tsx` that gives ≥ 44px, or add `h-11` on mobile only).
- MUST NOT hardcode pixel widths for layout containers, set `overflow: hidden` on `html/body`,
  or use `calc(100vh - …)` (use `svh` units as the shell does).
- MUST NOT use Radix `ScrollArea` for new regions.

## Test

`npm run ui:snapshot -- --route <path>` (desktop + mobile, light + dark — see `reactjs-ui-design` §8),
plus the browser device toolbar at 390px, 768px, 1440px when you need interaction:

- [ ] No horizontal page scroll at 390px; header actions wrap/stack
- [ ] Sidebar opens as a sheet on mobile and closes after navigation
- [ ] Tables scroll sideways or reflow; pagination usable
- [ ] Forms 1 column on mobile; submit reachable with the keyboard open
- [ ] Dialog bodies scroll with pinned header/footer
- [ ] Every bounded scroller is a `PerfectScrollArea` with a finite height chain
