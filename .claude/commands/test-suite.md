# Command: /test-suite

Generates comprehensive unit and integration tests based on the current context.

## Trigger
`/test-suite`

## Execution Steps
1. `<thinking>` Look at the currently active file. Determine its language: Setup `pytest` (Python), `cargo test` (Rust), `jest/vitest` (React), or `flutter test` (Dart).
2. Identify all edge cases, successful paths (happy path), and failure states.
3. Write mock definitions for external API calls or database hits.
4. Write the test cases.

## Runners in this repo
- **Backend** (`apps/backend`): pytest; reuse the fixtures in `tests/conftest.py` (`client`, `make_app`, `app_routers` override, `user_factory`, `admin_headers`, `user_headers`, `internal_headers`) — mongomock + fakeredis, no services needed. Run `.venv/bin/python -m pytest` (Postgres variants: `TEST_POSTGRES_DSN=… -m integration`). Details: `apps/backend/AI_GUIDE.md` §7.
- **Web** (`apps/web`): Vitest + Testing Library; use `src/test/render.tsx` (`renderWithProviders`) and `src/test/axios-mock.ts` (`createMockAdapter`, `ok`, `fail`). Run `npm run test:ci` (not `npm run test`, which watches). Details: `apps/web/AI_GUIDE.md` §8.

## Output Format
Provide valid test file code ready to be executed in the current environment's test runner.
