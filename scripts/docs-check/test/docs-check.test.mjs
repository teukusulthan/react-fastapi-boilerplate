// Self-tests for scripts/docs-check: a tiny fixture repo with known drift.
//   node --test scripts/docs-check/test/     (= npm run docs:check:test)
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { after, before, test } from "node:test";
import { runDocsCheck } from "../index.mjs";

const FENCE = "```";
let root;

const write = (rel, content) => {
  mkdirSync(dirname(join(root, rel)), { recursive: true });
  writeFileSync(join(root, rel), content);
};

/** Backend facts as backend_probe.py would return them. */
const backend = (imports = []) => ({
  routes: [
    ["GET", "/health/live"],
    ["POST", "/user/get-all"],
  ],
  settings: ["JWT_SECRET", "TABLE_USERS"],
  imports,
});

const run = (only, imports) => runDocsCheck({ root, only: [only], backend: backend(imports) }).issues;
const messages = (issues) => issues.map((i) => `${i.line}:${i.check}:${i.message}`);

before(() => {
  root = mkdtempSync(join(tmpdir(), "docs-check-"));
  write("package.json", JSON.stringify({ scripts: { ci: "x", setup: "x" } }));
  write("apps/web/package.json", JSON.stringify({ scripts: { "test:ci": "x", dev: "x" } }));
  write("apps/backend/.env.example", "BE_JWT_SECRET=change-me\n# BE_DOCS_ENABLED=true\n");
  write("apps/backend/core/config.py", 'class Settings:\n    JWT_SECRET: str\n    TABLE_USERS: str = "users"\n');
  write("apps/backend/service/user.py", "");
  write("apps/web/env/.env.example", "VITE_API_BASE_URL=/api/v1/apps\n");
  write("apps/web/src/config/env.ts", "export const env = { api: { baseUrl: import.meta.env.VITE_API_BASE_URL } }\n");
  write("apps/web/src/lib/utils.ts", "export function cn() {}\nexport const twMerge = 1\n");
  write("apps/web/src/lib/index.ts", "export * from './utils'\nexport { default as Thing } from './thing'\n");
  write(
    "docs/api-spec.md",
    ["| Method | Path |", "|---|---|", "| GET | `/health/live` |", "| POST | `/user/get-all` |", ""].join("\n"),
  );
});

after(() => rmSync(root, { recursive: true, force: true }));

test("a consistent document passes", () => {
  write(
    "AGENTS.md",
    [
      "See [the spec](docs/api-spec.md) and `apps/backend/service/user.py`, `service/user.py`.",
      "Run `npm run ci` from the repo root, and `cd apps/web && npm run test:ci`.",
      "Set `BE_JWT_SECRET`, `BE_TABLE_USERS` and `VITE_API_BASE_URL`; tables are `BE_TABLE_*`.",
      "Call `POST /user/get-all`.",
      `${FENCE}ts`,
      "import { cn, twMerge } from '@/lib/utils'",
      "import { Thing, cn as merge } from '@/lib'",
      FENCE,
      `${FENCE}python`,
      "from service.user import UserService",
      FENCE,
    ].join("\n"),
  );
  assert.deepEqual(messages(run("AGENTS.md")), []);
});

test("api-spec registry is compared with the app both ways", () => {
  const issues = runDocsCheck({
    root,
    only: ["docs/api-spec.md"],
    backend: { ...backend(), routes: [["GET", "/health/live"], ["DELETE", "/user/delete"]] },
  }).issues;
  assert.deepEqual(messages(issues), [
    "1:endpoint:DELETE /user/delete exists in the FastAPI app but is missing from the docs/api-spec.md registry",
    "4:endpoint:POST /user/get-all is in the registry but not in the FastAPI app",
  ]);
});

test("drift is reported with file:line", () => {
  write(
    "AGENTS.md",
    [
      "A [broken link](docs/missing.md) and a missing `apps/backend/service/nope.py` and `router/nope.py`.",
      "Run `npm run test:ci` from the repo root.",
      "Set `BE_NOT_A_SETTING` and `VITE_NOPE`.",
      "Call `GET /user/get-one`.",
      `${FENCE}ts`,
      "import { cn, missing } from '@/lib/utils'",
      "import Nope from '@/lib/nope'",
      FENCE,
      `${FENCE}python`,
      "from service.user import UserService",
      FENCE,
    ].join("\n"),
  );
  const issues = run("AGENTS.md", [{ module: "service.user", name: "UserService", error: "'service.user' has no attribute or submodule 'UserService'" }]);
  assert.equal(issues.every((i) => i.file === "AGENTS.md"), true);
  assert.deepEqual(messages(issues), [
    "1:link:broken link: docs/missing.md (docs/missing.md does not exist)",
    "1:path:path not found: apps/backend/service/nope.py",
    "1:path:path not found: router/nope.py (looked for apps/backend/router/nope.py)",
    '2:npm:npm script "test:ci" not found in the root package.json (it exists in apps/web: add `cd apps/web` or say "from apps/web")',
    "3:env:unknown env var BE_NOT_A_SETTING (not in apps/backend/.env.example or core/config.py)",
    "3:env:unknown env var VITE_NOPE (not in apps/web/env/.env.example or src/config/env.ts)",
    "4:endpoint:GET /user/get-one is not a route of the FastAPI app",
    "6:ts-import:'@/lib/utils' (apps/web/src/lib/utils.ts) does not export 'missing'",
    "7:ts-import:cannot resolve '@/lib/nope' (no apps/web/src/lib/nope[.ts|.tsx|/index.ts])",
    "10:py-import:from service.user import UserService: 'service.user' has no attribute or submodule 'UserService'",
  ]);
});

test("ignore markers and create markers silence intentional cases", () => {
  write(
    "AGENTS.md",
    [
      "Old name `BE_LEGACY_TOKEN` and `apps/be/`. <!-- docs-check: ignore-line -->",
      "<!-- docs-check: ignore-next-line -->",
      "See [gone](docs/gone.md).",
      "<!-- docs-check: ignore-start -->",
      "`apps/web/src/nowhere.ts`, `npm run nowhere`",
      "<!-- docs-check: ignore-end -->",
      "Create it at `apps/web/src/components/wrappers/NewWrapper.tsx`.",
      "Add a `note` resource: `apps/backend/service/note.py`, `BE_TABLE_NOTES`.",
      `${FENCE}python`,
      "from service.note import NoteService",
      "from service.user import Gone  # docs-check: ignore-line",
      FENCE,
    ].join("\n"),
  );
  assert.deepEqual(messages(run("AGENTS.md")), []);
});
