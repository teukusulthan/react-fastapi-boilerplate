// Shared helpers for the repo-level Node scripts (cross-platform: Windows, macOS, Linux).
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const isWindows = process.platform === "win32";

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
export const BACKEND_DIR = join(ROOT, "apps", "backend");
export const WEB_DIR = join(ROOT, "apps", "web");
export const VENV_DIR = join(BACKEND_DIR, ".venv");

export const BACKEND_PORT = Number(process.env.BACKEND_PORT || 8020);
export const WEB_PORT = Number(process.env.WEB_PORT || 3000);

/** Path of the backend virtualenv interpreter (may not exist yet). */
export function venvPython(venvDir = VENV_DIR) {
  return isWindows ? join(venvDir, "Scripts", "python.exe") : join(venvDir, "bin", "python");
}

export function hasVenv() {
  return existsSync(venvPython());
}

const useColor = process.stdout.isTTY && !process.env.NO_COLOR;
const wrap = (code) => (s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : String(s));
export const color = {
  bold: wrap("1"),
  dim: wrap("2"),
  red: wrap("31"),
  green: wrap("32"),
  yellow: wrap("33"),
  blue: wrap("34"),
  magenta: wrap("35"),
  cyan: wrap("36"),
};

export const log = {
  info: (msg) => console.log(`${color.cyan("›")} ${msg}`),
  ok: (msg) => console.log(`${color.green("✔")} ${msg}`),
  warn: (msg) => console.warn(`${color.yellow("!")} ${msg}`),
  error: (msg) => console.error(`${color.red("✖")} ${msg}`),
};

/** Quote one argument for display only (never passed to a shell). */
const showArg = (a) => (/[\s"']/.test(a) ? JSON.stringify(a) : a);
export const formatCommand = (cmd, args = []) => [cmd, ...args].map(showArg).join(" ");

/**
 * Resolve how to invoke npm. Node >= 18.20/20.12 refuses to spawn `.cmd` files without a
 * shell on Windows, so when we run under npm we re-use the npm CLI entry point via node.
 */
export function npmInvocation(args) {
  const npmCli = process.env.npm_execpath;
  if (npmCli && /npm-cli\.(c?js|mjs)$/.test(npmCli)) {
    return { cmd: process.execPath, args: [npmCli, ...args], shell: false };
  }
  return isWindows
    ? { cmd: "npm.cmd", args, shell: true }
    : { cmd: "npm", args, shell: false };
}

/** Check whether an executable answers `--version`. */
export function commandExists(cmd, args = ["--version"]) {
  const res = spawnSync(cmd, args, { stdio: "ignore", shell: false });
  return !res.error && res.status === 0;
}

/**
 * Run a command with inherited stdio. Resolves with the exit code (never rejects for a
 * non-zero exit; rejects only if the process could not be started).
 */
export function run(cmd, args = [], { cwd = ROOT, env = process.env, shell = false, dryRun = false } = {}) {
  log.info(`${color.dim(`(${relativeToRoot(cwd)})`)} ${formatCommand(cmd, args)}`);
  if (dryRun) return Promise.resolve(0);
  return new Promise((resolvePromise, reject) => {
    const child = spawn(cmd, args, { cwd, env, stdio: "inherit", shell });
    child.on("error", reject);
    child.on("exit", (code, signal) => resolvePromise(code ?? (signal ? 1 : 0)));
  });
}

export function relativeToRoot(p) {
  const rel = p.startsWith(ROOT) ? p.slice(ROOT.length).replace(/^[\\/]/, "") : p;
  return rel || ".";
}
