import { defineConfig, devices } from '@playwright/test'

import { API_URL, BASE_URL, EXTERNAL_BASE_URL, SKIP_BUILD, WEB_PORT } from './e2e/support/env'

const isCI = Boolean(process.env.CI)

/**
 * End-to-end smoke suite against the REAL backend (see e2e/README.md).
 *
 * - Without E2E_BASE_URL, Playwright builds the app and serves it with `vite preview` on E2E_WEB_PORT;
 *   the preview server proxies /api/v1/apps to E2E_API_URL (DEV_PROXY_TARGET, see vite.config.ts).
 * - With E2E_BASE_URL (e.g. the Docker stack on http://localhost:8080), no web server is started.
 * The backend itself is never started here: `node scripts/e2e.mjs` (repo root) or CI does that.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',
  globalSetup: './e2e/support/global-setup.ts',
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  workers: isCI ? 2 : undefined,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  outputDir: 'test-results',
  reporter: isCI
    ? [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }], ['junit', { outputFile: 'test-results/junit.xml' }]]
    : [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [
    {
      name: 'chromium',
      // Desktop viewport: the sidebar is an off-canvas sheet below the md breakpoint.
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
  ],
  webServer: EXTERNAL_BASE_URL
    ? undefined
    : {
        command: `${SKIP_BUILD ? '' : 'npm run build && '}npm run preview -- --host 127.0.0.1 --port ${WEB_PORT} --strictPort`,
        url: BASE_URL,
        // Never silently reuse a stale preview of an old build unless asked to.
        reuseExistingServer: process.env.E2E_REUSE_SERVER === '1',
        timeout: 180_000,
        stdout: 'ignore',
        stderr: 'pipe',
        env: { DEV_PROXY_TARGET: API_URL },
      },
})
