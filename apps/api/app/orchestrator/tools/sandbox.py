"""Confines the Developer Agent's file/terminal tools to a per-user directory.

This is directory-level confinement only, not real OS sandboxing (no container, no
seccomp, no resource limits) - commands run with the same privileges as the API server
process. Acceptable for now because Phase 0 assumes a single, trusted admin user acting
on their own behalf; real isolation (separate containers per session) is a Phase 4/9
requirement before this could ever be exposed to untrusted or multi-tenant users.
"""
import os
import uuid

from app.core.config import get_settings


def user_workspace_dir(user_id: uuid.UUID) -> str:
    settings = get_settings()
    path = os.path.join(settings.WORKSPACES_DIR, str(user_id))
    os.makedirs(path, exist_ok=True)
    return path


def resolve_in_workspace(user_id: uuid.UUID, relative_path: str) -> str:
    base = user_workspace_dir(user_id)
    target = os.path.normpath(os.path.join(base, relative_path))
    if target != base and not target.startswith(base + os.sep):
        raise ValueError(f"Pfad '{relative_path}' verlaesst den Workspace-Sandbox-Ordner.")
    return target
