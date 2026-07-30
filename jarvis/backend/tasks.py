"""Loads the task overview shown when Z activates Jarvis."""
import json
import os

from jarvis.backend.config import TASKS_FILE


def get_tasks() -> list[str]:
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [str(t) for t in data] if isinstance(data, list) else []
    except Exception:
        return []
