#!/usr/bin/env node
// Run the Playwright e2e smoke suite (apps/web/e2e) against a REAL backend.
//
//   node scripts/e2e.mjs --docker                    # throwaway Mongo + Redis containers (removed afterwards)
//   E2E_MONGO_URI=mongodb://localhost:57017 E2E_REDIS_URL=redis://localhost:56379/0 node scripts/e2e.mjs
//   node scripts/e2e.mjs --no-backend                # backend already running at E2E_API_URL
//   node scripts/e2e.mjs --docker -- --headed        # everything after `--` goes to `playwright test`
//
// Steps: [docker: start mongo:7 + redis:7] -> seed (permissions + bootstrap admin) -> start the backend
// (venv python api.py, isolated BE_* env, never apps/backend/.env) -> wait for /health/ready ->
// `npm run test:e2e` in apps/web (Playwright builds + previews the web app) -> stop everything.
// Backend output goes to .cache/e2e/backend.log (printed on failure).
import { spawn, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { createWriteStream, existsSync, mkdirSync, readFileSync } from "node:fs";
import net from "node:net";
import { join } from "node:path";
import {
  BACKEND_DIR,
  ROOT,
  WEB_DIR,
  color,
  commandExists,
  hasVenv,
  isWindows,
  log,
  npmInvocation,
  venvPython,
} from "./lib/common.mjs";

const READY_TIMEOUT_MS = 90_000;
const STOP_GRACE_MS = 10_000;
const LOG_DIR = join(ROOT, ".cache", "e2e");
const BACKEND_LOG = join(LOG_DIR, "backend.log");
const DOCKER = {
  mongo: { name: "rfb-e2e-mongo", image: "mongo:7", port: 57017, containerPort: 27017 },
  redis: { name: "rfb-e2e-redis", image: "redis:7", port: 56379, containerPort: 6379 },
};

// ---------------------------------------------------------------------------- args
const rawArgs = process.argv.slice(2);
const sep = rawArgs.indexOf("--");
const ownArgs = sep === -1 ? rawArgs : rawArgs.slice(0, sep);
const playwrightArgs = sep === -1 ? [] : rawArgs.slice(sep + 1);

if (ownArgs.includes("--help") || ownArgs.includes("-h")) {
  console.log(`Usage: node scripts/e2e.mjs [--docker | --no-backend] [-- <playwright test args>]

  --docker       Start throwaway containers ${DOCKER.mongo.name} (${DOCKER.mongo.image}, 127.0.0.1:${DOCKER.mongo.port})
                 and ${DOCKER.redis.name} (${DOCKER.redis.image}, 127.0.0.1:${DOCKER.redis.port}); removed afterwards.
  --no-backend   Do not seed or start a backend; run Playwright against E2E_API_URL / E2E_BASE_URL.

Env (defaults in brackets):
  E2E_MONGO_URI       Mongo for the e2e backend (required without --docker/--no-backend)
  E2E_MONGO_DB        Database name [app_e2e]
  E2E_REDIS_URL       Redis URL, e.g. redis://:password@localhost:6379/0 (required without --docker/--no-backend)
  E2E_BACKEND_PORT    Port of the e2e backend [8021]
  E2E_ADMIN_EMAIL     Bootstrap admin email [admin@example.com]
  E2E_ADMIN_PASSWORD  Bootstrap admin password [e2e-admin-password]
  E2E_WEB_PORT, E2E_BASE_URL, E2E_SKIP_BUILD, E2E_REUSE_SERVER: see apps/web/e2e/README.md

The backend never reads apps/backend/.env here; it gets an isolated BE_* environment
(random JWT secret, BE_COOKIE_SECURE=false, console email backend, Redis key prefix "e2e").`);
  process.exit(0);
}
const known = new Set(["--docker", "--no-backend"]);
const unknown = ownArgs.filter((a) => !known.has(a));
if (unknown.length) {
  log.error(`Unknown argument(s): ${unknown.join(", ")} (see --help; Playwright args go after --)`);
  process.exit(1);
}
const useDocker = ownArgs.includes("--docker");
const noBackend = ownArgs.includes("--no-backend");
if (useDocker && noBackend) {
  log.error("--docker and --no-backend are mutually exclusive");
  process.exit(1);
}

const env = (key, fallback) => process.env[key]?.trim() || fallback;
const ADMIN_EMAIL = env("E2E_ADMIN_EMAIL", "admin@example.com");
const ADMIN_PASSWORD = env("E2E_ADMIN_PASSWORD", "e2e-admin-password");
const BACKEND_PORT = Number(env("E2E_BACKEND_PORT", "8021"));
const API_URL = noBackend ? env("E2E_API_URL", "http://127.0.0.1:8020") : `http://127.0.0.1:${BACKEND_PORT}`;
const MONGO_URI = useDocker ? `mongodb://127.0.0.1:${DOCKER.mongo.port}` : env("E2E_MONGO_URI");
const REDIS_URL = useDocker ? `redis://127.0.0.1:${DOCKER.redis.port}/0` : env("E2E_REDIS_URL");
const MONGO_DB = env("E2E_MONGO_DB", "app_e2e");
const WEB_ORIGIN = env("E2E_BASE_URL", `http://127.0.0.1:${env("E2E_WEB_PORT", "4173")}`);

// ----------------------------------------------------------------------- helpers
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function portInUse(port) {
  return new Promise((resolve) => {
    const sock = net.connect({ port, host: "127.0.0.1" });
    const done = (inUse) => {
      sock.destroy();
      resolve(inUse);
    };
    sock.setTimeout(500, () => done(false));
    sock.once("connect", () => done(true));
    sock.once("error", () => done(false));
  });
}

/** Run to completion with inherited stdio; resolves with the exit code. */
function runStep(cmd, args, opts) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { stdio: "inherit", ...opts });
    child.on("error", reject);
    child.on("exit", (code, signal) => resolve(code ?? (signal ? 1 : 0)));
  });
}

function killTree(child, signal) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  if (isWindows) {
    spawnSync("taskkill", ["/pid", String(child.pid), "/T", "/F"], { stdio: "ignore" });
    return;
  }
  try {
    process.kill(-child.pid, signal);
  } catch {
    try {
      child.kill(signal);
    } catch {
      /* already gone */
    }
  }
}

function backendEnv() {
  // Only BE_* keys we set: inherit the rest of the environment but drop any BE_* from the shell.
  const base = Object.fromEntries(Object.entries(process.env).filter(([k]) => !k.startsWith("BE_")));
  return {
    ...base,
    PYTHONUNBUFFERED: "1",
    // A path that never exists: the backend must not pick up apps/backend/.env.
    BE_ENV_FILE: join(LOG_DIR, "no-env-file"),
    BE_ENVIRONMENT: "development",
    BE_HOST: "127.0.0.1",
    BE_PORT: String(BACKEND_PORT),
    BE_RELOAD: "false",
    BE_WORKERS: "1",
    BE_DB_PROVIDER: "mongo",
    BE_AUTH_PROVIDER: "local",
    BE_MONGO_URI: MONGO_URI,
    BE_MONGO_DB: MONGO_DB,
    BE_REDIS_URL: REDIS_URL,
    BE_REDIS_KEY_PREFIX: "e2e",
    BE_JWT_SECRET: randomBytes(32).toString("hex"),
    BE_COOKIE_SECURE: "false",
    BE_EMAIL_BACKEND: "console",
    BE_PUBLIC_WEB_URL: WEB_ORIGIN,
    // Repeated local runs must not hit the per-IP auth limit (10/min by default); it stays enabled.
    BE_RATE_LIMIT_AUTH: "100",
    BE_BOOTSTRAP_ADMIN_EMAIL: ADMIN_EMAIL,
    BE_BOOTSTRAP_ADMIN_PASSWORD: ADMIN_PASSWORD,
    BE_BOOTSTRAP_ADMIN_USERNAME: "admin",
    BE_BOOTSTRAP_ADMIN_FULLNAME: "Administrator",
  };
}

async function waitFor(label, check, timeoutMs, isDead = () => false) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (isDead()) throw new Error(`${label}: process exited early`);
    if (await check()) return;
    await sleep(1000);
  }
  throw new Error(`${label}: not ready after ${timeoutMs / 1000}s`);
}

async function httpOk(url) {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(2000) });
    await res.body?.cancel();
    return res.ok;
  } catch {
    return false;
  }
}

function mongoPing() {
  const code = "import sys\nfrom pymongo import MongoClient\nMongoClient(sys.argv[1], serverSelectionTimeoutMS=2000).admin.command('ping')";
  const res = spawnSync(venvPython(), ["-c", code, MONGO_URI], { cwd: BACKEND_DIR, stdio: "ignore" });
  return res.status === 0;
}

function tailLog(lines = 60) {
  if (!existsSync(BACKEND_LOG)) return;
  const text = readFileSync(BACKEND_LOG, "utf8").trimEnd().split(/\r?\n/).slice(-lines).join("\n");
  console.log(color.dim(`--- last ${lines} lines of ${BACKEND_LOG} ---\n${text}\n---`));
}

// ------------------------------------------------------------------------- state
const started = { containers: [], backend: null };
let cleaningUp = null;

async function cleanup() {
  if (cleaningUp) return cleaningUp;
  cleaningUp = (async () => {
    const backend = started.backend;
    if (backend && backend.exitCode === null && backend.signalCode === null) {
      log.info("Stopping backend …");
      const exited = new Promise((r) => backend.once("exit", r));
      killTree(backend, "SIGTERM");
      const timer = setTimeout(() => killTree(backend, "SIGKILL"), STOP_GRACE_MS);
      await exited;
      clearTimeout(timer);
    }
    for (const name of started.containers) {
      log.info(`Removing container ${name} …`);
      spawnSync("docker", ["rm", "-f", "-v", name], { stdio: "ignore" });
    }
  })();
  return cleaningUp;
}

let interrupted = false;
for (const sig of ["SIGINT", "SIGTERM", ...(isWindows ? [] : ["SIGHUP"])]) {
  process.on(sig, async () => {
    if (interrupted) process.exit(130);
    interrupted = true;
    log.warn(`${sig} received — cleaning up (again to force)`);
    await cleanup();
    process.exit(130);
  });
}

// -------------------------------------------------------------------------- main
async function startContainers() {
  if (!commandExists("docker", ["info"])) throw new Error("--docker needs a running Docker daemon (`docker info` failed)");
  for (const svc of Object.values(DOCKER)) {
    spawnSync("docker", ["rm", "-f", "-v", svc.name], { stdio: "ignore" }); // leftovers of an aborted run
    if (await portInUse(svc.port)) throw new Error(`Port ${svc.port} is already in use (needed for ${svc.name})`);
    log.info(`Starting ${svc.name} (${svc.image}) on 127.0.0.1:${svc.port}`);
    const res = spawnSync(
      "docker",
      ["run", "-d", "--name", svc.name, "-p", `127.0.0.1:${svc.port}:${svc.containerPort}`, svc.image],
      { stdio: ["ignore", "ignore", "inherit"] },
    );
    if (res.status !== 0) throw new Error(`docker run ${svc.image} failed`);
    started.containers.push(svc.name);
  }
}

async function startBackend() {
  if (!hasVenv()) throw new Error(`Backend virtualenv missing (${venvPython()}). Run \`npm run setup:backend\`.`);
  if (!MONGO_URI || !REDIS_URL) {
    throw new Error("Set E2E_MONGO_URI and E2E_REDIS_URL (dedicated, disposable services), or pass --docker / --no-backend.");
  }
  if (await portInUse(BACKEND_PORT)) throw new Error(`Port ${BACKEND_PORT} is already in use (set E2E_BACKEND_PORT)`);

  log.info(`Waiting for Mongo (db ${MONGO_DB}) …`);
  await waitFor("Mongo", async () => mongoPing(), 60_000);

  const beEnv = backendEnv();
  log.info("Seeding permissions + bootstrap admin …");
  const seedCode = await runStep(venvPython(), ["-m", "scripts.seed"], { cwd: BACKEND_DIR, env: beEnv });
  if (seedCode !== 0) throw new Error(`Seed failed (exit ${seedCode})`);

  log.info(`Starting backend on 127.0.0.1:${BACKEND_PORT} (log: ${BACKEND_LOG})`);
  const out = createWriteStream(BACKEND_LOG, { flags: "w" });
  const child = spawn(venvPython(), ["api.py"], {
    cwd: BACKEND_DIR,
    env: beEnv,
    stdio: ["ignore", "pipe", "pipe"],
    detached: !isWindows,
    windowsHide: true,
  });
  child.stdout.pipe(out);
  child.stderr.pipe(out);
  started.backend = child;
  await waitFor(
    "Backend /health/ready",
    () => httpOk(`${API_URL}/health/ready`),
    READY_TIMEOUT_MS,
    () => child.exitCode !== null || child.signalCode !== null,
  );
  log.ok(`Backend ready at ${API_URL}`);
}

let exitCode = 1;
try {
  mkdirSync(LOG_DIR, { recursive: true });
  if (useDocker) await startContainers();
  if (!noBackend) await startBackend();

  const inv = npmInvocation(["run", "test:e2e", ...(playwrightArgs.length ? ["--", ...playwrightArgs] : [])]);
  log.info(`Running Playwright (API ${API_URL}) …`);
  exitCode = await runStep(inv.cmd, inv.args, {
    cwd: WEB_DIR,
    shell: inv.shell,
    env: { ...process.env, E2E_API_URL: API_URL, E2E_ADMIN_EMAIL: ADMIN_EMAIL, E2E_ADMIN_PASSWORD: ADMIN_PASSWORD },
  });
  if (exitCode === 0) log.ok("E2E suite passed");
  else log.error(`E2E suite failed (exit ${exitCode}). Report: apps/web/playwright-report (npm run test:e2e:report in apps/web)`);
} catch (err) {
  log.error(err instanceof Error ? err.message : String(err));
  exitCode = 1;
} finally {
  if (exitCode !== 0 && !noBackend) tailLog();
  await cleanup();
}
process.exit(exitCode);
