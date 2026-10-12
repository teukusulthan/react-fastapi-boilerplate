#!/usr/bin/env node
/* global document, window -- page.evaluate / addInitScript callbacks run in the browser */
/**
 * UI snapshot — screenshots of real routes with a mocked API, for reviewing UI work.
 *
 *   npm run ui:snapshot -- --route /administrator/user
 *   npm run ui:snapshot -- --route / --route /ui-kit --theme dark --viewport desktop
 *   npm run ui:snapshot -- --route /administrator/user --state empty --state error
 *
 * Run `npm run ui:snapshot -- --help` for every option. See printHelp() below.
 */
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { parseArgs } from 'node:util'

import { chromium } from 'playwright'

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url))
const WEB_DIR = path.resolve(SCRIPT_DIR, '../..')
const FIXTURES_DIR = path.join(SCRIPT_DIR, 'fixtures')
const API_PREFIX = '/api/v1/apps'
const THEME_STORAGE_KEY = 'theme-storage' // stores/useThemeStore.ts (zustand persist)
const VIEWPORTS = {
  desktop: { width: 1440, height: 900, isMobile: false },
  mobile: { width: 390, height: 844, isMobile: true },
}
const STATES = ['default', 'loading', 'empty', 'error']
const DEFAULT_ANCHOR = '2026-01-15T09:30:00.000Z'

function printHelp() {
  console.log(`Usage: npm run ui:snapshot -- [options]

Starts Vite (or uses --url), mocks ${API_PREFIX}/** with fixtures and writes PNGs to .ui-snapshots/.

Options
  --route <path>        Route to capture (repeatable). Default: /
  --theme <t>           light | dark | both (default: both)
  --viewport <v>        desktop (1440×900) | mobile (390×844) | both (default: both)
  --state <s>           default | loading | empty | error (repeatable, default: default)
                          loading: data endpoints never answer · empty: lists return [] · error: data endpoints return 500
  --anonymous           Serve /auth/me as 401 (signed out). Implied for /auth/* routes.
  --click <selector>    Click this Playwright selector before the screenshot (e.g. "text=Add user") — for dialogs/menus.
  --viewport-only       Capture only the viewport (default: the whole scrollable main area).
  --url <origin>        Use an already-running dev server (e.g. http://localhost:3000) instead of starting Vite.
  --out <dir>           Output directory (default: .ui-snapshots)
  --wait <ms>           Extra settle time before each screenshot (default: 300)
  -h, --help            Show this help

Fixtures (scripts/ui-snapshot/fixtures/*.json, any file name):
  { "endpoint": "/user/get-all", "data": <payload> }   (auth-me.json may add "anchor": "<ISO>" = frozen browser clock)
  Array payloads are served as get-all lists with FindDTO paging, search, "is" filters and sorting.
  Add a fixture for every new endpoint your screen calls. Unknown writes answer 200 with the request body.

Output: <route-slug>-<theme>-<viewport>[-<state>].png — open every PNG and review it.`)
}

function parseCli() {
  const { values } = parseArgs({
    options: {
      route: { type: 'string', multiple: true },
      theme: { type: 'string', default: 'both' },
      viewport: { type: 'string', default: 'both' },
      state: { type: 'string', multiple: true },
      anonymous: { type: 'boolean', default: false },
      click: { type: 'string' },
      'viewport-only': { type: 'boolean', default: false },
      url: { type: 'string' },
      out: { type: 'string', default: '.ui-snapshots' },
      wait: { type: 'string', default: '300' },
      help: { type: 'boolean', short: 'h', default: false },
    },
    allowPositionals: false,
  })
  if (values.help) {
    printHelp()
    process.exit(0)
  }
  const pick = (value, allowed, name) => {
    const list = value === 'both' ? allowed : [value]
    for (const item of list) if (!allowed.includes(item)) fail(`Invalid --${name} "${item}" (expected ${allowed.join(' | ')} | both)`)
    return list
  }
  const states = values.state ?? ['default']
  for (const state of states) if (!STATES.includes(state)) fail(`Invalid --state "${state}" (expected ${STATES.join(' | ')})`)
  return {
    routes: values.route ?? ['/'],
    themes: pick(values.theme, ['light', 'dark'], 'theme'),
    viewports: pick(values.viewport, Object.keys(VIEWPORTS), 'viewport'),
    states,
    anonymous: values.anonymous,
    click: values.click,
    fullPage: !values['viewport-only'],
    url: values.url?.replace(/\/+$/, ''),
    outDir: path.resolve(WEB_DIR, values.out),
    wait: Number(values.wait) || 0,
  }
}

function fail(message) {
  console.error(`ui:snapshot: ${message}`)
  process.exit(1)
}

/* ── Fixtures & mock API ──────────────────────────────────────────────────── */

function loadFixtures() {
  const fixtures = new Map()
  if (!fs.existsSync(FIXTURES_DIR)) return fixtures
  for (const file of fs.readdirSync(FIXTURES_DIR)) {
    if (!file.endsWith('.json')) continue
    const content = JSON.parse(fs.readFileSync(path.join(FIXTURES_DIR, file), 'utf8'))
    if (typeof content.endpoint !== 'string') fail(`Fixture ${file} needs an "endpoint" (e.g. "/user/get-all")`)
    fixtures.set(content.endpoint, content)
  }
  return fixtures
}

const envelope = (data, { status = 200, message = 'OK', pagination = null, errorCode = null } = {}) => ({
  metaData: { status: status < 400, responseCode: status, message, executionTime: 4, requestId: 'ui-snapshot', pagination, errorCode },
  data,
})

function compare(a, b) {
  if (a === b) return 0
  if (a === null || a === undefined) return 1
  if (b === null || b === undefined) return -1
  return String(a).localeCompare(String(b), 'en', { numeric: true })
}

/** Apply a FindDTO (search, "is" filters, sort, paging) to an array fixture. */
function queryList(items, query = {}) {
  let rows = [...items]
  if (query.search) {
    const needle = String(query.search).toLowerCase()
    const fields = query.searchBy?.length ? query.searchBy : Object.keys(rows[0] ?? {})
    rows = rows.filter((row) =>
      fields.some((field) =>
        String(row[field] ?? '')
          .toLowerCase()
          .includes(needle),
      ),
    )
  }
  for (const filter of query.filters ?? []) {
    if (filter.value && 'is' in filter.value) rows = rows.filter((row) => row[filter.field] === filter.value.is)
    if (filter.value?.isOneOf) rows = rows.filter((row) => filter.value.isOneOf.includes(row[filter.field]))
  }
  if (query.orderBy) {
    const direction = query.order === 'asc' ? 1 : -1
    rows.sort((a, b) => compare(a[query.orderBy], b[query.orderBy]) * direction)
  }
  const page = Math.max(1, query.page ?? 1)
  const size = Math.max(1, query.size ?? 10)
  const totalElements = rows.length
  return { items: rows.slice((page - 1) * size, page * size), pagination: { page, size, totalElements, totalPages: Math.ceil(totalElements / size) } }
}

async function installApiMock(page, fixtures, { state, anonymous }) {
  await page.route(`**${API_PREFIX}/**`, async (route) => {
    const request = route.request()
    const endpoint = new URL(request.url()).pathname.slice(API_PREFIX.length) || '/'
    const method = request.method()

    if (endpoint === '/auth/me') {
      if (anonymous)
        return route.fulfill({ status: 401, json: envelope(null, { status: 401, message: 'Not authenticated', errorCode: 'AUTHENTICATION_ERROR' }) })
      const me = fixtures.get('/auth/me')
      return route.fulfill({ json: envelope(me?.data ?? null) })
    }
    if (endpoint.startsWith('/auth/'))
      return route.fulfill({ status: 401, json: envelope(null, { status: 401, message: 'Not authenticated', errorCode: 'AUTHENTICATION_ERROR' }) })

    if (state === 'loading') return // never answer: the screen stays in its loading state
    if (state === 'error')
      return route.fulfill({
        status: 500,
        json: envelope(null, { status: 500, message: 'The server could not complete the request.', errorCode: 'INTERNAL_ERROR' }),
      })

    const fixture = fixtures.get(endpoint)
    if (endpoint.endsWith('/get-all')) {
      const items = state === 'empty' ? [] : Array.isArray(fixture?.data) ? fixture.data : []
      const { items: pageItems, pagination } = queryList(items, request.postDataJSON() ?? {})
      return route.fulfill({ json: envelope(pageItems, { pagination }) })
    }
    if (fixture) return route.fulfill({ json: envelope(fixture.data) })
    if (method !== 'GET') return route.fulfill({ json: envelope(request.postDataJSON() ?? null) })
    return route.fulfill({
      status: 404,
      json: envelope(null, { status: 404, message: `No fixture for ${method} ${endpoint}`, errorCode: 'RESOURCE_NOT_FOUND' }),
    })
  })
}

/* ── Vite lifecycle ───────────────────────────────────────────────────────── */

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.unref()
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address()
      server.close(() => resolve(port))
    })
  })
}

async function waitForServer(url, child, timeoutMs = 60_000) {
  const started = Date.now()
  while (Date.now() - started < timeoutMs) {
    if (child.exitCode !== null) throw new Error(`Vite exited with code ${child.exitCode}`)
    try {
      const response = await fetch(url)
      if (response.ok) return
    } catch {
      // not up yet
    }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error(`Vite did not start within ${timeoutMs / 1000}s`)
}

async function startVite() {
  const port = await freePort()
  const viteBin = path.join(WEB_DIR, 'node_modules', 'vite', 'bin', 'vite.js')
  const child = spawn(process.execPath, [viteBin, '--port', String(port), '--strictPort', '--host', '127.0.0.1'], {
    cwd: WEB_DIR,
    env: { ...process.env, BROWSER: 'none', FORCE_COLOR: '0' },
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: process.platform !== 'win32',
  })
  let log = ''
  child.stdout.on('data', (chunk) => (log += chunk))
  child.stderr.on('data', (chunk) => (log += chunk))
  const origin = `http://127.0.0.1:${port}`
  try {
    await waitForServer(origin, child)
  } catch (error) {
    stopProcess(child)
    throw new Error(`${error.message}\n${log}`)
  }
  return { origin, child }
}

function stopProcess(child) {
  if (!child || child.exitCode !== null) return
  try {
    if (process.platform !== 'win32') process.kill(-child.pid, 'SIGTERM')
    else child.kill('SIGTERM')
  } catch {
    child.kill('SIGKILL')
  }
}

/* ── Capture ──────────────────────────────────────────────────────────────── */

const slugify = (route) =>
  route
    .replace(/[?#].*$/, '')
    .replace(/^\/+|\/+$/g, '')
    .replace(/[^a-z0-9]+/gi, '-')
    .toLowerCase() || 'home'

/** Height needed to show the whole main scroll area (the app scrolls inside PerfectScrollArea, not the window). */
async function measureFullHeight(page, viewportHeight) {
  return page.evaluate((minHeight) => {
    const main = document.querySelector('[data-slot="sidebar-inset"] .perfect-scroll-area')
    const docHeight = document.documentElement.scrollHeight
    if (!main) return Math.max(minHeight, docHeight)
    const content = main.firstElementChild
    const overflow = (content?.scrollHeight ?? 0) - main.clientHeight
    return Math.max(minHeight, docHeight + Math.max(0, overflow))
  }, viewportHeight)
}

async function capture(browser, origin, fixtures, options, job) {
  const viewport = VIEWPORTS[job.viewport]
  const anchor = fixtures.get('/auth/me')?.anchor ?? DEFAULT_ANCHOR
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 2,
    isMobile: viewport.isMobile,
    hasTouch: viewport.isMobile,
    colorScheme: job.theme,
    locale: 'en-US',
    timezoneId: 'UTC',
    reducedMotion: 'reduce',
  })
  await context.addInitScript(
    ({ key, theme }) => {
      try {
        window.localStorage.setItem(key, JSON.stringify({ state: { theme }, version: 0 }))
      } catch {
        // storage unavailable
      }
      document.documentElement.classList.toggle('dark', theme === 'dark')
    },
    { key: THEME_STORAGE_KEY, theme: job.theme },
  )
  const page = await context.newPage()
  await page.clock.setFixedTime(new Date(anchor))
  const anonymous = options.anonymous || job.route.startsWith('/auth')
  await installApiMock(page, fixtures, { state: job.state, anonymous })

  await page.goto(origin + job.route, { waitUntil: job.state === 'loading' ? 'domcontentloaded' : 'networkidle' })
  await page.evaluate(() => document.fonts.ready)
  if (job.state === 'loading') await page.waitForTimeout(800)
  if (options.click) {
    await page.locator(options.click).first().click()
    await page.waitForTimeout(400)
  }
  await page.waitForTimeout(options.wait)

  if (options.fullPage && !options.click) {
    const height = await measureFullHeight(page, viewport.height)
    if (height > viewport.height) {
      await page.setViewportSize({ width: viewport.width, height: Math.min(height, 12_000) })
      await page.waitForTimeout(250)
    }
  }

  const suffix = job.state === 'default' ? '' : `-${job.state}`
  const file = path.join(options.outDir, `${slugify(job.route)}-${job.theme}-${job.viewport}${suffix}.png`)
  await page.screenshot({ path: file, animations: 'disabled' })
  await context.close()
  return file
}

async function main() {
  const options = parseCli()
  const fixtures = loadFixtures()
  fs.mkdirSync(options.outDir, { recursive: true })

  let vite = null
  const cleanup = () => stopProcess(vite?.child)
  process.on('SIGINT', () => {
    cleanup()
    process.exit(130)
  })
  process.on('SIGTERM', () => {
    cleanup()
    process.exit(143)
  })

  let browser = null
  try {
    const origin = options.url ?? (vite = await startVite()).origin
    browser = await chromium.launch()
    const written = []
    for (const route of options.routes)
      for (const state of options.states)
        for (const theme of options.themes)
          for (const viewport of options.viewports) {
            const file = await capture(browser, origin, fixtures, options, { route, state, theme, viewport })
            written.push(file)
            console.log(path.relative(process.cwd(), file))
          }
    console.log(`\n${written.length} screenshot(s) in ${path.relative(process.cwd(), options.outDir) || '.'} — open and review every one.`)
  } finally {
    await browser?.close()
    cleanup()
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exit(1)
})
