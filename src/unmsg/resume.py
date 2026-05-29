"""Resume support: skip sources already converted, per an existing manifest.

A source is skipped only if its previous manifest entry succeeded *and* every
output it recorded still exists with a matching SHA-256 — so a missing or edited
output is reconverted, never trusted. Skipped sources' manifest entries are
carried forward unchanged.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from unmsg.core.manifest import MANIFEST_NAME, Entry


def plan_resume(sources: list[Path], out_root: Path) -> tuple[list[Path], list[Entry]]:
    """Split ``sources`` into (still-to-convert, carried-entries-for-skipped)."""
    intact = _intact_entries(out_root)
    pending: list[Path] = []
    carried: list[Entry] = []
    for source in sources:
        entry = intact.get(Path(source).name)
        if entry is None:
            pending.append(Path(source))
        else:
            carried.append(entry)
    return pending, carried


def _intact_entries(out_root: Path) -> dict[str, Entry]:
    manifest = _load(out_root)
    intact: dict[str, Entry] = {}
    for entry in manifest.get("messages", []):
        if entry.get("status") != "success":
            continue
        outputs = entry.get("outputs", [])
        if outputs and _outputs_match(outputs, out_root):
            intact[str(entry.get("source", ""))] = entry
    return intact


def _outputs_match(outputs: list[dict[str, str]], out_root: Path) -> bool:
    for output in outputs:
        target = out_root / output.get("path", "")
        if not target.is_file():
            return False
        if _sha256(target) != output.get("sha256"):
            return False
    return True


def _load(out_root: Path) -> dict[str, object]:
    try:
        data = json.loads((out_root / MANIFEST_NAME).read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
