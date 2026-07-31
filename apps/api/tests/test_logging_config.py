import json
import logging

from app.core.logging_config import _JsonFormatter, configure_logging


def test_json_formatter_produces_valid_json():
    record = logging.LogRecord(
        name="test.logger", level=logging.INFO, pathname=__file__, lineno=1, msg="hallo Z", args=(), exc_info=None
    )
    formatted = _JsonFormatter().format(record)
    payload = json.loads(formatted)
    assert payload["message"] == "hallo Z"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"


def test_json_formatter_includes_exception_info():
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="failed",
            args=(),
            exc_info=True,
        )
        import sys

        record.exc_info = sys.exc_info()
    formatted = _JsonFormatter().format(record)
    payload = json.loads(formatted)
    assert "ValueError: boom" in payload["exception"]


def test_configure_logging_does_not_raise():
    configure_logging()
    logging.getLogger("test").info("configure_logging smoke test")
