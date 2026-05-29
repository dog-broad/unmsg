"""Logging setup with PII redaction on by default.

The log pane and any on-disk log can carry subjects, addresses, and paths. For a
tool whose promise is privacy, those are redacted unless the user explicitly
opts into verbose logging. No log is ever sent anywhere.
"""

from __future__ import annotations

import logging
import re

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_WIN_PATH = re.compile(r"[A-Za-z]:\\[^\s,;]+")
_NIX_PATH = re.compile(r"(?<!\w)/(?:[^\s,;/]+/)+[^\s,;/]+")

LOGGER_NAME = "unmsg"


class RedactingFilter(logging.Filter):
    """Replace emails and filesystem paths in log messages with placeholders."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(record.getMessage())
        record.args = ()
        return True


def _redact(text: str) -> str:
    text = _EMAIL.sub("[email]", text)
    text = _WIN_PATH.sub("[path]", text)
    text = _NIX_PATH.sub("[path]", text)
    return text


def setup_logging(
    *, level: str = "INFO", redact: bool = True, handler: logging.Handler | None = None
) -> logging.Logger:
    """Configure and return the ``unmsg`` logger.

    Idempotent: re-running replaces handlers rather than stacking them. Pass a
    custom ``handler`` (e.g. one that writes into the GUI log pane).
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level.upper())
    logger.handlers.clear()

    target = handler or logging.StreamHandler()
    target.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-5s  %(message)s"))
    if redact:
        target.addFilter(RedactingFilter())
    logger.addHandler(target)
    logger.propagate = False
    return logger
