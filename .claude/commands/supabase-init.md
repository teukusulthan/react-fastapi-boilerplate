# /supabase-init

Bring up sandbox-level self-hosted Supabase via Docker. Generates fresh secrets, starts the stack, and emits `<sandbox>/.supabase/credentials.env` that be-python (`<cwd>/apps/backend/`), specialist agents, and the `supabase-db` MCP all consume.

Trigger the [`supabase-init`](../skills/supabase-init/SKILL.md) skill.

## Usage

```
/supabase-init
/supabase-init teardown
/supabase-init print-env
```

## Pre-condition

- Docker Engine + compose v2 installed.
- Free local ports `8000` (Kong) and `5432` (Postgres) — or override via env.
- Run **once per sandbox** — re-running on a healthy stack is idempotent (skip rotation, just re-emit `credentials.env`).

## Action

Open `.claude/skills/supabase-init/SKILL.md` and run the bundled `scripts/init.py`:

```
python .claude/skills/supabase-init/scripts/init.py
```

Or for teardown / re-emit:

```
python .claude/skills/supabase-init/scripts/teardown.py
python .claude/skills/supabase-init/scripts/print_env.py
```

## Next step

`<sandbox>/.supabase/credentials.env` is now the source of truth for `SUPABASE_*` env vars. Source it into:
- `<cwd>/apps/backend/.env`
- Each `<cwd>/apps/agents/<role>/.env` that touches Supabase
- `<cwd>/apps/mcp/supabase-db/.env` if scaffolded
