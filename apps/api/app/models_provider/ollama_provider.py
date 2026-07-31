import json
from collections.abc import AsyncIterator

import httpx

from app.models_provider.base import ChatMessage, ModelProvider


class OllamaProvider(ModelProvider):
    """Talks to a local Ollama server - no API key, runs entirely on-device."""

    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")

    async def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}]
            + [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content")
                    if content:
                        yield content
