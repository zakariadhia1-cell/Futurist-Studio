"""Wraps a persistent Playwright browser that Jarvis can drive on Z's behalf."""
from typing import Optional

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from jarvis.backend.config import BROWSER_HEADLESS

_playwright = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_page: Optional[Page] = None


def _ensure_started() -> Page:
    global _playwright, _browser, _context, _page
    if _page is not None and not _page.is_closed():
        return _page
    if _playwright is None:
        _playwright = sync_playwright().start()
    if _browser is None:
        _browser = _playwright.chromium.launch(headless=BROWSER_HEADLESS)
    if _context is None:
        _context = _browser.new_context()
    _page = _context.new_page()
    return _page


def open_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    page = _ensure_started()
    page.goto(url, wait_until="domcontentloaded", timeout=15000)
    return f"{url} wurde im Browser geoeffnet."


def screenshot_current_page() -> Optional[bytes]:
    """Return a PNG screenshot of the currently open page, or None if no page is open."""
    if _page is None or _page.is_closed():
        return None
    return _page.screenshot(type="png")


def shutdown() -> None:
    global _playwright, _browser, _context, _page
    for obj in (_page, _context, _browser):
        try:
            if obj is not None:
                obj.close()
        except Exception:
            pass
    if _playwright is not None:
        _playwright.stop()
    _playwright = _browser = _context = _page = None
