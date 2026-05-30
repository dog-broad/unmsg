"""Coverage for the smaller UI widgets and the error-details dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QFileDialog

from unmsg.ui.dialogs.error_details import ErrorDetailsDialog
from unmsg.ui.theme import LIGHT, badge_palette
from unmsg.ui.widgets.drop_zone import DropZone
from unmsg.ui.widgets.file_list import FileList


class _Event:
    """A duck-typed Qt drag/drop event for direct method calls."""

    def __init__(self, urls: list[QUrl] | None = None) -> None:
        self._urls = urls or []
        self.accepted = False

    def mimeData(self):
        return self

    def hasUrls(self) -> bool:
        return bool(self._urls)

    def urls(self) -> list[QUrl]:
        return self._urls

    def acceptProposedAction(self) -> None:
        self.accepted = True


def test_drop_zone_drag_enter_and_drop_emit_paths(qtbot, tmp_path):
    zone = DropZone()
    qtbot.addWidget(zone)
    emitted: list[list[Path]] = []
    zone.paths_dropped.connect(lambda ps: emitted.append(list(ps)))

    f = tmp_path / "x.msg"
    f.write_bytes(b"x")
    enter = _Event([QUrl.fromLocalFile(str(f))])
    zone.dragEnterEvent(enter)
    assert enter.accepted
    assert zone.property("dragActive") is True

    drop = _Event([QUrl.fromLocalFile(str(f))])
    zone.dropEvent(drop)
    assert emitted == [[f]]
    assert zone.property("dragActive") is False

    # dragLeave clears the active state too
    zone._set_drag_active(True)
    zone.dragLeaveEvent(_Event())
    assert zone.property("dragActive") is False


def test_drop_zone_browse_uses_file_dialog(qtbot, monkeypatch, tmp_path):
    zone = DropZone()
    qtbot.addWidget(zone)
    picked = tmp_path / "picked.msg"
    picked.write_bytes(b"x")
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        staticmethod(lambda *a, **kw: ([str(picked)], "")),
    )
    emitted: list[list[Path]] = []
    zone.paths_dropped.connect(lambda ps: emitted.append(list(ps)))
    zone.browse()
    assert emitted == [[picked]]


def test_file_list_paint_runs_via_grab(qtbot, tmp_path):
    fl = FileList()
    qtbot.addWidget(fl)
    fl.resize(600, 200)
    fl.set_tokens(LIGHT)
    fl.set_badges(badge_palette("light", system_is_dark=False))
    a = tmp_path / "a.msg"
    b = tmp_path / "b.msg"
    for src in (a, b):
        src.write_bytes(b"x")
    assert fl.add_paths([a, b]) == 2
    fl.set_state(
        a,
        "done",
        identity="2024-03-15_Quarterly Report",
        secondary="Done · 3 files",
        formats=["md", "html", "pdf"],
        bundle=tmp_path / "bundle",
    )
    fl.set_state(b, "failed", error="bad file", secondary="Couldn't convert")
    fl.show()
    # forces the delegate's paint() and _paint_chips()
    fl.grab()
    assert fl.row_state(0) == "done"
    assert fl.row_state(1) == "failed"
    assert fl.row_primary(0).startswith("2024-03-15")


def test_file_list_filter_and_visibility(qtbot, tmp_path):
    fl = FileList()
    qtbot.addWidget(fl)
    a = tmp_path / "alpha.msg"
    b = tmp_path / "bravo.msg"
    for src in (a, b):
        src.write_bytes(b"x")
    fl.add_paths([a, b])
    fl.set_filter("alpha")
    assert fl.visible_count() == 1
    fl.set_filter("")
    assert fl.visible_count() == 2
    assert sorted(p.name for p in fl.paths()) == ["alpha.msg", "bravo.msg"]


def test_file_list_dedupe_and_remove(qtbot, tmp_path):
    fl = FileList()
    qtbot.addWidget(fl)
    f = tmp_path / "dup.msg"
    f.write_bytes(b"x")
    fl.add_paths([f])
    assert fl.add_paths([f]) == 0  # already there
    fl.selectAll()
    fl.remove_selected()
    assert fl.count() == 0


def test_error_dialog_toggles_details_and_copies(qtbot, monkeypatch):
    dlg = ErrorDetailsDialog(
        "Couldn't read the file.",
        "Traceback hidden — email@example.com /tmp/secret/path.msg",
    )
    qtbot.addWidget(dlg)
    dlg.show()  # so child visibility propagates
    from PySide6.QtWidgets import QPushButton

    buttons = dlg.findChildren(QPushButton)
    show = next(b for b in buttons if b.text() == "Show details")
    show.setChecked(True)
    assert dlg._details.isVisible()
    text = dlg._details.toPlainText()
    # email + path are redacted
    assert "email@example.com" not in text
    assert "/tmp/secret/path.msg" not in text
    # copy puts the (redacted) text on the clipboard
    copy = next(b for b in buttons if b.text() == "Copy details")
    copy.click()
    assert QApplication.clipboard().text() == text
