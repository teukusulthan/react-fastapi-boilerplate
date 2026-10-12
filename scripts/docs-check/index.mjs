#!/usr/bin/env node
// Docs consistency checker: fails when the Markdown docs drift from the code.
//
//   node scripts/docs-check/index.mjs                 (= npm run docs:check)
//   node scripts/docs-check/index.mjs --skip-backend  (no venv: skip Python imports + endpoints)
//   node scripts/docs-check/index.mjs AGENTS.md docs/api-spec.md   (only these files)
//
// See scripts/docs-check/README.md for the checks and the ignore markers.
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { API_SPEC, LINKS_ONLY, SCOPE } from "./config.mjs";
import {
  checkApiSpec,
  checkEndpointMentions,
  checkEnvVars,
  checkNpmScripts,
  checkPaths,
  checkTsImports,
  collectPythonImports,
  reportPythonImports,
} from "./lib/checks.mjs";
import { parseMarkdown } from "./lib/markdown.mjs";
import { listRepoFiles, probeBackend, Repo } from "./lib/repo.mjs";

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

/**
 * Run every check. Returns { issues, files, skippedBackend }.
 * @param {{root?: string, only?: string[], skipBackend?: boolean, backend?: object, files?: string[]}} [opts]
 *   `backend` injects precomputed backend facts ({routes, settings, imports}); tests use it.
 */
export function runDocsCheck(opts = {}) {
  const root = opts.root ?? ROOT;
  const files = opts.files ?? listRepoFiles(root);
  const inScope = files.filter((f) => SCOPE.some((re) => re.test(f)) || LINKS_ONLY.some((re) => re.test(f)));
  const targets = opts.only?.length ? inScope.filter((f) => opts.only.includes(f)) : inScope;
  const repo = new Repo(root, { files });
  repo.stats = {};
  const docs = targets.sort().map((path) => ({ path, linksOnly: LINKS_ONLY.some((re) => re.test(path)), ...parseMarkdown(readFileSync(join(root, path), "utf8")) }));

  const issues = [];
  const pyImports = [];
  for (const doc of docs) {
    issues.push(...checkPaths(doc, repo, { linksOnly: doc.linksOnly }));
    if (doc.linksOnly) continue;
    issues.push(...checkNpmScripts(doc, repo), ...checkTsImports(doc, repo));
    pyImports.push(...collectPythonImports(doc));
  }

  let backend = opts.backend ?? null;
  const skippedBackend = !backend && !!opts.skipBackend;
  if (!backend && !opts.skipBackend) {
    const unique = new Map();
    for (const { module, names } of pyImports) {
      const set = unique.get(module) ?? new Set();
      names.forEach((n) => set.add(n));
      unique.set(module, set);
    }
    backend = probeBackend(root, [...unique].map(([module, names]) => ({ module, names: [...names] })));
  }
  repo.backend = backend;

  for (const doc of docs) if (!doc.linksOnly) issues.push(...checkEnvVars(doc, repo));
  if (backend) {
    issues.push(...reportPythonImports(pyImports, backend.imports ?? []));
    repo.stats["py imports"] = pyImports.reduce((n, i) => n + i.names.length, 0);
    repo.stats["app routes"] = backend.routes.length;
    for (const doc of docs) {
      if (doc.linksOnly) continue;
      if (doc.path === API_SPEC) issues.push(...checkApiSpec(doc, backend.routes, repo));
      issues.push(...checkEndpointMentions(doc, backend.routes, repo));
    }
  }
  issues.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line);
  return { issues, files: docs.length, skippedBackend, stats: repo.stats };
}

function main(argv) {
  const started = Date.now();
  const skipBackend = argv.includes("--skip-backend") || process.env.DOCS_CHECK_SKIP_BACKEND === "1";
  const only = argv.filter((a) => !a.startsWith("--")).map((a) => a.replace(/\\/g, "/").replace(/^\.\//, ""));
  let result;
  try {
    result = runDocsCheck({ skipBackend, only });
  } catch (err) {
    console.error(`docs-check: ${err.message}`);
    return 2;
  }
  const { issues, files, skippedBackend, stats } = result;
  const counted = Object.entries(stats).map(([k, v]) => `${v} ${k}`).join(", ");
  for (const i of issues) console.error(`${i.file}:${i.line}: [${i.check}] ${i.message}`);
  const secs = ((Date.now() - started) / 1000).toFixed(1);
  const note = skippedBackend ? " (backend checks skipped)" : "";
  if (issues.length) {
    console.error(`\ndocs-check: ${issues.length} problem(s) in ${files} file(s) checked, ${secs}s${note}.`);
    console.error("Fix the docs, or mark intentional cases (see scripts/docs-check/README.md).");
    return 1;
  }
  console.log(`docs-check: ${files} file(s) OK, ${secs}s${note}.\n  verified: ${counted}`);
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
