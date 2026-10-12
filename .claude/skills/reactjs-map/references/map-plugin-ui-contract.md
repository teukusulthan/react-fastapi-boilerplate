# MapPlugin UI Contract — Slots, Overlays, and Styling

> This document is the **single source of truth** for all UI styling, layout, and theming decisions
> inside `src/modules/map-plugin/components/` (not present in the boilerplate yet — create it on demand).
> Read it before touching any slot or overlay component.
>
> **Visual rules:** [`reactjs-ui-design`](../../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win. This contract owns slot layout, z-index and map-specific overlay behavior. Panels use the shadcn
> semantic tokens (they follow light **and** dark mode); floating panels are `rounded-xl` surfaces with
> `shadow-md`; controls are shadcn primitives (`Button`, `Tabs`, `Checkbox`, `Popover`…).

---

## 1. Core Styling Rule — When to Use What

| What | Use | Never |
|---|---|---|
| Static structural layout (flex, overflow, position type, fixed dimensions) | Tailwind classes | `style={{}}` |
| Dynamic/computed values (state-dependent width, props-driven top/left, animated maxHeight) | `style={{}}` inline — **only those properties** | Full `style={{}}` objects |
| Design system colors, borders, backgrounds | shadcn semantic token classes (`bg-card`, `border-border`, `text-muted-foreground`, etc.) | Hardcoded hex, `rgba(...)`, raw CSS colors, legacy `bg-background-primary`/`text-font-*` in new code |
| Buttons **floating on the map** (layer toggle, side collapse strip) | `<Button size="icon" className="shadow-md">` (primary) or `variant="outline"` + `shadow-md` | Borderless, shadowless light buttons on light tiles |

**Pattern: mix className + minimal style**

```tsx
// ✅ CORRECT — structural in className, only dynamic value inline
<div
  className="h-full bg-card text-card-foreground border border-border rounded-xl flex flex-col overflow-hidden shrink-0 shadow-md"
  style={{ width: open ? panelWidth : 0, transition: 'width 0.28s cubic-bezier(0.4,0,0.2,1)' }}
/>

// ✅ CORRECT — animated height (dynamic) stays inline
<div
  className="overflow-hidden w-full"
  style={{ maxHeight: collapsed ? 0 : 800, transition: 'max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1)' }}
/>

// ❌ WRONG — all styles in style={{}}
<div style={{ overflow: 'hidden', width: '100%', background: 'var(--card)', border: '1px solid var(--border)' }} />

// ❌ WRONG — hardcoded color
<div style={{ background: '#fff', borderBottom: '1px solid #e6e9f0' }} />
```

---

## 2. Token Reference (semantic, light + dark)

All UI chrome (panels, tabs, headers, buttons, cards) uses the shadcn semantic tokens from
`src/styles/variable.css` / `tailwind.css` — never dark navy/glass-morphism, never raw hex. Because the
tokens are redefined under `.dark`, panels follow the app theme automatically.

| Purpose | Tailwind class | CSS var (for `style`/props only) |
|---|---|---|
| Panel / card surface | `bg-card text-card-foreground` | `var(--color-card)` |
| Muted / secondary surface (tab bar, skeleton) | `bg-muted` | `var(--color-muted)` |
| Border | `border-border` | `var(--color-border)` |
| Primary text | `text-foreground` | `var(--color-foreground)` |
| Secondary / muted text, placeholders | `text-muted-foreground` | `var(--color-muted-foreground)` |
| Disabled | `text-muted-foreground/50` or `opacity-50` | — |
| Primary accent | `bg-primary text-primary-foreground` / `text-primary` | `var(--color-primary)` |
| Hover fill | `hover:bg-accent` / `hover:bg-muted/50` | — |
| Error | `text-destructive` | `var(--color-destructive)` |
| Success / warning / info | `text-success` / `text-warning` / `text-info` (tints: `bg-success/10`) | `var(--color-success)` … |
| Series / data colors | `chart-1` … `chart-5` | `var(--color-chart-1)` … |

Radius: controls `rounded-md`, floating panels `rounded-xl`. Shadow: floating panels `shadow-md`,
popovers `shadow-md`, nothing heavier.

**Overlay buttons on the map canvas:** toggle buttons that float directly on the map (layer panel
button, side panel collapse strip) need contrast against the tiles — use the primary `Button` or an
`outline` `Button` (which sits on `bg-card`) with `shadow-md`. They are still `rounded-md`.

**Only when the active `design/` theme is Tactical** (or a map-specific dark skin is requested): the
same classes apply — the Tactical theme changes the token values, not the component classes.

---

## 3. Z-Index Stack

All overlays live inside the canvas div (`position: relative`). Z-indices must respect this order:

| Layer | z-index | Tailwind | Component |
|---|---|---|---|
| Layer panel button + panel | 10 | `z-10` | `MapPluginShell` layer toggle |
| Side panel (floating mode) | 20 | `z-20` | `MapSideSlot` |
| Date filter + popup | 30 | `z-30` | `MapFloatingDateFilter` wrapper |
| Tooltip | 100 | `z-100` | `MapTooltip` |

> **Why date filter must be z-30:** The `DatePickerPopup` has `zIndex: 200` **within** the date filter's stacking context. If the date filter container itself has `z-index < 20` (side panel), the entire panel including its children is hidden behind the panel. The container's z-index is the deciding level.

> **Alternate/simpler pattern — portal past the stack instead of out-z-indexing it.** If the date
> picker's *popover* (not the closed trigger) is rendered via `createPortal` straight into
> `document.body` with its own high z-index, it escapes the map's internal stacking context entirely —
> only the closed trigger/pill needs a z-index high enough to sit above the map's other overlays. This
> avoids having to keep a whole z-index ladder in sync as more floating panels are added. Whichever
> approach a given codebase uses, don't mix them on the same control — decide once whether the popover
> lives inside the stacking context (needs a carefully-ordered z-index) or portals out of it (only the
> trigger needs a z-index).

---

## 4. MapPluginShell — Layout Contract

```tsx
// Root shell — fills the hosting page/card 100%
<div className="map-plugin-shell relative w-full h-full flex flex-col overflow-hidden">

  {/* Canvas area — fills remaining height after sticky/bottom slots */}
  <div className="relative flex-1 min-h-0">

    {/* Mapbox container — fills canvas area 100% */}
    <div ref={containerRef} className="w-full h-full" />

    {/* Layer toggle — top-left overlay */}
    <div className="absolute top-2.5 left-2.5 z-10 flex flex-col gap-1.5 items-start">
      <Button
        size="icon"
        variant={panelOpen ? 'default' : 'outline'}
        aria-label="Toggle layer panel"
        aria-expanded={panelOpen}
        className="size-8 shadow-md"
      >
        <i className="ph ph-stack" aria-hidden="true" />
      </Button>
      {panelOpen && <MapLayerPanel />}
    </div>

    {/* Date filter — top-right, z-30 so popup renders above side panel */}
    <div className="absolute top-2.5 right-2.5 z-30">
      <MapFloatingDateFilter />
    </div>

    {/* Side slot — floating right panel */}
    <MapSideSlot topOffset={62} />  {/* 62 = 10px margin + 44px filter height + 8px gap */}

  </div>  {/* end canvas */}

  {/* Bottom slot — document flow, below canvas */}
  <MapBottomSlot />

  {/* Sticky slot — document flow, always at very bottom */}
  <MapStickySlot />

</div>
```

**`topOffset` calculation for `MapSideSlot`:**
- `showdateFilter !== false` → `topOffset = 62` (10px + ~44px filter + 8px gap)
- `showdateFilter === false` → `topOffset = 0`

**`ResizeObserver` — mandatory:**
Add to `MapPluginShell` to trigger `map.resize()` on container dimension changes (bottom slot collapse/expand, sidebar toggle):

```tsx
useEffect(() => {
  if (!containerRef.current) return
  const ro = new ResizeObserver(() => { mapRef.current?.resize() })
  ro.observe(containerRef.current)
  return () => ro.disconnect()
}, [])
```

---

## 4a. Date filter control — recommended shape

Where a map exposes its own date-range filter, prefer these conventions:

- **Never fall back to a raw `<input type="date">`** for the trigger — it renders in the browser's
  locale-dependent format (often `mm/dd/yyyy`), which is both off-brand and frequently the wrong date
  order for the target locale. Build (or reuse) a proper pill/button trigger showing the committed
  range in an explicit, locale-correct format.
- **Reuse the app's shared date-range picker component** for the popover/calendar — don't hand-roll a
  second calendar implementation just because it's triggered from a map. Consistency with the rest of
  the app's filter UI (same quick-range tabs, same calendar grid) matters more than map-specific styling.
- **Seed the control with a sensible default range on mount** (e.g. "today," or whatever the page's
  default query window is) rather than leaving it visually empty — an empty-looking date trigger reads
  as "no data loaded yet" even when the map already fetched with an implicit default range.
- **Anchor the popover toward the side it should grow.** If the calendar can expand from a compact
  quick-tab row into a much wider view (e.g. an "advanced" tab revealing preset rail + dual month
  grids), anchor the popover by the edge it should stay pinned to (commonly `right`, when the trigger
  sits at the map's right edge) so the expansion grows away from the trigger rather than covering it or
  drifting off-screen.
- **Isolate any value-shape mismatch behind one small conversion helper**, reused on both the read and
  write side, rather than hand-rolling ad hoc string parsing at each call site — e.g. if the map's own
  store keeps dates in one string format and the shared picker communicates in another (epoch ms, ISO,
  etc.), write (or reuse) a single pair of `to<Format>`/`from<Format>` helpers and use them everywhere
  that boundary is crossed.

---

## 5. MapSideSlot — Right Panel Contract

```tsx
// Floating mode wrapper — `top` is dynamic from props, rest is Tailwind
<div
  className="absolute right-2.5 bottom-2.5 z-20 flex items-stretch flex-row-reverse"
  style={{ top: topOffset }}
>
  {/* Panel — width is dynamic (open toggle), border/shadow conditional */}
  <div
    className={cn(
      'h-full bg-card text-card-foreground rounded-xl flex flex-col overflow-hidden shrink-0 transition-[width] duration-300',
      open && 'border border-border shadow-md',   // collapsed (width 0): no frame
    )}
    style={{ width: open ? panelWidth : 0 }}   // dynamic
  >
    {/* Tab bar — Swiper (horizontal scroll of many tabs) */}
    <div className="border-b border-border shrink-0 overflow-hidden bg-muted/50">
      <Swiper modules={[FreeMode, Mousewheel]} freeMode grabCursor simulateTouch
              mousewheel={{ forceToAxis: true, sensitivity: 1 }} slidesPerView="auto"
              style={{ padding: '0 4px' }}>
        {widgets.map((w) => {
          const active = activeTab === w.widgetId
          return (
            <SwiperSlide key={w.widgetId} style={{ width: 'auto' }}>
              <button
                type="button"
                aria-pressed={active}
                className={cn(
                  'cursor-pointer whitespace-nowrap border-0 border-b-2 bg-transparent px-3 py-2 text-xs select-none transition-colors',
                  'focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none',
                  active ? 'border-primary font-medium text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground',
                )}
              >
                {w.name}
              </button>
            </SwiperSlide>
          )
        })}
      </Swiper>
    </div>

    {/* Widget content */}
    <div className="flex-1 min-h-0 relative overflow-hidden">
      {widgets.map((w) => (
        <div key={w.widgetId} className="flex-col h-full overflow-hidden"
             style={{ display: activeTab === w.widgetId ? 'flex' : 'none' }}>
          <MapWidgetHost ... />
        </div>
      ))}
    </div>
  </div>

  {/* Collapse toggle — floating on map, primary Button for contrast */}
  <div className="flex items-center self-center shrink-0">
    <Button
      size="icon"
      aria-label={open ? 'Collapse panel' : 'Expand panel'}
      className="h-14 w-5 rounded-l-md rounded-r-none shadow-md"
    >
      <i className={`ph ph-caret-${open ? 'right' : 'left'}`} aria-hidden="true" />
    </Button>
  </div>
</div>
```

**Default panel width:** `470px` — fixed, do not derive from widget config `width`.

**Tab state** is expressed with `cn()` conditionals on token classes — no inline colors. When the tab
count is small and doesn't need Swiper's free scroll, use the shadcn `Tabs` primitive instead.

---

## 6. MapBottomSlot — Bottom Panel Contract

```tsx
// Wrapper — in document flow below canvas
<div className="w-full relative shrink-0">

  {/* Tab above panel — absolute, pointer-events isolated */}
  <div className="absolute -top-5 inset-x-0 flex justify-center z-1 pointer-events-none">
    <button
      type="button"
      onClick={() => setCollapsed((c) => !c)}
      aria-label={collapsed ? 'Expand bottom panel' : 'Collapse bottom panel'}
      aria-expanded={!collapsed}
      className="pointer-events-auto bg-card border border-border border-b-0 rounded-t-md text-muted-foreground w-12 h-5 flex items-center justify-center cursor-pointer text-xs leading-none hover:bg-muted transition-colors focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
    >
      <i className={`ph ph-caret-${collapsed ? 'up' : 'down'}`} aria-hidden="true" />
    </button>
  </div>

  {/* Animated content — maxHeight is the only dynamic value */}
  <div
    className="overflow-hidden w-full"
    style={{ maxHeight: collapsed ? 0 : 800, transition: 'max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1)' }}
  >
    <div className="flex gap-2 px-2 py-1.5 overflow-x-auto bg-card border-t border-border">
      {widgets.map((w) => (
        <div key={w.widgetId} className="shrink-0"
             style={{ width: w.width ?? 'auto', height: w.height ?? 'auto' }}>
          <MapWidgetHost ... />
        </div>
      ))}
    </div>
  </div>
</div>
```

---

## 7. MapStickySlot — Contract

```tsx
// Pure document flow, zero inline styles
<div className="w-full shrink-0">
  {widgets.map((w) => <MapWidgetHost key={w.widgetId} ... />)}
</div>
```

---

## 8. MapTooltip — Contract

```tsx
// Position is dynamic (from click event coords) — only those stay inline
<div
  className="map-tooltip-portal absolute z-100 pointer-events-none"
  style={{
    left: tooltipPosition.x + 12,
    top: tooltipPosition.y - 8,
    maxWidth: tooltip.width ?? 280,
  }}
>
  ...
</div>
```

---

## 9. MapPluginWidget — Contract

```tsx
// Error state — shadcn Alert, not plain red text
<Alert variant="destructive" className="m-4">
  <i className="ph ph-warning-circle size-4" aria-hidden="true" />
  <AlertTitle>Map unavailable</AlertTitle>
  <AlertDescription>Map config not found for referenceId: {referenceId}</AlertDescription>
</Alert>

// Wrapper
<div className={`w-full h-full relative overflow-hidden ${className ?? ''}`}>
  <MapPluginShell ... />
</div>
```

---

## 10. Widget Content Components — Token Rules

Components rendered inside `MapSideSlot`, `MapBottomSlot`, `MapStickySlot`:

### ✅ Mandatory

| Rule | Reason |
|---|---|
| Panel backgrounds `bg-card`; tab bars `bg-muted/50` or shadcn `Tabs` | Semantic surfaces, light + dark |
| Borders `border-border` | Consistent border token |
| Text `text-foreground` / `text-muted-foreground` | Semantic text tokens |
| Accent colors passed as CSS var strings: `"var(--color-primary)"`, `"var(--color-destructive)"`, `"var(--color-chart-1)"` | Never pass raw hex as props |
| Sentiment / status colors: positive → `var(--color-success)`, negative → `var(--color-destructive)`, neutral → `var(--color-muted-foreground)` | Data-viz colors must trace to tokens |
| Loading → `Skeleton` (`bg-muted`, `rounded-md`/`rounded-lg`) shaped like the content | Designed loading state |
| Empty → `EmptyState`; error → `Alert variant="destructive"` + Retry | Designed empty/error states (`reactjs-ui-design` §5.7) |
| Lists/tables inside panels → `@/modules/data-table` or shadcn `Table` | No unstyled tables |

### ❌ Forbidden

| Pattern | Reason |
|---|---|
| `rgba(10,20,40,...)`, `#1e293b`, glassmorphism in panel/widget chrome | Not part of the visual direction; breaks light/dark |
| `rgba(255,255,255,...)` for text/border in widget content | Breaks on light surfaces |
| `color: '#111827'`, `'#6b7280'`, `'#9ca3af'`, `gray-*`/`slate-*` classes | Tailwind default palette, not design tokens |
| `background: '#fff'` or `'#f8fafc'` | Use `bg-card` / `bg-muted` |
| Raw hex in `accentColor` prop: `accentColor="#3b82f6"` | Must be `accentColor="var(--color-primary)"` |
| Native `<select>`, `<input type="checkbox">`, hand-built dropdowns/modals | Use shadcn `Select`, `Checkbox`, `DropdownMenu`, `Dialog`/`Sheet` |
| `onMouseEnter`/`onMouseLeave` JS handlers for hover color | Use Tailwind `hover:` classes instead |

---

## 11. Pre-Implementation Checklist for Any MapPlugin UI Change

- [ ] Static layout → Tailwind; dynamic values only → `style={{}}`
- [ ] All panel chrome colors → shadcn semantic tokens (works in light and dark; no navy/glass)
- [ ] Floating panels `rounded-xl border border-border bg-card shadow-md`; controls are shadcn primitives
- [ ] Overlay buttons on map canvas → primary or outline `Button` with `shadow-md`
- [ ] z-index stack respected: layer=10, side=20, date=30, tooltip=100
- [ ] `topOffset` for `MapSideSlot` = `62` when date filter is shown, `0` when hidden
- [ ] `ResizeObserver` on `containerRef` triggers `map.resize()` — do not remove
- [ ] `accentColor` props passed as `"var(--*)"` strings, never raw hex
- [ ] Hover states via Tailwind `hover:` classes — no `onMouseEnter`/`onMouseLeave` handlers
- [ ] Widget content loading uses `Skeleton`; empty uses `EmptyState`
- [ ] Error states use `Alert variant="destructive"` (+ Retry where it can be retried)
- [ ] Reviewed with `npm run ui:snapshot -- --route <path>` (`reactjs-ui-design` §8)
