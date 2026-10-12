# Slicing UI — Rules & Constraints

> Visual direction (radius, shadow, spacing, typography, states, component priority, review loop) is
> owned by [`reactjs-ui-design`](../../reactjs-ui-design/SKILL.md) and `.claude/rules/web/ui-design.md`.
> These rules cover the slicing workflow: token discipline, placement and conflict resolution.

---

## Pre-Execution Validator

> Run this checklist **before writing any FE code**. Any failure = fix first.

### Step 1 — Load the visual contract

- [ ] Loaded `reactjs-ui-design` (playbook) and `.claude/rules/web/ui-design.md`
- [ ] Read `src/styles/variable.css` and `src/styles/tailwind.css` (semantic variables and their classes)
- [ ] Checked `src/components/ui/`, `src/components/common/` and `src/modules/data-table/` for what already exists
      (or opened `/ui-kit` in dev)
- [ ] **Only if a `design/` theme exists** (`design/design-system.md`): read the active
      `design/[platform]/[theme]/DESIGN.md` and confirm its values are imported into the semantic variables
      (font, palette, radius, default mode). If not, import them first per `reactjs-design-system` Step 4.

### Step 2 — Block map

- [ ] Every block of the design is mapped to a building block (`PageHeader`, `StatCard`, `DataTable`,
      `SectionCard`, `EmptyState`, `StatusBadge`, shadcn primitive …) — see SKILL.md Step 0
- [ ] Missing shadcn primitives identified for installation (`npx shadcn@latest add <name>` in `apps/web`)

### Step 3 — Forbidden pattern pre-check

Before writing, verify you will NOT use:

- [ ] Hardcoded colors (`#ffffff`, `rgb(...)`, `hsl(...)`)
- [ ] Arbitrary Tailwind values (`bg-[#2EB3E8]`, `p-[16px]`, `text-[14px]`, `rounded-[14px]`)
- [ ] Tailwind default palette classes (`bg-blue-500`, `text-gray-900`)
- [ ] `font-family` inside component files
- [ ] Direct CSS variable references in `className` (`bg-[var(--base-neutral-100)]`)
- [ ] Hand-built dropdown/select/dialog/popover/tooltip/tabs/checkbox/switch/date picker/toast, native
      `<select>` / `<input type="checkbox">`, `alert()` / `confirm()`
- [ ] `rounded-none` / square surfaces, pill buttons, colored or glow shadows (unless a selected
      `design/` theme mandates it — and then via variables only)
- [ ] `lucide-react` imports (Phosphor only)

---

## Allowed

### Styling priority

```
1. Primitive / common pattern / its variants   ← always first
2. Tailwind semantic classes via cn()           ← layout, spacing, small adjustments
3. styled-components                            ← only when Tailwind cannot express it
4. ❌ Inline styles for visuals                  ← FORBIDDEN
```

### Token usage

| # | Rule |
|---|---|
| ✅ | shadcn semantic classes for surfaces, text, borders: `bg-background`, `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`, `border-border`, `border-input`, `ring-ring` |
| ✅ | `bg-primary text-primary-foreground` for the primary action (via `<Button>`) |
| ✅ | Status: `destructive`, `success`, `warning`, `info` — tinted (`bg-success/10 text-success`) for badges/alerts |
| ✅ | Tailwind default type/spacing scale (`text-sm`, `text-2xl`, `p-6`, `gap-4`) |
| ✅ | Radius: `rounded-md` controls, `rounded-lg` inner tiles, `rounded-xl` surfaces, `rounded-full` avatars/dots/switches |
| ✅ | `cn()` from `@/utils/cn` for conditional and merged class names |
| ✅ | The `.dark {}` cascade in `variable.css` — do not fork dark mode styles per component |
| ✅ | Brand scales (`secondary-*`, `tertiary-*`, `quaternary-*`, `quinary-*`) and `chart-1…5` — data visualization only |

### styled-components (fallback only)

| ✅ Use when… | ❌ Do NOT use when… |
|---|---|
| Complex `@keyframes` animations | Basic layout, color, spacing |
| `clip-path`, `mask`, `filter` with dynamic values | Conditional classes (use `cn()`) |
| `::before` / `::after` with dynamic content | Static styles Tailwind covers |
| Third-party overrides requiring CSS specificity | Anything expressible with Tailwind |

Place in a co-located `*.styles.ts`, name descriptively (`AnimatedBar`), use CSS variables only, never
`style={{}}` on them.

### Component structure

| # | Rule |
|---|---|
| ✅ | **MANDATORY:** check `src/components/ui/`, `src/components/common/`, `src/modules/` before creating any component |
| ✅ | shadcn primitives → `src/components/ui/` (single primitive, no domain logic) |
| ✅ | Generic page patterns → `src/components/common/` (no API calls, no domain logic) |
| ✅ | Shell → `src/components/layouts/`; 3rd-party adapters → `src/components/wrappers/` |
| ✅ | Generic modules reused by 2+ features → `src/modules/<name>/` (lists: `src/modules/data-table/`) |
| ✅ | Domain UI → `src/features/<domain>/<feature>/components/`; data via the feature's TanStack Query hooks |
| ✅ | Pages → `src/pages/<area>/<Name>Page.tsx`, thin default export |
| ✅ | Accept `className?: string` and forward it via `cn()` (last) |
| ✅ | Imports one-way: `pages → features → modules → components/common → components/ui` |

---

## Forbidden

### Hard-coded values

| # | Rule |
|---|---|
| ❌ | Raw colors — never `bg-[#0d5eba]` or `style={{ color: '#5b5d63' }}` |
| ❌ | Arbitrary values when the scale covers the case — never `text-[14px]`, `p-[16px]`, `rounded-[8px]` |
| ❌ | Tailwind's default palette (`blue-500`, `red-400`, `gray-200`) |
| ❌ | Overriding `--base-*` or semantic variables inside component files |
| ❌ | Removing or renaming existing CSS variables / Tailwind aliases (additive only) |
| ❌ | Legacy aliases (`bg-background-primary`, `text-font-*`, `border-border-primary`) in new code |

### Component structure violations

| # | Rule |
|---|---|
| ❌ | API calls in primitives, common patterns, modules or components — use feature hooks → services |
| ❌ | Domain components in `src/components/` |
| ❌ | `components/ui` importing from `components/common`, `modules` or `features`; `components/common` importing from `features` |
| ❌ | Raw `<button>`, `<input>`, `<select>`, `<table>` where a primitive exists |
| ❌ | Hand-rolled copies of `PageHeader`/`StatCard`/`EmptyState`/`DataTable` inside features |
| ❌ | New layout shells for a single page |

### Styling anti-patterns

| # | Rule |
|---|---|
| ❌ | `style={{...}}` for visuals |
| ❌ | `@apply` inside component files (only in `components.css` via `@utility`) |
| ❌ | Inline `<style>` blocks in React components |
| ❌ | `!important` |
| ❌ | Per-component dark mode classes that duplicate what tokens already do |
| ❌ | Re-styling a primitive at every call site instead of fixing its variant once |
| ❌ | Cards inside cards, borders around every element, square surfaces, glow/colored shadows, gradients |

### Composition violations

| # | Rule |
|---|---|
| ❌ | Treating token correctness as done when the composition diverges from the playbook recipe (§5) |
| ❌ | Pages without `PageHeader`, lists without the `DataTable` toolbar/pagination, async surfaces without loading/empty/error |

---

## Additive-only rule

Adding variables/aliases is allowed; removing or reducing existing ones is never allowed.

### Token gap procedure

1. Confirm no existing semantic variable fits (check `muted`, `accent`, status first).
2. Add to `src/styles/variable.css` in **both** `:root` and `.dark`:
   ```css
   :root { --your-new-token: var(--base-neutral-200); }
   .dark { --your-new-token: var(--base-neutral-700); }
   ```
3. Register in `src/styles/tailwind.css` `@theme inline { --color-your-new-token: var(--your-new-token); }`.
4. Use the Tailwind class only: `<div className="bg-your-new-token">`. Never `bg-[var(--x)]`, never
   `style={{ background: 'var(--x)' }}`.

---

## shadcn/ui compatibility

shadcn primitives consume `--background`, `--foreground`, `--card`, `--popover`, `--primary`, `--muted`,
`--accent`, `--border`, `--input`, `--ring`, `--sidebar-*`. These are wired in `variable.css` — never
overridden in component files.

| # | Rule |
|---|---|
| ✅ | Use shadcn token names (`bg-background`, `text-foreground`, `bg-card`) — they resolve through the wired variables |
| ✅ | After `npx shadcn@latest add`, run the playbook §3 post-install checklist (Phosphor, `React.forwardRef`, tokens, radius/shadow, `@/utils/cn`) |
| ❌ | Overriding shadcn CSS variables inside component files or JSX |
| ❌ | Hex values or Tailwind palette colors in shadcn variants |
| ❌ | Leaving `lucide-react` imports in installed components |

After a re-brand or `design/` theme switch: check `/ui-kit` in light and dark (`npm run ui:snapshot --
--route /ui-kit`); if a component doesn't switch, its variable is missing from `.dark {}`.

---

## Verification

Code is complete when **all** of the following are true:

### Tokens

- [ ] Zero raw colors, zero Tailwind palette classes, zero arbitrary values
- [ ] Only shadcn semantic classes + Tailwind default type/spacing scale
- [ ] Radius per playbook (controls `rounded-md`, surfaces `rounded-xl`); shadows `shadow-xs` resting, `shadow-md/lg` floating only

### Composition

- [ ] Every block maps to a building block (SKILL.md Step 0); no hand-rolled copies of common patterns
- [ ] Page starts with `PageHeader`; lists use `DataTable` in one card with toolbar + pagination
- [ ] No cards in cards, no double borders, one primary action per view

### Structure

- [ ] Files placed per the folder table; one-way imports; no API calls outside hooks/services
- [ ] Route **and** menu entry added together (unless explicitly hidden)
- [ ] Every component accepts and forwards `className` via `cn()`

### States & accessibility

- [ ] Loading (skeletons), empty (`EmptyState`), error (`Alert` + Retry), disabled, hover, `focus-visible`
- [ ] WCAG AA contrast; visible focus; icon-only buttons have `aria-label` + `Tooltip`; semantic HTML

### Dark mode & responsive

- [ ] All tokens switch under `.dark` with no extra overrides
- [ ] Verified at 390px, 768px, 1440px — no horizontal page scroll; tables scroll inside their card

### Review loop

- [ ] `npm run ui:snapshot -- --route <path>` run; every PNG opened and checked against playbook §8; fixes re-snapshotted
- [ ] `reactjs-anti-slop` checklist passed
- [ ] `npm run typecheck && npm run lint && npm run test:ci` pass
