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


# F2 (docs/FIX_PLAN.md, S2 in docs/AUDIT_REPORT.md): spawned shells (the PTY terminal
# and the run_terminal_command tool) used to inherit the full API process environment
# ({**os.environ, ...}, or simply omitting `env=` - both hand over everything). Any user
# or prompt-injected agent running `env` or `cat /proc/self/environ` in that shell would
# dump JWT_SECRET_KEY, DATABASE_URL, ENCRYPTION_KEY, every provider API key, etc. An
# explicit allowlist of the handful of variables an interactive shell actually needs to
# function closes that without breaking normal shell usage.
_ALLOWED_HOST_ENV_VARS = ("PATH", "TERM", "LANG")


def safe_shell_env(user_id: uuid.UUID) -> dict[str, str]:
    """Minimal environment for a shell spawned on behalf of `user_id` - an explicit
    allowlist from the host process plus workspace-scoped HOME/PWD, never the full
    os.environ."""
    workdir = user_workspace_dir(user_id)
    env = {key: os.environ[key] for key in _ALLOWED_HOST_ENV_VARS if key in os.environ}
    env["HOME"] = workdir
    env["PWD"] = workdir
    return env
