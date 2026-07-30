"""In-memory ModelProvider used by tests and local development without API keys."""
import asyncio
from collections.abc import AsyncIterator

from app.models_provider.base import ChatMessage, ModelProvider


class FakeProvider(ModelProvider):
    def __init__(self, response: str = "Das ist eine Test-Antwort von Jarvis."):
        self._response = response

    async def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        for word in self._response.split(" "):
            await asyncio.sleep(0)
            yield word + " "
