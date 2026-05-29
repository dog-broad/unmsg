"""The progress strip: the working state and the primary actions."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ProgressStrip(QWidget):
    convert_clicked = Signal()
    cancel_clicked = Signal()
    open_output_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)

        bar_row = QHBoxLayout()
        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._status = QLabel("Ready")
        bar_row.addWidget(self._bar, 3)
        bar_row.addWidget(self._status, 2)
        outer.addLayout(bar_row)

        actions = QHBoxLayout()
        self._convert = QPushButton("Convert")
        self._convert.setObjectName("cta")
        self._cancel = QPushButton("Cancel")
        self._open = QPushButton("Open Output")
        self._convert.clicked.connect(self.convert_clicked)
        self._cancel.clicked.connect(self.cancel_clicked)
        self._open.clicked.connect(self.open_output_clicked)
        actions.addWidget(self._convert)
        actions.addWidget(self._cancel)
        actions.addStretch(1)
        actions.addWidget(self._open)
        outer.addLayout(actions)

        self.set_idle()

    def set_idle(self) -> None:
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._status.setText("Ready")
        self._convert.setEnabled(True)
        self._cancel.setEnabled(False)
        self._open.setEnabled(False)

    def set_running(self, total: int) -> None:
        self._bar.setRange(0, max(total, 1))
        self._bar.setValue(0)
        self._convert.setEnabled(False)
        self._cancel.setEnabled(True)
        self._open.setEnabled(False)

    def set_progress(self, done: int, total: int, name: str) -> None:
        self._bar.setValue(done)
        self._status.setText(f"{done} of {total} • {name}")

    def set_done(self, done: int, total: int) -> None:
        self._bar.setValue(self._bar.maximum())
        self._status.setText(f"All done. {done} of {total} converted.")
        self._convert.setEnabled(True)
        self._cancel.setEnabled(False)
        self._open.setEnabled(True)
