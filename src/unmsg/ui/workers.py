"""Background batch conversion for the GUI.

The core is synchronous; this worker runs it on a :class:`QThread` so the window
stays responsive, emits per-file results for live row updates, and supports
cancellation **between files** (a file in flight always finishes cleanly, so no
half-written bundle is ever left behind).
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from unmsg.core import ConvertOptions, convert_file
from unmsg.core.models import ConvertResult
from unmsg.updates import check_for_update

logger = logging.getLogger("unmsg.ui.worker")


class BatchWorker(QObject):
    progress = Signal(int, int, str)  # done, total, current source name
    file_result = Signal(object)  # ConvertResult, per file
    finished = Signal(list)  # list[ConvertResult]

    def __init__(
        self, sources: list[Path], out_root: Path, options: ConvertOptions
    ) -> None:
        super().__init__()
        self._sources = sources
        self._out_root = out_root
        self._options = options
        self._cancelled = False

    def cancel(self) -> None:
        """Request a stop; honoured before the next file begins."""
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        results: list[ConvertResult] = []
        total = len(self._sources)
        for index, source in enumerate(self._sources, start=1):
            if self._cancelled:
                logger.debug("cancelled before %s", source.name)
                break
            logger.debug("converting %d/%d: %s", index, total, source.name)
            result = convert_file(source, self._out_root, self._options)
            logger.debug(
                "  -> %s (%d output file(s))", result.status, len(result.output_paths)
            )
            results.append(result)
            self.file_result.emit(result)
            self.progress.emit(index, total, source.name)
        self.finished.emit(results)


class UpdateWorker(QObject):
    """Runs the opt-in update check off the GUI thread."""

    found = Signal(str, str)  # latest version, download url
    finished = Signal()

    @Slot()
    def run(self) -> None:
        info = check_for_update()
        if info is not None and info.is_newer:
            self.found.emit(info.latest, info.url)
        self.finished.emit()
