"""AgentRunner: the execution loop(s) every agent runs through.

Two entry points, chosen by whether the agent has any tools configured:
- stream_agent_reply: plain conversation, real token-by-token streaming from the
  provider. Used when an agent has no tools (config.tools is empty/absent) - this is
  the original Phase 1 path, unchanged.
- run_agent_turn: tool-calling loop (Phase 3). Each iteration is a non-streaming call
  that either returns text (done) or tool_calls (execute them, append results, loop
  again, up to max_iterations). Delegation is just another tool call
  (delegate_to_agent), so the Executive Agent needs no special-cased code path here -
  it runs through the exact same loop as every other tool-using agent.

Trade-off worth naming: because tool-calling and streaming aren't combined here (see
ModelProvider.chat_with_tools's docstring), an agent with tools loses live token-by-
token streaming for its final answer - the caller gets the complete text back and can
simulate streaming (e.g. chunk it word-by-word) for a consistent UI, same as before.
"""
from collections.abc import AsyncIterator, Callable

from app.models.agent import Agent
from app.models.message import Message
from app.models_provider import registry
from app.models_provider.base import ChatMessage, ModelProvider
from app.orchestrator.tool_registry import ToolContext, execute_tool, get_tools

ProviderFactory = Callable[[str], ModelProvider]

MAX_TOOL_ITERATIONS = 6


def _build_system_prompt(agent: Agent, memory_context: str | None) -> str:
    if memory_context:
        return f"{agent.system_prompt}\n\n{memory_context}"
    return agent.system_prompt


def _history_to_chat_messages(history: list[Message]) -> list[ChatMessage]:
    return [ChatMessage(role=m.role, content=m.content) for m in history if m.role in ("user", "assistant")]


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
    """
    factory = provider_factory or registry.get_provider
    provider = factory(model_provider)
    system_prompt = _build_system_prompt(agent, memory_context)
    chat_messages = _history_to_chat_messages(history)
    async for chunk in provider.stream_chat(system_prompt=system_prompt, messages=chat_messages, model=model_name):
        yield chunk


async def run_agent_turn(
    agent: Agent,
    model_provider: str,
    model_name: str,
    history: list[Message],
    tool_context: ToolContext,
    provider_factory: ProviderFactory | None = None,
    memory_context: str | None = None,
    max_iterations: int = MAX_TOOL_ITERATIONS,
) -> str:
    """Runs the tool-calling loop and returns the agent's final text answer."""
    factory = provider_factory or registry.get_provider
    provider = factory(model_provider)
    system_prompt = _build_system_prompt(agent, memory_context)

    tool_names: list[str] = (agent.config or {}).get("tools", [])
    tools = get_tools(tool_names)
    tool_specs = [t.as_spec() for t in tools]

    chat_messages = _history_to_chat_messages(history)

    for _ in range(max_iterations):
        result = await provider.chat_with_tools(system_prompt, chat_messages, model_name, tool_specs)
        if not result.tool_calls:
            return result.text or ""

        chat_messages.append(
            ChatMessage(role="assistant", content=result.text or "", tool_calls=result.tool_calls)
        )
        for call in result.tool_calls:
            output = await execute_tool(call.name, call.arguments, tool_context)
            chat_messages.append(ChatMessage(role="tool", content=output, tool_call_id=call.id))

    return "Ich konnte die Anfrage nicht innerhalb der erlaubten Schritte abschliessen."
