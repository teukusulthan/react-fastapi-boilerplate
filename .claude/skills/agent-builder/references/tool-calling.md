# Variant — Tool-calling

**Model:** `z-ai/glm-4.7:nitro` (OpenRouter, premium-throughput tier).
**Use cases:** agentic crawler, multi-step research, deep analysis where the agent needs to call tools (HTTP fetch, DB query, API lookup, file I/O) and chain reasoning steps.

## Why this model

GLM-4.7 ranks high on tool-calling benchmarks and reliably emits valid tool-call JSON for nested arguments. The `:nitro` suffix gives premium routing (lower latency, higher throughput). For prompt-completion-only agents (no tools), prefer `structured-output`; for image input, prefer `multimodal`.

## Tools come from the project's MCPHub group

Per the [agent-builder rules](../SKILL.md#tool-connectivity--mcp-first-via-the-project-group-mandatory), the agent connects to **one URL**: the project's MCPHub group. The group already contains every tool the project needs — existing hub servers (e.g. `brave-search`, Indonesian datasets) plus any custom MCPs the project built via [`skills/mcp-builder`](../../mcp-builder/SKILL.md).

You don't pick servers in agent code. The group is the contract.

## Minimal worked example

A research agent that summarizes a webpage and surfaces related news. Connects to the project group — does not name any specific server.

```python
# <cwd>/apps/agents/research/agent.py
import os
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.mcp import MCPTools

# --- public entry point ---

async def run(url: str) -> str:
    """Summarize a page and surface related news. Returns markdown text."""
    async with MCPTools(
        transport="streamable-http",
        url=f"{os.environ['MCP_HUB_URL']}/mcp/{os.environ['MCP_HUB_GROUP']}",
        client_params=dict(headers={"Authorization": f"Bearer {os.environ['MCP_HUB_API_KEY']}"}),
    ) as mcp:
        agent = Agent(
            model=OpenRouter(id="z-ai/glm-4.7:nitro"),
            description="A research assistant that fetches a page, summarizes it, and finds related news.",
            instructions=[
                "1. Fetch the given URL and read its content.",
                "2. Produce a one-paragraph summary (≤ 80 words).",
                "3. Search for 3 related news articles published in the last 30 days.",
                "4. Return markdown with sections: ## Summary, ## Related news (bullet list with titles + URLs).",
                "If a tool call fails, explain the failure rather than fabricating content.",
            ],
            tools=[mcp],
        )
        response = await agent.arun(f"Research this page: {url}")
        return response.content

if __name__ == "__main__":
    import asyncio, sys
    print(asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "https://example.com")))
```

## Smart routing (when the group has many tools)

If the project group has grown to many servers and the LLM is selecting tools poorly, swap the URL to scoped smart routing — same group, but the hub uses vector search to expose only the relevant subset per call:

```python
url=f"{os.environ['MCP_HUB_URL']}/mcp/$smart/{os.environ['MCP_HUB_GROUP']}"
```

No other code changes. Only do this when you've measured that the un-smart group is causing wrong tool selections — the un-smart group is faster and the model usually picks well.

## What if the agent needs a tool not yet in the group?

That's a project-bootstrap or project-evolution question, not an agent-code question.

1. **Existing hub server**: ask the team to run the MCPHub group-add API to put it into `$MCP_HUB_GROUP` (covered in [`bootstrap-project`](../../../commands/bootstrap-project.md)).
2. **No existing server fits**: build a new one via [`skills/mcp-builder`](../../mcp-builder/SKILL.md). That skill handles registration with the hub *and* addition to the project group.

The agent itself does not change in either case — when the group gains a tool, the agent's next run sees it automatically.

## Common pitfalls

- **Always `async with MCPTools(...)` (or `await mcp.connect()`).** Without connecting, tool calls silently fail.
- **Don't bypass the group.** The temptation to write `url=…/mcp/{some-specific-server}` for "speed" creates drift between agents and the project's tool inventory. Every agent should use the same group URL.
- **Don't connect to hub-wide endpoints.** `/mcp` and `/mcp/$smart` (without a group suffix) leak tools across projects.
- **Bearer token in `client_params={"headers": {...}}`, not the URL.**
- **Failures should return strings from the MCP tool, not raise.** A raised exception in a tool ends the agent run; a returned `"error: ..."` lets the agent reason about the failure. (FastMCP servers should use `raise ToolError(...)` — same effect, structured envelope.)
- **Cap tool output sizes inside the MCP server, not in the agent.** Large blobs returning into the prompt are the #1 cause of tool-loop blowouts.
- **No `print` in agent code** — use logging. The agent's `arun` handles user-visible output.

## Triggering this agent (FastAPI)

```python
# routers/agents.py
from fastapi import APIRouter
from pydantic import BaseModel
from agents.research import run as run_research

router = APIRouter(prefix="/agents")

class ResearchIn(BaseModel):
    url: str

@router.post("/research")
async def research(body: ResearchIn):
    return {"markdown": await run_research(body.url)}
```

For webhook trigger (another agent or external system fires this), add a separate handler that verifies the signature and forwards to `run_research`.
