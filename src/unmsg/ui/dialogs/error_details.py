"""A friendly error dialog — reassuring message up top, details on request."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from unmsg.logging_setup import _redact


class ErrorDetailsDialog(QDialog):
    """Shows a human message; details are redacted and copyable, never scary."""

    def __init__(self, message: str, details: str = "", parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("Something needs your attention")
        layout = QVBoxLayout(self)

        headline = QLabel(message)
        headline.setWordWrap(True)
        layout.addWidget(headline)

        self._details = QPlainTextEdit(_redact(details))
        self._details.setReadOnly(True)
        self._details.setVisible(False)
        layout.addWidget(self._details)

        show = QPushButton("Show details")
        show.setCheckable(True)
        show.toggled.connect(self._details.setVisible)
        layout.addWidget(show)

        copy = QPushButton("Copy details")
        copy.clicked.connect(self._copy)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.addButton(copy, QDialogButtonBox.ButtonRole.ActionRole)
        layout.addWidget(buttons)

    def _copy(self) -> None:
        QApplication.clipboard().setText(self._details.toPlainText())
