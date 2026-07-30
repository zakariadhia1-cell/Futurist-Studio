"""ToolRegistry: a flat namespace of tools, each usable by whichever agents list it in
their `config.tools`. New agents get new tool *assignments*, not a new execution
mechanism - every tool call goes through the same execute() path regardless of agent."""
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models_provider.base import ToolSpec


@dataclass
class ToolContext:
    db: AsyncSession
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    handler: Callable[[dict, ToolContext], Awaitable[str]]

    def as_spec(self) -> ToolSpec:
        return ToolSpec(name=self.name, description=self.description, input_schema=self.input_schema)


_REGISTRY: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    _REGISTRY[tool.name] = tool


def get_tool(name: str) -> Tool | None:
    return _REGISTRY.get(name)


def get_tools(names: list[str]) -> list[Tool]:
    tools = []
    for name in names:
        tool = get_tool(name)
        if tool is not None:
            tools.append(tool)
    return tools


async def execute_tool(name: str, arguments: dict, context: ToolContext) -> str:
    tool = get_tool(name)
    if tool is None:
        return f"Unbekanntes Tool: '{name}'"
    try:
        return await tool.handler(arguments, context)
    except Exception as exc:  # noqa: BLE001 - tool failures surface to the model, not as a crash
        return f"Tool '{name}' ist fehlgeschlagen: {exc}"
