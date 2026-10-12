# Env Template — apps/web (Vite)

All env files live in `apps/web/env/` (`envDir` in `vite.config.ts`). Only `.env.example` is committed.

## env/.env.example (current, committed)

```env
# App
VITE_APP_NAME=App
VITE_APP_DESCRIPTION=Internal web application

# API — relative path (proxied by the Vite dev server / production reverse proxy) or an absolute URL
VITE_API_BASE_URL=/api/v1/apps

# Map
VITE_MAPBOX_TOKEN=

# Dev server only (read by vite.config.ts, never exposed to the browser)
DEV_PROXY_TARGET=http://localhost:8020
```

## env/.env (local overrides, gitignored — optional)

```env
VITE_APP_NAME=My Console
VITE_MAPBOX_TOKEN=pk.<your-public-token>
# Backend running elsewhere (e.g. another machine / docker):
DEV_PROXY_TARGET=http://192.168.1.50:8020
```

## env/.env.production (gitignored — only if a value differs in prod builds)

```env
VITE_APP_NAME=My Console
# Keep the relative base URL when nginx proxies /api/v1/apps → backend (default setup):
VITE_API_BASE_URL=/api/v1/apps
```

## src/config/env.ts (shape — see the real file)

```ts
import { z } from 'zod'

const optionalString = <T extends z.ZodType>(schema: T) =>
  z.preprocess((value) => (typeof value === 'string' && value.trim() === '' ? undefined : value), schema)

const envSchema = z.object({
  VITE_API_BASE_URL: optionalString(apiBaseUrl.default('/api/v1/apps')),
  VITE_APP_NAME: optionalString(z.string().trim().default('App')),
  VITE_APP_DESCRIPTION: optionalString(z.string().trim().default('')),
  VITE_MAPBOX_TOKEN: optionalString(z.string().trim().default('')),
  MODE: z.string().default('development'),
  DEV: z.boolean().default(false),
  PROD: z.boolean().default(false),
})

export function parseEnv(raw: Record<string, unknown>): AppEnv { /* safeParse → readable error → AppEnv */ }

const env: AppEnv = parseEnv(import.meta.env)
export default env
```

## Usage

```ts
import env from '@/config/env'

env.api.baseUrl        // '/api/v1/apps'
env.app.name           // 'App'
env.map.mapboxToken    // ''
env.app.isDev          // true under `vite`
```
