"""Fetches current world news headlines via a public RSS feed (no API key required)."""
import feedparser

from jarvis.backend.config import NEWS_RSS_URL


def get_news_digest(max_items: int = 6) -> str:
    try:
        feed = feedparser.parse(NEWS_RSS_URL)
        entries = feed.entries[:max_items]
        if not entries:
            return "Keine aktuellen Nachrichten gefunden."
        lines = [f"- {entry.title}" for entry in entries]
        return "Aktuelle Schlagzeilen:\n" + "\n".join(lines)
    except Exception as exc:
        return f"Nachrichten konnten nicht geladen werden: {exc}"
