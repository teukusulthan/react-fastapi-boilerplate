# Architecture — Rules & PR Checklist

Companion to [../SKILL.md](../SKILL.md). Paths are relative to `apps/web/`.

## Folder rules

### ✅ Allowed

| Location | Contents |
|---|---|
| `src/pages/{area}/{Name}Page.tsx` | Route entry, composition only, default export |
| `src/features/{domain}/{feature}/…` | Domain components, hooks, constants, config, schemas, utils, types, store + `index.ts` barrel |
| `src/features/{domain}/components/` | Domain components shared by 2+ features of the same domain |
| `src/features/shared/{feature}/` | Cross-domain business features (real: `shared/auth`) |
| `src/components/ui/` | shadcn/Radix primitives bound to the active design tokens |
| `src/components/common/` | Domain-agnostic page patterns and composites (`PageHeader`, `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`, `ConfirmDialog`, loading/error states, pagination) |
| `src/components/layouts/` | App shell: `AppLayout`, `AppHeader`, `AppSidebar`, `SidebarNavItem`, `AuthLayout` |
| `src/components/wrappers/` | Providers and 3rd-party adapters: `AppProviders`, `PerfectScrollArea` (+ chart/map wrappers when created) |
| `src/modules/{name}/` | Generic systems with own state/fetching reused by 2+ features (reference: `src/modules/data-table/`) |
| `src/services/` | `api-client.ts`, `api-error.ts`, `api-endpoints.ts`, `api-factory*.ts`, `{resource}.service.ts` |
| `src/stores/` | Global Zustand stores |
| `src/hooks/` | Cross-domain hooks |
| `src/lib/` | Library singletons (`query-client.ts`) |
| `src/types/` | Global ambient types (`*.d.ts`, types only) |
| `src/utils/` | Pure helpers |
| `src/config/` | `env.ts`, `constants.ts`, `theme-config.ts`, `menu/*` |
| `src/styles/` | `variable.css`, `tailwind.css`, `components.css` |
| `src/routes/` | `index.tsx`, `*.routes.tsx`, `guards/` |
| `src/test/` | vitest setup and test helpers |
| `src/schemas/` *(create on demand)* | zod schemas shared by 2+ domains |
| `src/assets/` *(create on demand)* | Images/SVGs imported from TS (processed by Vite) |
| `public/` | Files served as-is: `favicon.ico`, `manifest.json`, `robots.txt`, `images/*` |

### ❌ Not allowed

| Rule | Why |
|---|---|
| Domain components anywhere under `src/components/` | `components/` is domain-agnostic; use `features/` |
| A new subfolder in `src/components/` for a feature/page | Same reason |
| Fetching logic in components/pages | Services + TanStack Query hooks only |
| `hooks/` or helper code inside `src/pages/` | Co-locate in the owning feature |
| Importing a feature's internals (`@/features/x/y/hooks/…`) from outside the feature | Import the barrel `@/features/x/y` |
| Cross-imports between pages | Share through features/stores |
| Runtime code (functions, consts, classes) in `src/types/*.d.ts` | Ambient declaration files are types only |
| `ApiError` or other runtime classes in `types/` | It lives in `src/services/api-error.ts` |
| Reading `import.meta.env` outside `src/config/env.ts` | Env is validated once there |
| Schemas inside component files, `utils/` or `types/` | `features/…/schemas/` or `src/schemas/` |
| Files directly in `src/` (except `main.tsx`, `index.css`, `vite-env.d.ts`) | Keep the root navigable |

## Naming

| Type | Convention | Example |
|---|---|---|
| Component | `PascalCase.tsx` | `UserStatusBadge.tsx` |
| shadcn primitive | `kebab-case.tsx` | `components/ui/button-group.tsx` |
| Page | `PascalCase` + `Page` | `LoginPage.tsx` |
| Global hook file | `use-kebab.ts` | `hooks/use-debounced-value.ts` |
| Feature hook file | `useCamel.ts` | `hooks/useUserListQuery.ts` |
| Service | `{resource}.service.ts` | `permission.service.ts` |
| Store | `use{Name}Store.ts` | `useThemeStore.ts` |
| Routes | `{area}.routes.tsx` | `auth.routes.tsx` |
| Schema | `{name}.schema.ts` | `login.schema.ts` |
| Menu | `{area}.menu.ts` | `app.menu.ts` |
| Models / API types | `PascalCase` | `UserDetail`, `ApiList<T>` |
| Payload interfaces | `I` prefix | `IGroupCreatePayload` |
| Form value types | `T` prefix | `TLoginFormValues` |
| Constants | `UPPER_SNAKE_CASE` | `PAGE_SIZE_OPTIONS` |

No abbreviations (`usrMgmt`), no spaces, English only, one component per file.

## TypeScript

`tsconfig.app.json` has `strict`, `noUnusedLocals`, `noUnusedParameters`; ESLint enforces
`no-explicit-any`, `consistent-type-imports` (inline `type` imports) and
`react-hooks/exhaustive-deps`.

- Use `unknown` + narrowing (or zod `.parse`) instead of `any` / blind `as` casts.
- `as const` for constant arrays/objects (`USER_SEARCH_FIELDS`, query-key factories).
- Derive types (`Pick`, `Omit`, `Partial`, `z.infer`) instead of duplicating shapes.
- API response types come from `src/types/api.d.ts` (`ApiEnvelope<T>`, `ApiList<T>`) and
  `src/types/models.d.ts`; services return unwrapped data (`T` or `{ items, pagination }`).
- `@ts-expect-error` only with an explanatory comment; no non-null `!` without a check.

```ts
// ✅ typed service call (services return unwrapped data; errors are ApiError)
import { userService } from '@/services/user.service'
import type { UserDetail } from '@/types/models'

const user: UserDetail = await userService.getOne({ id })
```

## Import order

Enforced by Prettier/ESLint conventions in the codebase: third-party packages, blank line,
`@/…` imports, blank line, relative imports (`../`, `./`). Type-only imports use
`import type` / inline `type`.

## PR checklist

- [ ] Every new file sits in the location from the SKILL table; no domain code in `src/components/`
- [ ] Pages are composition-only; features are imported via their barrel
- [ ] New navigable route wired in `src/routes/` **and** `src/config/menu/`
- [ ] Fetching goes through a service + TanStack Query hook; errors handled as `ApiError`
- [ ] No `import.meta.env` outside `config/env.ts`; new env keys added to the zod schema and `env/.env.example`
- [ ] No hex colors in classes/styles; shadcn semantic token classes (`bg-card`, `text-muted-foreground`, `border-border`…) per `reactjs-ui-design` §2
- [ ] Bounded scroll regions use `PerfectScrollArea`
- [ ] Naming follows the table above
- [ ] `npm run typecheck`, `npm run lint`, `npm run test:ci` (apps/web) — or `npm run ci` at the root — pass
