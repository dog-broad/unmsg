"""Batch conversion: ordering, progress hook, per-input results."""

from __future__ import annotations

import unmsg.core.batch as batch_mod
from unmsg.core import ConvertOptions, convert_batch


def test_batch_converts_all_and_reports_progress(monkeypatch, tmp_path, make_record):
    monkeypatch.setattr(
        batch_mod,
        "convert_file",
        lambda src, out, opts: _ok_result(src),
    )
    files = [tmp_path / "b.msg", tmp_path / "a.msg"]
    for f in files:
        f.write_bytes(b"x")

    seen: list[int] = []
    results = convert_batch(
        files,
        tmp_path / "out",
        ConvertOptions(),
        progress=lambda d, t, p: seen.append(d),
    )

    assert len(results) == 2
    assert seen == [1, 2]


def test_batch_sorts_inputs_deterministically(monkeypatch, tmp_path):
    order: list[str] = []
    monkeypatch.setattr(
        batch_mod,
        "convert_file",
        lambda src, out, opts: order.append(src.name) or _ok_result(src),
    )
    files = [tmp_path / "zeta.msg", tmp_path / "alpha.msg", tmp_path / "mid.msg"]
    for f in files:
        f.write_bytes(b"x")
    convert_batch(files, tmp_path / "out")
    assert order == ["alpha.msg", "mid.msg", "zeta.msg"]


def test_batch_dedupes_repeated_inputs(monkeypatch, tmp_path):
    monkeypatch.setattr(
        batch_mod, "convert_file", lambda src, out, opts: _ok_result(src)
    )
    f = tmp_path / "dup.msg"
    f.write_bytes(b"x")
    results = convert_batch([f, f], tmp_path / "out")
    assert len(results) == 1


def _ok_result(src):
    from unmsg.core.models import ConvertResult

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
