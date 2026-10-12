# /mcp-builder

Build a new pure-tool FastMCP server at `<cwd>/apps/mcp/<server-name>/` and register it with the MCPHub project group. Use when an agent needs a tool that does not yet exist in the hub — site-specific crawlers, internal-API wrappers, niche dataset parsers.

Trigger the [`mcp-builder`](../skills/mcp-builder/SKILL.md) skill.

## Usage

```
/mcp-builder
/mcp-builder buatkan mcp baru untuk crawl LPSE
/mcp-builder wrap our internal HRIS API as an MCP
```

## Pre-condition

- `<cwd>/brief/` exists with a Workforce Manifest section that lists the missing tool, OR the user explicitly names the tool needed.
- `MCP_HUB_URL` + `MCP_HUB_API_KEY` available; project group already created (`MCP_HUB_GROUP=<slug>`).

## Action

Open `.claude/skills/mcp-builder/SKILL.md` and follow:
1. Confirm no existing hub server already covers the tool (Pre-Step 1).
2. Scaffold the server skeleton at `<cwd>/apps/mcp/<server-name>/` with typed `@mcp.tool()` definitions, `ToolError` raises, and a `pyproject.toml`.
3. Implement the tool bodies (fetch/parse/transform logic).
4. Test locally (`python server.py` + FastMCP Client call).
5. Register the server with the hub and add it to the project group.

## Next step

Agents in the project group automatically pick the new tool up via MCPHub — no agent code change needed. User can re-run `/agent-builder` to verify or update agent instructions to reference the new tool.
