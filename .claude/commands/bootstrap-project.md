# /bootstrap-project

Scaffold app project(s) from boilerplates into `<cwd>/apps/{web,backend,mobile,agent}/` based on the brief's Stage field. Wraps the bundled `init_boilerplate.sh` (POSTs to scaffold-service, unzips in place).

Trigger the `bootstrap-project` skill.

> **This repository is already scaffolded** (`apps/backend`, `apps/web`) and the `bootstrap-project` skill (with `init_boilerplate.sh`) is **not bundled** in `.claude/skills/` here — it belongs to the scaffold system. Skip this command in this repo; to add another app, use the scaffold system and then document the new app in `AGENTS.md` and `apps/orchestra.md`.

## Usage

```
/bootstrap-project
/bootstrap-project poc — web only
/bootstrap-project mvp — web + backend + agent
```

## Pre-condition

- `<cwd>/brief/00_OVERVIEW.md` exists (Stage field set).
- `<cwd>/design/` exists (for visual decisions during scaffold orientation).
- For Supabase-backed stacks: `<sandbox>/.supabase/credentials.env` exists (run `/supabase-init` first if missing).

## Action

Open `.claude/skills/bootstrap-project/SKILL.md` and follow the four steps:
1. Determine stage (read brief's Stage field).
2. Initialize boilerplates via `bash .claude/skills/bootstrap-project/scripts/init_boilerplate.sh -p <name> -s <stack> [-t <theme>]` per required stack, run from `<cwd>/`.
3. Dispatch orientation sub-agents (read each app's AI_GUIDE.md + key skills + brief + design).
4. Hand off to `sprint-builder`.

## Next step

When apps are scaffolded and oriented, user invokes `/sprint-builder`. Workforce-of-agents projects then trigger `/agent-builder` per role and `/mcp-builder` for any new tool.
