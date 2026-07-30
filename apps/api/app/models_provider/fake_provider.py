"""In-memory ModelProvider used by tests and local development without API keys."""
import asyncio
from collections.abc import AsyncIterator

from app.models_provider.base import ChatMessage, ChatResult, ModelProvider, ToolSpec


class FakeProvider(ModelProvider):
    def __init__(self, response: str = "Das ist eine Test-Antwort von Jarvis."):
        self._response = response

    async def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        for word in self._response.split(" "):
            await asyncio.sleep(0)
            yield word + " "


class ScriptedToolProvider(ModelProvider):
    """Returns a pre-scripted sequence of ChatResults, one per call to chat_with_tools -
    lets tests exercise the AgentRunner's tool-call loop deterministically."""

    def __init__(self, script: list[ChatResult]):
        self._script = list(script)
        self.calls: list[list[ChatMessage]] = []  # records message history seen on each call

    async def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        result = await self.chat_with_tools(system_prompt, messages, model, tools=[])
        yield result.text or ""

    async def chat_with_tools(
        self, system_prompt: str, messages: list[ChatMessage], model: str, tools: list[ToolSpec]
    ) -> ChatResult:
        self.calls.append(messages)
        if not self._script:
            raise AssertionError("ScriptedToolProvider: Skript erschoepft, aber weiterer Aufruf erfolgt.")
        return self._script.pop(0)
