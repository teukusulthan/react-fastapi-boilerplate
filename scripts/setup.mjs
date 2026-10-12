#!/usr/bin/env node
// One-shot local setup for the monorepo (Windows, macOS, Linux).
//
//   node scripts/setup.mjs                 # backend + web
//   node scripts/setup.mjs backend         # apps/backend/.venv + requirements-dev.txt
//   node scripts/setup.mjs web             # npm ci in apps/web
//
// Options:
//   --python <version|path>   interpreter request for the backend venv (default: the
//                             backend's .python-version if present, else 3.12 with uv /
//                             the newest local Python >= 3.10 without uv)
//   --recreate                delete and recreate apps/backend/.venv
//   --no-uv                   do not use uv even if it is installed
//   --dry-run                 print the commands without running them
import { spawnSync } from "node:child_process";
import { copyFileSync, existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { randomBytes } from "node:crypto";
import { join } from "node:path";
import {
  BACKEND_DIR,
  VENV_DIR,
  WEB_DIR,
  color,
  commandExists,
  isWindows,
  log,
  npmInvocation,
  relativeToRoot,
  run,
  venvPython,
} from "./lib/common.mjs";

const MIN_PY = [3, 10];
const DEFAULT_UV_PY = "3.12";

function parseArgs(argv) {
  const opts = { targets: [], python: null, recreate: false, noUv: false, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") opts.help = true;
    else if (a === "--recreate") opts.recreate = true;
    else if (a === "--no-uv") opts.noUv = true;
    else if (a === "--dry-run") opts.dryRun = true;
    else if (a === "--python") opts.python = argv[++i];
    else if (a.startsWith("--python=")) opts.python = a.slice("--python=".length);
    else if (a === "backend" || a === "web") opts.targets.push(a);
    else {
      log.error(`Unknown argument: ${a}`);
      opts.help = true;
      opts.bad = true;
    }
  }
  if (opts.targets.length === 0) opts.targets = ["backend", "web"];
  return opts;
}

function usage() {
  console.log(`Usage: node scripts/setup.mjs [backend] [web] [--python <ver>] [--recreate] [--no-uv] [--dry-run]

  backend   create apps/backend/.venv (uv if available, else python -m venv) and
            install apps/backend/requirements-dev.txt; create apps/backend/.env from
            .env.example if it does not exist (random BE_JWT_SECRET, BE_INTERNAL_TOKEN,
            BE_DATA_ENCRYPTION_KEY and bootstrap-admin password)
  web       npm ci in apps/web (falls back to npm install if the lockfile is out of sync);
            create apps/web/env/.env from env/.env.example if no env file exists

With no target, both are set up.`);
}

/** Return "major.minor" for an interpreter command, or null if unusable / too old. */
function probePython(cmd, preArgs = []) {
  const res = spawnSync(cmd, [...preArgs, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"], {
    encoding: "utf8",
    shell: false,
  });
  if (res.error || res.status !== 0) return null;
  const [maj, min] = res.stdout.trim().split(".").map(Number);
  if (maj > MIN_PY[0] || (maj === MIN_PY[0] && min >= MIN_PY[1])) return { cmd, preArgs, version: `${maj}.${min}` };
  return null;
}

function findSystemPython(request) {
  const candidates = [];
  if (request) {
    if (isWindows && /^\d+\.\d+$/.test(request)) candidates.push(["py", [`-${request}`]]);
    candidates.push([/^\d+\.\d+$/.test(request) ? `python${request}` : request, []]);
  } else if (isWindows) {
    candidates.push(["py", ["-3.12"]], ["py", ["-3"]], ["python", []], ["python3", []]);
  } else {
    candidates.push(
      ["python3.12", []],
      ["python3.13", []],
      ["python3.11", []],
      ["python3.10", []],
      ["python3", []],
      ["python", []],
    );
  }
  for (const [cmd, pre] of candidates) {
    const found = probePython(cmd, pre);
    if (found) return found;
  }
  return null;
}

function ensureBackendEnv(dryRun) {
  const envFile = join(BACKEND_DIR, ".env");
  const example = join(BACKEND_DIR, ".env.example");
  if (existsSync(envFile) || !existsSync(example)) return;
  log.info(`Creating ${relativeToRoot(envFile)} from .env.example`);
  if (dryRun) return;
  let content = readFileSync(example, "utf8");
  // Replace empty / "change-me…" placeholder secrets with random values so the app boots.
  const fill = (name, value) => {
    content = content.replace(
      new RegExp(`^(${name}=)[ \\t]*(?:["']?change-me[^\\r\\n]*)?$`, "m"),
      (_match, key) => `${key}${value}`,
    );
  };
  fill("BE_JWT_SECRET", randomBytes(48).toString("hex"));
  fill("BE_INTERNAL_TOKEN", randomBytes(32).toString("hex"));
  // Fernet key (url-safe base64 of 32 bytes, padded) used to encrypt TOTP secrets at rest.
  fill("BE_DATA_ENCRYPTION_KEY", randomBytes(32).toString("base64").replace(/\+/g, "-").replace(/\//g, "_"));
  const adminPassword = randomBytes(12).toString("base64url");
  const before = content;
  fill("BE_BOOTSTRAP_ADMIN_PASSWORD", adminPassword);
  writeFileSync(envFile, content);
  log.ok(`Wrote ${relativeToRoot(envFile)} — review it before running the backend.`);
  if (content !== before) {
    const email = /^BE_BOOTSTRAP_ADMIN_EMAIL=(.*)$/m.exec(content)?.[1]?.trim() || "(BE_BOOTSTRAP_ADMIN_EMAIL)";
    log.info(`Bootstrap admin for \`npm run seed\`: ${email} / ${adminPassword} (stored in ${relativeToRoot(envFile)})`);
  }
}

async function setupBackend(opts) {
  console.log(color.bold("\nBackend (apps/backend)"));
  const reqDev = join(BACKEND_DIR, "requirements-dev.txt");
  const reqFile = existsSync(reqDev) ? reqDev : join(BACKEND_DIR, "requirements.txt");
  if (!existsSync(reqFile)) throw new Error(`No requirements file found in ${relativeToRoot(BACKEND_DIR)}`);

  if (opts.recreate && existsSync(VENV_DIR)) {
    log.info(`Removing ${relativeToRoot(VENV_DIR)}`);
    if (!opts.dryRun) rmSync(VENV_DIR, { recursive: true, force: true });
  }

  const useUv = !opts.noUv && commandExists("uv");
  const venvExists = existsSync(venvPython());
  const hasPinFile = existsSync(join(BACKEND_DIR, ".python-version"));

  if (useUv) {
    if (!venvExists || opts.recreate) {
      const pyArgs = opts.python ? ["--python", opts.python] : hasPinFile ? [] : ["--python", DEFAULT_UV_PY];
      const code = await run("uv", ["venv", ".venv", ...pyArgs], { cwd: BACKEND_DIR, dryRun: opts.dryRun });
      if (code !== 0) throw new Error("uv venv failed");
    } else {
      log.ok(`Re-using existing ${relativeToRoot(VENV_DIR)} (pass --recreate to rebuild it)`);
    }
    const code = await run("uv", ["pip", "install", "--python", venvPython(), "-r", relativeToRoot(reqFile)], {
      dryRun: opts.dryRun,
    });
    if (code !== 0) throw new Error("uv pip install failed");
  } else {
    if (!venvExists || opts.recreate) {
      const py = findSystemPython(opts.python);
      if (!py) {
        throw new Error(
          `No Python >= ${MIN_PY.join(".")} found. Install Python 3.12 (or uv: https://docs.astral.sh/uv/) and retry.`,
        );
      }
      log.info(`Using ${[py.cmd, ...py.preArgs].join(" ")} (Python ${py.version})`);
      const code = await run(py.cmd, [...py.preArgs, "-m", "venv", ".venv"], { cwd: BACKEND_DIR, dryRun: opts.dryRun });
      if (code !== 0) throw new Error("python -m venv failed");
    } else {
      log.ok(`Re-using existing ${relativeToRoot(VENV_DIR)} (pass --recreate to rebuild it)`);
    }
    // Venvs created by uv have no pip; bootstrap it if needed.
    if (!opts.dryRun && spawnSync(venvPython(), ["-m", "pip", "--version"], { stdio: "ignore" }).status !== 0) {
      const ensure = await run(venvPython(), ["-m", "ensurepip", "--upgrade"]);
      if (ensure !== 0) throw new Error("ensurepip failed (try --recreate)");
    }
    let code = await run(venvPython(), ["-m", "pip", "install", "--upgrade", "pip"], { dryRun: opts.dryRun });
    if (code !== 0) throw new Error("pip upgrade failed");
    code = await run(venvPython(), ["-m", "pip", "install", "-r", relativeToRoot(reqFile)], { dryRun: opts.dryRun });
    if (code !== 0) throw new Error("pip install failed");
  }

  ensureBackendEnv(opts.dryRun);
  log.ok("Backend ready. Run it with `npm run dev:backend` (http://localhost:8020/docs).");
}

function ensureWebEnv(dryRun) {
  const envDir = join(WEB_DIR, "env");
  const example = join(envDir, ".env.example");
  if (!existsSync(example)) return;
  const existing = [".env", ".env.local", ".env.development", ".env.development.local"].some((f) =>
    existsSync(join(envDir, f)),
  );
  if (existing) return;
  log.info(`Creating ${relativeToRoot(join(envDir, ".env"))} from env/.env.example`);
  if (!dryRun) copyFileSync(example, join(envDir, ".env"));
}

async function setupWeb(opts) {
  console.log(color.bold("\nWeb (apps/web)"));
  const hasLock = existsSync(join(WEB_DIR, "package-lock.json"));
  const base = ["--prefix", relativeToRoot(WEB_DIR), "--no-audit", "--no-fund"];
  let code = 1;
  if (hasLock) {
    const inv = npmInvocation(["ci", ...base]);
    code = await run(inv.cmd, inv.args, { shell: inv.shell, dryRun: opts.dryRun });
    if (code !== 0) log.warn("npm ci failed (lockfile out of sync?) — falling back to npm install");
  }
  if (code !== 0) {
    const inv = npmInvocation(["install", ...base]);
    code = await run(inv.cmd, inv.args, { shell: inv.shell, dryRun: opts.dryRun });
    if (code !== 0) throw new Error("npm install failed");
  }
  ensureWebEnv(opts.dryRun);
  log.ok("Web ready. Run it with `npm run dev:web` (http://localhost:3000).");
}

const opts = parseArgs(process.argv.slice(2));
if (opts.help) {
  usage();
  process.exit(opts.bad ? 1 : 0);
}

try {
  if (opts.targets.includes("backend")) await setupBackend(opts);
  if (opts.targets.includes("web")) await setupWeb(opts);
  console.log(`\n${color.green("Setup complete.")} Start everything with ${color.bold("npm run dev")}.`);
} catch (err) {
  log.error(err.message);
  process.exit(1);
}
