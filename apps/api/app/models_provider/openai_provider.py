import json
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.models_provider.base import ChatMessage, ChatResult, ModelProvider, ToolCall, ToolSpec


def _to_openai_messages(system_prompt: str, messages: list[ChatMessage]) -> list[dict]:
    converted: list[dict] = [{"role": "system", "content": system_prompt}]
    for m in messages:
        if m.role == "tool":
            converted.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})
        elif m.role == "assistant" and m.tool_calls:
            converted.append(
                {
                    "role": "assistant",
                    "content": m.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                        }
                        for tc in m.tool_calls
                    ],
                }
            )
        else:
            converted.append({"role": m.role, "content": m.content})
    return converted


class OpenAIProvider(ModelProvider):
    def __init__(self, api_key: str):
        self._client = AsyncOpenAI(api_key=api_key)

    async def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=model,
            messages=_to_openai_messages(system_prompt, messages),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def chat_with_tools(
        self, system_prompt: str, messages: list[ChatMessage], model: str, tools: list[ToolSpec]
    ) -> ChatResult:
        if not tools:
            return await super().chat_with_tools(system_prompt, messages, model, tools)

        response = await self._client.chat.completions.create(
            model=model,
            messages=_to_openai_messages(system_prompt, messages),
            tools=[
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": t.input_schema},
                }
                for t in tools
            ],
        )
        message = response.choices[0].message

        if message.tool_calls:
            return ChatResult(
                tool_calls=[
                    ToolCall(id=tc.id, name=tc.function.name, arguments=json.loads(tc.function.arguments))
                    for tc in message.tool_calls
                ]
            )
        return ChatResult(text=message.content or "")

    async def analyze_image(self, image_b64: str, media_type: str, instruction: str, model: str) -> str:
        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}},
                    ],
                }
            ],
        )
        return response.choices[0].message.content or ""
