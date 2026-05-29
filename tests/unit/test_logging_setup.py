"""Logging setup: redaction on by default, idempotent configuration."""

from __future__ import annotations

import logging

from unmsg.logging_setup import LOGGER_NAME, _redact, setup_logging


def test_redacts_email_and_paths():
    out = _redact("sent alice@example.com from C:\\Users\\me\\secret.msg")
    assert "alice@example.com" not in out
    assert "secret.msg" not in out
    assert "[email]" in out
    assert "[path]" in out


def test_redacts_unix_path():
    assert "[path]" in _redact("read /home/me/mail/secret.msg now")


def test_setup_is_idempotent():
    setup_logging()
    setup_logging()
    logger = logging.getLogger(LOGGER_NAME)
    assert len(logger.handlers) == 1


def test_redacting_filter_applied_by_default(caplog):
    logger = setup_logging(level="DEBUG", handler=logging.StreamHandler())
    record = logging.LogRecord(
        LOGGER_NAME, logging.INFO, __file__, 1, "to bob@example.com", (), None
    )
    logger.handlers[0].filters[0].filter(record)
    assert "bob@example.com" not in record.getMessage()


def test_verbose_mode_keeps_detail():
    logger = setup_logging(redact=False, handler=logging.StreamHandler())
    assert not logger.handlers[0].filters
