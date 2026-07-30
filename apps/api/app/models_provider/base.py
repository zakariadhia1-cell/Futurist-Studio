"""Provider-agnostic chat interface. Every LLM backend (OpenAI, Anthropic, Ollama, ...)
implements this so the orchestrator never depends on a specific vendor SDK."""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


class ModelProvider(ABC):
    @abstractmethod
    def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        """Yield response text chunks as they arrive."""
        raise NotImplementedError
