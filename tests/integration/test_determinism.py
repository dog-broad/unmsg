"""The same input and options must produce identical output bytes."""

from __future__ import annotations

from unmsg.core import ConvertOptions, convert_file


def _patch(monkeypatch, record):
    import unmsg.core.pipeline as pipeline

    monkeypatch.setattr(pipeline, "read_msg", lambda path: record)


def _convert(tmp_path, name, record):
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / name
    convert_file(src, out, ConvertOptions(formats=("md", "html", "html_single")))
    return out


def test_output_bytes_are_stable(monkeypatch, tmp_path, make_record, inline_image):
    record = make_record(
        body_html='<html><body><p>Hi</p><img src="cid:image001"></body></html>',
        attachments=[inline_image],
    )
    _patch(monkeypatch, record)

    first = _convert(tmp_path, "run1", record)
    second = _convert(tmp_path, "run2", record)

    files1 = sorted(p.relative_to(first) for p in first.rglob("*") if p.is_file())
    files2 = sorted(p.relative_to(second) for p in second.rglob("*") if p.is_file())
    assert files1 == files2

    for rel in files1:
        assert (first / rel).read_bytes() == (second / rel).read_bytes(), rel


def test_sha256_matches_written_bytes(monkeypatch, tmp_path, make_record):
    import hashlib

    _patch(monkeypatch, make_record())
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    result = convert_file(src, out, ConvertOptions(formats=("md", "html")))
    for path, digest in result.sha256.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
