# Regression Gate Checklist — read before saying "done"

Every item exists because skipping it is how a new feature quietly breaks an old one — the exact
failure mode this skill is protecting against.

## Before you start

- [ ] Identify what code you're about to touch. Does a test already cover it?
  - Yes → run it now, confirm it's green on the unmodified code (a baseline).
  - No → Step 2 (characterization test) is not optional. Write one before changing anything.

## While implementing

- [ ] The new/changed-behavior test (Step 1) failed for the right reason before you wrote the fix —
      if it passed immediately, it's not actually testing the new behavior.
- [ ] You didn't widen an existing test's assertion just to make it pass — if the old assertion is now
      wrong, that's a deliberate behavior change; say so out loud, don't quietly loosen it.

## Before declaring done

- [ ] `cd apps/backend && .venv/bin/pytest` (or `nx run backend:test`) — full suite, exit code 0.
- [ ] `cd apps/web && npm run test` (or `nx run web:test`) — full suite, exit code 0.
- [ ] Every test file that existed before your change still exists (nothing silently deleted).
- [ ] No `.skip`, `.only`, `xfail`, or commented-out test bodies left behind — `.only` in particular
      silently narrows an entire suite to one test and will hide a real regression from CI-less runs.
- [ ] If you touched a shared type/DTO/endpoint contract, you ran BOTH suites even if the task looked
      one-sided — a backend response-shape change is the most common cross-boundary break.
- [ ] If a pre-existing test broke and you "fixed" it by changing its expectation, you can articulate
      *why* the old expectation was wrong (not just "it was in the way").

## Red flags that mean you're not actually done

- A test file was deleted instead of updated.
- The full suite wasn't run — only the file you just wrote was run.
- A characterization test for zero-coverage code was skipped "to save time."
- `pytest`/`vitest` output wasn't actually read — just glanced at for a green summary line, missing a
  skipped/xfailed test that used to pass for real.
