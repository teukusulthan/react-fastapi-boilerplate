# docs-check

Fails when the Markdown docs drift from the code. It runs in `npm run ci`, in the GitLab job
`docs:check` (lint stage) and, optionally, as a pre-commit hook.

```bash
npm run docs:check                                   # whole repo (about 2 s)
node scripts/docs-check/index.mjs AGENTS.md docs/api-spec.md   # only these files
node scripts/docs-check/index.mjs --skip-backend      # no venv: skip Python imports + endpoints
npm run docs:check:test                              # self-tests (fixture repo with known drift)
```

Exit code `0` = clean, `1` = drift found, `2` = the checker could not run (for example, no backend venv).
On success it prints how many references of each kind it verified, so a check that silently stops
matching is visible.

## Scope

`CLAUDE.md`, `AGENTS.md`, `README.md`, `.claude/rules/**/*.md`, `.claude/skills/**/*.md`,
`.claude/commands/**/*.md`, `docs/**/*.md`, `apps/*/AI_GUIDE.md`, `apps/*/README.md`,
`apps/web/e2e/README.md` and `scripts/*/README.md`. The archived skills in `.claude/skills-library/`
describe other projects and are not checked; only the links of its `README.md` are.

## Checks

Every problem is printed as `file:line: [check] message`.

| Check | What must hold |
|---|---|
| `link` | Relative Markdown links (outside code) point to an existing file or folder. |
| `path` | Backticked repo paths exist: `apps/…`, `.claude/…`, `docs/…`, `scripts/…`, `changelog/…` from the repo root (inside a skill, `scripts/…` may also be the skill's own folder); `src/…` = `apps/web/src/…` in web docs; `core/…`, `db/…`, `dto/…`, `service/…`, `router/…`, `util/…`, `migrations/…`, `templates/…`, `tests/…` = `apps/backend/…` in backend docs. Root guides (`CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/**`, `.claude/rules/architecture.md`) use both. |
| `npm` | `npm run <script>` exists in the right `package.json`. The context is, first match wins: a preceding `cd apps/web` / `cd apps/backend` / `cd ../..` (same code span or earlier in the code block, including comment lines like `# from the repo root`); a qualifier next to it ("at the root", "(apps/web)", "the root `npm run ci`"); a hint on the line; a document under `apps/web/`; otherwise either `package.json` is accepted. |
| `env` | `BE_*` names exist in `apps/backend/.env.example`, `core/config.py` or as `BE_` + a `Settings` field; `VITE_*` names in `apps/web/env/.env.example` or `src/config/env.ts`. `BE_TABLE_*` checks the prefix; `BE_<NAME>` is a placeholder. |
| `py-import` | `from <pkg>… import X` lines (`<pkg>` = `core`, `db`, `dto`, `service`, `router`, `util` or `scripts`) in Python code blocks import in the backend venv (module, then attribute or submodule). |
| `ts-import` | `@/…` imports (and `export … from`, `import()`, `vi.mock()`) in TS/JS code blocks of web and root docs resolve to a file under `apps/web/src`, and named/default imports are exported (regex export scan that follows `export * from` barrels). |
| `endpoint` | The method + path rows of the `docs/api-spec.md` registry tables and the routes of the FastAPI app are the same set (both directions). Backticked `` `METHOD /path` `` mentions in `docs/api/*.md`, the root guides and the app guides must be real routes. |

## Design

- `index.mjs` (Node ESM, no dependencies) parses the Markdown and runs the file, npm, env and TS
  checks; `lib/markdown.mjs` (fences, inline code, markers), `lib/repo.mjs` (file list from
  `git ls-files --cached --others --exclude-standard`, or a directory walk without git; package scripts;
  env keys; web module resolution and export scan), `lib/checks.mjs` (the checks), `config.mjs` (scope
  and documented exceptions).
- `backend_probe.py` runs once in `apps/backend/.venv` for the Python facts: it builds the real app with
  `create_app()` (all optional routers on, with a dummy `BE_JWT_SECRET` and Google client so
  `google_router` mounts), reads the routes from the OpenAPI schema plus the registry routers (the
  lifespan never runs, so no Mongo/Redis), lists the `Settings` fields, and tries each documented import.
  Python checks Python, Node checks everything else; each half stays small and uses only what its
  ecosystem already has.

## Intentional exceptions

Prefer fixing the doc. When a doc names something that should not exist (a recipe's new file, a
counter-example, a name from another project), mark it:

| Marker | Effect |
|---|---|
| `create it at`, `(create)`, `create on demand`, ``create `…` ``, "new file", `not present yet`, `**not present**`, `if exists` on the line | path, Python-import and TS-import checks skip the line |
| `<!-- docs-check: ignore-line -->` (or `# docs-check: ignore-line` / `// docs-check: ignore-line` inside code) | every check skips the line |
| `<!-- docs-check: ignore-next-line -->` | every check skips the next line |
| `<!-- docs-check: ignore-start -->` … `<!-- docs-check: ignore-end -->` | every check skips the block |
| `<!-- docs-check: ignore-file -->` | every check skips the file |

Recurring cases live in `config.mjs`, each with a reason: the example names of the recipes
(`note`, `reports`, `product`, …), the "create on demand" locations the skills document as not present
(`src/modules/dynamic-filter/`, `MapboxWrapper.tsx`, `apps/agents/`, …), generated paths (`.env`,
`.venv`, `build/`, `test-results/`, …), template files whose links are relative to the generated
file, and env names that are documented on purpose (`VITE_APP_URL` in the "add a canonical URL"
recipe, the agents' own `BE_URL`, …).
