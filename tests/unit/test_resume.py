"""Resume: skip only sources whose outputs still match the manifest."""

from __future__ import annotations

import json
from pathlib import Path

from unmsg.core.manifest import MANIFEST_NAME
from unmsg.resume import plan_resume


def _write_manifest(out_root: Path, entries: list[dict]) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    payload = {"schema": 1, "tool": "unmsg", "version": "x", "messages": entries}
    (out_root / MANIFEST_NAME).write_text(json.dumps(payload), encoding="utf-8")


def _entry(out_root: Path, source: str, *, status: str = "success") -> dict:
    rel = f"{source.replace('.msg', '')}.md"
    target = out_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("body", encoding="utf-8")
    import hashlib

    digest = hashlib.sha256(b"body").hexdigest()
    return {
        "source": source,
        "status": status,
        "outputs": [{"path": rel, "sha256": digest}],
        "warnings": [],
        "error": None,
    }


def test_no_manifest_means_everything_pending(tmp_path):
    sources = [tmp_path / "a.msg", tmp_path / "b.msg"]
    pending, carried = plan_resume(sources, tmp_path / "out")
    assert pending == sources
    assert carried == []


def test_intact_success_is_skipped_and_carried(tmp_path):
    out = tmp_path / "out"
    _write_manifest(out, [_entry(out, "a.msg")])
    pending, carried = plan_resume([tmp_path / "a.msg", tmp_path / "b.msg"], out)
    assert [p.name for p in pending] == ["b.msg"]
    assert [c["source"] for c in carried] == ["a.msg"]


def test_missing_output_forces_reconvert(tmp_path):
    out = tmp_path / "out"
    entry = _entry(out, "a.msg")
    (out / entry["outputs"][0]["path"]).unlink()  # delete the produced file
    _write_manifest(out, [entry])
    pending, carried = plan_resume([tmp_path / "a.msg"], out)
    assert [p.name for p in pending] == ["a.msg"]
    assert carried == []


def test_checksum_mismatch_forces_reconvert(tmp_path):
    out = tmp_path / "out"
    entry = _entry(out, "a.msg")
    (out / entry["outputs"][0]["path"]).write_text("tampered", encoding="utf-8")
    _write_manifest(out, [entry])
    pending, _ = plan_resume([tmp_path / "a.msg"], out)
    assert [p.name for p in pending] == ["a.msg"]


def test_failed_entry_is_not_skipped(tmp_path):
    out = tmp_path / "out"
    _write_manifest(out, [_entry(out, "a.msg", status="failed")])
    pending, carried = plan_resume([tmp_path / "a.msg"], out)
    assert [p.name for p in pending] == ["a.msg"]
    assert carried == []
