# Engineering Standards — Best Approach, Best Practice

> Always-on rule for every agent and every task in this repo (backend, web, docs, tooling).
> "Works" is the minimum. The bar is: the solution a senior engineer on this team would choose,
> implemented the way the documented patterns and current best practice say it should be.
> Company rules (`architecture.md`, e.g. React 18) always win over a personal "better" idea —
> propose changes to them instead of working around them.

## 1. Understand before you change

- Read the code you are about to touch and its callers/tests. Find the existing pattern for this kind
  of change (the recipes in `AGENTS.md` §5, the reference modules `role` and `administrator/user`)
  and follow it. Consistency with the codebase beats a locally clever solution.
- Reproduce a bug before fixing it (failing test first), and fix the **root cause**, not the symptom.
- For library/framework APIs, check the current official docs (context7 MCP or the docs site) instead
  of relying on memory — versions here are recent (FastAPI, Pydantic v2, React Router 7, TanStack
  Query 5, Tailwind v4, Zod 4).

## 2. Choose the best approach, deliberately

For anything beyond a trivial change, before writing code:
1. Identify at least two viable approaches (e.g. extend the existing module vs. new module; DB
   constraint vs. app check; server-side vs. client-side filtering).
2. Pick by these criteria, in order: **correctness → security → data integrity → consistency with
   existing patterns → simplicity/maintainability → performance → effort**.
3. State the choice and the main trade-off in one or two lines in your final report.

If the best approach needs a decision that belongs to the user (new dependency/stack change, breaking
API change, data migration, deleting features, cost/infra), stop and ask with a recommendation —
don't silently pick the convenient option.

## 3. Best practices that are not optional

- **Security by default:** validate input at the boundary (DTOs with `extra="forbid"`, zod on the web),
  enforce authz on every route, least privilege, no secrets in code/logs/responses, parameterized
  queries only, no weakening of security to make something pass.
- **Correct data handling:** uniqueness and integrity enforced by the database (unique indexes,
  constraints), not only by "check then write"; timezone-aware UTC; explicit pagination limits.
- **Errors:** raise typed errors and let the global handlers render them; never swallow exceptions,
  never `except Exception: pass`, never return error strings as success. Web: surface `ApiError`
  messages and keep the UI in a valid state.
- **Types:** no `any` / untyped `dict` where a model or type exists; keep TypeScript strict and Pydantic
  models precise. No `# type: ignore` / `@ts-expect-error` / `eslint-disable` without a one-line reason.
- **Simplicity:** the smallest design that fully solves the problem. No speculative abstractions,
  no copy-paste duplication (extract once a pattern repeats), no dead code, no commented-out code,
  no TODO stubs left behind.
- **Performance hygiene:** no N+1 queries, no blocking I/O in `async def`, no unbounded lists or
  payloads, memoize/paginate on the web where data can grow.
- **Accessibility & UX (web):** semantic elements, labels, keyboard and focus support, all states
  (loading/empty/error); UI per `.claude/rules/web/ui-design.md`.
- **Dependencies:** prefer what is installed; add a library only if it clearly beats a small local
  implementation, is maintained, and fits the stack — say why in the report.

## 4. Tests and verification are part of the work

- Every behavior change ships with tests at the right level (unit for logic, API tests for endpoints
  incl. RBAC/validation, component/hook tests for web logic, e2e only for critical journeys).
- Run the real checks (`npm run ci`, or the per-app commands in `CLAUDE.md`) and read the output.
  UI work also gets the screenshot review loop. Never report success you did not observe.
- Keep docs in sync in the same change (`docs/`, AI guides, skills, changelog) — `npm run docs:check`
  enforces the mechanical part.

## 5. Scope discipline (best ≠ bigger)

- Do what the task asks, fully and properly. Don't expand scope with unrequested features, rewrites or
  dependency upgrades — note them as recommendations instead.
- When you touch code, leave it at least as clean as you found it (fix obvious problems in the lines
  you change); larger refactors need their own task.
- Shortcuts that are never acceptable: disabling/skipping tests, deleting failing assertions, hardcoding
  values to pass a check, bypassing repositories/envelope/router registry, editing generated
  lockfiles by hand, `--no-verify`.

## 6. Report honestly

Finish with: what changed (files), the approach chosen and why, how it was verified (commands + real
results), and known limitations or follow-ups. If something is unverified, say so plainly.
