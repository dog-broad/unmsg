"""The drop zone: the empty-state invitation and the main way files get in."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout


class DropZone(QFrame):
    """Accepts dragged ``.msg`` files and folders, or a click to browse."""

    paths_dropped = Signal(list)  # list[Path]

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)

        label = QLabel("Drop .msg files or folders here\n\nor click to browse", self)
        label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        label.setAlignment(label.alignment())

    def _set_drag_active(self, active: bool) -> None:
        self.setProperty("dragActive", active)
        style = self.style()
        style.unpolish(self)
        style.polish(self)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_drag_active(True)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_drag_active(False)

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_drag_active(False)
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        if paths:
            self.paths_dropped.emit(paths)
            event.acceptProposedAction()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.browse()

    def browse(self) -> None:
        """Open a file picker for ``.msg`` files and emit the selection."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choose .msg files", "", "Outlook messages (*.msg)"
        )
        if files:
            self.paths_dropped.emit([Path(f) for f in files])
