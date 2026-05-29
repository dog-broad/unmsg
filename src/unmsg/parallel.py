"""Parallel batch conversion with a real per-file timeout (application layer).

The core stays synchronous; this runs conversions across worker *processes* (one
message per worker, capped at the CPU count) so a batch uses every core and a
single pathological message can be force-terminated on timeout without taking
the batch down. Results are returned in input order, so output stays
deterministic regardless of finish order.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import queue as queue_mod
import time
from collections.abc import Callable, Iterable
from pathlib import Path

from unmsg.core.models import ConvertResult
from unmsg.core.options import ConvertOptions
from unmsg.core.pipeline import convert_file

ProgressHook = Callable[[int, int, Path], None]
ConvertFn = Callable[[Path, Path, ConvertOptions], ConvertResult]

_POLL_SECONDS = 0.05
_DRAIN_SECONDS = 1.0


def convert_batch_parallel(
    sources: Iterable[Path | str],
    out_root: Path | str,
    options: ConvertOptions | None = None,
    *,
    jobs: int | None = None,
    timeout: float = 0.0,
    progress: ProgressHook | None = None,
    convert: ConvertFn = convert_file,
) -> list[ConvertResult]:
    """Convert ``sources`` across up to ``jobs`` worker processes.

    ``timeout`` (seconds, 0 = none) force-terminates a worker whose message runs
    too long, recording it as failed. ``convert`` is the per-file function (kept
    injectable so it can be exercised without a real parser).
    """
    paths = sorted({Path(s) for s in sources}, key=lambda p: str(p).lower())
    if not paths:
        return []
    opts = options or ConvertOptions()
    root = Path(out_root)
    worker_cap = jobs or (os.cpu_count() or 1)
    worker_cap = max(1, min(worker_cap, len(paths)))

    ctx = mp.get_context("spawn")
    results: list[ConvertResult | None] = [None] * len(paths)
    running: dict[int, tuple[mp.process.BaseProcess, queue_mod.Queue, float]] = {}
    next_index = 0
    completed = 0
    total = len(paths)

    while completed < total:
        while len(running) < worker_cap and next_index < total:
            index = next_index
            next_index += 1
            result_queue: queue_mod.Queue = ctx.Queue()
            proc = ctx.Process(
                target=_run_one,
                args=(convert, paths[index], root, opts, result_queue),
                daemon=True,
            )
            proc.start()
            running[index] = (proc, result_queue, time.monotonic())

        for index, (proc, result_queue, started) in list(running.items()):
            outcome = _collect(paths[index], proc, result_queue, started, timeout)
            if outcome is not None:
                results[index] = outcome
                running.pop(index)
                completed += 1
                if progress is not None:
                    progress(completed, total, paths[index])

        if running:
            time.sleep(_POLL_SECONDS)

    return [result for result in results if result is not None]


def _run_one(
    convert: ConvertFn,
    source: Path,
    out_root: Path,
    opts: ConvertOptions,
    result_queue: queue_mod.Queue,
) -> None:
    result_queue.put(convert(source, out_root, opts))


def _collect(
    source: Path,
    proc: mp.process.BaseProcess,
    result_queue: queue_mod.Queue,
    started: float,
    timeout: float,
) -> ConvertResult | None:
    try:
        return result_queue.get_nowait()
    except queue_mod.Empty:
        pass

    if timeout and (time.monotonic() - started) > timeout:
        proc.terminate()
        proc.join(_DRAIN_SECONDS)
        return _failed(source, "This message took too long and was skipped.")

    if not proc.is_alive():
        # Finished but the result may still be flushing from the queue feeder.
        try:
            return result_queue.get(timeout=_DRAIN_SECONDS)
        except queue_mod.Empty:
            return _failed(source, "Couldn't convert this message.")

    return None


def _failed(source: Path, message: str) -> ConvertResult:
    return ConvertResult(
        source=source,
        bundle_dir=None,
        output_paths=[],
        attachments_saved=[],
        inline_images_saved=[],
        status="failed",
        warnings=[],
        error=message,
        duration_ms=0,
    )
