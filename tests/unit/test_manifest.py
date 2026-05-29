"""Manifest: shape, relative paths, sorting, determinism."""

from __future__ import annotations

import json
from pathlib import Path

from unmsg._version import __version__
from unmsg.core.manifest import build_manifest, write_manifest
from unmsg.core.models import ConvertResult


def _result(source: str, out_root: Path, status: str = "success") -> ConvertResult:
    bundle = out_root / source.replace(".msg", "")
    md = bundle / f"{source.replace('.msg', '')}.md"
    return ConvertResult(
        source=Path(source),
        bundle_dir=bundle,
        output_paths=[md],
        attachments_saved=[],
        inline_images_saved=[],
        status=status,
        warnings=[],
        error=None,
        duration_ms=5,
        sha256={md: "abc123"},
    )


def test_manifest_shape_and_relative_paths(tmp_path):
    res = _result("report.msg", tmp_path)
    manifest = build_manifest([res], tmp_path)
    assert manifest["schema"] == 1
    assert manifest["version"] == __version__
    entry = manifest["messages"][0]
    assert entry["source"] == "report.msg"
    assert entry["outputs"][0]["path"] == "report/report.md"  # relative, posix
    assert entry["outputs"][0]["sha256"] == "abc123"


def test_manifest_sorted_by_source(tmp_path):
    results = [_result("zeta.msg", tmp_path), _result("alpha.msg", tmp_path)]
    manifest = build_manifest(results, tmp_path)
    assert [m["source"] for m in manifest["messages"]] == ["alpha.msg", "zeta.msg"]


def test_manifest_is_deterministic(tmp_path):
    results = [_result("a.msg", tmp_path), _result("b.msg", tmp_path)]
    assert build_manifest(results, tmp_path) == build_manifest(results, tmp_path)


def test_write_manifest_creates_file(tmp_path):
    out = tmp_path / "out"
    path = write_manifest([_result("a.msg", out)], out)
    assert path == out / "manifest.json"
    data = json.loads(path.read_text("utf-8"))
    assert data["messages"][0]["source"] == "a.msg"


def test_carried_entries_are_merged_and_sorted(tmp_path):
    carried = [{"source": "zzz.msg", "status": "success", "outputs": []}]
    manifest = build_manifest([_result("aaa.msg", tmp_path)], tmp_path, carried=carried)
    assert [m["source"] for m in manifest["messages"]] == ["aaa.msg", "zzz.msg"]


def test_failed_result_records_error(tmp_path):
    res = _result("bad.msg", tmp_path, status="failed")
    res.error = "Couldn't read this message."
    res.sha256 = {}
    manifest = build_manifest([res], tmp_path)
    entry = manifest["messages"][0]
    assert entry["status"] == "failed"
    assert entry["outputs"] == []
    assert entry["error"] == "Couldn't read this message."
