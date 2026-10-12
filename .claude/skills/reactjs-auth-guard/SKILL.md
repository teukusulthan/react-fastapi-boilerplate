---
name: reactjs-auth-guard
description: How route protection works in apps/web and how to configure it — AuthGuard (session bootstrapped from GET /auth/me), GuestGuard (guest-only pages + safe post-login redirect), RoleGuard (roles/privileges, 403 rendered in place). Covers protecting new routes, admin-only routes, privilege checks, and running without login.
---

# Auth Guard Skill (React / TypeScript)

## How auth works (read first)

- The backend sets **httpOnly cookies** (`token`, `refresh_token`). JavaScript never sees or stores a
  token — there is **no token in any store**.
- `src/stores/useAuthStore.ts` (zustand, **not persisted**) mirrors the session:
  `status: 'unknown' | 'authenticated' | 'anonymous'`, `user: UserProfile | null`,
  `endReason: 'logout' | 'expired' | null`, `setUser(user)`, `clearSession(reason?)`.
- On app start the status is `unknown`. The guards call `useSession()`
  (`src/features/shared/auth/hooks/useSession.ts`), which runs `GET /auth/me` once (TanStack Query key
  `AUTH_QUERY_KEYS.me`) and calls `setUser` (200) or `clearSession('expired')` (401). Network/5xx errors
  leave the status `unknown` and expose `error` + `retry`.
- The API client refreshes on 401 (`POST /auth/refresh`, single-flight). If refresh is rejected it calls
  `endClientSession()` → store `anonymous` + `queryClient.clear()` → AuthGuard redirects to login.
- Logout: `useLogout()` → `POST /auth/logout` then `endClientSession('logout')` (redirect to plain `/auth/login`).

## The guards (`src/routes/guards/`)

| Guard | Use for | Behaviour |
|---|---|---|
| `AuthGuard` | every authenticated route (wraps `AppLayout` in `main.routes.tsx`) | `unknown` → `<FullScreenLoader>`; transient error → `<ServerUnavailable onRetry>`; `anonymous` → `<Navigate to="/auth/login?redirect=<current path>">` (no redirect param after a deliberate logout); `authenticated` → `children ?? <Outlet />` |
| `GuestGuard` | guest-only pages (`/auth/login`, future register / forgot-password) | `authenticated` → `<Navigate to={getSafeRedirect(?redirect)}>` (same-origin path only, never `/auth/*`, default `/`) — this is where the post-login redirect happens |
| `RoleGuard` | role/privilege-restricted sections; must be **inside** AuthGuard | `allowedRoles?: readonly string[]` (permission alias, e.g. `ADMIN_ROLES`), `requiredPrivileges?: readonly string[]` (all required); superusers (`SUPERUSER_ROLES` = admin, owner) always pass; denied → renders `<ForbiddenPage />` **in place** (URL kept, no redirect) |

All three render `children` when given, else `<Outlet />`, so they work as wrapper elements or as layout routes.

Access logic lives in `hasAccess(user, { roles, privileges })` / `isSuperuser(user)`
(`src/features/shared/auth/utils/access.ts`, exported from `@/features/shared/auth`). Use the same helper to
hide UI (e.g. `AppSidebar` hides the Administrator section). Client checks are UX only — the backend
enforces RBAC (403 `PERMISSION_ERROR`).

---

## Scenario A — Protect a new page

Authenticated pages are children of the `/` route in `src/routes/main.routes.tsx`, which is already wrapped
in `AuthGuard` — just add the child route (and its menu entry, see `.claude/skills/reactjs-menu-config/SKILL.md`):

```tsx
const ReportsPage = lazy(() => import('@/pages/reports/ReportsPage'))

const mainRoutes: RouteObject[] = [
  {
    path: '/',
    element: (
      <AuthGuard>
        <AppLayout />
      </AuthGuard>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'reports', element: <ReportsPage /> },   // ← new, protected by the parent AuthGuard
      ...adminRoutes,
    ],
  },
]
```

Do not wrap individual children in another `AuthGuard`.

## Scenario B — Role / privilege restricted section

Use `RoleGuard` as a layout route. Real example — `src/routes/admin.routes.tsx`:

```tsx
const adminRoutes: RouteObject[] = [
  {
    path: 'administrator',
    element: <RoleGuard allowedRoles={ADMIN_ROLES} />,
    children: [
      { index: true, element: <Navigate to="user" replace /> },
      { path: 'user', element: <UserPage /> },
    ],
  },
]
```

Privilege-based (user's `permission.privileges` must include all of them):

```tsx
{ path: 'billing', element: <RoleGuard requiredPrivileges={['billing:read']} />, children: [/* … */] }
```

Hide the matching UI with `hasAccess(user, { privileges: ['billing:read'] })`. Role names are backend
permission aliases; shared lists live in `src/config/constants.ts` (`ADMIN_ROLES`, `SUPERUSER_ROLES` — keep
the latter in sync with backend `BE_SUPERUSER_ALIASES`).

## Scenario C — Guest-only / public auth pages

Add them under the `auth` route in `src/routes/auth.routes.tsx` (parent element `AuthLayout`):

```tsx
{ path: 'register', element: <GuestGuard><RegisterPage /></GuestGuard> },  // guest-only
{ path: 'verify-email', element: <VerifyEmailPage /> },                     // public either way (existing)
```

Public auth endpoints called from these pages must be in `NO_REFRESH_ENDPOINTS` (`src/services/api-client.ts`)
so a 401 is shown as an error instead of triggering a refresh.

## Scenario D — App without login (rare)

If a project genuinely has no authentication, remove the `<AuthGuard>` wrapper from `main.routes.tsx` and any
`RoleGuard` routes, and stop rendering `UserMenu`. Do **not** fake a session by calling `setUser` with a mock
user. Re-adding auth = restoring the wrapper; the guards need no changes.

---

## Rules

- ✅ Session state comes only from `useAuthStore` (`status`, `user`) — never from cookies, localStorage or a token.
- ✅ `RoleGuard` is always nested under `AuthGuard` (it assumes `user` is resolved).
- ✅ Forbidden access renders 403 in place; unknown URLs hit the `*` route (`NotFoundPage`).
- ❌ Don't persist the auth store or add a `token` field to it.
- ❌ Don't redirect to a `/forbidden` route (none exists) — RoleGuard renders `ForbiddenPage`.
- ❌ Don't build redirect URLs by hand — use `buildLoginPath()` / `getSafeRedirect()` (open-redirect safe).
- ❌ Don't call `/auth/me` yourself in pages — read `useAuthStore((s) => s.user)`.

## Common mistakes

- Wrapping `/auth/login` in `AuthGuard` → redirect loop. Use `GuestGuard`.
- Checking `user.role === 'admin'` inline → misses superuser `owner` and privileges. Use `hasAccess`.
- Clearing the store on logout but not the query cache → use `endClientSession()` / `useLogout()`.

## Checklist

- [ ] New authenticated route is a child of the `AuthGuard`-wrapped `/` route
- [ ] Restricted sections use `RoleGuard` with `allowedRoles` and/or `requiredPrivileges`
- [ ] Matching menu entries/buttons are hidden with `hasAccess`
- [ ] Guest-only pages use `GuestGuard`; their endpoints are in `NO_REFRESH_ENDPOINTS`
- [ ] Guard tests still pass (`src/routes/guards/guards.test.tsx`, `npm run test`)
