"""Structured (JSON) logging, configured once at app startup. Plain stdlib logging - no
extra dependency - since a custom Formatter is all that's needed to make logs machine-
parseable (for whatever log aggregator ends up reading them in production).

Sentry is wired in as a genuinely optional extra: only initialized if SENTRY_DSN is set,
same pattern as every other optional integration in this codebase (ElevenLabs, n8n) -
stays out of the way entirely for local dev.
"""
import json
import logging
import sys

from app.core.config import get_settings


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    settings = get_settings()

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)

    if settings.SENTRY_DSN:
        import sentry_sdk

        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENV, traces_sample_rate=0.1)
