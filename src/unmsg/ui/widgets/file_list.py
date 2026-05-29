"""The file list and its custom row delegate.

Each row shows the message's identity (its output bundle name once converted,
otherwise the file name), a muted status line, a coloured state dot, and small
chips for the formats produced. Colours come from the active theme tokens so the
list stays consistent across light/dark/high-contrast.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QContextMenuEvent,
    QFont,
    QPainter,
)
from PySide6.QtWidgets import (
    QApplication,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from unmsg.ui.theme import LIGHT

_PATH_ROLE = Qt.ItemDataRole.UserRole
_STATE_ROLE = Qt.ItemDataRole.UserRole + 1
_ERROR_ROLE = Qt.ItemDataRole.UserRole + 2
_BUNDLE_ROLE = Qt.ItemDataRole.UserRole + 3
_PRIMARY_ROLE = Qt.ItemDataRole.UserRole + 4
_SECONDARY_ROLE = Qt.ItemDataRole.UserRole + 5
_FORMATS_ROLE = Qt.ItemDataRole.UserRole + 6

_STATE_TOKEN = {
    "queued": "ink_muted",
    "working": "accent",
    "done": "success",
    "warning": "warning",
    "failed": "error",
}
_STATE_LABEL = {
    "queued": "Ready",
    "working": "Converting…",
    "done": "Done",
    "warning": "Converted with a note",
    "failed": "Couldn't convert",
}
_ROW_HEIGHT = 56


class FileRowDelegate(QStyledItemDelegate):
    """Paints a two-line row with a state dot and format chips."""

    def __init__(self) -> None:
        super().__init__()
        self._tokens = LIGHT

    def set_tokens(self, tokens: dict[str, str]) -> None:
        self._tokens = tokens

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:  # type: ignore[no-untyped-def]
        return QSize(0, _ROW_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:  # type: ignore[no-untyped-def]
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        t = self._tokens
        rect = option.rect

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(t["border"]))

        left = rect.left() + 16
        # state dot
        state = index.data(_STATE_ROLE) or "queued"
        dot = QColor(t.get(_STATE_TOKEN.get(state, "ink_muted"), t["ink_muted"]))
        painter.setBrush(dot)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(left, rect.center().y() - 5, 10, 10))

        text_left = left + 24
        text_right = rect.right() - 16

        # format chips (right-aligned), drawn first to reserve space
        chips = index.data(_FORMATS_ROLE) or []
        chip_left = self._paint_chips(painter, rect, text_right, chips, t)

        # primary line
        primary = index.data(_PRIMARY_ROLE) or ""
        font = QFont(option.font)
        font.setPointSizeF(font.pointSizeF() + 0.5)
        painter.setFont(font)
        painter.setPen(QColor(t["ink"]))
        primary_rect = rect.adjusted(
            text_left - rect.left(), 8, chip_left - rect.right() - 8, 0
        )
        painter.drawText(
            primary_rect,
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop),
            _elide(painter, primary, primary_rect.width()),
        )

        # secondary line
        secondary = index.data(_SECONDARY_ROLE) or _STATE_LABEL.get(state, "")
        small = QFont(option.font)
        small.setPointSizeF(max(8.0, option.font.pointSizeF() - 1.0))
        painter.setFont(small)
        painter.setPen(QColor(t["ink_muted"]))
        secondary_rect = rect.adjusted(text_left - rect.left(), 0, -16, -8)
        painter.drawText(
            secondary_rect,
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom),
            _elide(painter, secondary, secondary_rect.width()),
        )
        painter.restore()

    def _paint_chips(
        self, painter: QPainter, rect, right: int, chips: list[str], t: dict[str, str]
    ) -> int:
        if not chips:
            return right
        chip_font = QFont()
        chip_font.setPointSizeF(8.0)
        painter.setFont(chip_font)
        x = right
        metrics = painter.fontMetrics()
        for fmt in reversed(chips):
            label = _CHIP_LABEL.get(fmt, fmt)
            w = metrics.horizontalAdvance(label) + 16
            chip_rect = QRectF(x - w, rect.center().y() - 9, w, 18)
            painter.setBrush(QColor(t["surface"]))
            painter.setPen(QColor(t["border"]))
            painter.drawRoundedRect(chip_rect, 2, 2)
            painter.setPen(QColor(t["ink_muted"]))
            painter.drawText(chip_rect, int(Qt.AlignmentFlag.AlignCenter), label)
            x -= w + 6
        return x


_CHIP_LABEL = {
    "md": "md",
    "html": "html",
    "html_single": "html·1",
    "txt": "txt",
    "json": "json",
    "eml": "eml",
    "pdf": "pdf",
}


def _elide(painter: QPainter, text: str, width: int) -> str:
    return painter.fontMetrics().elidedText(
        text, Qt.TextElideMode.ElideRight, max(width, 0)
    )


class FileList(QListWidget):
    """Shows queued files and their state; supports per-row actions and filter."""

    def __init__(self) -> None:
        super().__init__()
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setUniformItemSizes(True)
        self._delegate = FileRowDelegate()
        self.setItemDelegate(self._delegate)

    def set_tokens(self, tokens: dict[str, str]) -> None:
        self._delegate.set_tokens(tokens)
        self.viewport().update()

    def add_paths(self, paths: list[Path]) -> int:
        existing = {self._path(i) for i in range(self.count())}
        added = 0
        for path in sorted(paths, key=lambda p: str(p).lower()):
            if path in existing:
                continue
            item = QListWidgetItem()
            item.setData(_PATH_ROLE, str(path))
            item.setData(_STATE_ROLE, "queued")
            item.setData(_PRIMARY_ROLE, path.name)
            item.setData(_SECONDARY_ROLE, "Ready")
            item.setData(_FORMATS_ROLE, [])
            self.addItem(item)
            existing.add(path)
            added += 1
        return added

    def paths(self) -> list[Path]:
        return [self._path(i) for i in range(self.count())]

    def set_state(
        self,
        path: Path,
        state: str,
        *,
        error: str = "",
        bundle: Path | None = None,
        identity: str = "",
        secondary: str = "",
        formats: list[str] | None = None,
    ) -> None:
        for i in range(self.count()):
            if self._path(i) == path:
                item = self.item(i)
                item.setData(_STATE_ROLE, state)
                item.setData(_ERROR_ROLE, error)
                item.setData(_BUNDLE_ROLE, str(bundle) if bundle else "")
                if identity:
                    item.setData(_PRIMARY_ROLE, identity)
                item.setData(_SECONDARY_ROLE, secondary or _STATE_LABEL.get(state, ""))
                if formats is not None:
                    item.setData(_FORMATS_ROLE, formats)
                return

    def remove_selected(self) -> None:
        for item in self.selectedItems():
            self.takeItem(self.row(item))

    def set_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for row in range(self.count()):
            name = self.item(row).data(_PRIMARY_ROLE).lower()
            path = self._path(row).name.lower()
            hidden = bool(needle) and needle not in name and needle not in path
            self.item(row).setHidden(hidden)

    def visible_count(self) -> int:
        return sum(1 for row in range(self.count()) if not self.item(row).isHidden())

    def row_state(self, row: int) -> str:
        return str(self.item(row).data(_STATE_ROLE))

    def row_primary(self, row: int) -> str:
        return str(self.item(row).data(_PRIMARY_ROLE))

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
