# Orchestra — Apps

> A quick index of what exists under `apps/`. For conventions and recipes, read
> [`../AGENTS.md`](../AGENTS.md) and each app's `AI_GUIDE.md`.
> **Update this file whenever you add a feature, module, page or app** (keep it short: one row each).

## Apps

| App | Path | Port (dev) | Guide |
|-----|------|------------|-------|
| Backend (FastAPI) | `apps/backend/` | 8020 | [`backend/AI_GUIDE.md`](backend/AI_GUIDE.md) · [`backend/README.md`](backend/README.md) |
| Web (React + Vite) | `apps/web/` | 3000 | [`web/AI_GUIDE.md`](web/AI_GUIDE.md) · [`web/README.md`](web/README.md) |

There is no mobile app, agent or MCP server yet. When one is added (`apps/mobile/`, `apps/agents/<role>/`,
`apps/mcp/<server>/`), add a row.

## Features implemented

| Feature | Backend | Web |
|---------|---------|-----|
| Health probes | `router/health.py` (`/health/live`, `/health/ready`) | — |
| Auth: login, logout, refresh, `/auth/me` | `router/auth.py`, `service/auth/{login,tokens}.py` | `features/shared/auth/` (LoginView, useSession, useLogout), `pages/auth/LoginPage.tsx`, `routes/guards/*` |
| Auth: 2FA (email / TOTP) | `service/auth/two_factor.py` | `TwoFactorForm.tsx` (login step); setup/enable/disable only in `services/auth.service.ts` |
| Auth: register, forgot/change password, verify email | `service/auth/{registration,password}.py` | Verify-email page only (`pages/auth/VerifyEmailPage.tsx`); the rest only in `services/auth.service.ts` |
| Auth: Google sign-in | `service/auth/google.py` (mounted when configured) | — |
| Users (admin CRUD + self profile) | `router/user.py`, `service/user.py` | `features/administrator/user/` (list + search), `pages/administrator/user/UserPage.tsx` |
| Permissions (RBAC) | `router/permission.py`, `service/permission.py` | `services/permission.service.ts` (no page) |
| Groups | `router/group.py`, `service/group.py` | `services/group.service.ts` (no page) |
| Roles (reference CRUD module) | `router/role.py`, `service/role.py` | `services/role.service.ts` (no page) |
| Uploads (S3) | `router/upload.py`, `service/upload.py`, `util/s3.py` | `services/upload.service.ts` (no page) |
| Dashboard | — | `features/dashboard/overview/`, `pages/dashboard/DashboardPage.tsx` |
| Seed | `scripts/seed.py` | — |

## Key files

| Concern | Backend (`apps/backend/`) | Web (`apps/web/src/`) |
|---------|---------------------------|------------------------|
| Entry / wiring | `api.py`, `core/app_factory.py`, `router/__init__.py` (registry) | `main.tsx`, `routes/index.tsx`, `components/wrappers/AppProviders.tsx` |
| Config | `core/config.py`, `.env.example` | `config/env.ts`, `env/.env.example`, `vite.config.ts` |
| Auth / access | `core/deps.py`, `core/security.py` | `stores/useAuthStore.ts`, `routes/guards/`, `features/shared/auth/utils/access.ts` |
| Data / API layer | `db/` (`schema.py`, `mongo/`, `supabase/`), `migrations/supabase/` | `services/api-client.ts`, `services/api-endpoints.ts`, `services/api-factory*.ts` |
| Envelope / errors | `core/responses.py`, `core/errors.py` | `types/api.d.ts`, `services/api-error.ts` |
| Navigation | — | `config/menu/*.menu.ts`, `components/layouts/AppSidebar.tsx` |
| Tests | `tests/` (`conftest.py` fixtures) | `src/test/`, `**/*.test.ts(x)` |
