// The individual checks. Each returns issues: { file, line, check, message }.
import { posix } from "node:path";
import {
  API_SPEC,
  BACKEND_DOCS,
  BACKEND_PREFIXES,
  ENDPOINT_DOCS,
  EXAMPLE_ENV_VARS,
  GENERATED_PATHS,
  MIXED_DOCS,
  PLANNED_PATHS,
  RECIPE_EXAMPLES,
  ROOT_PREFIXES,
  TEMPLATE_DOCS,
  TS_IMPORT_DOCS,
  WEB_DOCS,
} from "../config.mjs";
import { inlineCodeSpans, stripInlineCode } from "./markdown.mjs";

const issue = (file, line, check, message) => ({ file, line, check, message });
/** Count one verified reference (shown in the summary so a silently-broken check is visible). */
const tally = (repo, kind, n = 1) => {
  if (repo?.stats) repo.stats[kind] = (repo.stats[kind] ?? 0) + n;
};
const matchesAny = (res, s) => res.some((re) => re.test(s));
const isGenerated = (p) => matchesAny(GENERATED_PATHS, p);
/** A path the docs may name although it does not exist: generated, planned or a recipe example. */
const isExempt = (p) => isGenerated(p) || matchesAny(PLANNED_PATHS, p) || matchesAny(RECIPE_EXAMPLES.paths, p);
/** `.claude/skills/<name>` of a document inside a skill, else null. */
const skillDir = (docPath) => docPath.match(/^\.claude\/skills\/[^/]+/)?.[0] ?? null;
const prose = (doc) => doc.lines.filter((l) => !l.block && !l.ignored);
const allLines = (doc) => doc.lines.filter((l) => !l.ignored);

// ------------------------------------------------------------------------------------ paths

/** Characters that mark a placeholder or a pattern rather than a concrete path. */
const PLACEHOLDER = /[<>{}[\]*…$|()='",@]|\.\.\.|(^|[/_.-])(N{2,}|X{2,})([/_.-]|$)/;

function cleanPathToken(token) {
  let t = token.replace(/^[('"]+/, "").replace(/[)'",;:.!?]+$/, "");
  t = t.replace(/^\.\//, "");
  t = t.replace(/::.*$/, "").replace(/#.*$/, "").replace(/\?.*$/, "");
  t = t.replace(/:\d+(-\d+)?$/, "").replace(/:[A-Za-z_][\w.]*$/, "");
  return t;
}

/** Candidate repo paths for a backticked token, by prefix and document context. */
function resolveCandidates(token, docPath) {
  const web = matchesAny(WEB_DOCS, docPath) || matchesAny(MIXED_DOCS, docPath);
  const backend = matchesAny(BACKEND_DOCS, docPath) || matchesAny(MIXED_DOCS, docPath);
  const skill = skillDir(docPath);
  if (ROOT_PREFIXES.some((p) => token.startsWith(p))) {
    const c = [token];
    if (skill && token.startsWith("scripts/")) c.push(`${skill}/${token}`); // a skill's own scripts/
    if (token.startsWith("scripts/") && backend) c.push(`apps/backend/${token}`);
    if (token.startsWith("scripts/") && matchesAny(WEB_DOCS, docPath)) c.push(`apps/web/${token}`);
    return c;
  }
  if (token.startsWith("src/") && web) return [`apps/web/${token}`];
  if (backend && BACKEND_PREFIXES.some((p) => token.startsWith(p))) return [`apps/backend/${token}`];
  return null;
}

/** Check 1: relative Markdown links and backticked repo paths exist. */
export function checkPaths(doc, repo, { linksOnly = false } = {}) {
  const out = [];
  const dir = posix.dirname(doc.path);
  if (matchesAny(TEMPLATE_DOCS, doc.path)) return out;
  for (const line of prose(doc)) {
    // Markdown links (inline code removed so `[x](y)` examples are not links).
    const text = stripInlineCode(line.text);
    for (const m of text.matchAll(/!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)/g)) {
      const target = m[1];
      if (/^([a-z][a-z0-9+.-]*:|#|\/\/)/i.test(target) || /[<{]/.test(target)) continue;
      let p = decodeURI(target.replace(/[#?].*$/, ""));
      if (!p) continue;
      p = p.startsWith("/") ? p.slice(1) : posix.normalize(posix.join(dir, p));
      tally(repo, "links");
      if (p.startsWith("..")) {
        out.push(issue(doc.path, line.no, "link", `link escapes the repository: ${target}`));
      } else if (!repo.exists(p) && !isGenerated(p)) {
        out.push(issue(doc.path, line.no, "link", `broken link: ${target} (${p} does not exist)`));
      }
    }
    if (linksOnly || line.create) continue;
    // Backticked repo paths.
    for (const { code } of inlineCodeSpans(line.text)) {
      for (const raw of code.split(/\s+/)) {
        const token = cleanPathToken(raw);
        if (!token || PLACEHOLDER.test(token) || !/[/]/.test(token)) continue;
        const candidates = resolveCandidates(token, doc.path);
        if (!candidates) continue;
        tally(repo, "paths");
        if (candidates.some((c) => repo.exists(c) || isExempt(c))) continue;
        out.push(issue(doc.path, line.no, "path", `path not found: ${token}${candidates[0] !== token ? ` (looked for ${candidates.join(", ")})` : ""}`));
      }
    }
  }
  return out;
}

// ------------------------------------------------------------------------------ npm scripts

const ROOT_HINT = /\b(repo(sitory)? root|from the root|at the root|root `?package\.json|\(root\))/i;
const WEB_HINT = /\b(from|in|inside|within|under)\s+`?apps\/web\b|\(`?apps\/web`?\)|\bcd\s+`?apps\/web\b/;
const NPM_TOKEN = /\bcd\s+([^\s&;|)]+)|\bnpm\s+run\s+(?:-[-\w]+\s+)*([A-Za-z0-9][\w:.-]*\w)/g;

/** Map a `cd <dir>` target to a package context, or undefined when it says nothing useful. */
function cdContext(target) {
  const t = target.replace(/[`"']/g, "").replace(/\/$/, "");
  if (/(^|\/)apps\/web$/.test(t)) return "web";
  if (/(^|\/)apps\/backend$/.test(t)) return "backend";
  if (/^(\.\.\/\.\.|\$CI_PROJECT_DIR|\$\{CI_PROJECT_DIR\}|-)$/.test(t)) return "root";
  return undefined;
}

/** "root" | "web" | null from hint phrases in a piece of text (null when none or both). */
function hintContext(text) {
  const root = ROOT_HINT.test(text);
  const web = WEB_HINT.test(text) && !/\bapps\/backend\b/.test(text);
  return root === web ? null : root ? "root" : "web";
}

/**
 * Check 2: `npm run <script>` mentions exist in the right package.json.
 *
 * Context of each occurrence, first match wins:
 *   1. the working directory set by a preceding `cd apps/web|apps/backend|../..` (same line or
 *      earlier in the same code block), or by a comment line in the block ("# from the repo root");
 *   2. a qualifier right after it ("`npm run ci` at the root", "`npm run test:ci` (apps/web)") or a
 *      "root" right before it ("the root `npm run ci`");
 *   3. a hint anywhere on the line (only when the line hints at one package);
 *   4. a document under apps/web -> web;
 *   5. otherwise either package.json is accepted.
 */
export function checkNpmScripts(doc, repo) {
  const out = [];
  const blockCwd = new Map();
  for (const line of doc.lines) {
    if (line.block && !blockCwd.has(line.block)) blockCwd.set(line.block, null);
    let cwd = line.block ? blockCwd.get(line.block) : null;
    if (line.block && /^\s*(#|\/\/)/.test(line.text) && !/\bnpm\s+run\b/.test(line.text)) {
      cwd = hintContext(line.text) ?? cwd; // "# from the repo root", "# or inside apps/web"
    }
    const matches = [...line.text.matchAll(NPM_TOKEN)];
    // In prose a `cd` only applies inside its own inline code span.
    const spans = line.block ? [] : inlineCodeSpans(line.text).map((s) => [s.index, s.end]);
    const spanOf = (idx) => spans.findIndex(([a, b]) => idx >= a && idx <= b);
    let cdSpan = -2;
    matches.forEach((m, i) => {
      if (m[1]) {
        const ctx = cdContext(m[1]);
        if (ctx !== undefined) {
          cwd = ctx;
          cdSpan = spanOf(m.index);
        }
        return;
      }
      if (!line.block && cdSpan !== -2 && spanOf(m.index) !== cdSpan) {
        cwd = null;
        cdSpan = -2;
      }
      if (line.ignored) return;
      const name = m[2];
      tally(repo, "npm scripts");
      const next = matches.slice(i + 1).find((n) => n[2]);
      const after = line.text.slice(m.index + m[0].length, next ? next.index : undefined);
      const before = line.text.slice(Math.max(0, m.index - 12), m.index);
      let ctx = cwd;
      if (!ctx && /\broot\s*`?$/i.test(before)) ctx = "root";
      ctx ||= hintContext(after) || hintContext(line.text);
      if (!ctx && doc.path.startsWith("apps/web/")) ctx = "web";
      ctx ||= "either";
      const inRoot = repo.rootScripts.has(name);
      const inWeb = repo.webScripts.has(name);
      const [ok, where] = {
        root: [inRoot, "the root package.json"],
        web: [inWeb, "apps/web/package.json"],
        backend: [false, "apps/backend (it has no package.json)"],
        either: [inRoot || inWeb, "the root or the apps/web package.json"],
      }[ctx];
      if (ok) return;
      const hint =
        ctx !== "web" && inWeb
          ? ' (it exists in apps/web: add `cd apps/web` or say "from apps/web")'
          : ctx !== "root" && inRoot
            ? ' (it exists in the root package.json: say "from the repo root")'
            : "";
      out.push(issue(doc.path, line.no, "npm", `npm script "${name}" not found in ${where}${hint}`));
    });
    if (line.block) blockCwd.set(line.block, cwd);
  }
  return out;
}

// ------------------------------------------------------------------------------- env vars

/** Check 3: BE_* / VITE_* names exist in the env examples or config. */
export function checkEnvVars(doc, repo) {
  const out = [];
  for (const line of allLines(doc)) {
    for (const m of line.text.matchAll(/(?<![\w$])(BE|VITE)_([A-Z0-9_]*)(?![a-z])(\*|<|\{)?/g)) {
      const [, kind, rest, wildcard] = m;
      const known = kind === "BE" ? repo.beVars : repo.viteVars;
      tally(repo, "env vars");
      const where = kind === "BE" ? "apps/backend/.env.example or core/config.py" : "apps/web/env/.env.example or src/config/env.ts";
      if (wildcard === "<" || wildcard === "{") continue; // BE_<NAME>, VITE_{X} placeholders
      const full = `${kind}_${rest}`;
      const asWritten = wildcard === "*" ? `${full}*` : full;
      if (EXAMPLE_ENV_VARS.some((e) => (e.endsWith("*") ? asWritten.startsWith(e.slice(0, -1)) : e === asWritten))) continue;
      if (matchesAny(RECIPE_EXAMPLES.envVars, full)) continue;
      if (wildcard === "*" || rest.endsWith("_") || !rest) {
        const prefix = `${kind}_${rest}`;
        if (!rest || [...known].some((k) => k.startsWith(prefix))) continue;
        out.push(issue(doc.path, line.no, "env", `no ${prefix}* variable in ${where}`));
        continue;
      }
      const name = `${kind}_${rest}`;
      if (!known.has(name)) out.push(issue(doc.path, line.no, "env", `unknown env var ${name} (not in ${where})`));
    }
  }
  return out;
}

// ------------------------------------------------------------------------- python imports

const PY_LANGS = new Set(["python", "py", "python3"]);
const PY_IMPORT = /^[ \t]*from[ \t]+((?:core|db|dto|service|router|util|scripts)(?:\.\w+)*)[ \t]+import[ \t]+(\([^)]*\)|[^\n]*)/gm;

/** Check 4 (collect): backend `from X import Y` lines in Python code blocks. */
export function collectPythonImports(doc) {
  const found = [];
  for (const block of doc.blocks) {
    if (!PY_LANGS.has(block.lang)) continue;
    const text = block.lines.map((l) => l.text).join("\n");
    for (const m of text.matchAll(PY_IMPORT)) {
      const lineIdx = text.slice(0, m.index).split("\n").length - 1 + (text.slice(m.index).match(/^\n*/)[0].length);
      const line = block.lines[Math.min(lineIdx, block.lines.length - 1)];
      if (line.ignored || line.create) continue;
      const module = m[1];
      if (matchesAny(RECIPE_EXAMPLES.pythonModules, module)) continue;
      const names = m[2]
        .replace(/[()]/g, "")
        .replace(/#.*$/gm, "")
        .split(/[,\n]/)
        .map((n) => n.trim().split(/\s+as\s+/)[0].trim())
        .filter((n) => /^[A-Za-z_*][\w]*$/.test(n));
      const real = names.filter((n) => !matchesAny(RECIPE_EXAMPLES.pythonNames, n));
      if (real.length) found.push({ file: doc.path, line: line.no, module, names: real });
    }
  }
  return found;
}

/** Check 4 (report): map backend_probe import results back to the documents. */
export function reportPythonImports(collected, probeImports) {
  const errors = new Map(probeImports.filter((r) => r.error).map((r) => [`${r.module}\0${r.name}`, r.error]));
  const out = [];
  for (const item of collected) {
    for (const name of item.names) {
      const err = errors.get(`${item.module}\0${name}`);
      if (err) out.push(issue(item.file, item.line, "py-import", `from ${item.module} import ${name}: ${err}`));
    }
  }
  return out;
}

// ----------------------------------------------------------------------------- ts imports

const TS_LANGS = new Set(["ts", "tsx", "typescript", "js", "jsx", "javascript", "mjs"]);

function lineOf(block, text, index) {
  const idx = text.slice(0, index).split("\n").length - 1;
  return block.lines[Math.min(idx, block.lines.length - 1)];
}

/** Check 5: `@/…` imports in TS/JS code blocks resolve, and named imports are exported. */
export function checkTsImports(doc, repo) {
  const out = [];
  if (!matchesAny(TS_IMPORT_DOCS, doc.path)) return out;
  for (const block of doc.blocks) {
    if (!TS_LANGS.has(block.lang)) continue;
    const text = block.lines.map((l) => l.text).join("\n");
    const seen = [];
    const re = /\b(import|export)\s+(type\s+)?([^;'"`]*?)\s*from\s*['"](@\/[^'"]+)['"]|\bimport\s*\(\s*['"](@\/[^'"]+)['"]\s*\)|\bimport\s+['"](@\/[^'"]+)['"]|\bvi\.mock\(\s*['"](@\/[^'"]+)['"]/g;
    for (const m of text.matchAll(re)) {
      const spec = m[4] ?? m[5] ?? m[6] ?? m[7];
      const line = lineOf(block, text, m.index);
      if (line.ignored || line.create || /[{}<>[\]*]/.test(spec) || matchesAny(RECIPE_EXAMPLES.tsModules, spec)) continue;
      const base = `apps/web/src/${spec.slice(2)}`;
      if (["", ".ts", ".tsx", ".d.ts"].some((ext) => matchesAny(PLANNED_PATHS, base + ext))) continue;
      tally(repo, "ts imports");
      const file = repo.resolveWebModule(spec);
      if (!file) {
        out.push(issue(doc.path, line.no, "ts-import", `cannot resolve '${spec}' (no apps/web/src/${spec.slice(2)}[.ts|.tsx|/index.ts])`));
        continue;
      }
      if (!m[4] || !/\.(m?[jt]sx?)$/.test(file)) continue;
      const clause = m[3].trim();
      if (m[1] === "export" && /^\*/.test(clause)) continue;
      const wanted = [];
      const named = clause.match(/\{([\s\S]*)\}/);
      if (named) {
        for (const part of named[1].split(",")) {
          const n = part.replace(/^\s*type\s+/, "").trim().split(/\s+as\s+/)[0].trim();
          if (/^[A-Za-z_$][\w$]*$/.test(n)) wanted.push(n);
        }
      }
      const head = clause.replace(/\{[\s\S]*\}/, "").replace(/,/g, " ").trim();
      if (m[1] === "import" && /^[A-Za-z_$][\w$]*$/.test(head)) wanted.push("default");
      const exported = repo.exportsOf(file);
      for (const n of wanted) {
        if (!exported.has(n) && !matchesAny(RECIPE_EXAMPLES.tsNames, n)) {
          const key = `${spec}\0${n}`;
          if (seen.includes(key)) continue;
          seen.push(key);
          out.push(issue(doc.path, line.no, "ts-import", n === "default" ? `'${spec}' (${file}) has no default export` : `'${spec}' (${file}) does not export '${n}'`));
        }
      }
    }
  }
  return out;
}

// ------------------------------------------------------------------------------ endpoints

const METHOD_PATH = /`(GET|POST|PUT|PATCH|DELETE)\s+(\/[^`\s]*)`/g;
const normalizeRoute = (p) => p.replace(/\?.*$/, "").replace(/\{[^}]*\}/g, "{}").replace(/\/+$/, "") || "/";

function routeSet(routes) {
  return new Set(routes.map(([m, p]) => `${m} ${normalizeRoute(p)}`));
}

/** Check 6a: the docs/api-spec.md registry matches the app's routes, both ways. */
export function checkApiSpec(doc, routes, repo = null) {
  const out = [];
  const app = routeSet(routes);
  const documented = new Set();
  for (const line of prose(doc)) {
    const m = line.text.match(/^\s*\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*`([^`]+)`/);
    if (!m) continue;
    const key = `${m[1]} ${normalizeRoute(m[2].trim())}`;
    documented.add(key);
    tally(repo, "registry endpoints");
    if (!app.has(key)) out.push(issue(doc.path, line.no, "endpoint", `${key} is in the registry but not in the FastAPI app`));
  }
  for (const key of [...app].sort()) {
    if (!documented.has(key)) out.push(issue(doc.path, 1, "endpoint", `${key} exists in the FastAPI app but is missing from the ${API_SPEC} registry`));
  }
  return out;
}

/** Check 6b: backticked `METHOD /path` mentions in API docs and guides exist in the app. */
export function checkEndpointMentions(doc, routes, repo = null) {
  if (!matchesAny(ENDPOINT_DOCS, doc.path)) return [];
  const app = routeSet(routes);
  const out = [];
  for (const line of prose(doc)) {
    if (line.create) continue;
    for (const m of line.text.matchAll(METHOD_PATH)) {
      const path = normalizeRoute(m[2]);
      if (/[<*…]/.test(path) || matchesAny(RECIPE_EXAMPLES.endpoints, path)) continue;
      const key = `${m[1]} ${path}`;
      tally(repo, "endpoint mentions");
      if (!app.has(key)) out.push(issue(doc.path, line.no, "endpoint", `${key} is not a route of the FastAPI app`));
    }
  }
  return out;
}
