# /review — Code Review Workflow

Perform a structured code review on staged changes or a specified file/PR.

## Usage

```
/review
/review src/api/handlers/files.rs
/review --pr 42
```

## Review Checklist

Run through each category systematically:

### 1. Correctness
- Does the code do what it claims?
- Are edge cases handled (empty inputs, null/None, out-of-range values)?
- Are error paths tested?

### 2. Security
- Is user input validated before use?
- Are there any SQL injection vectors? (No string interpolation in queries)
- Are authorization checks present on every endpoint (`require_auth` / `get_current_user` / `require_admin` / `require_privilege`)? Do input DTOs use `extra="forbid"`?
- Are secrets handled correctly (not logged, not returned in responses)?
- Are file uploads validated for type and size?

### 3. Performance
- Any N+1 query patterns?
- Missing database indexes on filter/sort columns?
- Unbounded list queries without pagination?

### 4. Code Style
- Follows project rules?
- Naming conventions correct for the language?
- No dead code or commented-out blocks?

### 5. Architecture
- Does the code respect layer boundaries?
  - Backend (FastAPI): router → service → `db.Repository` (no pymongo/psycopg outside `apps/backend/db/`); routers registered only in `router/__init__.py`
  - Web (React/Vite): page → feature component → TanStack Query hook → service (`apiRequests`/`createResourceService`) → API
  - Mobile (Flutter): view → viewmodel(Provider) → service → API
- Is business logic in the right layer (not in handlers/screens)?

### 6. UI (web changes)
- Follows `.claude/rules/web/ui-design.md` and the `reactjs-ui-design` playbook: shadcn primitives (no hand-built dropdown/select/dialog, no native `<select>`/checkbox, no `lucide-react`), `components/common` patterns, `DataTable` from `src/modules/data-table/` for lists?
- Semantic token classes only (no raw hex, Tailwind palette colors, arbitrary values, inline styles); `rounded-md` controls / `rounded-xl` surfaces, no `rounded-none`, no cards in cards?
- Loading (skeleton), empty (`EmptyState`) and error (destructive `Alert` + retry) states present?
- Was it looked at? `npm run ui:snapshot -- --route <path>` PNGs (light/dark, desktop/mobile) reviewed against the playbook §8 checklist.

### 7. Tests
- Are tests added or updated for the change?
- Are tests testing behavior, not implementation?
- Any missing edge case coverage?

### 8. API Contracts
- Response shape matches API conventions?
- Correct HTTP status codes?
- Every route declares `response_model=ApiResponse[...]`; errors are raised (`core/errors.py`) and come back as `{metaData: {status: false, errorCode, message, …}, data: details}` (see `docs/api-spec.md`)?
- New/changed endpoints reflected in `docs/api-spec.md`, `docs/api/*.md` and the web types?

## Output Format

Structure the review as:

```
## Summary
[1-2 sentence overview of what changed and overall assessment]

## Issues

### Critical (must fix before merge)
- [file:line] Description

### Suggestions (nice to have)
- [file:line] Description

## Positives
- [What was done well]
```

## Persona

Review as an `@code-reviewer` agent who cares about:
- Long-term maintainability over cleverness
- Security first
- Clear, honest feedback without unnecessary softening
