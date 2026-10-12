#!/usr/bin/env node
// Run a CLI installed in apps/web/node_modules/.bin from the repo root, with apps/web as
// the working directory. File arguments given relative to the repo root (as pre-commit
// passes them) are rewritten relative to apps/web.
//
//   node scripts/web-tool.mjs prettier --write apps/web/src/main.tsx
//   node scripts/web-tool.mjs eslint --fix apps/web/src/App.tsx
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { isAbsolute, join, relative, resolve } from "node:path";
import { ROOT, WEB_DIR, isWindows, log } from "./lib/common.mjs";

const [tool, ...rest] = process.argv.slice(2);
if (!tool || tool === "--help" || tool === "-h") {
  console.log("Usage: node scripts/web-tool.mjs <bin> [args/files...]");
  process.exit(tool ? 0 : 1);
}

const bin = join(WEB_DIR, "node_modules", ".bin", isWindows ? `${tool}.cmd` : tool);
if (!existsSync(bin)) {
  log.error(`${tool} is not installed in apps/web/node_modules. Run \`npm run setup:web\`.`);
  process.exit(1);
}

const args = rest.map((arg) => {
  if (arg.startsWith("-")) return arg;
  const abs = isAbsolute(arg) ? arg : resolve(ROOT, arg);
  return existsSync(abs) ? relative(WEB_DIR, abs) : arg;
});

// .cmd shims need a shell on Windows; quote arguments for cmd.exe in that case.
const quote = (a) => (/[\s&()^|<>"]/.test(a) ? `"${a.replace(/"/g, '""')}"` : a);
const child = isWindows
  ? spawn(quote(bin), args.map(quote), { cwd: WEB_DIR, stdio: "inherit", shell: true })
  : spawn(bin, args, { cwd: WEB_DIR, stdio: "inherit" });

child.on("error", (err) => {
  log.error(err.message);
  process.exit(1);
});
child.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
