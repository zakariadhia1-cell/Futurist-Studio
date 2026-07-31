import asyncio

from app.orchestrator.tool_registry import Tool, ToolContext, register
from app.orchestrator.tools.sandbox import safe_shell_env, user_workspace_dir

_TIMEOUT_SECONDS = 20
_MAX_OUTPUT_CHARS = 8_000


async def _run_terminal_command(arguments: dict, ctx: ToolContext) -> str:
    command = str(arguments.get("command", "")).strip()
    if not command:
        return "Kein Befehl angegeben."

    workdir = user_workspace_dir(ctx.user_id)
    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=workdir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=safe_shell_env(ctx.user_id),
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        proc.kill()
        return f"Befehl abgebrochen: Zeitlimit ({_TIMEOUT_SECONDS}s) ueberschritten."

    output = stdout.decode("utf-8", errors="replace")
    if len(output) > _MAX_OUTPUT_CHARS:
        output = output[:_MAX_OUTPUT_CHARS] + "\n... (gekuerzt)"
    return f"Exit-Code {proc.returncode}:\n{output}"


register(
    Tool(
        name="run_terminal_command",
        description=(
            "Fuehrt einen Shell-Befehl im persoenlichen Workspace-Ordner des Nutzers aus "
            "(20s Zeitlimit). Kein Zugriff ausserhalb dieses Ordners."
        ),
        input_schema={
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
        handler=_run_terminal_command,
    )
)
