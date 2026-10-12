---
name: reactjs-icon
description: Implementation guide for icons in apps/web. Phosphor Web (CSS icon font, bundled locally from @phosphor-icons/web) is the only allowed icon source. Covers direct `<i>` usage, the renderIcon utility, weight variants, menu-config wiring and svg-code brand icons.
---

# Icon Skill (React / TypeScript / Vite)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns the icon source (Phosphor only), `renderIcon` and menu icon wiring.

## When to use

Any time you render an icon in `apps/web`: buttons, shell components, menu entries, status screens, tables.

---

## Setup (already done in the boilerplate — do not touch)

Phosphor Web is an npm dependency (`@phosphor-icons/web`) and its font stylesheets are **imported once
in `apps/web/src/main.tsx`** and bundled by Vite (no CDN, no `<link>` tags, no proxy):

```ts
// apps/web/src/main.tsx
import '@phosphor-icons/web/regular'
import '@phosphor-icons/web/fill'
import '@phosphor-icons/web/bold'
import '@phosphor-icons/web/light'
import '@phosphor-icons/web/duotone'
```

- `vite.config.ts` has a `phosphorWoff2Only()` plugin that strips the woff/ttf/svg font formats from the
  bundled `@font-face` rules — keep it.
- Supported weights = the five imported above (`IconWeight` in `src/types/icon.d.ts`). `thin` is **not**
  bundled; if you really need it, add `import '@phosphor-icons/web/thin'` to `main.tsx` **and** extend
  `IconWeight` + `WEIGHT_CLASS` in `src/utils/icon-renderer.tsx`.
- ✅ Icons are available globally — no per-component setup.
- ❌ Do NOT add `<link>` tags for Phosphor in `index.html`, `@import url(...)` in CSS, or a remote CDN/proxy.
- ❌ `@phosphor-icons/react`, `lucide-react`, `react-icons` must NOT be added to `package.json`.

---

## Pattern 1 — Direct `<i>` tag

For static icons in shell components, buttons and UI elements (this is what the boilerplate does, e.g.
`features/administrator/user/components/UserListView.tsx` and the `src/components/ui/*` primitives).

```tsx
<i className="ph ph-house" aria-hidden="true" />                       {/* regular */}
<i className="ph-fill ph-fire" aria-hidden="true" />                   {/* fill */}
<i className="ph-bold ph-warning" aria-hidden="true" />                {/* bold */}
<i className="ph ph-house size-4" aria-hidden="true" />                {/* 16px (also the default): controls, table rows */}
<i className="ph ph-users size-5 text-muted-foreground" aria-hidden="true" />  {/* 20px: page headers, empty states */}
```

Sizing: `size-*` alone sizes a Phosphor `<i>` (global rule in `src/index.css` maps `size-3` … `size-12`
to the glyph's font-size; unsized icons are 16px), so no `text-*`/`leading-none` is needed — an
explicit `text-*` on the icon still wins. `size-4` (16px) in buttons, inputs, menu items and table rows;
`size-5` (20px) in page headers and empty-state tiles. Inside shadcn primitives keep the `[&_i]` / `[&_svg]` sizing rules
they already apply instead of adding your own. Color: `text-muted-foreground` for decorative icons,
inherit `currentColor` on interactive ones; status icons use the status token (`text-success`,
`text-destructive`…). Never raw palette classes or arbitrary `text-[20px]` sizes. Icon-only buttons:
`<Button size="icon" variant="ghost" aria-label="…">` wrapped in a `Tooltip`.

**Icon slug format:** kebab-case matching [phosphoricons.com](https://phosphoricons.com)

- ✅ `chart-line-up`, `clock-countdown`, `wifi-high`
- ❌ `chartLineUp`, `ClockCountdown`, `WifiHigh`

---

## Pattern 2 — `renderIcon()` utility

Use when the icon name / type / weight comes from config (menu items, dynamic data).

```tsx
import { renderIcon, type IconWeight } from '@/utils/icon-renderer'

renderIcon({ icon: 'house' })                              // <i class="ph ph-house">
renderIcon({ icon: 'house', weight: 'fill' })              // <i class="ph-fill ph-house">
renderIcon({ icon: 'house', weight: 'bold', size: 20 })    // font-size: 20px

// From menu config — exactly what components/layouts/SidebarNavItem.tsx does
const weight: IconWeight | undefined = isActive ? item.additional?.iconStyleActive : item.additional?.iconStyle
renderIcon({ icon: item.icon, iconType: item.additional?.iconType, weight })
```

Real signature (`apps/web/src/utils/icon-renderer.tsx`, types in `apps/web/src/types/icon.d.ts`):

```ts
export type IconType = 'phosphor' | 'svg-code'
export type IconWeight = 'regular' | 'fill' | 'bold' | 'light' | 'duotone'

export interface RenderIconOptions {
  icon: string          // Phosphor slug, or an SVG string for 'svg-code'
  iconType?: IconType   // default 'phosphor'
  weight?: IconWeight   // default 'regular'
  size?: number         // px → inline font-size (phosphor) or width/height (svg-code)
  className?: string
}
export function renderIcon(options: RenderIconOptions): ReactElement
```

Components that take an icon slug as a prop (e.g. `StatusScreen` in `components/common/StatusScreen.tsx`)
expect the bare slug (`icon="users"`), not a class string.

---

## Weight Reference

| Weight  | `<i>` class            | `renderIcon` weight |
| ------- | ---------------------- | ------------------- |
| Regular | `ph ph-{name}`         | `'regular'`         |
| Fill    | `ph-fill ph-{name}`    | `'fill'`            |
| Bold    | `ph-bold ph-{name}`    | `'bold'`            |
| Light   | `ph-light ph-{name}`   | `'light'`           |
| Duotone | `ph-duotone ph-{name}` | `'duotone'`         |

---

## Menu Config Wiring

In `src/config/menu/app.menu.ts` / `administrator.menu.ts` (type `IMenu` from `src/types/menu.d.ts`):

```ts
{
  icon: 'chart-line-up',        // Phosphor slug
  additional: {
    iconType: 'phosphor',       // 'svg-code' only for brand icons
    iconStyle: 'regular',       // weight when inactive
    iconStyleActive: 'fill',    // weight when the nav item is active
    // …container, mainPage, redirectToEnabled, redirectTo
  },
}
```

`SidebarNavItem` picks `iconStyle` / `iconStyleActive` based on the active route. See
`.claude/skills/reactjs-menu-config/SKILL.md`.

---

## svg-code — Custom Brand Icons

Only for icons not available in Phosphor (brand logos, design-team assets):

```ts
// menu config
{ icon: '<svg viewBox="0 0 24 24">...</svg>', additional: { iconType: 'svg-code', /* … */ } }

// direct
renderIcon({ icon: '<svg viewBox="0 0 24 24">...</svg>', iconType: 'svg-code', size: 20 })
```

⚠️ `svg-code` uses `dangerouslySetInnerHTML` — never pass user-supplied or API-supplied strings (XSS).

---

## Rules

| Library                           | Status                                              |
| --------------------------------- | --------------------------------------------------- |
| Phosphor Web CSS (`ph ph-{name}`) | ✅ Required                                         |
| `@phosphor-icons/react`           | ❌ Forbidden                                        |
| `lucide-react`                    | ❌ Forbidden (also when adding shadcn components — swap their lucide imports for `<i className="ph …">` using the lucide → Phosphor map in [`reactjs-ui-design` §3](../reactjs-ui-design/SKILL.md#lucide--phosphor-map)) |
| `react-icons`                     | ❌ Forbidden                                        |
| Raw inline SVG in JSX             | ❌ Forbidden (use `svg-code` via `renderIcon`)      |

## Common mistakes

- Copying or `npx shadcn@latest add`-ing a component that imports `lucide-react` — replace each icon with a
  Phosphor `<i>` per the lucide → Phosphor map in `reactjs-ui-design` §3 (`ChevronDown` → `ph ph-caret-down`,
  `X` → `ph ph-x`, `Check` → `ph ph-check`, `MoreHorizontal` → `ph ph-dots-three`, `Loader2` →
  `ph ph-spinner animate-spin` …).
- Using a weight that is not bundled (`ph-thin`) → renders nothing.
- camelCase slugs (`ph-chartLineUp`) → renders nothing.
- Missing `aria-hidden="true"` on decorative icons / missing `aria-label` on icon-only buttons.

## Pre-Submission Checklist

- [ ] No import from `lucide-react`, `@phosphor-icons/react`, or `react-icons`
- [ ] All icons use `<i className="ph{-weight} ph-{name}">` or `renderIcon()`
- [ ] Only bundled weights used (regular, fill, bold, light, duotone)
- [ ] `aria-hidden="true"` on decorative icons; icon-only buttons have `aria-label`
- [ ] Slugs are kebab-case Phosphor names
- [ ] Menu entries set `additional.iconType: 'phosphor'`, `iconStyle`, `iconStyleActive`
