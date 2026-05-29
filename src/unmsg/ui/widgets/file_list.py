"""The file list with per-row conversion state and a right-click menu."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QContextMenuEvent
from PySide6.QtWidgets import QApplication, QListWidget, QListWidgetItem, QMenu

_PATH_ROLE = Qt.ItemDataRole.UserRole
_STATE_ROLE = Qt.ItemDataRole.UserRole + 1
_ERROR_ROLE = Qt.ItemDataRole.UserRole + 2
_BUNDLE_ROLE = Qt.ItemDataRole.UserRole + 3

_ICON = {
    "queued": "📄",
    "working": "⟳",
    "done": "✓",
    "warning": "⚠",
    "failed": "✗",
}


class FileList(QListWidget):
    """Shows queued files and their state; supports per-row actions."""

    def __init__(self) -> None:
        super().__init__()
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

    def add_paths(self, paths: list[Path]) -> int:
        existing = {self._path(i) for i in range(self.count())}
        added = 0
        for path in sorted(paths, key=lambda p: str(p).lower()):
            if path in existing:
                continue
            item = QListWidgetItem(f"{_ICON['queued']}  {path.name}")
            item.setData(_PATH_ROLE, str(path))
            item.setData(_STATE_ROLE, "queued")
            self.addItem(item)
            existing.add(path)
            added += 1
        return added

    def paths(self) -> list[Path]:
        return [self._path(i) for i in range(self.count())]

    def set_state(
        self, path: Path, state: str, *, error: str = "", bundle: Path | None = None
    ) -> None:
        for i in range(self.count()):
            if self._path(i) == path:
                item = self.item(i)
                item.setText(f"{_ICON.get(state, '?')}  {path.name}")
                item.setData(_STATE_ROLE, state)
                item.setData(_ERROR_ROLE, error)
                item.setData(_BUNDLE_ROLE, str(bundle) if bundle else "")
                return

    def remove_selected(self) -> None:
        for item in self.selectedItems():
            self.takeItem(self.row(item))

    def set_filter(self, text: str) -> None:
        """Hide rows whose file name doesn't contain ``text`` (case-insensitive)."""
        needle = text.strip().lower()
        for row in range(self.count()):
            name = self._path(row).name.lower()
            self.item(row).setHidden(bool(needle) and needle not in name)

    def visible_count(self) -> int:
        return sum(1 for row in range(self.count()) if not self.item(row).isHidden())

    def _path(self, row: int) -> Path:
        return Path(self.item(row).data(_PATH_ROLE))

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        item = self.itemAt(event.pos())
        if item is None:
            return
        menu = QMenu(self)
        bundle = item.data(_BUNDLE_ROLE)
        if bundle:
            self._add(menu, "Show in Explorer", lambda: _reveal(Path(bundle)))
        self._add(menu, "Show source", lambda: _reveal(self._path(self.row(item))))
        if item.data(_STATE_ROLE) == "failed":
            self._add(menu, "Copy error", lambda: _copy(item.data(_ERROR_ROLE)))
        self._add(menu, "Remove", self.remove_selected)
        menu.exec(event.globalPos())

    @staticmethod
    def _add(menu: QMenu, label: str, handler) -> None:  # type: ignore[no-untyped-def]
        action = QAction(label, menu)
        action.triggered.connect(handler)
        menu.addAction(action)


def _copy(text: str) -> None:
    QApplication.clipboard().setText(text or "")


def _reveal(path: Path) -> None:
    """Open the OS file browser at ``path`` (best effort, never raises)."""
    try:
        if sys.platform == "win32":
            subprocess.run(["explorer", "/select,", str(path)], check=False)
        elif sys.platform == "darwin":
            subprocess.run(["open", "-R", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path.parent)], check=False)
    except OSError:
        pass
