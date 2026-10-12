// Configuration for scripts/docs-check: what is scanned, and the few documented exceptions.
//
// Keep exceptions here (with a reason) rather than scattering ignore markers, when the same
// intentional "not present yet" path or example name shows up in several documents.

/** Markdown files that are checked (repo-relative, forward slashes). */
export const SCOPE = [
  /^CLAUDE\.md$/,
  /^AGENTS\.md$/,
  /^README\.md$/,
  /^\.claude\/rules\/.+\.md$/,
  /^\.claude\/skills\/.+\.md$/,
  /^\.claude\/commands\/.+\.md$/,
  /^docs\/.+\.md$/,
  /^apps\/[^/]+\/AI_GUIDE\.md$/,
  /^apps\/[^/]+\/README\.md$/,
  /^apps\/web\/e2e\/README\.md$/,
  /^scripts\/[^/]+\/README\.md$/,
];

/**
 * Files in scope for the link check only. The archived skills describe other projects, so their
 * contents are not checked, but the library README's links must resolve.
 */
export const LINKS_ONLY = [/^\.claude\/skills-library\/README\.md$/];

/** Documents whose `src/...` paths mean `apps/web/src/...`. */
export const WEB_DOCS = [
  /^apps\/web\//,
  /^\.claude\/skills\/reactjs-[^/]+\//,
  /^\.claude\/rules\/web\//,
  /^\.claude\/skills\/orchestra\/references\/web\.md$/,
  /^\.claude\/skills\/html-to-react\//,
  /^\.claude\/commands\/(generate-ui|generate-screen|sync-types|switch-design-system)\.md$/,
];

/** Documents whose `core/…`, `db/…`, `dto/…`, … paths mean `apps/backend/...`. */
export const BACKEND_DOCS = [
  /^apps\/backend\//,
  /^\.claude\/skills\/fastapi-[^/]+\//,
  /^\.claude\/rules\/backend\//,
  /^\.claude\/skills\/orchestra\/references\/backend\.md$/,
  /^\.claude\/commands\/(generate-api|sync-types)\.md$/,
];

/** Cross-stack guides: both `src/...` (web) and backend-relative paths are checked. */
export const MIXED_DOCS = [
  /^CLAUDE\.md$/,
  /^AGENTS\.md$/,
  /^README\.md$/,
  /^docs\//,
  /^\.claude\/rules\/architecture\.md$/,
];

/** Backticked paths with these prefixes are resolved from the repo root. */
export const ROOT_PREFIXES = ["apps/", ".claude/", "docs/", "scripts/", "changelog/"];

/** Backend-relative prefixes (resolved against apps/backend in backend and mixed docs). */
export const BACKEND_PREFIXES = [
  "core/",
  "db/",
  "dto/",
  "service/",
  "router/",
  "util/",
  "migrations/",
  "templates/",
  "tests/",
];

/**
 * Paths that are generated locally (setup, build, test runs) and therefore absent from a clean
 * checkout. A reference to them is fine.
 */
export const GENERATED_PATHS = [
  /(^|\/)\.env$/,
  /(^|\/)\.venv(\/|$)/,
  /(^|\/)node_modules(\/|$)/,
  /(^|\/)__pycache__(\/|$)/,
  /(^|\/)\.nx(\/|$)/,
  /(^|\/)\.cache(\/|$)/,
  /(^|\/)\.pytest_cache(\/|$)/,
  /(^|\/)coverage(\/|$)/,
  /^apps\/web\/build(\/|$)/,
  /^apps\/web\/\.ui-snapshots(\/|$)/,
  /^apps\/web\/(test-results|playwright-report)(\/|$)/,
  /^apps\/backend\/report(-postgres)?\.xml$/,
];

/**
 * A line containing one of these phrases documents a file the reader is told to create, so its
 * paths and imports are not required to exist (path, Python-import and TS-import checks).
 */
export const CREATE_MARKERS = [
  /create it at/i,
  /\(create\)/i,
  /create on demand/i,
  /\bcreate\s+`/i, // "create `apps/backend/db/mysql/`"
  /\bnew\W{0,4}\s+file\b/i, // "add a **new** file such as `…`"
  /not present yet/i,
  /\*\*not present\*\*/i,
  /\bif (it )?exists\b/i,
];

/**
 * Example names used by the documented recipes ("add a `note` resource", "a `reports` page", "a
 * `product` service"). Paths, Python modules, TS module specifiers, model names, env vars and
 * endpoints built from them are recipe output, not drift.
 */
const EXAMPLE = String.raw`(notes?|reports?|products?|catalog)`;
export const RECIPE_EXAMPLES = {
  paths: [new RegExp(String.raw`(^|[/_.-])${EXAMPLE}([/_.-]|$)`, "i"), /(^|\/)manager\.menu\.ts$/],
  pythonModules: [new RegExp(String.raw`(^|\.)${EXAMPLE}(\.|$)`)],
  tsModules: [new RegExp(String.raw`(^|/)${EXAMPLE}([/.]|$)`, "i")],
  tsNames: [/^(Note|Notes|Report|Reports|Product|Products)(DTO|Response|Create|Update)?$/],
  pythonNames: [/^(NOTES?|REPORTS?|PRODUCTS?)$/, /^(Note|Report|Product)\w*$/, /^get_(note|report|product)\w*$/],
  envVars: [new RegExp(String.raw`^(BE|VITE)_(TABLE_|FEATURE_)?${EXAMPLE}$`, "i")],
  endpoints: [/^\/notes?\//, /^\/x\//, /^\/(add|update|delete|get-one|get-all)$/],
};

/**
 * Locations the skills document as "not present in the boilerplate yet, create it on demand"
 * (each skill says so in its own status note). Paths and `@/…` imports under them are recipes.
 */
export const PLANNED_PATHS = [
  /^apps\/web\/src\/modules\/(dynamic-filter|dynamic-widget|map-plugin)(\/|$)/, // reactjs-dynamic-*, reactjs-map
  /^apps\/web\/src\/components\/wrappers\/(EChartWrapper|useChartTheme|MapboxWrapper)\.tsx?$/, // reactjs-chart, reactjs-map
  /^apps\/web\/src\/config\/map(\/|$)/, // reactjs-map Pattern B
  /^apps\/web\/src\/types\/map\.d\.ts$/, // reactjs-map shared types
  /^apps\/web\/src\/utils\/map\.ts$/, // reactjs-map runtime guards
  /^apps\/web\/src\/services\/(map|widget)\.service\.ts$/, // reactjs-map tile/widget services
  /^apps\/web\/src\/hooks\/useTour\.ts$/, // tour skill
  /^apps\/(agents?|mcp|mobile)(\/|$)/, // agent-builder, mcp-builder, Flutter commands
  /^apps\/web\/src\/(schemas|assets)(\/|$)/, // reactjs-architecture: "create on demand" folders
  /^apps\/web\/public\/data(\/|$)/, // POC mock data (apps/web/AI_GUIDE.md §6, docs/mock-data.md)
  /^apps\/web\/src\/services\/mock(-client|-endpoints|\.service)\.ts$/, // same
  // Scaffold-system skills that are not bundled here (AGENTS.md §10); their commands say so.
  /^\.claude\/skills\/(bootstrap-project|design-system-setup)(\/|$)/,
];

/**
 * Env var names that are documented on purpose although no setting has them (yet). A trailing `*`
 * matches a prefix (`BE_MYSQL_*`).
 */
export const EXAMPLE_ENV_VARS = [
  "BE_URL", // agent apps' own .env (apps/agents/<role>/.env, agent-builder): the backend URL
  "BE_X", // placeholders in prose
  "BE_NAME",
  "VITE_X",
  "VITE_KEY",
  "VITE_NAME",
  "VITE_APP_URL", // reactjs-seo-html: "to add a canonical URL, add VITE_APP_URL …"
  "VITE_MAP_TILE_URL", // reactjs-map: optional, "add it if tiles live elsewhere"
  "VITE_SENTRY_DSN", // reactjs-manage-env: naming example
  "BE_MYSQL_*", // fastapi-database-init: "add a MySQL provider" recipe
  "BE_MCP_HUB_*", // agent-builder: "not existing settings — add them"
];

/**
 * Templates whose links are relative to where the generated file will live (not to the template),
 * so only the env / npm / import checks apply to them.
 */
export const TEMPLATE_DOCS = [/^\.claude\/skills\/sprint-builder\/references\/(sprint|task)-template\.md$/, /\/references\/template\//];

/** Documents whose `@/…` imports are checked against apps/web/src (others may show other apps). */
export const TS_IMPORT_DOCS = [...WEB_DOCS, ...MIXED_DOCS];

/** Ignore markers (also usable as `# docs-check: ...` / `// docs-check: ...` inside code). */
export const MARKERS = {
  file: "docs-check: ignore-file",
  start: "docs-check: ignore-start",
  end: "docs-check: ignore-end",
  nextLine: "docs-check: ignore-next-line",
  line: "docs-check: ignore-line",
};

/** The endpoint registry compared both ways with the FastAPI app. */
export const API_SPEC = "docs/api-spec.md";

/** Documents whose backticked `METHOD /path` mentions must exist in the app (one way). */
export const ENDPOINT_DOCS = [
  /^docs\/api\/.+\.md$/,
  /^CLAUDE\.md$/,
  /^AGENTS\.md$/,
  /^README\.md$/,
  /^apps\/[^/]+\/(AI_GUIDE|README)\.md$/,
];
