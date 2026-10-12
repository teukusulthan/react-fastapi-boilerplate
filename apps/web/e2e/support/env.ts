/**
 * E2E configuration, read from the environment (never hardcode real credentials).
 * The defaults match what `node scripts/e2e.mjs` and the GitLab `web:e2e` job seed.
 */

const read = (key: string): string | undefined => {
  const value = process.env[key]?.trim()
  return value ? value : undefined
}

/** Origin of an already-running web app (e.g. http://localhost:8080). Unset = Playwright serves a fresh build. */
export const EXTERNAL_BASE_URL = read('E2E_BASE_URL')?.replace(/\/+$/, '')

/** Port of the `vite preview` server Playwright starts when E2E_BASE_URL is unset. */
export const WEB_PORT = Number(read('E2E_WEB_PORT') ?? 4173)

/** Backend origin the preview server proxies /api/v1/apps to. */
export const API_URL = read('E2E_API_URL') ?? 'http://127.0.0.1:8020'

/** Skip `npm run build` before `vite preview` (reuse the current build/ output). */
export const SKIP_BUILD = read('E2E_SKIP_BUILD') === '1'

export const BASE_URL = EXTERNAL_BASE_URL ?? `http://127.0.0.1:${WEB_PORT}`

/** Public API prefix the SPA calls (VITE_API_BASE_URL default; stripped by the proxy). */
export const API_PREFIX = '/api/v1/apps'

/** Seeded bootstrap admin (BE_BOOTSTRAP_ADMIN_EMAIL / BE_BOOTSTRAP_ADMIN_PASSWORD). */
export const ADMIN = {
  email: read('E2E_ADMIN_EMAIL') ?? 'admin@example.com',
  password: read('E2E_ADMIN_PASSWORD') ?? 'e2e-admin-password',
}
