"""Help & About in one place: quick start, the privacy promise, and links."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from unmsg._version import __version__

_DOCS_URL = "https://github.com/dog-broad/unmsg"


class HelpDialog(QDialog):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("UnMsg Help")
        layout = QVBoxLayout(self)

        heading = QLabel("UnMsg")
        heading.setObjectName("heading")
        body = QLabel(
            f"Version {__version__}\n\n"
            "Quick start\n"
            "  1. Drop .msg files or folders onto the window.\n"
            "  2. Pick your formats and output folder on the right.\n"
            "  3. Click Convert. Open Output to see the results.\n\n"
            "Everything happens on your machine — nothing is ever uploaded, and "
            "there is no telemetry of any kind. MIT licensed.\n\n"
            f"Documentation: {_DOCS_URL}"
        )
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        body.setOpenExternalLinks(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout.addWidget(heading)
        layout.addWidget(body)
        layout.addWidget(buttons)
