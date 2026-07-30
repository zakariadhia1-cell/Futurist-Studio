"""In-process Playwright session manager for the Browser Automation feature.

Scope note: the architecture doc (docs/architecture/FUTURIST_OS_ARCHITECTURE.md)
recommends running browser automation in a dedicated `browser-worker` container,
isolated from the main API process, since Chromium instances are heavy and can crash.
This Phase 4 implementation runs in-process instead - a deliberate scope reduction to
ship a working, testable feature now. The session/action API below is already the
right shape to move behind a job queue into a separate worker later without changing
the WebSocket contract the frontend depends on.
"""
import base64
import re
import uuid
from dataclasses import dataclass

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from app.core.config import get_settings

_playwright: Playwright | None = None
_browser: Browser | None = None


@dataclass
class BrowserSession:
    id: str
    user_id: uuid.UUID
    context: BrowserContext
    page: Page


_sessions: dict[str, BrowserSession] = {}

_HAS_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


async def _ensure_browser() -> Browser:
    global _playwright, _browser
    if _browser is None:
        _playwright = await async_playwright().start()
        # --no-sandbox: Chromium's own sandbox needs privileges (or a seccomp profile)
        # that a default Docker container doesn't grant; the container itself is the
        # isolation boundary here, so this is the standard, accepted trade-off for
        # running headless Chromium containerized.
        launch_kwargs = {"headless": True, "args": ["--no-sandbox"]}
        # Normally Playwright resolves its own downloaded browser (via `playwright
        # install chromium`) with no extra config needed. PLAYWRIGHT_EXECUTABLE_PATH is
        # an escape hatch for environments with a pre-provisioned browser binary in a
        # nonstandard location - leave unset in the common case.
        executable_path = get_settings().PLAYWRIGHT_EXECUTABLE_PATH
        if executable_path:
            launch_kwargs["executable_path"] = executable_path
        _browser = await _playwright.chromium.launch(**launch_kwargs)
    return _browser


async def create_session(user_id: uuid.UUID) -> BrowserSession:
    browser = await _ensure_browser()
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    page = await context.new_page()
    session_id = str(uuid.uuid4())
    session = BrowserSession(id=session_id, user_id=user_id, context=context, page=page)
    _sessions[session_id] = session
    return session


def get_session(session_id: str, user_id: uuid.UUID) -> BrowserSession | None:
    session = _sessions.get(session_id)
    if session is None or session.user_id != user_id:
        return None
    return session


def list_sessions(user_id: uuid.UUID) -> list[str]:
    return [s.id for s in _sessions.values() if s.user_id == user_id]


async def close_session(session_id: str, user_id: uuid.UUID) -> bool:
    session = get_session(session_id, user_id)
    if session is None:
        return False
    await session.context.close()
    del _sessions[session_id]
    return True


async def execute_action(session: BrowserSession, action: str, args: dict) -> str:
    page = session.page
    if action == "navigate":
        url = str(args.get("url", "")).strip()
        if not url:
            return "Keine URL angegeben."
        # Only bare hostnames like "google.com" need a scheme prepended - anything that
        # already has one (https:, data:, file:, about:, ...) must be left alone, or a
        # data: URL turns into the nonsensical "https://data:...".
        if not _HAS_SCHEME.match(url):
            url = f"https://{url}"
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return f"Navigiert zu {url}"
    if action == "click":
        selector = args.get("selector", "")
        await page.click(selector, timeout=5000)
        return f"Geklickt: {selector}"
    if action == "fill":
        selector = args.get("selector", "")
        value = args.get("value", "")
        await page.fill(selector, value, timeout=5000)
        return f"Ausgefuellt: {selector}"
    if action == "go_back":
        await page.go_back(timeout=10000)
        return "Zurueck navigiert."
    if action == "screenshot":
        return "Screenshot aktualisiert."
    return f"Unbekannte Aktion: {action}"


async def screenshot_base64(session: BrowserSession) -> str:
    png_bytes = await session.page.screenshot(type="png")
    return base64.b64encode(png_bytes).decode("ascii")


async def shutdown() -> None:
    """Closes the shared browser and its Playwright driver. Called from the app's
    shutdown lifecycle (see app/main.py) - Playwright's async driver is bound to the
    event loop it was started in, so it must not outlive that loop."""
    global _playwright, _browser
    _sessions.clear()
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None
