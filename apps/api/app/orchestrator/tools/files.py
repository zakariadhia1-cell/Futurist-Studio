import os

from app.orchestrator.tool_registry import Tool, ToolContext, register
from app.orchestrator.tools.sandbox import resolve_in_workspace

_MAX_READ_CHARS = 20_000


async def _read_file(arguments: dict, ctx: ToolContext) -> str:
    path = str(arguments.get("path", "")).strip()
    if not path:
        return "Kein Pfad angegeben."
    try:
        full_path = resolve_in_workspace(ctx.user_id, path)
    except ValueError as exc:
        return str(exc)
    if not os.path.isfile(full_path):
        return f"Datei '{path}' existiert nicht."
    with open(full_path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    if len(content) > _MAX_READ_CHARS:
        content = content[:_MAX_READ_CHARS] + "\n... (gekuerzt)"
    return content


async def _write_file(arguments: dict, ctx: ToolContext) -> str:
    path = str(arguments.get("path", "")).strip()
    content = str(arguments.get("content", ""))
    if not path:
        return "Kein Pfad angegeben."
    try:
        full_path = resolve_in_workspace(ctx.user_id, path)
    except ValueError as exc:
        return str(exc)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Datei '{path}' gespeichert ({len(content)} Zeichen)."


register(
    Tool(
        name="read_file",
        description="Liest eine Datei aus dem persoenlichen Workspace-Ordner des Nutzers.",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Relativer Pfad im Workspace"}},
            "required": ["path"],
        },
        handler=_read_file,
    )
)

register(
    Tool(
        name="write_file",
        description="Schreibt/ueberschreibt eine Datei im persoenlichen Workspace-Ordner des Nutzers.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relativer Pfad im Workspace"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        handler=_write_file,
    )
)
