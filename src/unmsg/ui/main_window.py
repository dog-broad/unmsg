"""The main window: ties the widgets to the conversion core via a worker."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QThread, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from unmsg.config import Config, save_config
from unmsg.core.models import ConvertResult
from unmsg.logging_setup import LOGGER_NAME
from unmsg.ui.dialogs.error_details import ErrorDetailsDialog
from unmsg.ui.dialogs.help import HelpDialog
from unmsg.ui.dialogs.settings import SettingsDialog
from unmsg.ui.theme import apply_theme
from unmsg.ui.widgets.drop_zone import DropZone
from unmsg.ui.widgets.file_list import FileList, _reveal
from unmsg.ui.widgets.log_pane import LogPane
from unmsg.ui.widgets.options_panel import OptionsPanel
from unmsg.ui.widgets.progress_strip import ProgressStrip

_STATE = {"success": "done", "warning": "warning", "failed": "failed"}
logger = logging.getLogger(f"{LOGGER_NAME}.ui")


class MainWindow(QMainWindow):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._thread: QThread | None = None
        self._worker: object | None = None

        self.setWindowTitle("UnMsg")
        self.resize(config.ui.window_width, config.ui.window_height)

        root = QWidget()
        self.setCentralWidget(root)
        self._outer = QVBoxLayout(root)
        outer = self._outer

        outer.addLayout(self._build_top_bar())
        self._update_banner: QFrame | None = None
        outer.addLayout(self._build_body(), 1)

        self._progress = ProgressStrip()
        self._progress.convert_clicked.connect(self._start_convert)
        self._progress.cancel_clicked.connect(self._cancel)
        self._progress.open_output_clicked.connect(self._open_output)
        outer.addWidget(self._progress)

        self._log = LogPane(collapsed=config.ui.log_pane_collapsed)
        logging.getLogger(LOGGER_NAME).addHandler(self._log.handler)
        outer.addWidget(self._log)

        self._update_view()

    # ---- construction helpers -------------------------------------------

    def _build_top_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        title = QPushButton("UnMsg")
        title.setFlat(True)
        title.setEnabled(False)
        settings = QPushButton("Settings")
        settings.clicked.connect(self._open_settings)
        about = QPushButton("Help")
        about.clicked.connect(self._open_help)
        bar.addWidget(title)
        bar.addStretch(1)
        bar.addWidget(settings)
        bar.addWidget(about)
        return bar

    def _build_body(self) -> QHBoxLayout:
        body = QHBoxLayout()

        self._stack = QStackedWidget()
        self._drop = DropZone()
        self._drop.paths_dropped.connect(self._add_paths)
        self._files = FileList()
        list_page = self._build_list_page()
        self._stack.addWidget(self._drop)  # index 0: empty state
        self._stack.addWidget(list_page)  # index 1: file list

        self._options = OptionsPanel(self._config)

        body.addWidget(self._stack, 3)
        body.addWidget(self._options, 2)
        return body

    def _build_list_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter files…")
        self._filter.setClearButtonEnabled(True)
        self._filter.textChanged.connect(self._files.set_filter)
        layout.addWidget(self._filter)

        layout.addWidget(self._files, 1)

        actions = QHBoxLayout()
        add = QPushButton("Add files")
        add.clicked.connect(self._drop.browse)
        clear = QPushButton("Clear")
        clear.clicked.connect(self._clear_files)
        actions.addWidget(add)
        actions.addWidget(clear)
        actions.addStretch(1)
        layout.addLayout(actions)
        return page

    # ---- file handling --------------------------------------------------

    def _add_paths(self, paths: list[Path]) -> None:
        msgs: list[Path] = []
        for path in paths:
            if path.is_dir():
                msgs.extend(p for p in path.rglob("*.msg") if p.is_file())
            elif path.suffix.lower() == ".msg" and path.is_file():
                msgs.append(path)
        if msgs:
            added = self._files.add_paths(msgs)
            logger.info("Added %d file(s) to the queue", added)
        self._update_view()

    def _clear_files(self) -> None:
        self._files.clear()
        self._update_view()

    def _update_view(self) -> None:
        target = 1 if self._files.count() else 0
        if self._stack.currentIndex() == target:
            return
        self._stack.setCurrentIndex(target)
        self._fade_in(self._stack.currentWidget())

    def _fade_in(self, widget: QWidget) -> None:
        """A brief settle fade when the empty state and the list swap."""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(240)  # "settle" duration
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        self._anim = anim  # keep a reference so it isn't garbage-collected
        anim.start()

    # ---- conversion -----------------------------------------------------

    def _start_convert(self) -> None:
        sources = self._files.paths()
        if not sources:
            return
        options = self._options.to_options()
        out_root = self._options.output_dir()

        from unmsg.ui.workers import BatchWorker

        self._thread = QThread(self)
        worker = BatchWorker(sources, out_root, options)
        worker.moveToThread(self._thread)
        self._worker = worker

        self._thread.started.connect(worker.run)
        worker.progress.connect(self._progress.set_progress)
        worker.file_result.connect(self._on_file_result)
        worker.finished.connect(self._on_finished)

        self._progress.set_running(len(sources))
        self._thread.start()

    def _on_file_result(self, result: ConvertResult) -> None:
        state = _STATE.get(result.status, "failed")
        self._files.set_state(
            result.source, state, error=result.error or "", bundle=result.bundle_dir
        )
        if result.status == "failed":
            logger.warning("Could not convert a file: %s", result.error)

    def _on_finished(self, results: list[ConvertResult]) -> None:
        done = sum(1 for r in results if r.status != "failed")
        self._progress.set_done(done, len(results))
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None

    def _cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()  # type: ignore[attr-defined]

    def _open_output(self) -> None:
        _reveal(self._options.output_dir())

    # ---- dialogs & persistence -----------------------------------------

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._config, self)
        if dialog.exec():
            apply_theme(self._app(), self._config.ui.theme)
            self._persist()

    def _open_help(self) -> None:
        HelpDialog(self).exec()

    def show_error(self, message: str, details: str = "") -> None:
        ErrorDetailsDialog(message, details, self).exec()

    def show_update_banner(self, latest: str, url: str) -> None:
        """Show a dismissible 'a new version is available' strip (opt-in only)."""
        if self._update_banner is not None:
            return
        banner = QFrame()
        banner.setObjectName("card")
        row = QHBoxLayout(banner)
        row.addWidget(QLabel(f"Version {latest} is available."))
        row.addStretch(1)
        download = QPushButton("Download")
        download.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        later = QPushButton("Later")
        later.clicked.connect(self._dismiss_update_banner)
        row.addWidget(download)
        row.addWidget(later)
        self._outer.insertWidget(0, banner)
        self._update_banner = banner

    def _dismiss_update_banner(self) -> None:
        if self._update_banner is not None:
            self._update_banner.setParent(None)
            self._update_banner = None

    def _persist(self) -> None:
        self._config.ui.window_width = self.width()
        self._config.ui.window_height = self.height()
        self._config.ui.log_pane_collapsed = self._log.is_collapsed()
        self._options.write_into(self._config)
        save_config(self._config)

    def _app(self):  # type: ignore[no-untyped-def]
        from PySide6.QtWidgets import QApplication

        return QApplication.instance()

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._persist()
        super().closeEvent(event)
