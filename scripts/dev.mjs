#!/usr/bin/env node
// Run the backend (FastAPI, :8020) and web (Vite, :3000) dev servers together.
//
//   node scripts/dev.mjs            # both
//   node scripts/dev.mjs backend    # backend only
//   node scripts/dev.mjs web        # web only
//
// Output of each process is prefixed with its name. Readiness is detected from the
// process output and by probing the HTTP port. Ctrl+C stops every child process tree
// (Uvicorn reloader + workers, npm + Vite) and waits for a clean exit.
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import net from "node:net";
import { join } from "node:path";
import {
  BACKEND_DIR,
  BACKEND_PORT,
  WEB_DIR,
  WEB_PORT,
  color,
  hasVenv,
  isWindows,
  log,
  npmInvocation,
  venvPython,
} from "./lib/common.mjs";

const READY_TIMEOUT_MS = 120_000;
const STOP_GRACE_MS = 10_000;

const SERVICES = {
  backend: () => ({
    name: "backend",
    paint: color.cyan,
    cwd: BACKEND_DIR,
    cmd: venvPython(),
    args: ["api.py"],
    shell: false,
    // Auto-reload on code changes in dev (export BE_RELOAD=false to disable).
    env: { BE_RELOAD: "true", ...process.env, PYTHONUNBUFFERED: "1" },
    port: BACKEND_PORT,
    probePath: "/health/live",
    readyPattern: /Uvicorn running on|Application startup complete/i,
    urls: () => [
      ["API", `http://localhost:${BACKEND_PORT}`],
      ["Docs", `http://localhost:${BACKEND_PORT}/docs`],
    ],
    preflight: () => (hasVenv() ? null : `Backend virtualenv missing (${venvPython()}). Run \`npm run setup:backend\`.`),
  }),
  web: () => {
    const inv = npmInvocation(["run", "dev"]);
    return {
      name: "web",
      paint: color.magenta,
      cwd: WEB_DIR,
      cmd: inv.cmd,
      args: inv.args,
      shell: inv.shell,
      // Children write to a pipe; keep colours only when we are attached to a terminal.
      env: process.stdout.isTTY ? { ...process.env, FORCE_COLOR: "1" } : process.env,
      port: WEB_PORT,
      probePath: "/",
      readyPattern: /Local:\s+https?:\/\/\S+/i,
      urls: () => [["Web", `http://localhost:${WEB_PORT}`]],
      preflight: () =>
        existsSync(join(WEB_DIR, "node_modules"))
          ? null
          : "Web dependencies missing (apps/web/node_modules). Run `npm run setup:web`.",
    };
  },
};

// ---------------------------------------------------------------------------- args
const argv = process.argv.slice(2);
if (argv.includes("--help") || argv.includes("-h")) {
  console.log(`Usage: node scripts/dev.mjs [backend] [web]

Starts the selected dev servers (default: both) with prefixed output.
  backend  apps/backend: <venv python> api.py      -> http://localhost:${BACKEND_PORT}
  web      apps/web:     npm run dev               -> http://localhost:${WEB_PORT}
Env: BACKEND_PORT / WEB_PORT only change the readiness probe and banner; the servers
read their own ports from apps/backend/.env and apps/web/vite.config.ts.`);
  process.exit(0);
}
const unknown = argv.filter((a) => !(a in SERVICES));
if (unknown.length) {
  log.error(`Unknown argument(s): ${unknown.join(", ")} (expected: backend, web)`);
  process.exit(1);
}
const selected = (argv.length ? [...new Set(argv)] : ["backend", "web"]).map((n) => SERVICES[n]());

// ----------------------------------------------------------------------- helpers
const pad = Math.max(...selected.map((s) => s.name.length));
const prefixFor = (svc) => svc.paint(`[${svc.name}]`.padEnd(pad + 2));
// eslint-disable-next-line no-control-regex
const stripAnsi = (s) => s.replace(/\x1b\[[0-9;?]*[A-Za-z]/g, "");

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

async function probeHttp(port, path) {
  for (const host of ["127.0.0.1", "[::1]"]) {
    try {
      const res = await fetch(`http://${host}:${port}${path}`, { signal: AbortSignal.timeout(1000) });
      await res.body?.cancel();
      return true; // any HTTP response means the server is accepting requests
    } catch {
      /* not up yet */
    }
  }
  return false;
}

/** Kill a whole process tree. POSIX: children run in their own process group. */
function killTree(child, signal) {
  if (child.exitCode !== null || child.signalCode !== null) return;
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

// ------------------------------------------------------------------------- state
const running = new Map(); // name -> { svc, child, ready, exited }
let stopping = false;
let exitCode = 0;
let bannerShown = false;

function printBanner() {
  if (bannerShown) return;
  bannerShown = true;
  console.log("");
  console.log(color.green(color.bold("Dev servers ready")));
  for (const { svc } of running.values()) {
    for (const [label, url] of svc.urls()) console.log(`  ${label.padEnd(6)} ${color.bold(url)}`);
  }
  console.log(color.dim("  Press Ctrl+C to stop.\n"));
}

function markReady(name) {
  const entry = running.get(name);
  if (!entry || entry.ready) return;
  entry.ready = true;
  log.ok(`${name} is up`);
  if ([...running.values()].every((e) => e.ready)) printBanner();
}

function pipeOutput(entry, stream) {
  let buffer = "";
  stream.setEncoding("utf8");
  stream.on("data", (chunk) => {
    buffer += chunk;
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() ?? "";
    for (const line of lines) emit(entry, line);
  });
  stream.on("end", () => {
    if (buffer) emit(entry, buffer);
    buffer = "";
  });
}

function emit(entry, line) {
  if (!line.trim()) return;
  process.stdout.write(`${prefixFor(entry.svc)} ${line}\n`);
  if (!entry.ready && entry.svc.readyPattern.test(stripAnsi(line))) markReady(entry.svc.name);
}

function stopAll(reason) {
  if (stopping) return;
  stopping = true;
  if (reason) console.log(`\n${color.yellow(reason)}`);
  for (const { child } of running.values()) killTree(child, "SIGINT");
  const force = setTimeout(() => {
    for (const { svc, child } of running.values()) {
      if (child.exitCode === null && child.signalCode === null) {
        log.warn(`${svc.name} did not exit in ${STOP_GRACE_MS / 1000}s — killing it`);
        killTree(child, "SIGKILL");
      }
    }
  }, STOP_GRACE_MS);
  force.unref();
}

function onChildExit(entry, code, signal) {
  entry.exited = true;
  if (!stopping) {
    const how = signal ? `signal ${signal}` : `code ${code}`;
    log.error(`${entry.svc.name} exited unexpectedly (${how}) — stopping the others`);
    exitCode = code || 1;
    stopAll();
  }
  if ([...running.values()].every((e) => e.exited)) process.exit(exitCode);
}

// -------------------------------------------------------------------------- main
const problems = selected.map((s) => s.preflight()).filter(Boolean);
for (const svc of selected) {
  if (await portInUse(svc.port)) problems.push(`Port ${svc.port} (${svc.name}) is already in use.`);
}
if (problems.length) {
  for (const p of problems) log.error(p);
  process.exit(1);
}

console.log(color.bold(`Starting ${selected.map((s) => s.name).join(" + ")} …`));

for (const svc of selected) {
  const child = spawn(svc.cmd, svc.args, {
    cwd: svc.cwd,
    env: svc.env,
    shell: svc.shell,
    stdio: ["ignore", "pipe", "pipe"],
    detached: !isWindows, // own process group so the whole tree can be signalled
    windowsHide: true,
  });
  const entry = { svc, child, ready: false, exited: false };
  running.set(svc.name, entry);
  pipeOutput(entry, child.stdout);
  pipeOutput(entry, child.stderr);
  child.on("error", (err) => {
    log.error(`${svc.name} failed to start: ${err.message}`);
    onChildExit(entry, 1, null);
  });
  child.on("exit", (code, signal) => onChildExit(entry, code, signal));
}

// HTTP readiness probes (covers servers whose log format differs from the patterns).
const started = Date.now();
const probeTimer = setInterval(async () => {
  if (stopping) return clearInterval(probeTimer);
  const pending = [...running.values()].filter((e) => !e.ready && !e.exited);
  if (pending.length === 0) return clearInterval(probeTimer);
  for (const e of pending) {
    if (await probeHttp(e.svc.port, e.svc.probePath)) markReady(e.svc.name);
  }
  if (Date.now() - started > READY_TIMEOUT_MS) {
    clearInterval(probeTimer);
    log.warn(`Still waiting for: ${pending.map((e) => e.svc.name).join(", ")} (check the output above)`);
  }
}, 1000);

let interrupts = 0;
for (const sig of ["SIGINT", "SIGTERM", ...(isWindows ? [] : ["SIGHUP"])]) {
  process.on(sig, () => {
    interrupts += 1;
    if (interrupts > 1) {
      log.warn("Forcing shutdown");
      for (const { child } of running.values()) killTree(child, "SIGKILL");
      process.exit(130);
    }
    stopAll("Stopping dev servers… (Ctrl+C again to force)");
  });
}
