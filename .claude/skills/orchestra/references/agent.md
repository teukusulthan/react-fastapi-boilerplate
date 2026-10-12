# Agent Agent

Handles agent (Agno + FastMCP) and MCP-server tasks. Each agent role lives at `apps/agents/<role>/`, each MCP server at `apps/mcp/<server>/`.

> **This boilerplate ships no agent or MCP app.** `apps/agents/` and `apps/mcp/` do not exist until a project creates them with the `agent-builder` / `mcp-builder` skills. The backend (`apps/backend/`) has **no** `/agent-mgmt/*` router either — agent registry / run logging only exist if a project adds that module (see `agent-builder` § "Adapting to this repository").

---

## Step 0 — Pick the skill

| Task | Skill |
|------|-------|
| New LLM agent (tool-calling / structured-output / multimodal), orchestrator, ops triple | `agent-builder` |
| New MCP server (tool that doesn't exist in the hub yet) | `mcp-builder` |
| Backend route that calls an agent / MCP tool | `agent-builder` § Trigger patterns B + `fastapi-api-design` |

If an agent folder already exists, read its `AI_GUIDE.md` first (structure, memory conventions, critical rules).

---

## Step 1 — Detect Active Agent Roles

List folders under `apps/agents/` — each subfolder is one agent role.

| Indicator file | Confirms |
|----------------|----------|
| `agent.py` + `pyproject.toml` (agno dep) | Agno-based agent |
| `server.py` (FastMCP) | Exposes itself via MCP |
| `_runs.py` | Logs runs to a backend `/agent-mgmt/agent-runs` endpoint (no-op when `BE_URL` is unset) |
| `memory/state.json` | Has machine-readable state |

If multiple `apps/agents/<role>/` folders exist, all are in scope.

---

## Multi-Role Coordination

When the task spans more than one agent role:

1. Detect all `apps/agents/<role>/` directories
2. Plan changes independently per role — agents communicate via the MCPHub group, NOT direct Python imports
3. Coordinate identity changes via the project's brief (`brief/AA_AGENT_<role>.md` or `brief/00_OVERVIEW.md` Section 4 Workforce Manifest)

---

## Never

- Hardcode API keys, hub URLs, or the backend URL — env vars only
- Call backend internal endpoints without the `X-Internal-Token` header (value = `BE_INTERNAL_TOKEN` from `apps/backend/.env`)
- Crash the agent if the backend is unreachable — `_runs.py` is best-effort
- Read or write files outside `memory/` for agent persistent state
- Embed business logic in `server.py` — it is a thin FastMCP wrapper around `agent.run`
- Bypass MCPHub by calling other agents' Python code directly
