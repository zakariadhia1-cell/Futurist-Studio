"""Web search via DuckDuckGo HTML (no API key required)."""
import requests
from bs4 import BeautifulSoup


def web_search(query: str, max_results: int = 5) -> str:
    """Return a plain-text digest of top search results for the given query."""
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (compatible; JarvisAssistant/1.0)"},
            timeout=8,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for result in soup.select(".result")[:max_results]:
            title_el = result.select_one(".result__title")
            snippet_el = result.select_one(".result__snippet")
            title = title_el.get_text(strip=True) if title_el else ""
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            if title:
                results.append(f"- {title}: {snippet}")
        if not results:
            return f"Keine Suchergebnisse fuer '{query}' gefunden."
        return f"Suchergebnisse fuer '{query}':\n" + "\n".join(results)
    except Exception as exc:
        return f"Suche fehlgeschlagen: {exc}"
