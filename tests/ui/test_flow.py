"""Extra coverage for MainWindow phase transitions, dialogs, and the entrypoint."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from unmsg.config import Config
from unmsg.core.models import ConvertResult
from unmsg.ui.dialogs.help import HelpDialog
from unmsg.ui.dialogs.settings import SettingsDialog
from unmsg.ui.main_window import MainWindow


def _fail_result(src: Path) -> ConvertResult:
    return ConvertResult(
        source=src,
        bundle_dir=None,
        output_paths=[],
        attachments_saved=[],
        inline_images_saved=[],
        status="failed",
        warnings=[],
        error="Boom",
        duration_ms=1,
    )


def _warn_result(src: Path) -> ConvertResult:
    return ConvertResult(
        source=src,
        bundle_dir=src.parent / "bundle",
        output_paths=[src.parent / "bundle" / "x.md"],
        attachments_saved=[],
        inline_images_saved=[],
        status="warning",
        warnings=["PDF skipped — Pillow missing"],
        error=None,
        duration_ms=1,
    )


def test_phase_clear_files_and_convert_more(qtbot, tmp_path):
    win = MainWindow(Config())
    qtbot.addWidget(win)
    f = tmp_path / "a.msg"
    f.write_bytes(b"x")
    win._add_paths([f])
    assert win._phase == "ready"
    win._on_secondary()  # Clear → idle
    assert win._files.count() == 0
    assert win._phase == "idle"

    win._add_paths([f])
    win._set_phase("done")
    win._on_secondary()  # Convert more → ready
    assert win._phase == "ready"


def test_open_output_reveals_directory(qtbot, monkeypatch, tmp_path):
    seen: list[Path] = []
    import unmsg.ui.main_window as mw

    monkeypatch.setattr(mw, "_reveal", lambda p: seen.append(Path(p)))
    win = MainWindow(Config())
    qtbot.addWidget(win)
    win._options._output.setText(str(tmp_path))
    win._open_output()
    assert seen == [tmp_path]


def test_failed_and_warning_results_update_row(qtbot, tmp_path):
    win = MainWindow(Config())
    qtbot.addWidget(win)
    f = tmp_path / "a.msg"
    g = tmp_path / "b.msg"
    for src in (f, g):
        src.write_bytes(b"x")
    win._add_paths([f, g])
    win._on_file_result(_fail_result(f))
    win._on_file_result(_warn_result(g))
    win._on_finished([_fail_result(f), _warn_result(g)])
    assert win._files.row_state(0) == "failed"
    assert win._files.row_state(1) == "warning"
    assert win._phase == "done"
    assert "with notes" in win._status.text()


def test_cancel_request_passes_through_to_worker(qtbot, monkeypatch, tmp_path):
    """Pressing Cancel while working asks the worker to stop."""
    win = MainWindow(Config())
    qtbot.addWidget(win)
    win._set_phase("working")

    class FakeWorker:
        def __init__(self) -> None:
            self.cancelled = False

        def cancel(self) -> None:
            self.cancelled = True

    win._worker = FakeWorker()
    win._on_primary()  # routes to _cancel
    assert win._worker.cancelled is True


def test_open_settings_applies_changes(qtbot, monkeypatch):
    import unmsg.ui.main_window as mw

    monkeypatch.setattr(mw, "save_config", lambda c: None)
    captured: dict[str, object] = {}

    def fake_exec(self):  # type: ignore[no-untyped-def]
        self._theme.setCurrentText("dark")
        self.accept()
        captured["ok"] = True
        return 1

    monkeypatch.setattr(SettingsDialog, "exec", fake_exec, raising=True)
    win = MainWindow(Config())
    qtbot.addWidget(win)
    win._open_settings()
    assert captured.get("ok") is True
    assert win._config.ui.theme == "dark"


def test_open_help_dialog(qtbot, monkeypatch):
    seen: list[bool] = []
    monkeypatch.setattr(HelpDialog, "exec", lambda self: seen.append(True) or 0)
    win = MainWindow(Config())
    qtbot.addWidget(win)
    win._open_help()
    assert seen == [True]


def test_show_error_dialog_does_not_raise(qtbot, monkeypatch):
    from unmsg.ui.dialogs.error_details import ErrorDetailsDialog

    monkeypatch.setattr(ErrorDetailsDialog, "exec", lambda self: 0)
    win = MainWindow(Config())
    qtbot.addWidget(win)
    win.show_error("Boom", "trace")


def test_close_event_persists_config(qtbot, monkeypatch):
    saved: list[Config] = []
    import unmsg.ui.main_window as mw

    monkeypatch.setattr(mw, "save_config", lambda c: saved.append(c))
    win = MainWindow(Config())
    qtbot.addWidget(win)
    win.close()
    assert saved and isinstance(saved[0], Config)


def test_options_bar_toggles_and_summary_refresh(qtbot):
    win = MainWindow(Config())
    qtbot.addWidget(win)
    assert win._options.isHidden()
    win._options_bar.setChecked(True)
    assert not win._options.isHidden()
    win._options_bar.setChecked(False)
    assert win._options.isHidden()


def test_add_paths_descends_into_directories(qtbot, tmp_path):
    nested = tmp_path / "inbox" / "deep"
    nested.mkdir(parents=True)
    for name in ("a.msg", "b.txt", "c.msg"):
        (nested / name).write_bytes(b"x")
    win = MainWindow(Config())
    qtbot.addWidget(win)
    win._add_paths([tmp_path / "inbox"])
    assert win._files.count() == 2  # only the .msg files


def test_app_run_bootstraps_without_blocking(qtbot, monkeypatch):
    """Cover the GUI entrypoint with all real I/O stubbed out."""
    from PySide6.QtWidgets import QApplication

    import unmsg.config as config_mod
    import unmsg.crash as crash_mod
    from unmsg.ui import app as app_module
    from unmsg.ui.dialogs.first_run import FirstRunDialog
    from unmsg.ui.main_window import MainWindow

    cfg = Config()
    cfg.ui.first_run_done = False  # exercise the first-run branch
    cfg.advanced.check_updates = True  # exercise the update-check branch

    monkeypatch.setattr(config_mod, "load_config", lambda: cfg)
    monkeypatch.setattr(config_mod, "save_config", lambda c: None)
    monkeypatch.setattr(app_module, "_start_update_check", lambda w: None)
    monkeypatch.setattr(crash_mod, "install_excepthook", lambda **kw: None)
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    monkeypatch.setattr(FirstRunDialog, "exec", lambda self: 0)
    monkeypatch.setattr(MainWindow, "show", lambda self: None)

    assert app_module.run() == 0
    assert cfg.ui.first_run_done is True


def test_update_check_starts_thread(qtbot, monkeypatch):
    """The update-check helper wires up the worker on a thread."""
    from unmsg.ui import app as app_module

    win = MainWindow(Config())
    qtbot.addWidget(win)
    # the worker.run() is what would do the network call — stub it
    monkeypatch.setattr("unmsg.ui.workers.UpdateWorker.run", lambda self: None)
    app_module._start_update_check(win)
    assert hasattr(win, "_update_thread")
    win._update_thread.quit()
    win._update_thread.wait(2000)
