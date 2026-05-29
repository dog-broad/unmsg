"""The main window — a single-column flow: source, quiet options, one action.

There is always exactly one primary action (Convert → Cancel → Open output).
Options recede into a one-line bar that expands on demand. Rows show each
message's identity (its output bundle name once converted). Progress is a slim
line under the header. See the design rationale in the project's decision log.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, QThread, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
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
from unmsg.ui.theme import apply_theme, chevron_icon_path, tokens_for
from unmsg.ui.widgets.drop_zone import DropZone
from unmsg.ui.widgets.file_list import FileList, _reveal
from unmsg.ui.widgets.log_pane import LogPane
from unmsg.ui.widgets.options_panel import OptionsPanel

_STATE = {"success": "done", "warning": "warning", "failed": "failed"}
_FORMAT_ORDER = ["md", "html", "html_single", "txt", "json", "eml", "pdf"]
logger = logging.getLogger(f"{LOGGER_NAME}.ui")


class MainWindow(QMainWindow):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._thread: QThread | None = None
        self._worker: object | None = None
        self._phase = "idle"  # idle | ready | working | done
        self._last_results: list[ConvertResult] = []
        self._tokens = tokens_for(
            config.ui.theme,
            system_is_dark=config.ui.theme in ("dark", "high-contrast"),
        )

        self.setWindowTitle("UnMsg")
        self.resize(config.ui.window_width, config.ui.window_height)

        root = QWidget()
        self.setCentralWidget(root)
        self._outer = QVBoxLayout(root)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self._outer.addWidget(self._build_header())
        self._outer.addWidget(self._build_top_progress())
        self._update_banner: QFrame | None = None
        self._outer.addWidget(self._build_body(), 1)
        self._outer.addWidget(self._build_options_bar())
        self._options.setVisible(False)
        self._outer.addWidget(self._options)
        self._outer.addWidget(self._build_action_bar())

        self._log = LogPane(collapsed=config.ui.log_pane_collapsed)
        logging.getLogger(LOGGER_NAME).addHandler(self._log.handler)
        self._outer.addWidget(self._log)

        self._apply_list_tokens()
        self._update_view()
        self._set_phase("idle")

    # ---- construction ---------------------------------------------------

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 12)
        layout.setSpacing(2)

        top = QHBoxLayout()
        brand = QLabel("UnMsg")
        brand.setObjectName("brand")
        settings = QPushButton("Settings")
        settings.setObjectName("ghost")
        settings.clicked.connect(self._open_settings)
        help_button = QPushButton("Help")
        help_button.setObjectName("ghost")
        help_button.clicked.connect(self._open_help)
        top.addWidget(brand)
        top.addStretch(1)
        top.addWidget(settings)
        top.addWidget(help_button)
        layout.addLayout(top)

        trust = QLabel("Your messages never leave this machine.")
        trust.setObjectName("trustLine")
        layout.addWidget(trust)
        return header

    def _build_top_progress(self) -> QWidget:
        self._progress = QProgressBar()
        self._progress.setObjectName("topProgress")
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(3)
        self._progress.setVisible(False)
        return self._progress

    def _build_body(self) -> QWidget:
        self._stack = QStackedWidget()
        self._drop = DropZone()
        self._drop.paths_dropped.connect(self._add_paths)
        _elevate(self._drop)
        self._files = FileList()
        self._stack.addWidget(self._wrap(self._drop))  # 0: empty
        self._stack.addWidget(self._build_list_page())  # 1: list
        return self._stack

    def _wrap(self, widget: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.addWidget(widget)
        return page

    def _build_list_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(8)

        bar = QHBoxLayout()
        self._count = QLabel("")
        self._count.setObjectName("countLabel")
        add = QPushButton("Add files")
        add.setObjectName("ghost")
        add.clicked.connect(self._drop.browse)
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter…")
        self._filter.setClearButtonEnabled(True)
        self._filter.setMaximumWidth(220)
        self._filter.textChanged.connect(self._files.set_filter)
        bar.addWidget(self._count)
        bar.addStretch(1)
        bar.addWidget(add)
        bar.addWidget(self._filter)
        layout.addLayout(bar)
        layout.addWidget(self._files, 1)
        return page

    def _build_options_bar(self) -> QWidget:
        self._options = OptionsPanel(self._config)
        self._options_bar = QPushButton()
        self._options_bar.setObjectName("optionsBar")
        self._options_bar.setCheckable(True)
        self._options_bar.toggled.connect(self._toggle_options)
        self._refresh_options_summary()
        return self._options_bar

    def _build_action_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("actionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 12, 24, 16)
        self._status = QLabel("")
        self._status.setObjectName("statusLabel")
        self._secondary = QPushButton("")
        self._secondary.setObjectName("ghost")
        self._secondary.clicked.connect(self._on_secondary)
        self._primary = QPushButton("Convert")
        self._primary.setObjectName("cta")
        self._primary.clicked.connect(self._on_primary)
        layout.addWidget(self._status)
        layout.addStretch(1)
        layout.addWidget(self._secondary)
        layout.addWidget(self._primary)
        return bar

    # ---- options bar ----------------------------------------------------

    def _toggle_options(self, shown: bool) -> None:
        self._options.setVisible(shown)
        if not shown:
            self._refresh_options_summary()
        self._refresh_options_chevron()

    def _refresh_options_summary(self) -> None:
        formats = ", ".join(
            self._format_label(f) for f in self._options.selected_formats()
        )
        out = self._options.output_dir()
        summary = f"   Output  {_short_path(out)}        Formats  {formats or 'none'}"
        self._options_bar.setText(summary)
        self._refresh_options_chevron()

    def _refresh_options_chevron(self) -> None:
        color = self._tokens.get("ink_muted", "#5C6370")
        up = self._options.isVisible()
        self._options_bar.setIcon(QIcon(chevron_icon_path(color, up=up)))
        self._options_bar.setIconSize(QSize(12, 12))

    @staticmethod
    def _format_label(fmt: str) -> str:
        return {"html_single": "single-HTML", "json": "JSON", "eml": "EML"}.get(
            fmt, fmt.replace("_", " ").title() if fmt != "md" else "Markdown"
        )

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
        if self._files.count() and self._phase in ("idle", "done"):
            self._set_phase("ready")

    def _clear_files(self) -> None:
        self._files.clear()
        self._update_view()
        self._set_phase("idle")

    def _update_view(self) -> None:
        has_files = self._files.count() > 0
        target = 1 if has_files else 0
        if self._stack.currentIndex() != target:
            self._stack.setCurrentIndex(target)
            self._fade_in(self._stack.currentWidget())
        if has_files:
            self._count.setText(f"{self._files.count()} file(s)")

    def _fade_in(self, widget: QWidget) -> None:
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(240)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        self._anim = anim
        anim.start()

    # ---- phase / actions ------------------------------------------------

    def _set_phase(self, phase: str) -> None:
        self._phase = phase
        total = self._files.count()
        if phase == "idle":
            self._primary.setText("Convert")
            self._primary.setEnabled(False)
            self._secondary.setVisible(False)
            self._status.setText("")
            self._progress.setVisible(False)
        elif phase == "ready":
            self._primary.setText(f"Convert {total}" if total else "Convert")
            self._primary.setEnabled(bool(total))
            self._secondary.setText("Clear")
            self._secondary.setVisible(True)
            self._status.setText(f"{total} file(s) ready")
            self._progress.setVisible(False)
        elif phase == "working":
            self._primary.setText("Cancel")
            self._primary.setEnabled(True)
            self._secondary.setVisible(False)
            self._progress.setVisible(True)
        elif phase == "done":
            self._primary.setText("Open output")
            self._primary.setEnabled(True)
            self._secondary.setText("Convert more")
            self._secondary.setVisible(True)
            self._progress.setVisible(False)

    def _on_primary(self) -> None:
        if self._phase in ("idle", "ready"):
            self._start_convert()
        elif self._phase == "working":
            self._cancel()
        elif self._phase == "done":
            self._open_output()

    def _on_secondary(self) -> None:
        if self._phase == "ready":
            self._clear_files()
        elif self._phase == "done":
            self._set_phase("ready")

    # ---- conversion -----------------------------------------------------

    def _start_convert(self) -> None:
        sources = self._files.paths()
        if not sources:
            return
        if self._options.isVisible():
            self._options_bar.setChecked(False)
        options = self._options.to_options()
        out_root = self._options.output_dir()

        from unmsg.ui.workers import BatchWorker

        self._thread = QThread(self)
        worker = BatchWorker(sources, out_root, options)
        worker.moveToThread(self._thread)
        self._worker = worker
        self._thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.file_result.connect(self._on_file_result)
        worker.finished.connect(self._on_finished)

        self._progress.setRange(0, len(sources))
        self._progress.setValue(0)
        self._set_phase("working")
        self._thread.start()

    def _on_progress(self, done: int, total: int, name: str) -> None:
        self._progress.setValue(done)
        self._status.setText(f"Converting {done} of {total} — {name}")

    def _on_file_result(self, result: ConvertResult) -> None:
        state = _STATE.get(result.status, "failed")
        identity = result.bundle_dir.name if result.bundle_dir else result.source.name
        if result.status == "failed":
            secondary = result.error or "Couldn't convert"
        elif result.status == "warning":
            secondary = (
                result.warnings[0] if result.warnings else "Converted with a note"
            )
        else:
            secondary = "Done"
        self._files.set_state(
            result.source,
            state,
            error=result.error or "",
            bundle=result.bundle_dir,
            identity=identity,
            secondary=secondary,
            formats=_result_formats(result),
        )

    def _on_finished(self, results: list[ConvertResult]) -> None:
        self._last_results = results
        ok = sum(1 for r in results if r.status != "failed")
        warnings = sum(1 for r in results if r.status == "warning")
        note = f" · {warnings} with notes" if warnings else ""
        self._status.setText(f"All done — {ok} of {len(results)} converted{note}")
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None
        self._set_phase("done")
        self._status.setText(f"All done — {ok} of {len(results)} converted{note}")

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
            self._apply_list_tokens()
            self._persist()

    def _open_help(self) -> None:
        HelpDialog(self).exec()

    def show_error(self, message: str, details: str = "") -> None:
        ErrorDetailsDialog(message, details, self).exec()

    def show_update_banner(self, latest: str, url: str) -> None:
        if self._update_banner is not None:
            return
        banner = QFrame()
        banner.setObjectName("updateBanner")
        row = QHBoxLayout(banner)
        row.setContentsMargins(24, 8, 24, 8)
        row.addWidget(QLabel(f"Version {latest} is available."))
        row.addStretch(1)
        download = QPushButton("Download")
        download.setObjectName("ghost")
        download.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        later = QPushButton("Later")
        later.setObjectName("ghost")
        later.clicked.connect(self._dismiss_update_banner)
        row.addWidget(download)
        row.addWidget(later)
        self._outer.insertWidget(2, banner)
        self._update_banner = banner

    def _dismiss_update_banner(self) -> None:
        if self._update_banner is not None:
            self._update_banner.setParent(None)
            self._update_banner = None

    def _apply_list_tokens(self) -> None:
        is_dark = self._config.ui.theme in ("dark", "high-contrast")
        self._tokens = tokens_for(self._config.ui.theme, system_is_dark=is_dark)
        self._files.set_tokens(self._tokens)
        self._refresh_options_chevron()

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


def _result_formats(result: ConvertResult) -> list[str]:
    found: set[str] = set()
    for path in result.output_paths:
        name = path.name.lower()
        if name.endswith(".single.html"):
            found.add("html_single")
        elif name.endswith(".metadata.json"):
            found.add("json")
        elif name.endswith(".md"):
            found.add("md")
        elif name.endswith(".html"):
            found.add("html")
        elif name.endswith(".txt"):
            found.add("txt")
        elif name.endswith(".eml"):
            found.add("eml")
        elif name.endswith(".pdf"):
            found.add("pdf")
    return [fmt for fmt in _FORMAT_ORDER if fmt in found]


def _short_path(path: Path) -> str:
    text = str(path)
    return text if len(text) <= 40 else "…" + text[-39:]


def _elevate(widget: QWidget) -> None:
    """A soft drop shadow for gentle depth (subtle on dark themes)."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(24)
    shadow.setOffset(0, 3)
    shadow.setColor(QColor(0, 0, 0, 38))
    widget.setGraphicsEffect(shadow)
