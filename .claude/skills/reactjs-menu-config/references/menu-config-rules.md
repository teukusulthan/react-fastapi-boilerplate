# Menu Config — Rules & Constraints

Companion to [../SKILL.md](../SKILL.md). Files: `apps/web/src/config/menu/{app,administrator}.menu.ts`
+ `index.ts`; type `apps/web/src/types/menu.d.ts`.

## 1. One array per navigation surface

| Array | File | Rendered by |
|---|---|---|
| `APP_MENU` | `app.menu.ts` | `AppSidebar` "Menu" group (every signed-in user) |
| `ADMINISTRATOR_MENU` | `administrator.menu.ts` | `AppSidebar` admin sections (only `ADMIN_ROLES` / superusers) |
| `ALL_MENUS()` | `index.ts` | `usePageTitle`, future search/permission tooling |

A new surface = a new `*.menu.ts` file + export in `index.ts` + spread in `ALL_MENUS()` +
rendering code in `AppSidebar.tsx`.

## 2. Unique ids

- 5–7 random lowercase alphanumerics (`xk9qp`), unique across `ALL_MENUS()` and the reserved
  table in the SKILL. ❌ `'admin-user-menu'`, `'user'`.

## 3. Parent/child

- Top level: `idParent: ''`. Children: `idParent` = an existing id in the **same** array.
- `buildMenuTree()` renders one level of children; deeper nesting is ignored.
- A hidden/disabled parent hides its children.

## 4. Paths

- `path` = full route path registered in `src/routes/` (`/administrator/user`, not `user`).
- Wire route and menu in the same change.

## 5. Privileges (metadata)

```ts
privileges: [
  { label: 'View', value: 'view', description: '…', type: 'administrator' },
  { label: 'Create & Update', value: 'create_update', description: '…', type: 'administrator' },
  { label: 'Delete', value: 'delete', description: '…', type: 'administrator' },
]
```

- `value` in `snake_case`; `type: 'administrator'` in `ADMINISTRATOR_MENU`.
- `null` = no privilege catalogue (e.g. Dashboard, section headers).
- These are **not** checked at runtime. Real access control: `RoleGuard`
  (`allowedRoles` = permission aliases, `requiredPrivileges` = backend privilege strings
  such as `user:write`) and the backend RBAC.

## 6. `additional`

Required on every rendered entry; exactly these keys (`IMenuAdditional`):

```ts
additional: {
  container: 'full',        // 'boxed' | 'full' | 'fluid'
  iconType: 'phosphor',     // 'phosphor' | 'svg-code' (trusted SVG only)
  iconStyle: 'regular',     // 'regular' | 'fill' | 'bold' | 'light' | 'duotone'
  iconStyleActive: 'fill',
  mainPage: false,          // true on at most one entry per array
  redirectToEnabled: false,
  redirectTo: '',
}
```

❌ `iconType: 'lucide'`, ❌ `iconStyle: 'solid'`/`'thin'` (thin is not bundled), ❌ extra keys
not declared in `types/menu.d.ts`.

## 7. Icons

`icon` is a Phosphor slug in kebab-case (`chart-line-up`), rendered by `renderIcon()`
(`src/utils/icon-renderer.tsx`). ❌ React component names (`ChartLineUp`).

## 8. `ALL_MENUS` is a function

```ts
const menus = ALL_MENUS()   // ✅
const menus = ALL_MENUS     // ❌
```

## Definition of done

- [ ] id unique and recorded in the SKILL's reserved table
- [ ] `idParent` valid in the same array
- [ ] `path` equals a registered route
- [ ] all `IMenu` fields present; `additional` complete and valid
- [ ] `seo.title` set (page title)
- [ ] route protected with `RoleGuard` if it needs access control (menu privileges don't protect anything)
- [ ] `npm run typecheck && npm run test:ci` (apps/web) pass
