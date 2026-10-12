// Repository facts used by the checks: the file tree, package.json scripts, env keys, the web
// module graph (for `@/…` imports) and the backend facts from backend_probe.py.
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, posix } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SKIP_DIRS = new Set([".git", "node_modules", ".venv", "__pycache__", ".nx", ".cache", "build", ".pytest_cache", ".ruff_cache", "coverage", ".ui-snapshots"]);

/** Every file of the working tree that a clean checkout would have (tracked + untracked, not ignored). */
export function listRepoFiles(root) {
  const git = spawnSync("git", ["ls-files", "-z", "--cached", "--others", "--exclude-standard"], {
    cwd: root,
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (git.status === 0 && git.stdout) {
    // Drop files deleted in the working tree (still in the index until committed).
    return git.stdout.split("\0").filter((f) => f && existsSync(join(root, f)));
  }
  const out = [];
  const walk = (rel) => {
    for (const entry of readdirSync(join(root, rel), { withFileTypes: true })) {
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(entry.name)) walk(rel ? `${rel}/${entry.name}` : entry.name);
      } else out.push(rel ? `${rel}/${entry.name}` : entry.name);
    }
  };
  walk("");
  return out;
}

export class Repo {
  /** @param {string} root @param {{files?: string[], backend?: object|null}} [opts] */
  constructor(root, opts = {}) {
    this.root = root;
    this.files = new Set(opts.files ?? listRepoFiles(root));
    this.dirs = new Set();
    for (const f of this.files) {
      let d = posix.dirname(f);
      while (d && d !== "." && !this.dirs.has(d)) {
        this.dirs.add(d);
        d = posix.dirname(d);
      }
    }
    this.backend = opts.backend ?? null;
    this._exports = new Map();
  }

  exists(rel) {
    const p = posix.normalize(rel).replace(/\/$/, "");
    return p === "." || p === "" || this.files.has(p) || this.dirs.has(p);
  }

  read(rel) {
    try {
      return readFileSync(join(this.root, rel), "utf8");
    } catch {
      return "";
    }
  }

  scripts(pkgRel) {
    try {
      return new Set(Object.keys(JSON.parse(this.read(pkgRel)).scripts ?? {}));
    } catch {
      return new Set();
    }
  }

  get rootScripts() {
    return (this._rootScripts ??= this.scripts("package.json"));
  }

  get webScripts() {
    return (this._webScripts ??= this.scripts("apps/web/package.json"));
  }

  /** Known BE_* names: .env.example keys, literals in core/config.py, BE_ + Settings fields. */
  get beVars() {
    if (this._beVars) return this._beVars;
    const names = new Set();
    for (const m of this.read("apps/backend/.env.example").matchAll(/^[#\s]*(BE_[A-Z0-9_]+)\s*=/gm)) names.add(m[1]);
    const config = this.read("apps/backend/core/config.py");
    for (const m of config.matchAll(/\bBE_[A-Z0-9_]*[A-Z0-9]\b/g)) names.add(m[0]);
    const fields = this.backend?.settings ?? [...config.matchAll(/^ {4}([A-Z][A-Z0-9_]*)\s*:/gm)].map((m) => m[1]);
    for (const f of fields) names.add(`BE_${f}`);
    return (this._beVars = names);
  }

  /** Known VITE_* names: env/.env.example keys and literals in src/config/env.ts. */
  get viteVars() {
    if (this._viteVars) return this._viteVars;
    const names = new Set();
    for (const m of this.read("apps/web/env/.env.example").matchAll(/^[#\s]*(VITE_[A-Z0-9_]+)\s*=/gm)) names.add(m[1]);
    for (const m of this.read("apps/web/src/config/env.ts").matchAll(/\bVITE_[A-Z0-9_]*[A-Z0-9]\b/g)) names.add(m[0]);
    return (this._viteVars = names);
  }

  /** Resolve a web module specifier (`@/x` or a path relative to `fromFile`) to a repo file. */
  resolveWebModule(spec, fromFile = null) {
    let base;
    if (spec.startsWith("@/")) base = `apps/web/src/${spec.slice(2)}`;
    else if (spec.startsWith(".") && fromFile) base = posix.normalize(posix.join(posix.dirname(fromFile), spec));
    else return null;
    const candidates = [base, ...[".ts", ".tsx", ".d.ts", ".js", ".jsx", ".mjs"].map((e) => base + e), ...["index.ts", "index.tsx", "index.js"].map((i) => `${base}/${i}`)];
    return candidates.find((c) => this.files.has(c)) ?? null;
  }

  /** Exported names of a web module (regex based; follows `export * from` barrels). */
  exportsOf(file, seen = new Set()) {
    if (this._exports.has(file)) return this._exports.get(file);
    if (seen.has(file)) return new Set();
    seen.add(file);
    const src = this.read(file).replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    const names = new Set();
    const decl = /export\s+(?:declare\s+)?(?:default\s+)?(?:abstract\s+)?(?:async\s+)?(?:const|let|var|function\*?|class|type|interface|enum|namespace)\s+([A-Za-z_$][\w$]*)/g;
    for (const m of src.matchAll(decl)) names.add(m[1]);
    for (const m of src.matchAll(/export\s+(?:const|let|var)\s+\{([^}]*)\}/g)) {
      for (const part of m[1].split(",")) {
        const n = part.split(":").pop().trim();
        if (n) names.add(n);
      }
    }
    if (/export\s+default\b/.test(src) || /export\s*\{[^}]*\bas\s+default\b/.test(src)) names.add("default");
    for (const m of src.matchAll(/export\s+(?:type\s+)?\{([^}]*)\}/g)) {
      for (const part of m[1].split(",")) {
        const p = part.replace(/^\s*type\s+/, "").trim();
        if (!p) continue;
        const alias = p.split(/\s+as\s+/).pop().trim();
        names.add(alias);
      }
    }
    for (const m of src.matchAll(/export\s+\*\s+as\s+([A-Za-z_$][\w$]*)\s+from/g)) names.add(m[1]);
    for (const m of src.matchAll(/export\s+\*\s+from\s+['"]([^'"]+)['"]/g)) {
      const target = this.resolveWebModule(m[1], file);
      if (target) for (const n of this.exportsOf(target, seen)) if (n !== "default") names.add(n);
    }
    this._exports.set(file, names);
    return names;
  }
}

/**
 * Run backend_probe.py with the backend venv. Returns { routes, settings, imports } or throws.
 * @param {string} root
 * @param {{module: string, names: string[]}[]} imports
 */
export function probeBackend(root, imports) {
  const python = process.platform === "win32" ? join(root, "apps", "backend", ".venv", "Scripts", "python.exe") : join(root, "apps", "backend", ".venv", "bin", "python");
  if (!existsSync(python) || !statSync(python).isFile()) {
    throw new Error(`backend virtualenv not found at ${python} (run \`npm run setup:backend\`, or pass --skip-backend)`);
  }
  const res = spawnSync(python, [join(HERE, "..", "backend_probe.py")], {
    cwd: join(root, "apps", "backend"),
    input: JSON.stringify({ imports }),
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
  });
  if (res.status !== 0) throw new Error(`backend_probe.py failed (exit ${res.status}):\n${res.stderr || res.stdout}`);
  return JSON.parse(res.stdout);
}
