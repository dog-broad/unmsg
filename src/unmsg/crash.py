"""Crash reporting: a scrubbed file written to disk, never uploaded.

When something unexpected breaks, we write a redacted report next to the logs so
the user can choose whether to share it. Nothing is ever sent automatically —
consistent with the no-telemetry promise.
"""

from __future__ import annotations

import platform
import sys
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType

from unmsg import paths
from unmsg._version import __version__
from unmsg.logging_setup import _redact

Notifier = Callable[[Path], None]


def write_crash_report(exc: BaseException, *, log_dir: Path | None = None) -> Path:
    """Write a redacted crash report and return its path."""
    directory = log_dir or paths.log_dir()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = directory / f"crash_{stamp}.txt"
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    target.write_text(_report_body(tb), encoding="utf-8")
    return target


def _report_body(traceback_text: str) -> str:
    header = [
        f"UnMsg {__version__} crash report",
        f"Python {platform.python_version()} on {platform.platform()}",
        "",
        "This file stays on your machine. Personal data has been removed.",
        "",
        "",
    ]
    return "\n".join(header) + _redact(traceback_text)


def install_excepthook(
    *, log_dir: Path | None = None, notify: Notifier | None = None
) -> None:
    """Route uncaught exceptions to a disk report (and an optional notifier)."""
    previous = sys.excepthook

    def hook(
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        try:
            path = write_crash_report(exc, log_dir=log_dir)
            if notify is not None:
                notify(path)
        finally:
            previous(exc_type, exc, tb)

    sys.excepthook = hook
