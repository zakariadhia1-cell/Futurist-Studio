"""Talks to Claude — the "brain" of Jarvis."""
import base64
from datetime import datetime
from typing import Optional

import anthropic

from jarvis.backend.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ANTHROPIC_VISION_MODEL
from jarvis.backend.prompts import build_system_prompt

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY ist nicht gesetzt.")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def think(history: list[dict]) -> str:
    """Send the conversation to Claude and return Jarvis' raw reply (may contain an [ACTION:...] tag)."""
    current_time = datetime.now().strftime("%H:%M")
    system_prompt = build_system_prompt(current_time)

    response = get_client().messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=600,
        system=system_prompt,
        messages=history,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def see(image_png_bytes: bytes, instruction: str) -> str:
    """Ask Claude Vision to describe a screenshot."""
    b64 = base64.standard_b64encode(image_png_bytes).decode("utf-8")
    response = get_client().messages.create(
        model=ANTHROPIC_VISION_MODEL,
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64},
                    },
                    {"type": "text", "text": instruction},
                ],
            }
        ],
    )
    return "".join(block.text for block in response.content if block.type == "text")
