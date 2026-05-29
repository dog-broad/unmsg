"""Application bootstrap: ``unmsg-gui`` and ``python -m unmsg.ui.app``."""

from __future__ import annotations

import sys
from pathlib import Path


def run() -> int:
    """Start the desktop application and return its exit code."""
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from unmsg import paths
    from unmsg.config import load_config, save_config
    from unmsg.crash import install_excepthook
    from unmsg.logging_setup import setup_logging
    from unmsg.ui.assets import app_icon_svg
    from unmsg.ui.dialogs.error_details import ErrorDetailsDialog
    from unmsg.ui.dialogs.first_run import FirstRunDialog
    from unmsg.ui.main_window import MainWindow
    from unmsg.ui.theme import apply_theme

    app = QApplication.instance() or QApplication(sys.argv)
    app.setWindowIcon(QIcon(app_icon_svg()))
    config = load_config()
    setup_logging(level=config.logging.level, redact=config.logging.redact_pii)
    apply_theme(app, config.ui.theme)

    window = MainWindow(config)

    def on_crash(report: Path) -> None:
        ErrorDetailsDialog(
            "Something went wrong. A report was saved on your machine — nothing "
            "was sent anywhere.",
            f"Report saved to: {report}",
            window,
        ).exec()

    install_excepthook(log_dir=paths.log_dir(), notify=on_crash)

    window.show()

    if not config.ui.first_run_done:
        FirstRunDialog(window).exec()
        config.ui.first_run_done = True
        save_config(config)

    if config.advanced.check_updates:
        _start_update_check(window)

    return app.exec()


def _start_update_check(window: object) -> None:
    """Run the opt-in update check on a worker thread, banner on a hit."""
    from PySide6.QtCore import QThread

    from unmsg.ui.workers import UpdateWorker

    thread = QThread()
    worker = UpdateWorker()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.found.connect(window.show_update_banner)  # type: ignore[attr-defined]
    worker.finished.connect(thread.quit)
    # Keep references alive on the window so they aren't garbage-collected.
    window._update_thread = thread  # type: ignore[attr-defined]
    window._update_worker = worker  # type: ignore[attr-defined]
    thread.start()


if __name__ == "__main__":
    raise SystemExit(run())
