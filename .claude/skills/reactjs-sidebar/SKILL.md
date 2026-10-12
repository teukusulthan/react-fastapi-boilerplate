---
name: reactjs-sidebar
description: The apps/web sidebar — customized shadcn primitive in src/components/ui/sidebar.tsx (240px / 15rem, inset variant, icon-collapse, mobile sheet, persisted state) plus the config-driven AppSidebar/SidebarNavItem in src/components/layouts/. Covers styling via tokens, active state, header offset, collapse behavior, nested menus and common sidebar bugs. Load when changing sidebar look/behavior or fixing sidebar issues.
---

# Sidebar (React / TypeScript)

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md` win over any markup here. This skill owns sidebar behavior, structure, the header offset and menu rendering.

The sidebar is already built. Change it here:

| File | What it owns |
|---|---|
| `src/components/ui/sidebar.tsx` | Primitive (customized shadcn): `SidebarProvider` (open state persisted under `sidebar-state`, `Ctrl/⌘+B` shortcut, `--sidebar-width` CSS vars), `Sidebar` (`variant` `sidebar` \| `inset`; desktop fixed panel + in-flow gap spacer, mobile `Sheet`), `SidebarInset` (the main region; rounded inset panel when the sidebar is `variant="inset"`), `SidebarMenuButton` variants, `SidebarTrigger`, `useSidebar()`. Constants: `SIDEBAR_WIDTH = '15rem'` (240px), `SIDEBAR_WIDTH_MOBILE = '18rem'`, `SIDEBAR_WIDTH_ICON = '3.25rem'`. |
| `src/components/layouts/AppSidebar.tsx` | Which menus render, grouping (`buildMenuSections`), admin gating, mobile brand header, `PerfectScrollArea` around the content |
| `src/components/layouts/SidebarNavItem.tsx` | One entry: `SidebarMenuButton asChild` + `NavLink`, icon weight by active state, closes the mobile sheet on click |
| `src/components/layouts/AppHeader.tsx` | Hosts the `SidebarTrigger` (header is inside the same `SidebarProvider`) |
| `src/hooks/use-mobile.ts` | `useIsMobile()` (768px breakpoint) used by the primitive |
| `src/styles/variable.css` / `tailwind.css` | `--sidebar-*` tokens (`:root` + `.dark`) and `--color-sidebar-*` aliases → `bg-sidebar`, `border-sidebar-border`, `ring-sidebar-ring` |
| `src/config/menu/*` | The entries themselves (see `.claude/skills/reactjs-menu-config/SKILL.md`) |

Exports available from `@/components/ui/sidebar`: `Sidebar`, `SidebarContent`,
`SidebarFooter`, `SidebarGroup`, `SidebarGroupContent`, `SidebarGroupLabel`, `SidebarHeader`,
`SidebarInset`, `SidebarMenu`, `SidebarMenuBadge`, `SidebarMenuButton`, `SidebarMenuItem`,
`SidebarMenuSkeleton`, `SidebarMenuSub`, `SidebarMenuSubButton`, `SidebarMenuSubItem`,
`SidebarProvider`, `SidebarSeparator`, `SidebarTrigger`, `useSidebar`. There is **no**
`SidebarRail`. `AppLayout` renders the main region as `SidebarInset` (see
`.claude/skills/reactjs-app-layout/SKILL.md`).

## Current AppSidebar (real)

```tsx
export default function AppSidebar() {
  const user = useAuthStore((state) => state.user)
  const canAdminister = hasAccess(user, { roles: ADMIN_ROLES })

  const sections = useMemo(() => buildMenuSections(canAdminister ? [...APP_MENU, ...ADMINISTRATOR_MENU] : APP_MENU, MENU_GROUP_LABEL), [canAdminister])

  return (
    <Sidebar variant="inset" collapsible="icon" className="top-12 h-[calc(100svh-3rem)]">
      <SidebarHeader className="h-12 justify-center border-b px-4 md:hidden">
        <AppBrand />
      </SidebarHeader>
      <SidebarContent>
        <PerfectScrollArea className="h-full" contentClassName="flex flex-col gap-1 pt-1 pb-4">
          {sections.map((section) => (
            <SidebarGroup key={section.id}>
              <SidebarGroupLabel>{section.label}</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {section.items.map((item) => (
                    <SidebarNavItem key={item.id} item={item} />
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          ))}
        </PerfectScrollArea>
      </SidebarContent>
    </Sidebar>
  )
}
```

`buildMenuSections` (`src/utils/menu.ts`): consecutive top-level entries of the same `group` form one
section labelled by `MENU_GROUP_LABEL[group]`; a top-level entry with children becomes its own section
labelled by its `display` (e.g. the `qeuln` "Administrator" parent).

## Rules

- MUST keep shadcn/Radix behavior (`SidebarProvider`, `asChild`, `data-*` attributes,
  focus ring, `Sheet` on mobile); restyle via tokens and the `cva` strings in `sidebar.tsx`,
  not by replacing the primitive.
- MUST render navigation from `src/config/menu/*` via `buildMenuSections()` / `buildMenuTree()`; no local arrays.
- MUST keep the desktop panel offset below the `h-12` header: `top-12 h-[calc(100svh-3rem)]`
  on `<Sidebar>`. The primitive's gap spacer reserves the width in the flex row, so main
  content never sits under the fixed panel.
- MUST wrap scrollable sidebar content in `PerfectScrollArea` (not `overflow-auto`).
- MUST use `SidebarMenuButton asChild` with the `NavLink` inside (never `<NavLink>` around a
  `<button>`), and pass `isActive` computed with `isMenuPathActive()`.
- MUST pass `tooltip={item.display}` so collapsed (icon) mode stays usable.
- MUST close the mobile sheet after navigation (`isMobile && setOpenMobile(false)`).
- MUST use Phosphor icons via `renderIcon()`; no icon packages.
- Sidebar width changes go in `SIDEBAR_WIDTH` (one place) — the shell reads `--sidebar-width`.
- Collapsed-state visuals: rely on the primitive's `group-data-[collapsible=icon]:*`
  classes (already in `sidebarMenuButtonVariants`) or `useSidebar().state === 'collapsed'`.

## Styling

Tokens (both themes defined in `variable.css`):

```css
--sidebar, --sidebar-foreground, --sidebar-primary, --sidebar-primary-foreground,
--sidebar-accent, --sidebar-accent-foreground, --sidebar-border, --sidebar-ring
```

Menu button look lives in `sidebarMenuButtonVariants` (`src/components/ui/sidebar.tsx`) —
read the file for the exact strings. Target look (playbook §2): items `h-9 rounded-md px-2.5 text-sm`,
inactive `text-sidebar-foreground/80`, hover `bg-sidebar-accent text-sidebar-accent-foreground`,
active `bg-sidebar-accent text-sidebar-accent-foreground font-medium` (icon may take
`text-primary`), `focus-visible:ring-2 ring-sidebar-ring`. Group labels `text-xs font-medium
text-muted-foreground`. No square edge bars, no saturated fills for the active item. Change these
strings to restyle every item; don't override per item in `SidebarNavItem`. If the file still uses
legacy aliases (`text-font-*`, `bg-background-*`, `*-primary-base`), migrate them to the semantic
`sidebar-*` classes when you touch it.

## Recipes

### Nested (multi-level) items

`buildMenuTree()` returns one level of children. To render children under a navigable parent
instead of as a labelled group, use `SidebarMenuSub` / `SidebarMenuSubItem` /
`SidebarMenuSubButton asChild` in `AppSidebar.tsx`, and keep the parent row navigable:

```tsx
// ✅ parent navigates; a separate chevron button toggles the sub-list
<SidebarMenuItem>
  <SidebarMenuButton asChild isActive={isMenuPathActive(parent.path, pathname)} tooltip={parent.display}>
    <NavLink to={parent.path}>{renderIcon({ icon: parent.icon })}<span>{parent.display}</span></NavLink>
  </SidebarMenuButton>
  <button type="button" aria-label={`Toggle ${parent.display}`} aria-expanded={open} onClick={() => setOpen((v) => !v)}
          className="absolute top-1.5 right-1 rounded-md p-1 text-muted-foreground hover:bg-sidebar-accent group-data-[collapsible=icon]:hidden">
    <i className={open ? 'ph ph-caret-up' : 'ph ph-caret-down'} aria-hidden="true" />
  </button>
  {open && (
    <SidebarMenuSub>
      {parent.children.map((child) => (
        <SidebarMenuSubItem key={child.id}>
          <SidebarMenuSubButton asChild isActive={isMenuPathActive(child.path, pathname)}>
            <NavLink to={child.path}>{child.display}</NavLink>
          </SidebarMenuSubButton>
        </SidebarMenuSubItem>
      ))}
    </SidebarMenuSub>
  )}
</SidebarMenuItem>
```

Put the open/closed state in a small component in `src/components/layouts/` (one component
per file), not in a store.

### Parent path that should land on a child

The router handles it — e.g. `admin.routes.tsx` has `{ index: true, element: <Navigate to="user" replace /> }`.
If children can be hidden by config, redirect to the first **visible** child from
`buildMenuTree(...)` instead of a hardcoded child.

### Footer items (settings, help)

Add a `SidebarFooter` inside `<Sidebar>` after `<SidebarContent>`, rendering entries from
a menu array (e.g. a new `group: 'application'` entry filtered in `AppSidebar`), not
hardcoded links.

## Common bugs

| Symptom | Cause → fix |
|---|---|
| Sidebar covers the header | `top-12 h-[calc(100svh-3rem)]` missing on `<Sidebar>` |
| Content slides under the panel | Custom wrapper removed the primitive's `sidebar-gap` div — keep the primitive's desktop markup |
| Transparent sidebar | `--sidebar*` tokens missing in `variable.css` (`:root` or `.dark`) or aliases missing in `tailwind.css` |
| `<a>` inside `<button>` warning | `SidebarMenuButton` without `asChild` |
| Active item not highlighted for nested URLs | Use `isMenuPathActive(item.path, pathname)`, not strict equality |
| "/" highlighted everywhere | `NavLink end={item.path === '/'}` + `isMenuPathActive` (exact for `/`) |
| Mobile sheet stays open after click | Missing `setOpenMobile(false)` in the link `onClick` |
| Admin section visible to normal users | Admin tree must be built only when `hasAccess(user, { roles: ADMIN_ROLES })` |
| `useSidebar must be used within SidebarProvider` | Component rendered outside `AppLayout`'s `SidebarProvider` |

## Checklist

- [ ] Entries come from `src/config/menu/*`; admin entries gated by `ADMIN_ROLES`
- [ ] `<Sidebar variant="inset" collapsible="icon" className="top-12 h-[calc(100svh-3rem)]">` kept; main stays `SidebarInset`
- [ ] Content wrapped in `PerfectScrollArea`
- [ ] `SidebarMenuButton asChild` + `isActive` + `tooltip`
- [ ] Styling via semantic `sidebar-*` tokens / `sidebarMenuButtonVariants`, `rounded-md` items, no hex colors or legacy aliases
- [ ] Works collapsed (icons + tooltips), expanded, and on mobile (sheet)
- [ ] `npm run typecheck && npm run lint && npm run test:ci` (apps/web) pass
