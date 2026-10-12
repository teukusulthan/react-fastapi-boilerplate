#!/usr/bin/env node
// Run the backend virtualenv's Python with the given arguments, cross-platform.
//
//   node scripts/py.mjs api.py              (from apps/backend)
//   node ../../scripts/py.mjs -m pytest     (what the Nx targets do)
//
// Resolves apps/backend/.venv/bin/python (POSIX) or apps\backend\.venv\Scripts\python.exe
// (Windows). The current working directory is preserved. Exit code and signals are forwarded.
import { spawn } from "node:child_process";
import { hasVenv, isWindows, log, venvPython } from "./lib/common.mjs";

const args = process.argv.slice(2);

if (args[0] === "--help" || args[0] === "-h") {
  console.log(`Usage: node scripts/py.mjs <python args...>

Runs the backend virtualenv interpreter (${venvPython()}) with <python args...>.
Create the virtualenv first with: npm run setup:backend`);
  process.exit(0);
}

if (!hasVenv()) {
  log.error(`Backend virtualenv not found at ${venvPython()}`);
  log.error("Run `npm run setup:backend` from the repository root first.");
  process.exit(1);
}

const child = spawn(venvPython(), args, {
  stdio: "inherit",
  env: { ...process.env, PYTHONUNBUFFERED: process.env.PYTHONUNBUFFERED ?? "1" },
});

// The child shares our terminal, so it receives Ctrl+C directly; forward signals that are
// delivered only to us (e.g. `kill`, process managers) as well.
const forward = (signal) => {
  if (child.exitCode === null && !child.killed) child.kill(signal);
};
for (const signal of isWindows ? ["SIGINT", "SIGTERM"] : ["SIGINT", "SIGTERM", "SIGHUP"]) {
  process.on(signal, () => forward(signal));
}

child.on("error", (err) => {
  log.error(`Failed to start ${venvPython()}: ${err.message}`);
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (signal) {
    // Re-raise so callers see "terminated by signal" semantics; fall back to 128+n.
    process.exitCode = 128 + ({ SIGINT: 2, SIGTERM: 15, SIGHUP: 1 }[signal] ?? 1);
    return;
  }
  process.exit(code ?? 0);
});
