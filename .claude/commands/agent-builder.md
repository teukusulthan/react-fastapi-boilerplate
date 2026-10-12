# /agent-builder

Build a standalone Agno + FastMCP agent at `<cwd>/apps/agents/<role>/` and register it with MCPHub group + be-python `/agent-mgmt/agents`. Picks the right variant (tool-calling / structured-output / multimodal) based on the role.

Trigger the [`agent-builder`](../skills/agent-builder/SKILL.md) skill.

## Usage

```
/agent-builder
/agent-builder buatkan agent crawler untuk LPSE
/agent-builder add the validator role from workforce manifest
/agent-builder build a multimodal classifier
```

## Pre-condition

- `<cwd>/brief/00_OVERVIEW.md` exists with a Workforce Manifest section (or the user explicitly names a role).
- `<cwd>/apps/backend/` exists. **Note:** this boilerplate's backend does **not** include an `agent_mgmt` router or `/agent-mgmt/*` endpoints. If the workforce needs a registry/run log, add it first as a backend module (`AGENTS.md` §9 and recipe 5.1) — otherwise skip step 5's backend registration.
- For Supabase-touching agents: `<sandbox>/.supabase/credentials.env` exists.
- `MCP_HUB_URL`, `MCP_HUB_API_KEY`, `MCP_HUB_GROUP` set in the agent's `.env` (group = project slug from brief).

## Action

Open `.claude/skills/agent-builder/SKILL.md` and follow:
1. Scaffold via `bash .claude/skills/bootstrap-project/scripts/init_boilerplate.sh -p <role> -s agent-python && mv apps/agent apps/agents/<role>`.
2. Edit `agent.py` (variant, model, description, instructions).
3. Edit `server.py` (FastMCP name, instructions, docstring).
4. Local smoke test (`python server.py` + FastMCP Client call).
5. Register with MCPHub project group (+ POST to `${BE_URL}/agent-mgmt/agents` with `X-Internal-Token: $BE_INTERNAL_TOKEN` **only if** that router has been added to `apps/backend`).

## Next step

For agents that need a tool not yet in the MCPHub group, user invokes `/mcp-builder` to scaffold the missing server.
