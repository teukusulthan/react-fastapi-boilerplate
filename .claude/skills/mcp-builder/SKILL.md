---
name: mcp-builder
description: Build a new Python MCP (Model Context Protocol) server using FastMCP and register it with the team's MCP Hub so any Agno-based agent can use it. Use when an agent needs a tool that doesn't yet exist in the hub — site-specific crawlers, internal-API wrappers, specialized parsers, custom data sources. The deliverable is a runnable, typed, error-shaped MCP server in `<cwd>/apps/mcp/<server-name>/` plus a hub registration entry. Triggers: "buatkan mcp baru untuk crawl X", "wrap this internal API as an MCP", "add a tool for our agents to query Y", "create a reusable tool for the agents", "agent butuh tool yang belum ada di hub".
---

# MCP Builder

Builds reusable MCP tool servers with [FastMCP](https://gofastmcp.com). Output is a small Python project deployable as an HTTP service and registered with the team's [MCPHub](https://docs.mcphub.app/) so every agent can discover and call it.

> **MCP's position in the Argus paradigm:** MCP servers are the **tool fabric** that the workforce of agents uses to access the outside world (web/API/DB/parser). The brief's `## Workforce Manifest` at [`<cwd>/brief/00_OVERVIEW.md`](../brief-builder/SKILL.md) lists per-role **Tools (MCP)** — that is the inventory of MCPs that must exist in the project group before an agent can run. mcp-builder is invoked when the brief lists an MCP that does **not** yet exist in the hub.
>
> **Relationship to the backend:** in projects whose backend includes an agent-management module (the separate be-python boilerplate ships one as the `/agent-mgmt/*` router), that backend is the **service layer for the agents workforce** and MCP servers sit **below it** — the tool fabric the agents call via the MCPHub project group. Pattern: BE → AgentService.invoke → AgentMgmtService.fire_agent → MCPHub project group → MCP server tool. **This repository's backend (`apps/backend/`, FastAPI on port 8020) does not include that module**; its routes can still call MCP tools directly (see `agent-builder` § Trigger patterns B). Either way, every MCP server with critical I/O must follow the error/observability conventions in the "Error handling & observability" section below so a retry/escalation/DLQ chain can classify tool failures correctly.

## When to use

> **Scope: pure-tool MCPs only** (no LLM). Wraps a website, an API, a parser, a DB client. For LLM-powered agents, use [`agent-builder`](../agent-builder/SKILL.md) — it scaffolds standalone agents from the `agent-python/` boilerplate into `<cwd>/apps/agents/<role>/`. Both kinds of server end up registered in the project group the same way; the split is about what's *inside* the server (Python tools vs. an LLM call).

A new session can tell whether an MCP has already been built by listing `<cwd>/apps/mcp/`. If `<cwd>/apps/mcp/<server-name>/` already exists, the work is done — no rebuild.

Step 0: confirm no existing hub server already exposes the tool you need.

```bash
curl -sS -H "Authorization: Bearer $MCP_HUB_API_KEY" \
  "$MCP_HUB_URL/api/servers?page=1&limit=100"
```

If an existing server covers the use case, **don't build a new one** — instead, ensure that server is added to the project's MCPHub group (see "Register with the hub and the project group" below) and point the agent at the group.

Build a new MCP only when:
- The data source is bespoke (a specific portal, an internal API, a niche dataset).
- The transform is specialized (PDF table extraction, geo coordinate normalization, OCR pipeline).
- The wrapping makes the same logic reusable across **2+** future agents — if it's a one-shot, just write a regular Python function.

## File layout (project-level)

Each MCP server is its own project under `<cwd>/apps/mcp/`, sibling to `<cwd>/apps/web/`, `<cwd>/apps/backend/`, and `<cwd>/apps/agents/`:

```
<cwd>/apps/
├── fe/
├── be/
├── agents/
└── mcp/
    └── <server-name>/                ← kebab-case, descriptive (e.g. kemendagri-spending)
        ├── server.py                 ← the FastMCP server (entry point)
        ├── pyproject.toml            ← deps + run command
        ├── .env.example              ← documents required env vars (no secrets)
        ├── Dockerfile                ← optional: for hub-managed deployments
        └── README.md                 ← one screen of docs: what it does + tools it exposes
```

Naming: lowercase, hyphenated, ends with what the server *is*, not how it works. `kemendagri-spending` (good), `crawl-kemendagri-via-puppeteer` (bad — implementation leaks into the name).

## Minimal `server.py`

```python
# <cwd>/apps/mcp/<server-name>/server.py
import os
import logging
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("<server-name>")

mcp = FastMCP(
    name="<server-name>",
    instructions=(
        "One short paragraph describing what this server is for. "
        "Used by the LLM to decide whether to load tools from this server."
    ),
)

# --- secrets / config from env ---
# Fail loudly at import time if a required secret is missing.
def _env(key: str) -> str:
    v = os.environ.get(key)
    if not v:
        raise RuntimeError(f"{key} env var is required for this MCP server")
    return v

# Example: external API key needed by a tool below.
# API_KEY = _env("MY_DATA_SOURCE_API_KEY")

# --- tools ---

@mcp.tool
def search_records(
    query: Annotated[str, Field(description="Free-text search query.")],
    limit: Annotated[int, Field(description="Max results, 1..50.", ge=1, le=50)] = 10,
) -> list[dict]:
    """
    Search the <data source> for records matching the query.
    Returns a list of {id, title, url, snippet} dicts. Returns [] if nothing matches.
    """
    try:
        # ... do the actual fetching/parsing ...
        results = []
        if not results:
            return []
        return results[:limit]
    except Exception as e:
        log.exception("search_records failed")
        # ToolError is reported back to the client as a structured error, not a stack trace.
        raise ToolError(f"search_records failed: {type(e).__name__}: {e}") from e


@mcp.tool
def get_record(
    record_id: Annotated[str, Field(description="The record's stable ID.")]
) -> dict:
    """Fetch one record by ID. Returns the full record dict, or raises if not found."""
    # ...
    raise ToolError(f"record {record_id} not found")  # example shape


# --- run ---

if __name__ == "__main__":
    # HTTP transport for production / hub registration.
    # Bind 0.0.0.0 so containers / remote hosts can reach it.
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)
```

Key conventions in this skeleton — keep them all:

- **Typed parameters with `Annotated[..., Field(description=...)]`.** The `description` is the LLM's spec sheet for the parameter. Be precise — the model picks tools based on the docstring + descriptions.
- **One docstring per tool, three lines max.** First line: what it does. Then: input/output shape. Then: edge cases ("returns [] if no match").
- **`raise ToolError(...)` for failures.** FastMCP relays this as a structured error. Don't `return "error: ..."` — that's the agno pattern, but a FastMCP server should use `ToolError` so any client (not just agno agents) gets a clean error envelope.
- **No `print` calls; use `logging`.** stdout collides with stdio transport mode.
- **Cap response sizes inside the tool.** Truncate / paginate. Returning 100 KB blobs into an agent's prompt is what kills tool-calling loops.
- **Fail loudly at import time** for missing secrets — `_env()` helper above. Better than the server starting and every tool call returning "API_KEY missing."

## `pyproject.toml`

```toml
[project]
name = "<server-name>-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0",
    "httpx",                    # if your tools fetch HTTP
    "pydantic>=2.0",
    # ... domain-specific deps (beautifulsoup4, pypdf, etc.)
]

[project.scripts]
<server-name>-mcp = "server:main"   # optional CLI entry point
```

If you want a CLI entry point, add a small `def main(): mcp.run(...)` and reference it here.

## Local dev — run via FastMCP CLI

```bash
cd <cwd>/apps/mcp/<server-name>
# 1. quick run with auto-reload (stdio transport, dev only)
fastmcp run server.py --reload

# 2. HTTP transport on port 8000 (matches production)
fastmcp run server.py --transport http --port 8000
```

Test with the FastMCP client (no agno needed):

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as c:
        tools = await c.list_tools()
        print([t.name for t in tools])
        result = await c.call_tool("search_records", {"query": "test", "limit": 5})
        print(result.data)

asyncio.run(main())
```

## Resources (optional)

If your server has reference data the LLM should be able to *read* (not call as a tool), expose it as a resource:

```python
@mcp.resource("config://<server-name>/regions")
def list_regions() -> dict:
    """All region codes this server can query."""
    return {"regions": [{"code": "JKT", "name": "DKI Jakarta"}, ...]}
```

Resources are discovered by clients but not invoked unless the LLM explicitly asks.

## Register with the hub and the project group

Three steps. Required env: `MCP_HUB_URL`, `MCP_HUB_API_KEY` (Bearer token), and `MCP_HUB_GROUP` (the project group, set during `bootstrap-project`).

### 1. Run the server somewhere reachable from the hub

Options: a sidecar container next to the hub, a Coolify deploy, an internal Kubernetes service. The endpoint that matters: `http://<host>:<port>/mcp` (FastMCP's default streamable-HTTP path).

### 2. Register the server in MCPHub

```bash
SERVER_NAME=<server-name>           # the directory name from <cwd>/apps/mcp/<server-name>/
SERVER_URL=http://<host>:<port>/mcp # where you deployed it in step 1

curl -sS -X POST "$MCP_HUB_URL/api/servers" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MCP_HUB_API_KEY" \
  -d "$(cat <<JSON
{
  "name": "$SERVER_NAME",
  "config": {
    "type": "streamable-http",
    "url": "$SERVER_URL",
    "headers": {}
  }
}
JSON
)"
```

The hub responds with `{"success": true, "message": "Server added successfully"}`. From this point the server appears in `GET /api/servers` and is reachable as `$MCP_HUB_URL/mcp/<server-name>`.

If the server needs an upstream auth header (e.g. an internal API key the FastMCP server forwards), put it in `config.headers` so the hub injects it on every call.

### 3. Add the server to the project's group

This is the step that makes the new MCP reachable to the project's agents (which connect via `$MCP_HUB_URL/mcp/$MCP_HUB_GROUP`):

```bash
curl -sS -X POST "$MCP_HUB_URL/api/groups/$MCP_HUB_GROUP/servers" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MCP_HUB_API_KEY" \
  -d "{\"serverId\": \"$SERVER_NAME\"}"
```

Group must already exist — created by [`agent-builder` Step 0b](../agent-builder/SKILL.md#provision-the-project-group-one-time-per-project). If you're running mcp-builder before agent-builder has been used on this project, run that step first.

### 4. Verify the agent can see the new tools

```bash
# List the group's tools — your new server's tools should appear here.
curl -sS -H "Authorization: Bearer $MCP_HUB_API_KEY" \
  "$MCP_HUB_URL/api/servers" \
  | python -c "import json,sys; data=json.load(sys.stdin)['data']; print([s['name'] for s in data])"
```

The next agent run inside the project picks up the new tools automatically — no agent code changes required.

> **Live API reference**: <https://docs.mcphub.app/> and the MCPHub source on Context7 (`/samanhappy/mcphub`). The endpoint shapes above match MCPHub's current API; if the hub upgrades and the API drifts, update this skill.

## Error handling & observability

**Axiom "no human maintainer":** MCP server failures must never be silent — the agent has to decide retry / escalate based on the error response. Convention:

### Structured errors via `ToolError`

All tool failures use `raise ToolError(f"{type(e).__name__}: {e}")` — never `return "error: ..."` strings. FastMCP relays `ToolError` as a structured envelope that the agent can parse to decide retry policy:

```python
from fastmcp.exceptions import ToolError

@mcp.tool
def fetch_record(record_id: str) -> dict:
    try:
        resp = httpx.get(f"https://api.example.com/{record_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except httpx.TimeoutException as e:
        # Transient — agent retry layer (be-agent max_retries) will handle.
        raise ToolError(f"TimeoutException: {e}") from e
    except httpx.HTTPStatusError as e:
        # 4xx = non-recoverable (bad input); 5xx = transient.
        raise ToolError(f"HTTPStatusError {e.response.status_code}: {e}") from e
    except Exception as e:
        log.exception("fetch_record failed")
        raise ToolError(f"{type(e).__name__}: {e}") from e
```

**Why error class matters:** an agent-management module (e.g. be-python's `_is_transient()` in `service/agent_mgmt.py` of that separate boilerplate — not part of this repository) inspects the error class name to decide retry. Class names treated as transient: `TimeoutException`, `ReadTimeout`, `ConnectTimeout`, `ConnectError`, `RemoteProtocolError`, plus 5xx `HTTPStatusError`. An MCP tool that returns a generic `"error: ..."` string cannot be classified → no retry → immediate escalation.

### Observability via structured logging

Every tool invocation logs a short summary (input size, response size, latency, success/fail) — not the content. The monitor agent reads logs or metrics endpoints for drift detection:

```python
import time

@mcp.tool
def search_records(query: str, limit: int = 10) -> list[dict]:
    started = time.monotonic()
    try:
        results = _do_search(query)[:limit]
        log.info("search_records ok query_len=%d result_count=%d latency_ms=%d",
                 len(query), len(results), int((time.monotonic() - started) * 1000))
        return results
    except Exception as e:
        log.warning("search_records fail query_len=%d error_class=%s latency_ms=%d",
                    len(query), type(e).__name__, int((time.monotonic() - started) * 1000))
        raise ToolError(f"{type(e).__name__}: {e}") from e
```

**Don't log:** tool input verbatim (PII risk), full response payload (size + privacy), API keys, user identifiers. **Do log:** sizes, counts, error classes, latencies.

### Idempotency for retry safety

Agent-management modules (and orchestrator agents) retry failed tool calls. The tool must be idempotent — same input twice = same effect once:
- Read-only tools: trivially idempotent.
- Write tools: use upsert with a dedup key (e.g. `record_id`), an idempotency key in the body, or check-before-write.
- Charge/billing tools: protect with an idempotency key on the upstream API.

**Anti-pattern:** tool yang `INSERT` tanpa unique constraint → retry produces duplicate rows. Reframe ke upsert / merge.

## Auth

If your server holds secrets (calls a paid API, scrapes a rate-limited site), gate the tools using FastMCP's auth hooks. Two common shapes:

- **Bearer-token check** (cheapest):
  ```python
  from fastmcp.server.auth import require_scopes

  @mcp.tool(auth=require_scopes("internal"))
  def restricted(...): ...
  ```
- **Custom check function** for per-claim or per-tenant logic:
  ```python
  from fastmcp.server.auth import AuthContext
  def is_allowed(ctx: AuthContext) -> bool:
      return bool(ctx.token and ctx.token.claims.get("team") == "argus")
  @mcp.tool(auth=is_allowed)
  def restricted(...): ...
  ```

Don't reinvent auth in the tool body — use the hooks.

## Rules

- **One server, one domain.** A server bundles tools that share data/auth/rate-limit. Don't lump unrelated tools together — the LLM gets confused and the model spec sheet bloats.
- **Tools are async-safe and idempotent by default.** A tool may be retried; design it so retries don't double-charge / double-write.
- **No `print`, no bare `except`.** Use `logging` and `raise ToolError(...)`.
- **Document via docstring + `Field(description=...)`.** That's the LLM's contract — vague docstrings lead to wrong tool selection.
- **Secrets via env, fail at import.** Never inline credentials.
- **Version the server name.** If a breaking change is needed, register a new server (`<name>-v2`) rather than silently changing tool signatures.
- **Keep `server.py` under 300 lines.** If it grows, split into modules and import.

## End-to-end example (real shape, not pseudocode)

User asks: *"Buatkan agent untuk crawl pengumuman tender LPSE Kemenkeu — agent harus bisa search by tahun + kategori, dan ambil detail tender by ID."*

Project group: `dashboard_kemendagri` (the slug, set during `agent-builder` Step 0).

1. Confirm no existing hub server covers LPSE Kemenkeu (`/api/servers` returns nothing relevant).
2. Create `<cwd>/apps/mcp/lpse-kemenkeu/`:
   - `server.py` with two tools — `search_tenders(year, category, limit)` and `get_tender(tender_id)`.
   - Each tool fetches the LPSE site (with `httpx`), parses (`BeautifulSoup`), returns structured dicts.
   - Both raise `ToolError` on parse failure / 404.
3. Run locally with `fastmcp run server.py --reload`. Verify with the FastMCP `Client` quick script.
4. Deploy. Register with MCPHub:
   ```bash
   curl -sS -X POST "$MCP_HUB_URL/api/servers" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $MCP_HUB_API_KEY" \
     -d '{"name":"lpse-kemenkeu","config":{"type":"streamable-http","url":"http://lpse-kemenkeu.internal:8000/mcp"}}'
   ```
5. Add it to the project group:
   ```bash
   curl -sS -X POST "$MCP_HUB_URL/api/groups/dashboard_kemendagri/servers" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $MCP_HUB_API_KEY" \
     -d '{"serverId":"lpse-kemenkeu"}'
   ```
6. Build the agent via [`agent-builder`](../agent-builder/SKILL.md) tool-calling variant. The agent connects to `$MCP_HUB_URL/mcp/$MCP_HUB_GROUP` — it picks up the new tools on next run, no per-server URL hard-coding.
