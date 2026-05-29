"""Crash reporter: scrubbed, disk-only, hook routing."""

from __future__ import annotations

import sys

from unmsg.crash import install_excepthook, write_crash_report


def _boom() -> Exception:
    try:
        raise ValueError("failed reading alice@example.com at C:\\Users\\me\\x.msg")
    except ValueError as exc:
        return exc


def test_report_is_written_and_scrubbed(tmp_path):
    path = write_crash_report(_boom(), log_dir=tmp_path)
    assert path.exists()
    assert path.name.startswith("crash_") and path.suffix == ".txt"
    text = path.read_text("utf-8")
    assert "alice@example.com" not in text
    assert "x.msg" not in text
    assert "[email]" in text
    assert "ValueError" in text
    assert "UnMsg" in text


def test_install_excepthook_writes_and_notifies(tmp_path, monkeypatch):
    seen: list = []
    monkeypatch.setattr(sys, "excepthook", lambda *a: None)
    install_excepthook(log_dir=tmp_path, notify=seen.append)

    sys.excepthook(ValueError, _boom(), None)

    assert len(seen) == 1
    assert seen[0].exists()
    assert list(tmp_path.glob("crash_*.txt"))
