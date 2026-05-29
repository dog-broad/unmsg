"""Application bootstrap: ``unmsg-gui`` and ``python -m unmsg.ui.app``."""

from __future__ import annotations

import sys


def run() -> int:
    """Start the desktop application and return its exit code."""
    from PySide6.QtWidgets import QApplication

    from unmsg.config import load_config
    from unmsg.logging_setup import setup_logging
    from unmsg.ui.main_window import MainWindow
    from unmsg.ui.theme import apply_theme

    app = QApplication.instance() or QApplication(sys.argv)
    config = load_config()
    setup_logging(level=config.logging.level, redact=config.logging.redact_pii)
    apply_theme(app, config.ui.theme)

    window = MainWindow(config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
