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
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Page, Playwright, Route, async_playwright

from app.core.config import get_settings
from app.orchestrator.tools.ssrf_guard import resolve_safe_ip

_playwright: Playwright | None = None
_browser: Browser | None = None

# F5 (docs/FIX_PLAN.md, S5 in docs/AUDIT_REPORT.md): schemes that don't touch the
# network or the host filesystem - self-contained page content, safe to allow.
_SAFE_NON_NETWORK_SCHEMES = {"data", "about", "blob"}
# Schemes that read from the host filesystem or otherwise shouldn't be reachable from
# agent-supplied navigation - file: was the concrete exploit in S5
# (navigate({"url":"file:///etc/passwd"}) + screenshot).
_BLOCKED_SCHEMES = {"file"}


async def _guard_request(route: Route) -> None:
    """Blocks every request the page - or content it renders - tries to make, not just
    the top-level navigate() URL. A real headless browser is a much bigger SSRF surface
    than a single fetch: it follows redirects itself, loads subresources (images,
    scripts, XHR), and can run page JS that issues its own fetch() calls - checking only
    the initial navigate() URL (see execute_action below) would miss all of those.
    Registered once per session in create_session() via page.route("**/*", ...), so this
    covers navigation, redirects, and every subresource load for the session's lifetime.

    Residual risk, documented rather than silently accepted: like is_safe_url() before
    F7, this is resolve-then-decide, not a pinned connection - Chromium's own network
    stack re-resolves DNS independently when it actually connects, so a fast-enough
    DNS-rebinding attack has the same theoretical TOCTOU window F7 closed for
    pinned_request(). Playwright's public API doesn't expose a way to pin a request to a
    specific IP the way httpx's `extensions` do, so this is best-effort, not equivalent
    to F7's guarantee - accepted given the "single trusted admin" threat model stated
    throughout this codebase (see sandbox.py), not adequate for an untrusted
    multi-tenant deployment.
    """
    parsed = urlparse(route.request.url)
    if parsed.scheme in _SAFE_NON_NETWORK_SCHEMES:
        await route.continue_()
        return
    if parsed.scheme not in ("http", "https"):
        await route.abort()
        return
    hostname = parsed.hostname
    if not hostname or resolve_safe_ip(hostname) is None:
        await route.abort()
        return
    await route.continue_()


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
    await page.route("**/*", _guard_request)
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
        # F5: reject clearly upfront (a friendly message) rather than relying solely on
        # _guard_request()'s route.abort(), which would surface as an opaque
        # "net::ERR_FAILED" from Playwright. _guard_request() still runs regardless -
        # this is a fast, clear first check, not a replacement for it (redirects and
        # subresource loads only ever go through _guard_request, never through here).
        parsed = urlparse(url)
        if parsed.scheme in _BLOCKED_SCHEMES:
            return f"Navigation zu '{parsed.scheme}:'-URLs ist nicht erlaubt."
        if parsed.scheme in ("http", "https"):
            hostname = parsed.hostname
            if not hostname or resolve_safe_ip(hostname) is None:
                return "URL abgelehnt: nur oeffentliche http(s)-Adressen sind erlaubt (keine internen/privaten Ziele)."
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
