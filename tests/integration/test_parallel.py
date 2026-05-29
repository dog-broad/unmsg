"""Parallel runner: ordering, progress, worker cap, and kill-on-timeout.

The ``convert`` seam is injected with fast, module-level workers (picklable for
the spawn start method), so these exercise the scheduler without a real parser.
"""

from __future__ import annotations

import time
from pathlib import Path

from unmsg.core.models import ConvertResult
from unmsg.core.options import ConvertOptions
from unmsg.parallel import convert_batch_parallel


def _ok(source: Path, out_root: Path, opts: ConvertOptions) -> ConvertResult:
    return ConvertResult(
        source=source,
        bundle_dir=None,
        output_paths=[],
        attachments_saved=[],
        inline_images_saved=[],
        status="success",
        warnings=[],
        error=None,
        duration_ms=1,
    )


def _slow(source: Path, out_root: Path, opts: ConvertOptions) -> ConvertResult:
    time.sleep(30)
    return _ok(source, out_root, opts)


def test_empty_input_returns_empty():
    assert convert_batch_parallel([], "out", convert=_ok) == []


def test_all_inputs_converted_in_sorted_order(tmp_path):
    files = [tmp_path / f"{name}.msg" for name in ("charlie", "alpha", "bravo")]
    for f in files:
        f.write_bytes(b"x")
    seen: list[int] = []

    results = convert_batch_parallel(
        files,
        tmp_path / "out",
        ConvertOptions(),
        jobs=2,
        progress=lambda d, t, p: seen.append(d),
        convert=_ok,
    )

    assert [r.source.name for r in results] == ["alpha.msg", "bravo.msg", "charlie.msg"]
    assert all(r.status == "success" for r in results)
    assert sorted(seen) == [1, 2, 3]


def test_timeout_terminates_worker_and_marks_failed(tmp_path):
    f = tmp_path / "hang.msg"
    f.write_bytes(b"x")
    started = time.monotonic()

    results = convert_batch_parallel(
        [f], tmp_path / "out", ConvertOptions(), jobs=1, timeout=0.5, convert=_slow
    )

    assert len(results) == 1
    assert results[0].status == "failed"
    assert "too long" in (results[0].error or "")
    assert time.monotonic() - started < 15  # killed, not waited the full 30s
