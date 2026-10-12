# Variant — Structured output

**Model:** `openai/gpt-oss-120b:nitro` (OpenRouter, premium-throughput tier).
**Use cases:** single-shot extraction — text in → Pydantic model out. Form parsing, intent classification, entity extraction, content moderation, "give me a tagged summary of this article."

## Why this model

GPT-OSS-120B is fast, cheap on `:nitro`, and produces clean JSON. For single-step LLM calls without tool use, this is the workhorse. Reach for tool-calling only when the agent must take multiple steps; reach for multimodal only when the input is non-text.

## Minimal worked example

```python
# <cwd>/apps/agents/classify_intent/agent.py
from typing import Literal
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openrouter import OpenRouter

# --- output schema ---

class Intent(BaseModel):
    kind: Literal["question", "complaint", "request", "compliment", "spam"]
    urgency: Literal["low", "medium", "high"]
    summary: str = Field(description="One-sentence summary in the original language.")
    suggested_handler: Literal["bot", "human-tier1", "human-tier2", "ignore"]

# --- the agent ---

_agent = Agent(
    model=OpenRouter(id="openai/gpt-oss-120b:nitro"),
    description="Customer-support intent classifier.",
    instructions=[
        "Classify the message into one of the predefined kinds.",
        "Use 'high' urgency only for explicit threats, outages, payment failures, or safety issues.",
        "Suggest 'bot' only for FAQ-level questions.",
    ],
    output_schema=Intent,
    use_json_mode=True,   # forces JSON via prompt; keeps the response strictly parseable
)

# --- public entry point ---

async def run(text: str) -> Intent:
    response = await _agent.arun(f"Classify this customer message:\n\n{text}")
    return response.content   # already parsed into the Intent model

if __name__ == "__main__":
    import asyncio, sys
    msg = " ".join(sys.argv[1:]) or "Saya mau komplain, sudah 3 hari pesanan belum sampai!"
    print(asyncio.run(run(msg)))
```

## Common pitfalls

- **Prefer `Literal` enums to free-text.** The model commits to one of the listed values; downstream code can pattern-match safely.
- **`Field(description=...)` is the prompt for that field.** The model reads it. Use it to tighten the contract: `Field(description="One-sentence summary in the original language")` beats unannotated `str`.
- **Use `use_json_mode=True` for older / smaller models.** It forces JSON output via prompt scaffolding when the model doesn't natively support structured output. For models that do, drop it (slightly faster, no scaffolding overhead).
- **Don't add tools to a structured-output agent.** If you need tools, you're in the tool-calling variant — switch.
- **The response is already parsed.** `response.content` is an instance of your Pydantic model, not a string. No `json.loads` needed.

## Triggering this agent

Most common pattern: a webhook fires this on inbound messages.

```python
# routers/agents.py
from fastapi import APIRouter, Header
from pydantic import BaseModel
from agents.classify_intent import run as run_classify

router = APIRouter(prefix="/agents")

class MessageIn(BaseModel):
    channel: str
    user_id: str
    text: str

@router.post("/webhooks/inbound-message")
async def on_inbound(body: MessageIn, x_signature: str = Header(...)):
    verify_webhook_signature(body, x_signature)
    intent = await run_classify(body.text)
    # route based on intent.suggested_handler …
    return {"intent": intent.model_dump(), "routed_to": intent.suggested_handler}
```
