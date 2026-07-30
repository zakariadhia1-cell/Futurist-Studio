import httpx
from bs4 import BeautifulSoup

from app.orchestrator.tool_registry import Tool, ToolContext, register

_MAX_PAGE_CHARS = 6_000


async def _web_search(arguments: dict, ctx: ToolContext) -> str:
    query = str(arguments.get("query", "")).strip()
    if not query:
        return "Kein Suchbegriff angegeben."
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (compatible; FuturistOS/1.0)"},
            )
            resp.raise_for_status()
    except Exception as exc:
        return f"Suche fehlgeschlagen: {exc}"

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for result in soup.select(".result")[:5]:
        title_el = result.select_one(".result__title")
        snippet_el = result.select_one(".result__snippet")
        title = title_el.get_text(strip=True) if title_el else ""
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        if title:
            results.append(f"- {title}: {snippet}")
    if not results:
        return f"Keine Suchergebnisse fuer '{query}'."
    return f"Suchergebnisse fuer '{query}':\n" + "\n".join(results)


async def _read_page(arguments: dict, ctx: ToolContext) -> str:
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
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    if len(text) > _MAX_PAGE_CHARS:
        text = text[:_MAX_PAGE_CHARS] + " ... (gekuerzt)"
    return text or "Seite enthielt keinen lesbaren Text."


register(
    Tool(
        name="web_search",
        description="Durchsucht das Internet (DuckDuckGo) und gibt die Top-Ergebnisse mit Snippets zurueck.",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        handler=_web_search,
    )
)

register(
    Tool(
        name="read_page",
        description="Laedt eine Webseite und gibt ihren lesbaren Text zurueck (ohne Skripte/Navigation).",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
        handler=_read_page,
    )
)
