# E2E smoke suite (Playwright)

A small, fast smoke suite that drives the **real** backend through the built web app. It is not a
regression suite: it proves that sign-in, the authenticated shell, an admin data page and sign-out work
end to end. Component logic stays covered by Vitest (`npm run test:ci`).

| Spec | Checks |
|---|---|
| `admin-smoke.spec.ts` | seeded admin signs in → dashboard (h1, page title, sidebar `Main navigation`) → `/administrator/user` table has the admin row → sign out → `/auth/login`; the old session no longer opens `/administrator/user` |
| `auth.spec.ts` | anonymous `/` redirects to `/auth/login`; wrong credentials show `Invalid credentials` |

Layout: `playwright.config.ts` (in `apps/web`), `e2e/*.spec.ts`, `e2e/pages/` (page objects),
`e2e/support/` (env + global setup that fails fast if `/health/ready` is not reachable). Selectors are
roles, labels and visible text only; add a `data-testid` only where no accessible selector exists.
Vitest only picks up `src/**/*.test.{ts,tsx}`, so `e2e/` never runs under `npm run test:ci`.
TypeScript checks it via `tsconfig.e2e.json` (part of `npm run typecheck`).

## Run it locally

You need the backend virtualenv (`npm run setup:backend` from the repo root), the web deps and a Chromium for Playwright
(`npx playwright install chromium` once, from `apps/web`). Use **disposable** Mongo and Redis
instances: the seed creates an admin and the suite signs in and out.

```bash
# 1. One command, throwaway containers (mongo:7 on 127.0.0.1:57017, redis:7 on 127.0.0.1:56379; removed afterwards)
npm run test:e2e -- --docker

# 2. Your own disposable Mongo/Redis
E2E_MONGO_URI=mongodb://localhost:57017 E2E_REDIS_URL=redis://localhost:56379/0 npm run test:e2e

# 3. A backend that is already running and seeded (only Playwright runs)
E2E_API_URL=http://127.0.0.1:8020 E2E_ADMIN_PASSWORD=<your admin password> npm run test:e2e -- --no-backend
#    = cd apps/web && E2E_API_URL=… npm run test:e2e

# Playwright options go after `--`, e.g. a headed run of one spec:
npm run test:e2e -- --docker -- --headed e2e/auth.spec.ts
```

`npm run test:e2e` at the repo root runs `scripts/e2e.mjs`:

1. (`--docker`) starts `rfb-e2e-mongo` and `rfb-e2e-redis`;
2. runs `python -m scripts.seed` (permissions + bootstrap admin from `E2E_ADMIN_*`);
3. starts the backend (`<venv> api.py`) on `127.0.0.1:${E2E_BACKEND_PORT:-8021}` with an isolated
   `BE_*` environment: it never reads `apps/backend/.env`, uses a random JWT secret,
   `BE_COOKIE_SECURE=false` (plain HTTP), `BE_EMAIL_BACKEND=console`, Redis key prefix `e2e`, Mongo
   database `app_e2e` and `BE_RATE_LIMIT_AUTH=100` so repeated runs do not hit the 10/min auth limit;
4. waits for `/health/ready`, then runs `npm run test:e2e` in `apps/web` (Playwright builds the app and
   serves it with `vite preview` on `127.0.0.1:4173`, proxying `/api/v1/apps` to the backend);
5. stops the backend and removes the containers, also on failure or Ctrl+C. Backend output:
   `.cache/e2e/backend.log` (its tail is printed when something fails).

`apps/web` → `npm run test:e2e` is plain `playwright test`: it assumes the backend is reachable.
Open the last HTML report with `npm run test:e2e:report` (traces and screenshots are kept for failed
tests in `test-results/`).

The suite is **not** part of the root `npm run ci`, because it needs running services.

## Configuration

| Variable | Default | Used by |
|---|---|---|
| `E2E_ADMIN_EMAIL` | `admin@example.com` | seed + specs |
| `E2E_ADMIN_PASSWORD` | `e2e-admin-password` | seed + specs (test-only; set your own for a shared backend) |
| `E2E_API_URL` | `http://127.0.0.1:8020` (`scripts/e2e.mjs`: its own backend) | `vite preview` proxy target |
| `E2E_BASE_URL` | unset | use an already-running web app (e.g. Docker on `http://localhost:8080`); no preview server is started |
| `E2E_WEB_PORT` | `4173` | preview server port |
| `E2E_SKIP_BUILD` | unset | `1` = serve the existing `build/` without rebuilding |
| `E2E_REUSE_SERVER` | unset | `1` = reuse a preview server already listening on `E2E_WEB_PORT` |
| `E2E_MONGO_URI`, `E2E_REDIS_URL` | required (unless `--docker`/`--no-backend`) | `scripts/e2e.mjs` |
| `E2E_MONGO_DB` | `app_e2e` | `scripts/e2e.mjs` |
| `E2E_BACKEND_PORT` | `8021` | `scripts/e2e.mjs` |

The seed never resets an existing user's password. If you reuse a Mongo database seeded with another
admin password, pass that password in `E2E_ADMIN_PASSWORD` or drop the `app_e2e` database.

## CI

GitLab job `web:e2e` (stage `test`, `.gitlab-ci.yml`): image `mcr.microsoft.com/playwright:v1.63.0-noble`
(Node + browsers; keep the tag equal to `@playwright/test` in `package.json`), services `mongo:7` and
`redis:7`. It installs Python + `libmagic1`, creates `apps/backend/.venv` with uv, runs `npm ci`, then
`node scripts/e2e.mjs`. Artifacts (1 week): `apps/web/playwright-report/`, `apps/web/test-results/`
(traces, screenshots, `junit.xml`, shown in the MR widget) and `.cache/e2e/backend.log`.

## Adding a test

Keep it a smoke test: one user journey per spec, role/label selectors, web-first assertions
(`await expect(locator).toBeVisible()`), no fixed sleeps. Do not sign in as the admin with a wrong
password (it counts towards the per-identifier lockout); use a unique unknown identifier instead.
