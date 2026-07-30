from collections.abc import AsyncIterator

import anthropic

from app.models_provider.base import ChatMessage, ModelProvider


class AnthropicProvider(ModelProvider):
    def __init__(self, api_key: str):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        ) as stream:
            async for text in stream.text_stream:
                yield text
