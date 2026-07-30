"""Provider-agnostic chat interface. Every LLM backend (OpenAI, Anthropic, Ollama, ...)
implements this so the orchestrator never depends on a specific vendor SDK."""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant" | "tool"
    content: str = ""
    tool_calls: list[ToolCall] | None = None  # set on an assistant message that invoked tools
    tool_call_id: str | None = None  # set on a "tool" message: which call this is the result of


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict  # JSON schema for the tool's parameters


@dataclass
class ChatResult:
    """Either `text` or `tool_calls` is set, never both - a turn either answers or acts."""

    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class ModelProvider(ABC):
    @abstractmethod
    def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        """Yield response text chunks as they arrive. No tool-calling support - used for
        plain conversation turns (an agent with no tools configured)."""
        raise NotImplementedError

    async def chat_with_tools(
        self, system_prompt: str, messages: list[ChatMessage], model: str, tools: list[ToolSpec]
    ) -> ChatResult:
        """One turn of a tool-calling conversation: either the model answers (text) or
        asks to invoke one or more tools (tool_calls) - the caller (AgentRunner) executes
        those, appends the results as "tool" messages, and calls this again.

        Default implementation: providers that haven't implemented real tool-calling
        support (e.g. Ollama today) fall back to plain stream_chat when no tools are
        requested, and refuse outright when tools are requested.
        """
        if tools:
            raise NotImplementedError(f"{type(self).__name__} unterstuetzt kein Tool-Calling.")
        text = "".join([chunk async for chunk in self.stream_chat(system_prompt, messages, model)])
        return ChatResult(text=text)

    async def analyze_image(self, image_b64: str, media_type: str, instruction: str, model: str) -> str:
        """Describe/read an image (Phase 6: Vision/OCR). Default: unsupported - only
        providers with a vision-capable API override this."""
        raise NotImplementedError(f"{type(self).__name__} unterstuetzt keine Bildanalyse.")
