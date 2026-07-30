from collections.abc import AsyncIterator

import anthropic

from app.models_provider.base import ChatMessage, ChatResult, ModelProvider, ToolCall, ToolSpec


def _to_anthropic_messages(messages: list[ChatMessage]) -> list[dict]:
    converted = []
    for m in messages:
        if m.role == "tool":
            converted.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": m.tool_call_id, "content": m.content}
                    ],
                }
            )
        elif m.role == "assistant" and m.tool_calls:
            blocks = []
            if m.content:
                blocks.append({"type": "text", "text": m.content})
            for tc in m.tool_calls:
                blocks.append({"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.arguments})
            converted.append({"role": "assistant", "content": blocks})
        else:
            converted.append({"role": m.role, "content": m.content})
    return converted


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
            messages=_to_anthropic_messages(messages),
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def chat_with_tools(
        self, system_prompt: str, messages: list[ChatMessage], model: str, tools: list[ToolSpec]
    ) -> ChatResult:
        if not tools:
            return await super().chat_with_tools(system_prompt, messages, model, tools)

        response = await self._client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=_to_anthropic_messages(messages),
            tools=[{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in tools],
        )

        tool_calls = [
            ToolCall(id=block.id, name=block.name, arguments=block.input)
            for block in response.content
            if block.type == "tool_use"
        ]
        if tool_calls:
            return ChatResult(tool_calls=tool_calls)

        text = "".join(block.text for block in response.content if block.type == "text")
        return ChatResult(text=text)

    async def analyze_image(self, image_b64: str, media_type: str, instruction: str, model: str) -> str:
        response = await self._client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                        {"type": "text", "text": instruction},
                    ],
                }
            ],
        )
        return "".join(block.text for block in response.content if block.type == "text")
