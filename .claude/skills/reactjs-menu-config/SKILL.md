---
name: reactjs-menu-config
description: Navigation source of truth for apps/web — APP_MENU / ADMINISTRATOR_MENU in src/config/menu/*.menu.ts (IMenu type in src/types/menu.d.ts), how AppSidebar renders them (buildMenuTree, isMenuPathActive, renderIcon), how usePageTitle derives document.title from seo.title, and the reserved menu-ID table. Load when adding/removing/changing a menu entry, wiring a new page into navigation, or picking a menu id.
---

# Menu Config

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md` win over any markup here. This skill owns menu data (`IMenu` entries, IDs, paths, icons, `seo.title`); sidebar look lives in `reactjs-sidebar`.

Every navigable page has exactly one menu entry; the sidebar and the browser title are
derived from it. Layout components never hold their own nav arrays.

## Files

```
apps/web/src/
├── config/menu/
│   ├── app.menu.ts            ← APP_MENU: primary navigation for every signed-in user
│   ├── administrator.menu.ts  ← ADMINISTRATOR_MENU: /administrator/* (rendered only for ADMIN_ROLES)
│   └── index.ts               ← re-exports + ALL_MENUS() (function)
├── types/menu.d.ts            ← IMenu, IMenuAdditional, IPrivilege, IMenuNode
├── utils/menu.ts              ← buildMenuTree(), isMenuPathActive(), formatPageTitle()
├── hooks/use-page-title.ts    ← usePageTitle(override?)
└── components/layouts/
    ├── AppSidebar.tsx         ← renders APP_MENU + ADMINISTRATOR_MENU trees
    └── SidebarNavItem.tsx     ← one entry (NavLink + renderIcon)
```

Always read the live files before editing — the tables below are snapshots.

## Entry shape (`IMenu`, real example)

```ts
// src/config/menu/app.menu.ts
import type { IMenu } from '@/types/menu'

export const APP_MENU: IMenu[] = [
  {
    id: 'dk7f2q',            // unique across ALL_MENUS(), 5–7 random alphanumerics
    idParent: '',            // '' = top level, else the id of a parent in the SAME array
    display: 'Dashboard',    // label in the sidebar
    name: 'dashboard',       // kebab-case identifier
    path: '/',               // must equal a route path in src/routes/
    show: true,              // false = hidden from navigation (still routable)
    search: true,
    enabled: true,           // false = removed from navigation
    group: 'data',           // 'data' | 'system' | 'organization' | 'workspace' | 'application'
    type: 'menu',
    icon: 'squares-four',    // Phosphor slug (kebab-case)
    seo: { title: 'Dashboard', description: '' },
    privileges: null,
    additional: {
      container: 'full',     // 'boxed' | 'full' | 'fluid'
      iconType: 'phosphor',  // 'phosphor' | 'svg-code'
      iconStyle: 'regular',  // weight when inactive: regular | fill | bold | light | duotone
      iconStyleActive: 'fill',
      mainPage: true,        // one landing entry per array
      redirectToEnabled: false,
      redirectTo: '',
    },
  },
]
```

`tactical?: boolean` is also allowed by the type (flag for operational/tactical menus).
`IMenuAdditional` has exactly the seven keys above — don't add ad-hoc keys
(`iconCode`, `enableIframe`, `menuBgColorTheme`…) without extending `src/types/menu.d.ts`.

### What the app actually consumes

| Field | Consumed by |
|---|---|
| `id`, `idParent`, `show`, `enabled` | `buildMenuTree()` — top-level visible entries + their visible children (one level) |
| `display`, `path`, `icon`, `additional.iconType/iconStyle/iconStyleActive` | `SidebarNavItem` (`NavLink`, `renderIcon`, tooltip when collapsed) |
| `seo.title` | `usePageTitle()` → `document.title = "<seo.title> — <VITE_APP_NAME>"` |
| `privileges` | Metadata only (privilege catalogue for an admin UI). **Not enforced** — access is enforced by `RoleGuard` in routes and by the backend. |
| `name`, `search`, `group`, `type`, `container`, `mainPage`, `redirectTo*`, `tactical` | Metadata for future features (search, layouts); keep them filled consistently |

## How the sidebar renders

- `APP_MENU` → one "Menu" group of `SidebarNavItem`s.
- `ADMINISTRATOR_MENU` → only when `hasAccess(user, { roles: ADMIN_ROLES })`
  (`ADMIN_ROLES` in `src/config/constants.ts`; superusers `admin`/`owner` always pass). A
  top-level entry with children renders as a labelled group (`Administrator` → `Users`);
  a top-level entry without children renders as a single item.
- Active state: `isMenuPathActive(item.path, pathname)` — exact match or nested below the
  path (`/` only matches exactly).

## Adding a menu entry

1. Add the route first (see `.claude/skills/reactjs-app-layout/SKILL.md`). The menu
   `path` must be the full URL path of that route (`/administrator/role`).
2. Pick a new id: random 5–7 lowercase alphanumerics, not used in `ALL_MENUS()` and not in
   the reserved table below. Never semantic ids (`'admin-user'`).
3. Append the entry to the right array:
   - normal page → `APP_MENU`
   - `/administrator/*` page → `ADMINISTRATOR_MENU` with `idParent: 'qeuln'`, `group: 'system'`
4. Set `seo.title` (≤ 60 chars) — it becomes the page title.
5. If you add a new top-level menu array (e.g. `MANAGER_MENU`): new file
   `src/config/menu/manager.menu.ts`, export it from `index.ts`, include it in
   `ALL_MENUS()`, and render it in `AppSidebar.tsx` (with its own access check).

```ts
// ADMINISTRATOR_MENU child (shape of the real 'Users' entry)
{
  id: 'znhzx', idParent: 'qeuln', display: 'Roles', name: 'administrator-role',
  path: '/administrator/role', show: true, search: true, enabled: true,
  group: 'system', type: 'menu', icon: 'identification-badge',
  seo: { title: 'Roles', description: 'Manage roles' },
  privileges: [
    { label: 'View', value: 'view', description: 'List and view roles', type: 'administrator' },
    { label: 'Create & Update', value: 'create_update', description: 'Create and edit roles', type: 'administrator' },
    { label: 'Delete', value: 'delete', description: 'Delete roles', type: 'administrator' },
  ],
  additional: { container: 'full', iconType: 'phosphor', iconStyle: 'regular', iconStyleActive: 'fill',
                mainPage: false, redirectToEnabled: false, redirectTo: '' },
}
```

## Page title

```ts
// src/hooks/use-page-title.ts (real)
export function usePageTitle(override?: string): void {
  const { pathname } = useLocation()
  useEffect(() => {
    const menu = ALL_MENUS().find((item) => item.path === pathname)
    document.title = formatPageTitle(override ?? menu?.seo.title, env.app.name)
  }, [pathname, override])
}
```

- Called once per layout (`AppLayout`, and `AuthLayout` with an override) — never in pages.
- App name comes from `env.app.name` (`VITE_APP_NAME`, default `App`) via `src/config/env.ts`.
- Routes without a matching menu path fall back to the app name.

## Rules

- MUST keep `id` unique across all arrays and outside the reserved table.
- MUST keep `idParent` within the same array.
- MUST make `path` equal to a registered route; wire route + menu in the same change unless the task explicitly says the route is hidden/redirect/modal/callback-only.
- MUST use Phosphor slugs and valid weights; `svg-code` only for trusted, developer-authored SVG.
- MUST call `ALL_MENUS()` as a function.
- MUST NOT hardcode navigation arrays in layout/header/sidebar components.
- MUST NOT rely on menu `privileges` for security — protect routes with `RoleGuard` (`.claude/skills/reactjs-auth-guard/SKILL.md`).
- Disable an entry with `enabled: false` (or `show: false` to keep it routable but hidden) rather than deleting history-relevant ids.

## Reserved menu IDs

**In this boilerplate:**

| id | array | display | path |
|---|---|---|---|
| `dk7f2q` | APP_MENU | Dashboard | `/` |
| `qeuln` | ADMINISTRATOR_MENU | Administrator (section) | `/administrator` |
| `4sbm5a` | ADMINISTRATOR_MENU (child of `qeuln`) | Users | `/administrator/user` |

**Reserved for the product family** (pages that don't exist in the boilerplate yet; when
you build one of them, reuse its id; never reuse these ids for something else):

| id | display | path |
|---|---|---|
| `vgoif` | Licenses | `/about/licences` |
| `a62da` | Devices | `/administrator/device` |
| `aga7js` | Team | `/administrator/team` |
| `hs45k2` | Member | `/administrator/member` |
| `xkqwe` | Case Type | `/administrator/case-type` |
| `7hsda` | Poi | `/administrator/poi` |
| `akjss` | Marker | `/administrator/marker` |
| `asfac` | Catalog | `/administrator/catalog` |
| `ne5zz` | Topic | `/administrator/topic` |
| `ljshed` | Account Management | `/administrator/sc-account` |
| `2gg7b` | Topic Comparison | `/administrator/topic-comparison` |
| `bq2as` | Indicator | `/administrator/indicator` |
| `bd5ks` | Survey Management | `/administrator/survey-management` |
| `4sbm5` | User Activity | `/administrator/user-activity` |
| `znhzx` | Role | `/administrator/role` |
| `36uhy` | Group | `/administrator/group` |
| `rjer3` | Connection | `/administrator/connection` |
| `ns306` | Connection Group | `/administrator/connection-group` |
| `c7eic` | Permission | `/administrator/permission` |
| `seypi` | Workspace | `/administrator/workspace` |
| `hckwq` | Workspace Settings | `/administrator/workspace-settings` |
| `joskkeq` | Organization | `/administrator/organization` |
| `joskke` | Organization Member | `/administrator/organization-member` |
| `xdvad` | System Settings | `/administrator/system-settings` |
| `a7f3d` | Organizations (manager) | `/organization` |
| `02no1` | My Profile | `/settings/profile` |
| `xbzpn` | Plugins | `/plugins` |
| `ryvow` | Build | `/build` |
| `aksdj` | Management Data | `/management/data` |
| `dvfjb` | AI Tools | `/ai` |
| `ygxrt` / `4om4y` | Application(s) | `/apps` |
| `rdtzv` | Visualization | `/visualization` |
| `g1n2r` `af23g` `12afs` `v63ro` `e5h8j` `k2l7m` `68knd` `c9d6f` `h7t9y` | Organization settings children | `/settings/organization/*` |
| `kjunv` `vpikf` `gbais` `sfdoh` | Plugin children | `/plugins/*` |
| `eqmyi` `olsqg` `cnrcl` `ihuml` `gypan` `bxtebq` `uqgfg` `pegtl` `bxteb` `ibdft` `5dxob` | Build children | `/build/*` |
| `je87x` `jelgx` `jegxw` `hzkvf` `tlhvh` `kelgx` `jlmnx` `csgsc` `nqavo` | AI tools children | `/ai/*` |
| `otkde` | Computer Vision | `/management/data/cctv` |
| `officer` `offender-registry` `program-assignment` `nonca` `nonca1` | legacy semantic ids | — |

When you add an id, add it to the first table.

## Checklist

- [ ] Route exists and `path` matches it exactly
- [ ] New id unique (checked `ALL_MENUS()` + reserved table) and added to the table above
- [ ] `idParent` valid in the same array; admin pages are children of `qeuln`
- [ ] `seo.title` set; `additional` complete with valid Phosphor weights
- [ ] Sidebar shows the entry for the intended users; the title updates on navigation
- [ ] `npm run test:ci` (covers `utils/menu.test.ts`) and `npm run typecheck` pass

Detailed rules: [references/menu-config-rules.md](references/menu-config-rules.md)
