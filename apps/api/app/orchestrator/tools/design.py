"""Design Agent: image generation via OpenAI (uses the same OPENAI_API_KEY as the
embeddings fallback in Phase 2 - no separate image-gen provider to configure)."""
import base64
import os
import uuid

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.orchestrator.tool_registry import Tool, ToolContext, register
from app.orchestrator.tools.sandbox import user_workspace_dir


async def _generate_image(arguments: dict, ctx: ToolContext) -> str:
    prompt = str(arguments.get("prompt", "")).strip()
    if not prompt:
        return "Kein Prompt angegeben."

    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return "Bildgenerierung ist nicht konfiguriert (OPENAI_API_KEY fehlt in .env)."

    size = arguments.get("size", "1024x1024")
    if size not in ("1024x1024", "1024x1792", "1792x1024"):
        size = "1024x1024"

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        response = await client.images.generate(
            model="dall-e-3", prompt=prompt, size=size, n=1, response_format="b64_json"
        )
    except Exception as exc:
        return f"Bildgenerierung fehlgeschlagen: {exc}"

    image_bytes = base64.b64decode(response.data[0].b64_json)
    workspace = user_workspace_dir(ctx.user_id)
    images_dir = os.path.join(workspace, "images")
    os.makedirs(images_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    file_path = os.path.join(images_dir, filename)
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return f"Bild erstellt und gespeichert unter images/{filename} (Prompt: '{prompt}')."


register(
    Tool(
        name="generate_image",
        description=(
            "Erstellt ein Bild aus einer Textbeschreibung (z.B. Logo, Illustration, UI-Mockup) "
            "und speichert es im Workspace-Ordner des Nutzers unter images/."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Beschreibung des gewuenschten Bildes"},
                "size": {"type": "string", "enum": ["1024x1024", "1024x1792", "1792x1024"]},
            },
            "required": ["prompt"],
        },
        handler=_generate_image,
    )
)
