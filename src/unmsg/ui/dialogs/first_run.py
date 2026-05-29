"""The first-run welcome — one calm screen that teaches the core gesture."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class FirstRunDialog(QDialog):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("Welcome to UnMsg")
        layout = QVBoxLayout(self)

        heading = QLabel("Welcome")
        heading.setObjectName("heading")
        body = QLabel(
            "Drop your .msg files anywhere on the window to start, then click "
            "Convert.\n\nEverything happens on your machine — nothing is ever "
            "uploaded, and there is no telemetry."
        )
        body.setWordWrap(True)

        got_it = QPushButton("Got it")
        got_it.setObjectName("cta")
        got_it.clicked.connect(self.accept)

        layout.addWidget(heading)
        layout.addWidget(body)
        layout.addWidget(got_it)
