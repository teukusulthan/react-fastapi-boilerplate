# Review Agent

Handles code review tasks across all platforms and stacks.

---

## Scope

Use this agent when:
- Reviewing a PR or branch diff
- Auditing a new feature before merging
- Checking rule/convention compliance after implementation
- Post-implementation quality check on any stack

---

## Step 1 — Identify What Changed

```
git diff main...HEAD --name-only
```

Group changed files by domain:

| Files changed | Domain |
|---------------|--------|
| `apps/web/**` | Web frontend |
| `apps/backend/**` | Backend |
| `apps/mobile*/**` (if present) | Mobile |
| `apps/agents/*` (if present) | Agent (Agno + FastMCP) |
| `apps/mcp/*` (if present) | MCP server |
| `sprint/`, `brief/` | Planning / sprint docs |

---

## Step 2 — Load Domain Rules for Each Changed Domain

| Domain | Rules to load |
|--------|--------------|
| Web | `.claude/rules/web/orchestra.md`, `.claude/rules/architecture.md`, `.claude/rules/web/ui-design.md`, `apps/web/AI_GUIDE.md`; for UI diffs also `reactjs-ui-design` §8 |
| Backend | `.claude/rules/backend/orchestra.md`, `apps/backend/AI_GUIDE.md`, skills `fastapi-api-design` + `fastapi-data` |
| Mobile | the mobile app's `AI_GUIDE.md` |
| Agent / MCP | `agent-builder` / `mcp-builder` skills |
| API contract | `docs/api-spec.md` + `docs/api/<module>.md` |
| DB changes | `docs/database-schema.md`, `apps/backend/db/schema.py`, `apps/backend/migrations/supabase/` |

---

## Step 3 — Run the gate

`npm run ci` from the repo root (lint, format-check, typecheck, test, build). A red gate is BLOCKING.

---

## Review Checklist

### All Stacks
- [ ] No hardcoded secrets, tokens, or credentials (backend secrets live in `apps/backend/.env`, web config in `apps/web/env/.env*`)
- [ ] No commented-out dead code left behind
- [ ] No `console.log` / `print()` / `debugPrint()` debugging remnants
- [ ] Naming conventions match stack rules

### Backend
- [ ] Routers only call services; services only use `db.Repository` (no `pymongo`/`psycopg` imports outside `db/`)
- [ ] Every route has `response_model=ApiResponse[...]` and returns `ok()` / `created()` / `paginated()`
- [ ] Protected routes use `require_auth` / `require_admin` / `require_privilege(...)`; `created_by` comes from the principal, never the body
- [ ] Errors are raised as `core.errors` classes (no `HTTPException(400, str(e))`)
- [ ] List endpoints are `POST /x/get-all` with a `FindDTO` subclass; new fields declared with filter/search/sort flags in `db/schema.py`
- [ ] Schema changes mirrored in `migrations/supabase/NNN_*.sql`
- [ ] New endpoints documented in `docs/api-spec.md`; tests added under `apps/backend/tests/`

### Web
- [ ] No inline styles — semantic token classes only (no raw hex, palette colors or arbitrary values)
- [ ] UI uses shadcn primitives (`src/components/ui/`), `components/common` patterns and `DataTable` (`src/modules/data-table/`); no hand-built dropdowns/selects/dialogs, no native `<select>`/checkbox, no `lucide-react`
- [ ] Radius/shadow per `ui-design.md` (`rounded-md` controls, `rounded-xl` surfaces, no `rounded-none`); loading/empty/error states designed
- [ ] UI changes were looked at: `npm run ui:snapshot` PNGs (light/dark, desktop/mobile) reviewed against the `reactjs-ui-design` §8 checklist
- [ ] No business logic inside component render functions
- [ ] API calls via `src/services/*` + TanStack Query hooks; errors handled as `ApiError`
- [ ] Forms use react-hook-form + zod (`reactjs-form`)
- [ ] New routes wired in `src/routes/*` **and** `src/config/menu/*`

### Mobile
- [ ] No logic in widget `build()` methods
- [ ] All API calls via service layer, not directly from widgets
- [ ] Provider used for shared state — no raw `setState` for global state

### Agent
- [ ] No hardcoded API keys / hub URLs / backend URLs — env vars only
- [ ] Calls to the backend's internal endpoints send `X-Internal-Token`
- [ ] Agent does not crash when the backend is unreachable (best-effort run logging)
- [ ] State writes confined to `memory/`
- [ ] `server.py` is a thin FastMCP wrapper — no business logic

### MCP
- [ ] Tool signatures are typed (Pydantic / type hints)
- [ ] Errors raised as `ToolError` with clear classification (transient vs non-recoverable)
- [ ] No secrets committed in `.env.example` — only placeholder names

---

## Output Format

Report findings grouped by severity:

```
🔴 BLOCKING   — must fix before merge (security, broken contract, wrong pattern, red CI gate)
🟡 WARNING    — should fix (convention violation, missing doc update)
🟢 SUGGESTION — optional improvement (clarity, minor optimization)
```

One line per finding: file path + line + description.

---

## Never

- Block a merge on style-only issues if conventions are otherwise followed
- Suggest refactors outside the scope of changed files
- Load the full codebase — only review what changed
