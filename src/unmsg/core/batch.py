"""Convert many ``.msg`` files in one call.

Synchronous by design — the core does no threading. Callers (the CLI, the GUI)
pool it however they like. Inputs are sorted so a batch is deterministic.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from unmsg.core.models import ConvertResult
from unmsg.core.options import ConvertOptions
from unmsg.core.pipeline import convert_file

ProgressHook = Callable[[int, int, Path], None]


def convert_batch(
    sources: Iterable[Path | str],
    out_root: Path | str,
    options: ConvertOptions | None = None,
    *,
    progress: ProgressHook | None = None,
) -> list[ConvertResult]:
    """Convert every file in ``sources`` into ``out_root``.

    ``progress`` (if given) is called as ``progress(done, total, source)`` after
    each file. Returns one :class:`ConvertResult` per input, in sorted order.
    """
    paths = sorted({Path(s) for s in sources}, key=lambda p: str(p).lower())
    opts = options or ConvertOptions()
    total = len(paths)
    results: list[ConvertResult] = []

    for index, path in enumerate(paths, start=1):
        results.append(convert_file(path, out_root, opts))
        if progress is not None:
            progress(index, total, path)

    return results
