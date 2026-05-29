"""A collapsible log pane fed by the logging system (redacted by default)."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _LogBridge(QObject):
    """Carries log lines from any thread onto the GUI thread via a signal."""

    message = Signal(str)


class QtLogHandler(logging.Handler):
    """A logging handler that appends formatted records to the log pane."""

    def __init__(self, bridge: _LogBridge) -> None:
        super().__init__()
        self._bridge = bridge

    def emit(self, record: logging.LogRecord) -> None:
        self._bridge.message.emit(self.format(record))


class LogPane(QWidget):
    """Shows recent log lines; collapsible, default-collapsed on first run."""

    def __init__(self, collapsed: bool = True) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._toggle = QPushButton()
        self._toggle.setCheckable(True)
        self._toggle.clicked.connect(self._on_toggle)

        self._view = QPlainTextEdit()
        self._view.setObjectName("logPane")
        self._view.setReadOnly(True)
        self._view.setMaximumBlockCount(2000)

        layout.addWidget(self._toggle)
        layout.addWidget(self._view)

        self._bridge = _LogBridge()
        self._bridge.message.connect(self._append)
        self.handler = QtLogHandler(self._bridge)
        self.handler.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-5s  %(message)s")
        )

        self.set_collapsed(collapsed)

    def is_collapsed(self) -> bool:
        return not self._view.isVisible()

    def set_collapsed(self, collapsed: bool) -> None:
        self._view.setVisible(not collapsed)
        self._toggle.setChecked(not collapsed)
        self._toggle.setText("Log ▴" if not collapsed else "Log ▾")

    def _on_toggle(self) -> None:
        self.set_collapsed(self._view.isVisible())

    def _append(self, line: str) -> None:
        self._view.appendPlainText(line)
