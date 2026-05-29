"""End-to-end pipeline behaviour, driven by synthetic records on real disk."""

from __future__ import annotations

import extract_msg

from unmsg.core import ConvertOptions, convert_file
from unmsg.core.models import Attachment


def _patch_reader(monkeypatch, record):
    # pipeline binds read_msg by name, so patch it in the pipeline namespace.
    import unmsg.core.pipeline as pipeline

    monkeypatch.setattr(pipeline, "read_msg", lambda path: record)


def test_single_format_no_assets_flattens(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record(attachments=[]))
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"

    result = convert_file(src, out, ConvertOptions(formats=("md",)))
    assert result.status == "success"
    assert result.bundle_dir is None
    assert (out / "2024-03-15_Quarterly Report.md").exists()


def test_multi_format_creates_bundle(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"

    result = convert_file(src, out, ConvertOptions(formats=("md", "html")))
    bundle = out / "2024-03-15_Quarterly Report"
    assert result.bundle_dir == bundle
    assert (bundle / "2024-03-15_Quarterly Report.md").exists()
    assert (bundle / "2024-03-15_Quarterly Report.html").exists()
    assert len(result.sha256) == 2


def test_inline_image_saved_and_referenced(
    monkeypatch, tmp_path, make_record, inline_image
):
    record = make_record(
        body_html='<html><body><img src="cid:image001"></body></html>',
        attachments=[inline_image],
    )
    _patch_reader(monkeypatch, record)
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"

    result = convert_file(src, out, ConvertOptions(formats=("html",)))
    bundle = result.bundle_dir
    assert bundle is not None
    asset = bundle / "assets" / "inline_image_1.png"
    assert asset.exists()
    html = (bundle / "2024-03-15_Quarterly Report.html").read_text("utf-8")
    assert "assets/inline_image_1.png" in html
    assert result.inline_images_saved == [asset]


def test_regular_attachment_saved(monkeypatch, tmp_path, make_record, file_attachment):
    _patch_reader(monkeypatch, make_record(attachments=[file_attachment]))
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    result = convert_file(src, out, ConvertOptions(formats=("md",)))
    assert (result.bundle_dir / "attachments" / "budget.pdf").exists()


def test_unsupported_format_warns(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    result = convert_file(src, tmp_path / "out", ConvertOptions(formats=("md", "pdf")))
    assert result.status == "warning"
    assert any("pdf" in w for w in result.warnings)


def test_nested_message_converted_under_attachments(monkeypatch, tmp_path, make_record):
    inner = make_record(subject="Inner Memo", attachments=[])
    outer = make_record(
        subject="Outer",
        nested=[inner],
        attachments=[
            Attachment(
                "inner.msg",
                b"",
                "application/vnd.ms-outlook",
                None,
                0,
                is_nested_msg=True,
            )
        ],
    )
    _patch_reader(monkeypatch, outer)
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    convert_file(src, out, ConvertOptions(formats=("md",)))
    nested_md = out / "2024-03-15_Outer" / "attachments" / "2024-03-15_Inner Memo.md"
    assert nested_md.exists()


def test_read_failure_is_humanised(monkeypatch, tmp_path):
    import unmsg.core.pipeline as pipeline

    def boom(path):
        raise ValueError("internal parser explosion")

    monkeypatch.setattr(pipeline, "read_msg", boom)
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    result = convert_file(src, tmp_path / "out")
    assert result.status == "failed"
    assert "explosion" not in (result.error or "")
    assert "Couldn't read" in (result.error or "")


def test_text_only_body_uses_plain_text(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record(body_html="", body_text="Just text here"))
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    convert_file(src, out, ConvertOptions(formats=("md",)))
    md = (out / "2024-03-15_Quarterly Report.md").read_text("utf-8")
    assert "Just text here" in md


def test_conflict_rename_adds_suffix(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    opts = ConvertOptions(formats=("md",), on_conflict="rename")
    convert_file(src, out, opts)
    convert_file(src, out, opts)
    assert (out / "2024-03-15_Quarterly Report.md").exists()
    assert (out / "2024-03-15_Quarterly Report_1.md").exists()


def test_conflict_skip_leaves_original(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    opts = ConvertOptions(formats=("md",), on_conflict="skip")
    convert_file(src, out, opts)
    result = convert_file(src, out, opts)
    assert result.status == "warning"
    assert not (out / "2024-03-15_Quarterly Report_1.md").exists()


def test_conflict_overwrite_reuses_path(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    opts = ConvertOptions(formats=("md",), on_conflict="overwrite")
    convert_file(src, out, opts)
    convert_file(src, out, opts)
    assert not (out / "2024-03-15_Quarterly Report_1.md").exists()


def test_deeply_nested_messages_stop(monkeypatch, tmp_path, make_record):
    import unmsg.core.pipeline as pipeline

    # Lower the limit so the guard fires at a shallow (path-safe) depth.
    monkeypatch.setattr(pipeline, "_MAX_NEST_DEPTH", 1)
    leaf = make_record(subject="Leaf")
    middle = make_record(subject="Middle", nested=[leaf])
    top = make_record(subject="Top", nested=[middle])
    _patch_reader(monkeypatch, top)
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    result = convert_file(src, tmp_path / "out", ConvertOptions(formats=("md",)))
    assert any("deeply nested" in w for w in result.warnings)


def test_convert_stage_error_is_humanised(monkeypatch, tmp_path, make_record):
    import unmsg.core.pipeline as pipeline

    _patch_reader(monkeypatch, make_record())

    def boom(*args, **kwargs):
        raise OSError("disk gremlin")

    monkeypatch.setattr(pipeline, "_convert_record", boom)
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    result = convert_file(src, tmp_path / "out")
    assert result.status == "failed"
    assert "gremlin" not in (result.error or "")
    assert "Couldn't write" in (result.error or "")


def test_missing_file_humanised(monkeypatch, tmp_path):
    # Real read_msg raises FileNotFoundError for an absent path.
    monkeypatch.setattr(
        extract_msg, "Message", lambda p: (_ for _ in ()).throw(AssertionError)
    )
    result = convert_file(tmp_path / "ghost.msg", tmp_path / "out")
    assert result.status == "failed"
    assert "find" in (result.error or "").lower()
