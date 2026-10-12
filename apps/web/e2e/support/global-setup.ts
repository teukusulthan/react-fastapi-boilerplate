import { type FullConfig } from '@playwright/test'

import { API_PREFIX, BASE_URL } from './env'

const READY_TIMEOUT_MS = 30_000

/**
 * Fail fast with a clear message when the backend is not reachable through the web origin
 * (instead of every test timing out on the login form). Runs after the web server is up.
 */
export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL = config.projects[0]?.use.baseURL ?? BASE_URL
  const url = `${baseURL}${API_PREFIX}/health/ready`
  const deadline = Date.now() + READY_TIMEOUT_MS
  let lastProblem = 'no response'

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(3_000) })
      if (response.ok) return
      lastProblem = `HTTP ${response.status}`
    } catch (error) {
      lastProblem = error instanceof Error ? error.message : String(error)
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000))
  }

  throw new Error(
    `Backend not ready at ${url} (${lastProblem}). Start it first (node scripts/e2e.mjs does it for you), ` +
      'or point E2E_API_URL / E2E_BASE_URL at a running stack. See apps/web/e2e/README.md.',
  )
}
