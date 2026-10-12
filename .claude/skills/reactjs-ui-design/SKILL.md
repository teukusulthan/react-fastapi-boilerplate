---
name: reactjs-ui-design
description: The visual design playbook for apps/web — modern, minimal, slightly rounded, shadcn-first. Load BEFORE creating or restyling any UI (page, screen, dashboard, form, table, dialog, settings, empty/loading/error state) and whenever a UI looks basic, boring, cluttered or "AI-generic". Covers design tokens, component priority, adding shadcn components (Phosphor + React 18 fixes), page recipes with code, states, the screenshot review loop (npm run ui:snapshot) and the quality checklist. Triggers: "buat ui", "buatkan halaman", "create a page", "design this screen", "make it look better", "dashboard", "form", "table", "settings page".
---

# UI Design Playbook (`apps/web`)

The always-on summary is `.claude/rules/web/ui-design.md`. This skill is the how-to. Where another
skill (design-system, slicing-ui, administrator, form, data-display …) shows markup, **the visual
rules here win**; those skills own folder placement, data flow and behavior.

---

## 1. The look we want

**Modern, minimal, calm, information-dense but airy.** Reference points: Linear, Vercel dashboard,
Stripe dashboard, shadcn/ui "blocks". Not: Bootstrap/AdminLTE, Material 2, glassmorphism, neon,
gradient-heavy landing pages.

What makes UI look *boring/basic* (avoid):

- Everything the same size and weight; no focal point; title indistinguishable from body.
- Raw HTML: native `<select>`, unstyled `<table>`, default buttons, `<ul>` dumps of data.
- Content floating on a blank canvas with no structure, or a single "Welcome, X" line as a page.
- Square boxes with hard borders around everything; cards in cards; no breathing room.
- No states: blank areas while loading, "No data" text, errors as plain red text.
- Random icons/colors sprinkled without meaning.

What makes UI look *good* (do):

- One page title + one-line description + one primary action, top-left aligned.
- Content grouped into a few surfaces (cards / table) with consistent padding and gaps.
- Muted secondary information (`text-muted-foreground`), strong primary information.
- Small, deliberate details: status badges with a dot, avatar initials, `tabular-nums`, kbd hints,
  relative times with full date in a tooltip, icons that carry meaning, subtle hover rows.
- Every async surface has skeleton / empty / error states that look designed.

---

## 2. Tokens (the only allowed visual values)

Defined in `src/styles/variable.css` (`:root` + `.dark`) and mapped to Tailwind in
`src/styles/tailwind.css`. Use the **shadcn semantic classes**:

| Purpose | Class |
|---|---|
| Page canvas | `bg-background` (main area may use `bg-muted/40` for subtle layering — see AppLayout) |
| Surface (card, table wrapper, dialog) | `bg-card text-card-foreground` |
| Subtle fill (hover rows, secondary buttons, inline code, skeleton) | `bg-muted`, `bg-accent` |
| Primary text / secondary text | `text-foreground` / `text-muted-foreground` |
| Borders / inputs / focus | `border-border` / `border-input` / `ring-ring` (`focus-visible:ring-[3px] ring-ring/50` comes with primitives) |
| Primary action | `bg-primary text-primary-foreground` (via `<Button>`) |
| Danger | `destructive` (via `<Button variant="destructive">`, `<Alert variant="destructive">`) |
| Status | `success`, `warning`, `info`, `destructive` → tinted: `bg-success/10 text-success` |
| Sidebar | `bg-sidebar`, `text-sidebar-foreground`, `bg-sidebar-accent` … |
| Charts | `chart-1` … `chart-5` (and the extended brand palettes, data-viz only) |

Radius: `rounded-md` (8px) controls · `rounded-lg` (10px) inner panels/tiles · `rounded-xl` (12px)
cards, table wrappers, dialogs, popovers, sheets · `rounded-full` avatars, dots, switches only.

Shadow: `shadow-xs` resting surfaces and outline controls · `shadow-md` dropdown/popover ·
`shadow-lg` dialog/sheet/toast. Nothing else.

Spacing (4px grid): `gap-1.5`/`gap-2` label↔control, `gap-4` between fields and items,
`gap-6` between cards/sections, `gap-8` between major page regions. Card padding `p-6`
(compact `p-4`). Page padding is owned by `AppLayout` — don't add your own outer padding.

Typography: body `text-sm`; page title `text-2xl font-semibold tracking-tight`; card title
`text-base font-semibold`; stat value `text-2xl font-semibold tabular-nums`; helper `text-sm
text-muted-foreground`; caption/overline `text-xs text-muted-foreground` (`font-medium` allowed).

Forbidden: raw hex/rgb/hsl, Tailwind palette colors (`gray-200`, `blue-600`), arbitrary values
(`text-[13px]`, `p-[18px]`, `rounded-[14px]`), inline `style` for visuals, legacy brand palettes in UI
chrome, `!important`.

To re-brand an app, change only the semantic variables in `variable.css` (`--primary`, `--ring`,
`--radius`, chart colors). Never restyle per component.

---

## 3. Component priority — shadcn first

1. **`src/components/ui/*`** — themed shadcn primitives. Check the folder first (`ls src/components/ui`).
2. **Install from shadcn** if it exists there: https://ui.shadcn.com/docs/components
   ```bash
   cd apps/web && npx shadcn@latest add <name> [<name> ...]   # no -y / --overwrite (see below)
   ```
   Then apply the **post-install checklist** (mandatory, the CLI output is not final):
   - [ ] **Never overwrite blindly:** do not pass `-y`/`--yes` or `--overwrite`. Many components pull in
         dependencies that already exist here (`button`, `dialog`, `input`, …), and overwriting replaces the
         themed, React 18 versions with stock shadcn. When the CLI asks to overwrite, answer **no**; if a
         file did change, diff it (`git diff src/components/ui` or against a backup copy) and restore the themed parts before accepting.
   - [ ] **Files landed in `src/components/ui/`:** the CLI resolves `@/` through the `paths` in
         `apps/web/tsconfig.json` (`"@/*": ["./src/*"]`, already configured) and `components.json`
         aliases. If you ever see a literal `apps/web/@/` folder, the alias was not resolved — move the
         files into `src/`, delete the folder and fix `tsconfig.json`/`components.json`.
   - [ ] **`cn` import:** the CLI may write `import { cn } from "cn"` and install a junk `cn` npm package.
         Change it to `import { cn } from '@/utils/cn'` and `npm uninstall cn` (check `package.json`).
         ESLint `no-restricted-imports` blocks `from 'cn'`.
   - [ ] **Radix imports:** use the unified `radix-ui` package
         (`import { Dialog as DialogPrimitive } from 'radix-ui'`, `Slot.Root` for `asChild`). Individual
         `@radix-ui/react-*` imports are blocked by ESLint (`@radix-ui/*` pattern); do not add those
         packages to `package.json`.
   - [ ] **Icons:** replace every `lucide-react` import with Phosphor `<i>` (map below); `lucide-react`
         must not appear in `package.json` (ESLint `no-restricted-imports` blocks it).
   - [ ] **React 18 refs:** this app runs React 18. Every component that renders a DOM element and may be
         used with `asChild`/as a trigger must use `React.forwardRef` (shadcn's current output is written
         for React 19 and passes `ref` as a prop — that silently breaks on 18). Mirror `button.tsx`.
   - [ ] **Tokens:** only semantic classes from §2; radius/shadow per §2. Remove `dark:` overrides that the
         tokens already handle.
   - [ ] Run `npm run typecheck && npm run lint`, then look at it (`npm run ui:snapshot`).
3. **Compose** from patterns in `src/components/common/` and `src/modules/data-table/` (§5).
4. **Hand-write** only static, behavior-less markup.

Never hand-build: dropdown menu, select, combobox, dialog, alert dialog, sheet/drawer, popover, tooltip,
tabs, accordion, checkbox, radio, switch, toggle group, date picker, command palette, toast.

### lucide → Phosphor map

| lucide | Phosphor class |
|---|---|
| `Check` | `ph ph-check` |
| `ChevronDown` / `ChevronUp` / `ChevronLeft` / `ChevronRight` | `ph ph-caret-down` / `-up` / `-left` / `-right` |
| `ChevronsUpDown` | `ph ph-caret-up-down` |
| `X` | `ph ph-x` |
| `Circle` (radio dot) | `ph-fill ph-circle` |
| `Search` | `ph ph-magnifying-glass` |
| `MoreHorizontal` / `MoreVertical` | `ph ph-dots-three` / `ph ph-dots-three-vertical` |
| `Loader2` | `ph ph-spinner animate-spin` |
| `Minus` / `Plus` | `ph ph-minus` / `ph ph-plus` |
| `ArrowLeft` / `ArrowRight` | `ph ph-arrow-left` / `ph ph-arrow-right` |
| `Calendar` | `ph ph-calendar-blank` |
| `PanelLeft` | `ph ph-sidebar-simple` |
| `GripVertical` | `ph ph-dots-six-vertical` |

Sizing: Phosphor `<i>` icons are 16px by default and `size-*` alone sets the glyph size
(`size-3` … `size-12`, global rule in `src/index.css`): `<i className="ph ph-check size-5" aria-hidden="true" />`.
No extra `text-*`/`leading-none` needed (an explicit `text-*` on the icon still wins). Keep the `[&_i]` /
`[&_svg]` sizing rules the primitives already use.

`Button` (`src/components/ui/button.tsx`): `variant` = `default` / `destructive` / `outline` / `secondary` /
`ghost` / `link`; `size` = `xs` / `sm` / `default` / `lg` / `icon` / `icon-xs` / `icon-sm` / `icon-lg`
(`md` is a deprecated alias of `lg` — don't use it in new code). `loading` shows an inline spinner (replacing
a leading `<i>` icon), disables the button and keeps its width — use it instead of hand-rolled spinners.
Icon-only buttons: `<Button size="icon" variant="ghost" aria-label="…">` wrapped in a `Tooltip`.

---

## 4. Available building blocks (check the code, it is the source of truth)

`src/components/ui/` — shadcn new-york primitives, React 18 `forwardRef`, Phosphor icons, Radix from the
unified `radix-ui` package: alert, alert-dialog, avatar, badge, breadcrumb, button (+ `loading` prop),
button-group, calendar, card (Header/Title/Description/**Action**/Content/Footer), checkbox, collapsible,
command, dialog, dropdown-menu, empty, field (layout: FieldSet/FieldGroup/Field/FieldLabel/FieldDescription/
FieldError), form (react-hook-form binding), hover-card, input, input-group, kbd, label, pagination,
popover, progress, radio-group, select, separator, sheet, sidebar (+ `SidebarInset`, `variant="inset"`),
skeleton, sonner, spinner, switch, table, tabs (`variant="default" | "line"`), textarea, toggle,
toggle-group, tooltip.

`src/components/common/` — domain-agnostic page patterns:

| Component | Use for |
|---|---|
| `PageHeader` | `title`, `description`, `actions`, `meta` (badge next to title), `back` `{to,label}`. Top of every page. |
| `StatCard` | KPI tile: `label`, `value` (`null` → "—", never invent), `icon`, `helper`, `delta {value, trend}`, `loading`. |
| `EmptyState` | Wraps shadcn `Empty`: `icon`, `title`, `eyebrow`, `description`, `action`; `variant` plain/dashed; `size` default/compact/full. |
| `SectionCard` | Titled card: `title`, `description`, `actions`, `footer`; `layout="split"` (settings), `flush`, `tone="destructive"` (danger zone). |
| `StatusBadge` | Dot + label on a tint: `tone` = `success` / `warning` / `destructive` / `info` / `neutral`. |
| `ConfirmDialog` | AlertDialog wrapper; controlled (`open`/`onOpenChange`) or `trigger`; async `onConfirm` shows a spinner and closes on resolve. |
| `RelativeTime` | "3 hours ago" with the full date in a tooltip (`utils/date-formatter` `formatRelativeTime`). |
| `ThemeToggle` | Header icon button → Light / Dark / System menu. |
| `LoadingState`, `FullScreenLoader`, `ErrorFallback`, `StatusScreen` | Region / app-boot loading and route-level error screens (StatusScreen is built on EmptyState). |

`src/modules/data-table/` — `DataTable` (TanStack Table + shadcn Table, one card containing
toolbar → table → pagination; props `columns`, `data`, `loading` → skeleton rows (`meta.skeleton` per
column), `fetching`, `error` slot, `emptyState`, `toolbar`, server `pagination` + `onPageChange` /
`onPageSizeChange`, server `sort {orderBy, order}` + `onSortChange`), `DataTableToolbar` (search with clear,
`filters`, `actions`), `DataTableColumnHeader` (sortable, `aria-sort`), `DataTablePagination` ("Showing 1–10
of 42", rows per page, first/prev/next/last), `DataTableRowActions` (`…` menu from an `actions` array). Use
it for every list; `features/administrator/user` is the reference implementation.

If a pattern you need is missing and is generic, add it to `components/common/` (or a `modules/`
folder) with a demo in the UI kit page (`src/pages/ui-kit/parts/*`) — don't inline one-off copies in features.

---

## 5. Page recipes

### 5.1 Every page

```tsx
export function ProjectsView() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Projects"
        description="Manage the projects your team is working on."
        actions={<Button><i className="ph ph-plus" aria-hidden="true" />New project</Button>}
      />
      {/* toolbar / tabs (optional) */}
      {/* content surfaces */}
    </div>
  )
}
```

### 5.2 Dashboard

- Row 1: 3–4 `StatCard`s (`grid gap-4 sm:grid-cols-2 xl:grid-cols-4`). Only real metrics — if there is
  no data source yet, show the card with `—` and a helper, never invented numbers.
- Row 2: primary visual (chart card, `xl:col-span-2`) + secondary list card (recent activity) in
  `grid gap-6 xl:grid-cols-3`.
- Optional row 3: table of recent items (DataTable, 5 rows, "View all" link in card header).

### 5.3 List / admin CRUD

```
PageHeader (title, count in description, primary "Add X" button)
DataTable — the one rounded-xl card (never wrap it in another Card):
  toolbar={<DataTableToolbar searchValue onSearchChange filters={…Selects} actions={…reset/refresh} />}
          search InputGroup with ph-magnifying-glass + clear (sm:max-w-xs)
  table:  header row bg-muted/50 text-xs font-medium; rows hover:bg-muted/50;
          first column = primary identity (avatar + name + muted email); status = StatusBadge;
          dates = RelativeTime (tooltip with full date); last column = DataTableRowActions (dots menu)
  states: loading → skeleton rows · fetching → dimmed rows · error={<Alert …Try again />} · emptyState={<EmptyState … />}
  footer: rendered by DataTable when pagination + onPageChange are passed (DataTablePagination, border-t):
          "Showing 1–10 of 42" · rows per page · page x of y · first/prev/next/last
```
Reference: `src/features/administrator/user/components/UserListView.tsx`.
Create/edit in a `Dialog` (≤ 6 fields) or `Sheet` (side panel, more fields) or a dedicated page (complex).
Delete → `ConfirmDialog` → toast via `sonner` on success/failure.

### 5.4 Form

```tsx
<form className="flex max-w-2xl flex-col gap-6">
  <div className="grid gap-4 sm:grid-cols-2">
    <FormField … /> {/* Label (text-sm font-medium) → Input → description/error (text-sm) */}
  </div>
  <div className="flex justify-end gap-2">
    <Button type="button" variant="outline">Cancel</Button>
    <Button type="submit" loading={isPending}>Save changes</Button>
  </div>
</form>
```
Settings pages: stack `SectionCard`s; on `lg` use a two-column section (left: title + description
`lg:w-1/3`, right: fields). Danger zone = last `SectionCard` with `border-destructive/30`, destructive
button, confirmation dialog. Validate with zod; show server errors on the right field.

### 5.5 Detail page

`PageHeader` with back link/breadcrumb + status badge + actions (primary + overflow dropdown) →
`Tabs` (Overview / Activity / Settings) → `SectionCard`s with definition lists
(`grid grid-cols-[max-content_1fr] gap-x-8 gap-y-3 text-sm`, terms muted).

### 5.6 Auth pages

Centered card `max-w-sm`, logo mark + app name above, title `text-xl font-semibold`, one-line muted
description, form, small muted footer links. Subtle background (`bg-muted/40`), no illustrations,
no gradients.

### 5.7 Empty / loading / error

- Loading: skeletons that mirror the final layout (table rows, stat cards) — not a page spinner.
  Buttons show an inline spinner and stay the same width.
- Empty: `EmptyState` with a relevant Phosphor icon in a `bg-muted rounded-lg size-10` tile, a title
  ("No projects yet"), a one-line hint and the primary action. Filtered-empty says what to clear.
- Error: `Alert variant="destructive"` with the API message (`ApiError.message`) and a Retry button;
  full-screen `StatusScreen` only for route-level failures.
- Success/failure of actions: `toast.success` / `toast.error` (sonner). No `alert()`.

---

## 6. Interaction & motion

- Hover: background shift (`hover:bg-muted/50` rows, `hover:bg-accent` menu items) — never scale/jump.
- Focus: `focus-visible:ring-[3px] ring-ring/50` (built into primitives). Never remove outlines.
- Transitions: `transition-colors` 150ms; overlays use the primitives' `data-[state]` animations.
  Respect `prefers-reduced-motion`.
- Disabled: `disabled:opacity-50 disabled:pointer-events-none` (built in).
- Clickable rows/cards need a real link/button inside (keyboard + screen reader accessible).

---

## 7. Copy

Sentence case everywhere ("Add user", not "Add User"/"ADD USER"). Short, specific labels. Buttons are
verbs. Descriptions are one line. No fabricated numbers, testimonials or marketing fluff inside the app
(see `reactjs-anti-slop`). Dates: relative ("3h ago") with absolute in a tooltip; use
`utils/date-formatter`.

---

## 8. Review loop (mandatory before you say "done")

```bash
cd apps/web
npm run ui:snapshot -- --route /administrator/user                        # light + dark, desktop + mobile PNGs
npm run ui:snapshot -- --route / --route /ui-kit --theme dark             # several routes / one theme
npm run ui:snapshot -- --route /administrator/user --state empty --state loading --state error
npm run ui:snapshot -- --route /administrator/user --viewport desktop --click "button:has-text('Add user')"  # open a dialog/menu first
npm run ui:snapshot -- --help
```
The script starts Vite on a free port (or uses `--url http://localhost:3000`), mocks `/api/v1/apps/**` with
the fixtures in `scripts/ui-snapshot/fixtures/*.json` (`{ "endpoint": "/x/get-all", "data": … }`; arrays are
served as paginated get-all lists with search/filter/sort; add one for your new endpoint), freezes the
clock to the `anchor` in `auth-me.json`, and writes full-height PNGs to
`apps/web/.ui-snapshots/<route>-<theme>-<viewport>[-<state>].png` (`--viewport-only` to crop). `/auth/*`
routes are captured signed out. **Open every PNG** (Read tool) and check:

- [ ] One clear title + primary action; obvious hierarchy within 2 seconds.
- [ ] Consistent radius (controls 8px, surfaces 12px), no square boxes, no pills.
- [ ] Neutral surfaces, one accent; status colors only on status.
- [ ] Even spacing on the 4px grid; aligned left edges; nothing cramped or floating.
- [ ] No native controls, no unstyled tables/lists, no cards inside cards, no double borders.
- [ ] Loading / empty / error states designed (snapshot them with `--state`).
- [ ] Dark mode equally polished (contrast, borders visible but quiet).
- [ ] Mobile (390px): no horizontal page scroll, toolbars wrap, tables scroll inside their card.
- [ ] Text: sentence case, no truncation of key info, `tabular-nums` for numbers.

Then `npm run typecheck && npm run lint && npm run test:ci`.

The UI kit page (`/ui-kit`, dev builds only — hidden route, not in the menu) renders every primitive and
pattern; snapshot it in both themes to see what exists before building, and add new patterns there.
