# UI Design Rules — Web (`apps/web`)

> Always-on rules for ANY UI work (new page, component, form, table, dashboard, restyle).
> The full playbook with recipes, code and the review loop is the skill
> `.claude/skills/reactjs-ui-design/SKILL.md`. Load it before building UI.

## Visual direction: modern, minimal, calm

Think Linear / Vercel / Stripe dashboard, not "Bootstrap admin template".

- **Neutral first.** ~90% of the screen is neutral surfaces and text. One accent (`primary`) for the
  primary action, active navigation, focus and key highlights. Status colors only for status.
- **Slightly rounded.** Controls (button, input, select, badge) `rounded-md` (8px). Surfaces (card, table
  wrapper, dialog, popover, sheet) `rounded-xl` (12px). `rounded-full` only for avatars, status dots and
  switches. Never `rounded-none` on app UI, never pill-shaped buttons or bubbly 24px corners.
- **Quiet depth.** 1px low-contrast borders (`border-border`) + at most `shadow-xs` on resting surfaces.
  Real shadows (`shadow-md/lg`) only on floating layers (popover, dropdown, dialog, toast).
  No glows, no colored shadows, no glassmorphism, no gradient blobs.
- **Clear hierarchy.** Every page has one obvious title and one primary action. Typography does the
  work: size + weight + muted color, not boxes, borders or colors.
- **Generous, consistent spacing** on a 4px grid. Space separates groups; lines are the exception.
- **Real states.** Loading (skeletons shaped like the content), empty (icon + title + hint + action),
  error (inline alert with retry), disabled, hover, `focus-visible`. Never a blank area.

## Component priority (shadcn first)

1. **Use what's in `src/components/ui/`** (shadcn primitives themed to our tokens).
2. **Not installed but exists in shadcn?** Install it — never hand-roll it:
   `cd apps/web && npx shadcn@latest add <component>` → then apply the post-install fixes in the skill
   (Phosphor icons instead of `lucide-react`, `React.forwardRef` for React 18, token check).
3. **Compose** page patterns from `src/components/common/` (`PageHeader`, `StatCard`, `EmptyState`, …)
   and `src/modules/data-table/` before writing new layout code.
4. **Hand-write markup** only for static surfaces with no behavior.

Never hand-build a dropdown, select, combobox, dialog, popover, tabs, tooltip, checkbox, switch, radio,
date picker or toast. Never use native `<select>`, `<input type="checkbox">`, `alert()`, `confirm()`.

## Tokens (never raw values)

- Use the **shadcn semantic classes**: `bg-background`, `bg-card`, `bg-muted`, `bg-accent`,
  `text-foreground`, `text-muted-foreground`, `border-border`, `border-input`, `ring-ring`,
  `bg-primary text-primary-foreground`, `bg-destructive`, `bg-sidebar…`, `chart-1…5`.
  Legacy aliases (`bg-background-primary`, `text-font-*`, `border-border-primary`) still resolve but
  don't use them in new code.
- Status: `success`, `warning`, `info`, `destructive` — as subtle tints for badges/alerts
  (e.g. `bg-success/10 text-success`), solid only for one-off emphasis.
- The extra brand palettes (`secondary-*`, `tertiary-*`, `quaternary-*`, `quinary-*` color scales) are
  for data visualization only — never for buttons, cards, nav or page chrome.
- Tailwind's default type and spacing scale (`text-sm`, `text-2xl`, `p-6`, `gap-4`). No arbitrary
  values (`text-[13px]`, `p-[18px]`, `#hex`, `rgb()`), no Tailwind palette colors (`blue-500`).

## Typography

Inter. App body text is `text-sm` (14px). Page title `text-2xl font-semibold tracking-tight`; section
title `text-base font-semibold`; meta and helper text `text-sm text-muted-foreground`; captions
`text-xs`. Three weights only: 400 / 500 / 600. Numbers in tables and stats use `tabular-nums`.
No italic headings, no ALL CAPS paragraphs, no centered body text in app screens.

## Layout

- Page anatomy: `PageHeader` (title, description, actions) → optional toolbar/tabs → content.
  Page padding comes from `AppLayout`; sections are separated with `gap-6`/`gap-8`.
- Forms: single column, `max-w-2xl`; label above input; helper/error text below; actions bottom-right
  (primary rightmost). Long settings pages use the two-column section pattern from the skill.
- Lists: toolbar (search + filters + primary action) above a `DataTable` inside one card; row actions in
  a `DropdownMenu` (`ph-dots-three`), destructive actions confirmed with `AlertDialog`.
- No cards inside cards. No borders around every element. No full-width text inputs on wide screens.
- Responsive: verify 390px, 768px and 1440px. Light **and** dark.

## Icons

Phosphor only (`<i className="ph ph-<name>" aria-hidden />`), `size-4` (16px) in controls and table rows,
`size-5` in page headers/empty states, `text-muted-foreground` unless interactive. Icon-only buttons need
`aria-label` + `Tooltip`. Never `lucide-react` (the skill has the lucide → Phosphor map).

## Definition of done for UI work

1. Built from shadcn primitives + `components/common` patterns per the priority above.
2. All states covered (loading / empty / error / disabled / focus).
3. **Looked at it**: `npm run ui:snapshot -- --route <path>` (from `apps/web`) and reviewed the PNGs
   (light + dark, desktop + mobile) against the checklist in the skill. Fix before reporting done.
4. `npm run typecheck && npm run lint && npm run test:ci` pass.
