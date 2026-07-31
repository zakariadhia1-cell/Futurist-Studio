"""Parses and executes the [ACTION:...] tags Jarvis appends to its replies."""
import re
from dataclasses import dataclass
from typing import Optional

from jarvis.backend import browser, news, search, vision

_ACTION_RE = re.compile(r"\[ACTION:(SEARCH|OPEN|SCREEN|NEWS)\]\s*(.*)", re.IGNORECASE | re.DOTALL)


@dataclass
class ParsedReply:
    spoken_text: str
    action: Optional[str]
    action_arg: str


def parse_reply(raw_text: str) -> ParsedReply:
    match = _ACTION_RE.search(raw_text)
    if not match:
        return ParsedReply(spoken_text=raw_text.strip(), action=None, action_arg="")
    spoken_text = raw_text[: match.start()].strip()
    action = match.group(1).upper()
    action_arg = match.group(2).strip()
    return ParsedReply(spoken_text=spoken_text, action=action, action_arg=action_arg)


def execute_action(action: str, action_arg: str) -> str:
    """Run the requested action and return a plain-text result to feed back to Claude."""
    if action == "SEARCH":
        return search.web_search(action_arg)
    if action == "OPEN":
        return browser.open_url(action_arg)
    if action == "SCREEN":
        return vision.describe_screen()
    if action == "NEWS":
        return news.get_news_digest()
    return f"Unbekannte Aktion: {action}"
