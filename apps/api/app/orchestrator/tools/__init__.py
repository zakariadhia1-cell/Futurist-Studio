"""Importing this package registers every built-in tool (see tool_registry.register()).
Must be imported once at app startup - app/main.py does this."""
from app.orchestrator.tools import delegate, files, memory, research, tasks, terminal  # noqa: F401
