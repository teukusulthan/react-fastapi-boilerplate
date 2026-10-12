# /sprint-builder

Initialize and maintain `<cwd>/sprint/` — `01-sprint-planning.md` plus `backlog/`, `active/`, `archive/` folders, with per-stack subfolders inside each sprint.

Trigger the [`sprint-builder`](../skills/sprint-builder/SKILL.md) skill.

## Usage

```
/sprint-builder
/sprint-builder buat sprint baru untuk fitur tender-crawler
/sprint-builder promote 02-dashboard ke active
/sprint-builder archive 01-auth
```

## Pre-condition

`<cwd>/brief/00_OVERVIEW.md` exists (the project blueprint). Optional but recommended: `<cwd>/design/`.

## Action

Open `.claude/skills/sprint-builder/SKILL.md` and follow the steps to either:
- **Setup**: create `<cwd>/sprint/01-sprint-planning.md` and draft sprints from the brief.
- **Add sprint**: append a new entry to `01-sprint-planning.md` and scaffold its task tree under `backlog/`.
- **Promote**: move a sprint folder from `backlog/` → `active/`.
- **Archive**: move a finished sprint from `active/` → `archive/` and update the planning table.

If brief's Workforce Manifest contains agent role(s) (other than `pm`/`be_service`/`fe_shell`), the **first sprint is always `00-workforce-scaffold`** (provisions agent_mgmt + PM orchestrator + ops triple + FE foundation).

## Next step

User picks `/agent-builder` per role and `/mcp-builder` per new MCP tool referenced in the active sprint.
