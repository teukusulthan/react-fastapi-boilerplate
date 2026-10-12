---
name: tdd-workflow
description: "Mandatory red-green-refactor + full-suite regression gate for any custom/iterative feature or bugfix task, backend and/or frontend. Covers characterization-tests-first for code with no existing test, and the pre-completion checklist that must pass before a task is marked done. Use before starting ANY custom feature/bugfix task, and again before declaring it complete."
---

# tdd-workflow — Regression-Safety Gate

This is a **process** skill — it says *when* a test must exist and *when* a task is allowed to be
called done. It runs **alongside**, not instead of, the skills that say *how* to build and test:
`fastapi-unit-test` (backend infra/patterns) and `reactjs-unit-test` (frontend infra/patterns).

**Why this exists:** this codebase moves fast — features get added and customized iteratively, often in
one sitting, across both `apps/backend` and `apps/web`. Without a gate, a change made to satisfy one
request can silently break a feature built in an earlier session. This skill is that gate.

## Use this skill when

- Starting **any** custom feature or bugfix task — read this FIRST, before writing implementation code.
- The code you're about to change has **no existing test** — see Step 2 below before touching it.
- You're about to tell the user a task is done — Step 4 is mandatory, no exceptions.

## The workflow

### Step 1 — Red: write the test first

Write a test that encodes the new or changed behavior, and confirm it **fails for the right reason**
(the feature doesn't exist yet — not a typo or import error) before writing the implementation.
- Backend: `apps/backend/tests/feature/test_<feature>.py`, using `fastapi-unit-test`'s existing infra
  (`conftest.py` fixtures, `_test`-suffixed DB, `httpx.AsyncClient`/`ASGITransport`) — but asserting the
  actual new business outcome (status code + response shape + the new computation), not just a pure
  function. This is a **sibling** location to `fastapi-unit-test`'s `tests/unit/`, not a change to that
  skill's pure-function scope.
- Frontend: a `*.test.tsx`/`.ts` file per `reactjs-unit-test`'s patterns, co-located with the
  component/hook/store, encoding the new expected behavior.

### Step 2 — Characterization test first, if the touched code has zero coverage

Since this repo starts at zero tests, most "customize an existing feature" tasks touch code with no
coverage yet. Before changing such code:
1. Write a test asserting its **current** behavior (verify by actually running it against the
   unmodified code — it must pass as-is).
2. Only then proceed to Step 1 for the new/changed behavior.

Scope discipline: characterize only the specific function/endpoint/component you're about to touch —
not the whole module, not the whole file. This is a safety net for the one change you're making, not a
retroactive coverage mandate; keep it fast enough to not fight the pace of iterative work.

### Step 3 — Green, then refactor

Write the minimum implementation to pass the Step 1 test. Refactor if needed, with the new test AND any
Step 2 characterization test(s) as your safety net — both must stay green through the refactor.

### Step 4 — Pre-completion regression gate (mandatory, no exceptions)

A task is not "done" until ALL of the following are true:

- [ ] `apps/backend`: full `pytest` run is green — **not just the new test file**. (`cd apps/backend &&
      .venv/bin/pytest` or `nx run backend:test`.)
- [ ] `apps/web`: full `npm run test` (Vitest) run is green — **not just the new test file**.
      (`cd apps/web && npm run test` or `nx run web:test`.)
- [ ] Run both sides whenever the change could plausibly cross the API boundary, even if the task
      "felt" one-sided — a DTO/response-shape change is the classic case that looks backend-only but
      breaks a frontend test.
- [ ] The Step 1 test(s) and any Step 2 characterization test(s) are present and green.
- [ ] No test was deleted, `.skip`'d, or commented out to force a pass — a shrinking suite is itself a
      regression. If a test's expectation genuinely needs to change because the old behavior was wrong,
      say so explicitly and update it — don't silently delete it.

Full checklist with rationale: [references/regression-gate-checklist.md](references/regression-gate-checklist.md).

## Relationship to other skills

| Concern | Skill |
|---|---|
| How to write/run a backend test, infra setup | `fastapi-unit-test` |
| How to write/run a frontend test, infra setup | `reactjs-unit-test` |
| Backend endpoint/DTO shape | `fastapi-api-design` |
| **When** a test is required, **when** a task is actually done | **this skill** |

`erp-dashboard-migrator` also points here for incremental, session-spanning page customization (its
`tracker.csv` workflow across 80+ widgets) — the exact scenario this skill exists to protect.
