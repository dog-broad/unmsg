"""Background worker behaviour for the GUI."""

from __future__ import annotations

from pathlib import Path

from unmsg.core import ConvertOptions
from unmsg.core.models import ConvertResult
from unmsg.ui import workers as workers_mod
from unmsg.ui.workers import BatchWorker, UpdateWorker


def _ok(src: Path) -> ConvertResult:
    return ConvertResult(
        source=src,
        bundle_dir=None,
        output_paths=[],
        attachments_saved=[],
        inline_images_saved=[],
        status="success",
        warnings=[],
        error=None,
        duration_ms=1,
    )


def test_batch_worker_converts_each_and_emits_signals(qtbot, monkeypatch, tmp_path):
    monkeypatch.setattr(workers_mod, "convert_file", lambda s, o, opt: _ok(s))
    sources = [tmp_path / "a.msg", tmp_path / "b.msg"]
    for src in sources:
        src.write_bytes(b"x")

    worker = BatchWorker(sources, tmp_path / "out", ConvertOptions())
    progress: list[tuple[int, int]] = []
    results: list[ConvertResult] = []
    worker.progress.connect(lambda d, t, p: progress.append((d, t)))
    worker.file_result.connect(lambda r: results.append(r))
    finished: list[list[ConvertResult]] = []
    worker.finished.connect(lambda rs: finished.append(list(rs)))

    worker.run()
    assert progress == [(1, 2), (2, 2)]
    assert len(results) == 2
    assert len(finished[0]) == 2


def test_batch_worker_cancel_stops_before_next_file(qtbot, monkeypatch, tmp_path):
    seen: list[Path] = []

    def fake(src, out, opts):
        seen.append(src)
        return _ok(src)

    monkeypatch.setattr(workers_mod, "convert_file", fake)
    sources = [tmp_path / "a.msg", tmp_path / "b.msg"]
    for src in sources:
        src.write_bytes(b"x")

    worker = BatchWorker(sources, tmp_path / "out", ConvertOptions())
    worker.cancel()  # cancel before run starts
    finished: list[list[ConvertResult]] = []
    worker.finished.connect(lambda rs: finished.append(list(rs)))
    worker.run()
    assert seen == []
    assert finished == [[]]


def test_update_worker_emits_found_on_newer(qtbot, monkeypatch):
    from unmsg.updates import UpdateInfo

    monkeypatch.setattr(
        workers_mod,
        "check_for_update",
        lambda: UpdateInfo(current="0.0.0", latest="9.9.9", url="https://x", notes=""),
    )
    worker = UpdateWorker()
    found: list[tuple[str, str]] = []
    done: list[bool] = []
    worker.found.connect(lambda v, u: found.append((v, u)))
    worker.finished.connect(lambda: done.append(True))
    worker.run()
    assert found == [("9.9.9", "https://x")]
    assert done == [True]


def test_update_worker_quiet_when_no_update(qtbot, monkeypatch):
    monkeypatch.setattr(workers_mod, "check_for_update", lambda: None)
    worker = UpdateWorker()
    found: list[object] = []
    worker.found.connect(lambda *a: found.append(a))
    worker.run()
    assert found == []
