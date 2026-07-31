"""Importing this package registers every built-in tool (see tool_registry.register()).
Must be imported once at app startup - app/main.py does this."""
from app.orchestrator.tools import (  # noqa: F401
    automation,
    calendar_email,
    delegate,
    design,
    files,
    finance,
    marketing,
    mcp_tools,
    memory,
    research,
    tasks,
    terminal,
)
