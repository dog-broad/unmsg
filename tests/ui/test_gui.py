"""Offscreen GUI tests: file intake, conversion, and settings round-trip."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from unmsg.config import Config
from unmsg.ui.dialogs.settings import SettingsDialog
from unmsg.ui.main_window import MainWindow
from unmsg.ui.widgets.file_list import FileList


def test_drop_adds_files_and_switches_view(qtbot, tmp_path, make_record, monkeypatch):
    win = MainWindow(Config())
    qtbot.addWidget(win)
    assert win._stack.currentIndex() == 0  # empty state

    msg = tmp_path / "a.msg"
    msg.write_bytes(b"x")
    win._add_paths([msg])

    assert win._stack.currentIndex() == 1  # list view
    assert win._files.count() == 1


def test_file_list_state_transitions(qtbot, tmp_path):
    widget = FileList()
    qtbot.addWidget(widget)
    path = tmp_path / "x.msg"
    widget.add_paths([path])
    widget.set_state(path, "done", bundle=tmp_path)
    item = widget.item(0)
    assert "✓" in item.text()


def test_conversion_completes_and_writes_output(
    qtbot, tmp_path, make_record, monkeypatch
):
    import unmsg.core.pipeline as pipeline

    monkeypatch.setattr(pipeline, "read_msg", lambda path: make_record())

    config = Config()
    out = tmp_path / "out"
    config.output.directory = str(out)
    config.output.formats = ["md"]

    win = MainWindow(config)
    qtbot.addWidget(win)
    win._options._output.setText(str(out))

    src = tmp_path / "mail.msg"
    src.write_bytes(b"x")
    win._add_paths([src])
    win._start_convert()

    qtbot.waitUntil(lambda: win._thread is None, timeout=8000)

    assert (out / "2024-03-15_Quarterly Report.md").exists()
    assert "✓" in win._files.item(0).text()


def test_settings_round_trip(qtbot):
    config = Config()
    dialog = SettingsDialog(config)
    qtbot.addWidget(dialog)
    dialog._theme.setCurrentText("dark")
    dialog._redact.setChecked(False)
    dialog.accept()
    assert config.ui.theme == "dark"
    assert config.logging.redact_pii is False


def test_telemetry_stays_off_through_settings(qtbot):
    config = Config()
    dialog = SettingsDialog(config)
    qtbot.addWidget(dialog)
    dialog.accept()
    assert config.advanced.telemetry is False
