"""Fernet-based encryption for secrets stored at rest (e.g. MCP server environment
variables, which may hold API keys/tokens for whatever service the MCP server wraps).

Degrades gracefully instead of hard-failing when ENCRYPTION_KEY is unset - the same
pattern already used for other optional-but-important settings (ElevenLabs, n8n): stay
functional for local dev, but make the gap loudly visible via a one-time log warning.
Generate a real key for production with `Fernet.generate_key()`.

F9 (docs/FIX_PLAN.md): in production this fallback is unreachable, not just discouraged
- app/core/config.py::Settings._enforce_production_secrets() refuses to even start the
app if ENV=production and ENCRYPTION_KEY is empty, so by the time any code here runs,
ENCRYPTION_KEY is guaranteed set. The plaintext fallback below only ever executes in
dev/test, where that's the intended, documented behavior.
"""
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_warned = False


@lru_cache
def _get_fernet() -> Fernet | None:
    settings = get_settings()
    if not settings.ENCRYPTION_KEY:
        return None
    return Fernet(settings.ENCRYPTION_KEY.encode())


def _warn_once() -> None:
    global _warned
    if not _warned:
        logger.warning(
            "ENCRYPTION_KEY ist nicht gesetzt - Secrets werden unverschluesselt gespeichert. "
            "Fuer Produktion: einen Schluessel mit Fernet.generate_key() erzeugen und setzen."
        )
        _warned = True


def encrypt(value: str) -> str:
    fernet = _get_fernet()
    if fernet is None:
        _warn_once()
        return value
    return fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    fernet = _get_fernet()
    if fernet is None:
        return value
    try:
        return fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        # Stored before ENCRYPTION_KEY was set, or the key was rotated - surface the
        # original (garbled) value rather than crashing the caller with a 500.
        return value
