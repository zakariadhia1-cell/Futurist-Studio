"""Lets Jarvis 'see' the screen: screenshot + Claude Vision description."""
from jarvis.backend import browser
from jarvis.backend.brain import see

_INSTRUCTION = (
    "Das ist ein Screenshot von Z's Bildschirm. Beschreibe auf Deutsch in 2-3 knappen Saetzen, "
    "was zu sehen ist und was Z gerade zu tun scheint. Keine Ueberschriften, nur Fliesstext."
)


def describe_screen() -> str:
    png_bytes = browser.screenshot_current_page()
    if png_bytes is None:
        try:
            import mss

            with mss.mss() as sct:
                monitor = sct.monitors[1]
                raw = sct.grab(monitor)
                png_bytes = mss.tools.to_png(raw.rgb, raw.size)
        except Exception as exc:
            return f"Bildschirm konnte nicht erfasst werden: {exc}"

    try:
        return see(png_bytes, _INSTRUCTION)
    except Exception as exc:
        return f"Bildschirm konnte nicht analysiert werden: {exc}"
