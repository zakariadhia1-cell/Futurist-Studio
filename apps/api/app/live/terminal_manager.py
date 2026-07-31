"""In-process PTY-backed terminal sessions.

Real pseudo-terminal (via os.openpty), not just piped stdout - this means interactive
programs (less, vim, a shell prompt with job control) behave correctly, unlike a plain
subprocess with pipes. Confined to the user's workspace directory, same caveat as the
Developer Agent's run_terminal_command tool (app/orchestrator/tools/sandbox.py): this is
directory-level confinement only, not real OS-level sandboxing - a Phase 4/9 dependency
before this could be exposed to untrusted or multi-tenant users.
"""
import asyncio
import fcntl
import os
import pty
import struct
import termios
import uuid
from dataclasses import dataclass, field

from app.orchestrator.tools.sandbox import safe_shell_env, user_workspace_dir


@dataclass
class TerminalSession:
    id: str
    user_id: uuid.UUID
    master_fd: int
    process: asyncio.subprocess.Process
    output_queue: asyncio.Queue = field(default_factory=asyncio.Queue)


_sessions: dict[str, TerminalSession] = {}


def _set_winsize(fd: int, rows: int = 24, cols: int = 80) -> None:
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


async def create_session(user_id: uuid.UUID) -> TerminalSession:
    workdir = user_workspace_dir(user_id)
    master_fd, slave_fd = pty.openpty()
    _set_winsize(master_fd)

    env = safe_shell_env(user_id)
    env["TERM"] = "xterm-256color"
    process = await asyncio.create_subprocess_exec(
        "/bin/bash",
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=workdir,
        start_new_session=True,
        env=env,
    )
    os.close(slave_fd)  # the child holds its own dup'd copy; the parent doesn't need this one

    session_id = str(uuid.uuid4())
    session = TerminalSession(id=session_id, user_id=user_id, master_fd=master_fd, process=process)
    _sessions[session_id] = session

    loop = asyncio.get_event_loop()

    def _on_readable() -> None:
        try:
            data = os.read(master_fd, 4096)
        except OSError:
            data = b""
        if data:
            session.output_queue.put_nowait(data)
        else:
            loop.remove_reader(master_fd)
            session.output_queue.put_nowait(None)  # sentinel: shell exited

    loop.add_reader(master_fd, _on_readable)
    return session


def get_session(session_id: str, user_id: uuid.UUID) -> TerminalSession | None:
    session = _sessions.get(session_id)
    if session is None or session.user_id != user_id:
        return None
    return session


def list_sessions(user_id: uuid.UUID) -> list[str]:
    return [s.id for s in _sessions.values() if s.user_id == user_id]


def write_input(session: TerminalSession, data: str) -> None:
    os.write(session.master_fd, data.encode("utf-8"))


def resize(session: TerminalSession, rows: int, cols: int) -> None:
    _set_winsize(session.master_fd, rows, cols)


async def close_session(session_id: str, user_id: uuid.UUID) -> bool:
    session = get_session(session_id, user_id)
    if session is None:
        return False
    try:
        session.process.kill()
    except ProcessLookupError:
        pass
    await session.process.wait()
    try:
        asyncio.get_event_loop().remove_reader(session.master_fd)
    except (ValueError, OSError):
        pass
    try:
        os.close(session.master_fd)
    except OSError:
        pass
    del _sessions[session_id]
    return True
