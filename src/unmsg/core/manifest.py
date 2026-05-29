"""Per-batch manifest: a deterministic record of what a run produced.

``build_manifest`` is pure; ``write_manifest`` performs the single write. Entries
and outputs are sorted, paths are relative to the output root, and no wall-clock
timestamp is embedded — so the same inputs and version yield an identical
manifest that an archivist can diff and verify a copy against.
"""

from __future__ import annotations

import json
from pathlib import Path

from unmsg._version import __version__
from unmsg.core.models import ConvertResult

MANIFEST_SCHEMA = 1
MANIFEST_NAME = "manifest.json"


def build_manifest(results: list[ConvertResult], out_root: Path) -> dict[str, object]:
    messages = [_entry(result, out_root) for result in _sorted(results)]
    return {
        "schema": MANIFEST_SCHEMA,
        "tool": "unmsg",
        "version": __version__,
        "messages": messages,
    }


def write_manifest(
    results: list[ConvertResult], out_root: Path, *, path: Path | None = None
) -> Path:
    target = path or (out_root / MANIFEST_NAME)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build_manifest(results, out_root), indent=2, ensure_ascii=False)
    target.write_text(text + "\n", encoding="utf-8")
    return target


def _entry(result: ConvertResult, out_root: Path) -> dict[str, object]:
    outputs = [
        {"path": _rel(path, out_root), "sha256": digest}
        for path, digest in sorted(result.sha256.items(), key=lambda kv: str(kv[0]))
    ]
    return {
        "source": result.source.name,
        "status": result.status,
        "bundle": _rel(result.bundle_dir, out_root) if result.bundle_dir else None,
        "outputs": outputs,
        "warnings": result.warnings,
        "error": result.error,
    }


def _sorted(results: list[ConvertResult]) -> list[ConvertResult]:
    return sorted(results, key=lambda r: str(r.source).lower())


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name
