"""Marketing Agent: on-page SEO heuristics (no external SEO API required)."""
import httpx
from bs4 import BeautifulSoup

from app.orchestrator.tool_registry import Tool, ToolContext, register

_TITLE_MIN, _TITLE_MAX = 30, 60
_META_MIN, _META_MAX = 70, 160


async def _seo_analyze(arguments: dict, ctx: ToolContext) -> str:
    url = str(arguments.get("url", "")).strip()
    if not url:
        return "Keine URL angegeben."
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; FuturistOS/1.0)"})
            resp.raise_for_status()
    except Exception as exc:
        return f"Seite konnte nicht geladen werden: {exc}"

    soup = BeautifulSoup(resp.text, "html.parser")
    findings: list[str] = []

    title = soup.title.get_text(strip=True) if soup.title else None
    if not title:
        findings.append("[Fehlt] Kein <title>-Tag gefunden.")
    elif not (_TITLE_MIN <= len(title) <= _TITLE_MAX):
        findings.append(f"[Hinweis] Title-Tag ist {len(title)} Zeichen lang (empfohlen: {_TITLE_MIN}-{_TITLE_MAX}): '{title}'")
    else:
        findings.append(f"[OK] Title-Tag: '{title}' ({len(title)} Zeichen)")

    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc_content = meta_desc.get("content", "").strip() if meta_desc else ""
    if not desc_content:
        findings.append("[Fehlt] Keine Meta-Description gefunden.")
    elif not (_META_MIN <= len(desc_content) <= _META_MAX):
        findings.append(
            f"[Hinweis] Meta-Description ist {len(desc_content)} Zeichen lang (empfohlen: {_META_MIN}-{_META_MAX})"
        )
    else:
        findings.append(f"[OK] Meta-Description: {len(desc_content)} Zeichen")

    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 0:
        findings.append("[Fehlt] Keine H1-Ueberschrift gefunden.")
    elif len(h1_tags) > 1:
        findings.append(f"[Hinweis] {len(h1_tags)} H1-Ueberschriften gefunden (empfohlen: genau 1).")
    else:
        findings.append(f"[OK] Genau eine H1: '{h1_tags[0].get_text(strip=True)}'")

    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]
    if images:
        findings.append(f"[Hinweis] {len(missing_alt)}/{len(images)} Bildern fehlt das alt-Attribut.")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    word_count = len(soup.get_text(separator=" ").split())
    findings.append(f"[Info] Sichtbarer Textumfang: ca. {word_count} Woerter.")

    return f"SEO-Analyse fuer {url}:\n" + "\n".join(f"- {line}" for line in findings)


register(
    Tool(
        name="seo_analyze",
        description="Analysiert eine Webseite auf grundlegende On-Page-SEO-Faktoren (Title, Meta-Description, Ueberschriften, Bild-Alt-Texte, Textumfang).",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
        handler=_seo_analyze,
    )
)
