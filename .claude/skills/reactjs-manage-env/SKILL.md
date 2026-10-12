---
name: reactjs-manage-env
description: Add or change environment variables for apps/web (Vite). Env files live in apps/web/env/; browser vars use the VITE_ prefix and are validated with zod in src/config/env.ts (the only place that reads import.meta.env); DEV_PROXY_TARGET is a config-time-only key read by vite.config.ts; %VITE_*% placeholders in index.html. Use whenever a task needs a new env key, a changed default, or wiring env into code.
---

# ReactJS Manage Env Skill

## Layout (already in the boilerplate)

```
apps/web/
├── env/
│   ├── .env.example        ← committed: every key, safe defaults/placeholders
│   ├── .env                ← optional local dev overrides (gitignored)
│   ├── .env.staging        ← `npm run build:staging` (gitignored)
│   └── .env.production     ← production build (gitignored)
├── src/config/env.ts       ← zod schema + typed `env` object (the ONLY import.meta.env reader)
├── src/config/env.test.ts  ← parseEnv unit tests
├── index.html              ← %VITE_APP_NAME%, %VITE_APP_DESCRIPTION% placeholders
└── vite.config.ts          ← envDir: env/, loadEnv for DEV_PROXY_TARGET, html placeholder defaults
```

`.gitignore` (`apps/web/.gitignore`) ignores `env/.env` and `env/.env.*` except `.env.example`.
Every key has a default, so the app runs without any `env/.env`.

Vite loading: `vite` (dev) → `env/.env`, `env/.env.local`, `env/.env.development`;
`vite build` → `.env` + `.env.production`; `vite build --mode staging` → `.env` + `.env.staging`.

## Current keys

| Key | Exposed to browser | Default | Read by |
|---|---|---|---|
| `VITE_APP_NAME` | yes | `App` | `env.app.name`, `<title>` via `%VITE_APP_NAME%` |
| `VITE_APP_DESCRIPTION` | yes | `''` (html: "Internal web application") | `env.app.description`, meta description |
| `VITE_API_BASE_URL` | yes | `/api/v1/apps` | `env.api.baseUrl` → `apiClient` baseURL. Relative path (proxied) or absolute `http(s)://` URL; trailing `/` stripped |
| `VITE_MAPBOX_TOKEN` | yes | `''` | `env.map.mapboxToken` (public Mapbox token) |
| `DEV_PROXY_TARGET` | **no** (config time only) | `http://localhost:8020` | `vite.config.ts` → dev/preview proxy for `/api/v1/apps` (prefix stripped) |

Built-ins mapped by `env.ts`: `MODE` → `env.app.mode`, `DEV` → `env.app.isDev`, `PROD` → `env.app.isProd`.

The `/api/v1/apps` prefix must match three places: `VITE_API_BASE_URL`, `API_PREFIX` in `vite.config.ts`, and the
production reverse proxy (`apps/web/nginx.conf`). Change them together.

---

## Adding a key — step by step

### 1. Name it

- Browser-visible: `VITE_` + ALL_CAPS (`VITE_FEATURE_REPORTS`, `VITE_SENTRY_DSN`).
- Build/dev-tooling only (never shipped): no `VITE_` prefix, read in `vite.config.ts` via `loadEnv(mode, ENV_DIR, '')`
  like `DEV_PROXY_TARGET`.
- ❌ Never put secrets (API keys with write access, DB passwords, JWT secrets) in a `VITE_` var — everything
  `VITE_*` is in the public bundle. Backend secrets are `BE_*` in `apps/backend/.env`.

### 2. Add it to `env/.env.example`

Group by service with a `# Header` comment, value empty or a safe default:

```env
# Feature flags
VITE_FEATURE_REPORTS=false
```

### 3. Wire it into `src/config/env.ts`

Add to the zod schema (use `optionalString` so `KEY=` means "unset → default"), to `AppEnv`, and to the object
returned by `parseEnv`:

```ts
const envSchema = z.object({
  // …existing keys
  VITE_FEATURE_REPORTS: optionalString(z.enum(['true', 'false']).default('false')),
})

export interface AppEnv {
  // …
  feature: { reports: boolean }
}

// in parseEnv():
feature: { reports: values.VITE_FEATURE_REPORTS === 'true' },
```

Invalid values make `parseEnv` throw at startup with a list of bad keys ("Invalid environment configuration
(check env/.env*)") — keep validation strict (URLs via `.url()`/refine, enums for flags).

### 4. Use it

```ts
import env from '@/config/env'

if (env.feature.reports) { /* … */ }
```

### 5. Test it

Add a case to `src/config/env.test.ts` (`parseEnv({ VITE_FEATURE_REPORTS: 'true' })`), then run
`npm run test` / `npm run typecheck` in `apps/web` (or `npm run ci` at the repo root).

### 6. index.html (optional)

Need the value in static HTML? Use `%VITE_KEY%` and add a default to `HTML_ENV_DEFAULTS` in `vite.config.ts`
(unknown placeholders would otherwise ship literally). See `.claude/skills/reactjs-seo-html/SKILL.md`.

---

## Checklist

- [ ] Correct prefix (`VITE_` only if the browser needs it); ALL_CAPS
- [ ] `env/.env.example` updated (grouped, safe default)
- [ ] zod schema + `AppEnv` + `parseEnv` mapping updated in `src/config/env.ts`; test added
- [ ] Code reads `env.*` only — no `import.meta.env` outside `src/config/env.ts`
- [ ] No secrets in `VITE_*`; no real values committed

## Anti-patterns

| ❌ Don't | ✅ Do |
|---|---|
| `process.env.X` in app code | `env.*` from `@/config/env` (Vite has no `process.env` in the browser) |
| `import.meta.env.VITE_X` in components/services | add it to `env.ts` and import `env` |
| `REACT_APP_X` / camelCase keys | `VITE_X` ALL_CAPS |
| Env files at the app root | `apps/web/env/` (`envDir`) |
| `import.meta.env.X ?? ''` without validation | zod schema with defaults in `env.ts` |
| Storing auth token keys/names in env | auth is httpOnly cookies — nothing to configure on the web side |
| Hard-coding `http://localhost:8020` in code | `DEV_PROXY_TARGET` (dev proxy) + relative `VITE_API_BASE_URL` |

> Template files: `references/env-template.md`
