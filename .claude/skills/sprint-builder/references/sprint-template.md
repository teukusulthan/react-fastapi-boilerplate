# Sprint {NN} — {Slug Title}

**Status:** 📋 Planned | 🚧 In Progress | ✅ Done
**Created At:** {YYYY-MM-DD}
**Started At:** -
**Completed At:** -

## Goal

{One sentence — the user-visible outcome of this sprint. Reference any blueprint feature or sprint-planning row this maps to.}

## Acceptance

{How we know the goal is met. Observable behaviour, not implementation details. Example: "User can submit the login form, see a 200 response, and land on /dashboard with their name in the header."}

## Scope (stacks involved)

- [ ] frontend → see [`frontend/`](./frontend/)
- [ ] backend → see [`backend/`](./backend/)
- [ ] agent → see [`agent/`](./agent/)
- [ ] mcp → see [`mcp/`](./mcp/)
- [ ] mobile → see [`mobile/`](./mobile/)

(Tick the stacks this sprint touches. Subfolders are created only for ticked stacks.)

## Workforce members touched

> Reference brief's [`## Workforce Manifest`](../../../brief/00_OVERVIEW.md). List role-role yang sprint ini sentuh + apa kontribusi sprint ke role itu.

- `[role-name]` — {contribution: write tender_raw / read tender_raw / new MCP tool signature / FE wiring}
- `[role-name]` — {contribution}
- `be_service` — {expose tender CRUD via REST}
- `fe_shell` — {render tender list page}

## Cross-stack dependencies

{If this sprint touches data shared across workforce members, list foundation tasks and dependency relationships here. If there is no cross-stack data sharing (FE-only / BE-only standalone), write: "no shared data — stacks can run in parallel."}

## Dependency graph (optional, for shared-data sprints)

```
backend/00-schema-<feature>.md (foundation)
    ↓
    ├─ agent/01-<role>.md          (write to <table>)
    ├─ backend/01-<feature>-routes.md  (read <table>)
    └─ frontend/01-<feature>-list.md   (consume backend)

agent/01-<role>.md → agent/02-<sibling-role>.md (downstream chain via event)
```

> Foundation tasks `[x]` first → dependents unblock → parallel execution OK.

## Notes

(Running notes during execution — surprises, blockers, decisions, follow-ups.)

## Outcome

(Filled in when the sprint moves to `archive/` — one paragraph: what shipped, what was deferred, what was learned.)

---

> **Ref:** [Sprint Planning](../../01-sprint-planning.md) | Brief: see `<cwd>/brief/00_OVERVIEW.md` at the project root
