# Variant — Multimodal

**Model:** `google/gemini-2.5-flash-lite` (OpenRouter).
**Use cases:** inputs that include images, video frames, or audio. Image classification, OCR, document understanding, "what's in this photo?", "is this receipt valid?".

## Why this model

Gemini Flash Lite is the cheapest reliable multimodal model on OpenRouter — fast inference, native image input, low cost per call. For very large images or fine-grained vision tasks step up to `google/gemini-2.5-pro`. For text-only, never use this — switch to structured-output.

The model does **not** need the `:nitro` suffix — Gemini routing is already low-latency.

## Minimal worked example

```python
# <cwd>/apps/agents/analyze_image/agent.py
from pathlib import Path
from pydantic import BaseModel
from agno.agent import Agent
from agno.media import Image
from agno.models.openrouter import OpenRouter

# --- output schema (optional but recommended) ---

class ImageAnalysis(BaseModel):
    is_document: bool
    primary_subject: str
    text_visible: str = ""           # OCR'd text if any, otherwise empty
    notes: str

# --- the agent ---

_agent = Agent(
    model=OpenRouter(id="google/gemini-2.5-flash-lite"),
    description="Vision analyst — describes the image and extracts any visible text.",
    instructions=[
        "If the image is a document (receipt, form, invoice, sign), set is_document=True and extract all visible text.",
        "Otherwise, describe the primary subject in 1–2 words and add a short note.",
    ],
    output_schema=ImageAnalysis,
)

# --- public entry point ---

async def run(image_path: str | None = None, image_url: str | None = None) -> ImageAnalysis:
    if image_path:
        image = Image(filepath=Path(image_path))
    elif image_url:
        image = Image(url=image_url)
    else:
        raise ValueError("provide either image_path or image_url")

    response = await _agent.arun("Analyze this image.", images=[image])
    return response.content

if __name__ == "__main__":
    import asyncio, sys
    arg = sys.argv[1] if len(sys.argv) > 1 else "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"
    if arg.startswith("http"):
        print(asyncio.run(run(image_url=arg)))
    else:
        print(asyncio.run(run(image_path=arg)))
```

## Common pitfalls

- **Pass images via `images=[...]` keyword arg in `arun` / `print_response`** — not concatenated into the prompt string. Agno's `Image(filepath=...)` or `Image(url=...)` handles base64 encoding for you.
- **One concept per call.** Multimodal models drift if the prompt asks for many unrelated outputs at once. If you need multiple analyses, run multiple calls (or design a Pydantic schema covering everything in one shot).
- **Cap image size client-side** if you're proxying user uploads. > ~4 MB images slow the request without improving accuracy on Flash Lite.
- **`output_schema` works with multimodal too.** Combine for "image in → structured JSON out."
- **Don't store the image bytes in your DB if a URL works.** Pass `Image(url=...)` from object storage rather than re-uploading bytes through your backend.

## Triggering this agent

Manual button-trigger after an upload:

```python
# routers/agents.py
from fastapi import APIRouter, UploadFile, File
import tempfile
from agents.analyze_image import run as run_analyze

router = APIRouter(prefix="/agents")

@router.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    # Persist briefly to disk; or use object storage and pass the URL
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    result = await run_analyze(image_path=tmp_path)
    return result.model_dump()
```

For internal agent-to-agent: a tool-calling agent can return `{"image_url": "..."}` and the orchestrator forwards that URL to `run(image_url=...)`.
