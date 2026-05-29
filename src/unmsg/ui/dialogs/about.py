"""The About dialog: version, license, and the privacy promise."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from unmsg._version import __version__


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("About UnMsg")
        layout = QVBoxLayout(self)

        title = QLabel("UnMsg")
        title.setObjectName("heading")
        body = QLabel(
            f"Version {__version__}\n\n"
            "Turn Outlook .msg files into clean, readable formats.\n"
            "Everything happens on your machine - nothing is ever uploaded, "
            "and there is no telemetry of any kind.\n\n"
            "MIT licensed."
        )
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(buttons)
