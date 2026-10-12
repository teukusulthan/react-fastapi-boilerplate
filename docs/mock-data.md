# Mock Data

Mock data is simulated data for development, testing and prototypes. Use it in **POC** scope and in
**MVP** scope when the real data is incomplete or not yet validated (see
[`.claude/rules/project-scope.md`](../.claude/rules/project-scope.md)). Production scope never uses
mock data.

## Location

- Source datasets live in the repo-root `data/` folder (`data/mock/` today). Treat them as read-only;
  copy a file before editing it.
- To serve a dataset to the web app, copy it into `apps/web/public/data/`, where Vite serves it at
  `/data/<file>`. The consuming pattern (`mock-client.ts`, `mock-endpoints.ts`, `mockRequest()`) is
  described in [`apps/web/AI_GUIDE.md` §6](../apps/web/AI_GUIDE.md#6-mock-data-poc-scope-only).
- Every JSON mock served to the app uses the envelope
  `{ "metaData": { "status": true, ... }, "data": [ ... ] }`.

## Files

| File | Name | Description | Notes |
|---|---|---|---|
| `data/mock/mock-sentiment-layanan-publik.json` | Public-service sentiment | Sample texts with `sentiment` (`positive`, `neutral`, `negative`) and `score` | Uses `metadata` (lowercase, no `status`). Rename it to `metaData` and add `"status": true` when you copy it to `apps/web/public/data/`. |

## Implementation

| Consumer | Path | Endpoint / file | Status |
|---|---|---|---|
| — | — | — | No mock layer is wired yet; the web app uses the real backend |

Add a row here whenever you wire a mock dataset into an app.

## Rules

- Do not modify files in `data/` in place. Duplicate them first.
- Mock fetches live in services (`apps/web/src/services/*.service.ts`), never in components, hooks or
  stores.
- Remove mock wiring when the matching backend endpoint exists (MVP and production).
