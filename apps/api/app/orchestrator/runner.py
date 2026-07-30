"""AgentRunner: the single execution loop every agent (Executive and, later, its
delegates) runs through. Phase 1 keeps it deliberately simple - stream a reply from the
agent's configured model, no tool-calling or delegation yet (that lands in Phase 3)."""
from collections.abc import AsyncIterator, Callable

from app.models.agent import Agent
from app.models.message import Message
from app.models_provider import registry
from app.models_provider.base import ChatMessage, ModelProvider

ProviderFactory = Callable[[str], ModelProvider]


async def stream_agent_reply(
    agent: Agent,
    model_provider: str,
    model_name: str,
    history: list[Message],
    provider_factory: ProviderFactory | None = None,
    memory_context: str | None = None,
) -> AsyncIterator[str]:
    """Stream the agent's reply to the conversation so far. `history` excludes system
    prompt (that comes from the agent's own configuration, not the message log).

    `provider_factory` is resolved lazily (via `registry.get_provider` by default) rather
    than bound as a default argument, so tests can monkeypatch `registry.get_provider` to
    inject a FakeProvider without needing a real API key.

    `memory_context`, when given, is appended to the system prompt - this is how
    retrieved knowledge-base chunks and memory facts (Phase 2) reach the model without
    the orchestrator needing to know anything about embeddings or pgvector.
    """
    factory = provider_factory or registry.get_provider
    provider = factory(model_provider)
    system_prompt = agent.system_prompt
    if memory_context:
        system_prompt = f"{system_prompt}\n\n{memory_context}"
    chat_messages = [ChatMessage(role=m.role, content=m.content) for m in history if m.role in ("user", "assistant")]
    async for chunk in provider.stream_chat(system_prompt=system_prompt, messages=chat_messages, model=model_name):
        yield chunk
