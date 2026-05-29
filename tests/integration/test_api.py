"""Public Python API surface and behaviour (imported from the top-level package).

This locks the small, stable surface promised to library users: importing the
names, the option defaults, and the shapes returned by ``convert_file`` and
``convert_batch``.
"""

from __future__ import annotations

import unmsg
from unmsg import (
    Attachment,
    ConvertOptions,
    ConvertResult,
    MsgRecord,
    convert_batch,
    convert_file,
)


def test_public_names_are_exported():
    for name in (
        "Attachment",
        "ConvertOptions",
        "ConvertResult",
        "MsgRecord",
        "convert_batch",
        "convert_file",
        "__version__",
    ):
        assert name in unmsg.__all__
        assert hasattr(unmsg, name)


def test_default_options():
    opts = ConvertOptions()
    assert opts.formats == ("md", "html")
    assert opts.attachments is True
    assert opts.inline_images == "extract"
    assert opts.on_conflict == "rename"
    assert opts.naming_template == "{date}_{subject}"


def test_convert_file_returns_result(monkeypatch, tmp_path, make_record):
    import unmsg.core.pipeline as pipeline

    monkeypatch.setattr(pipeline, "read_msg", lambda path: make_record())
    src = tmp_path / "in.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"

    result = convert_file(src, out, ConvertOptions(formats=("md",)))

    assert isinstance(result, ConvertResult)
    assert result.status == "success"
    assert result.output_paths
    assert all(isinstance(p, type(src)) for p in result.output_paths)
    assert result.sha256  # checksum recorded for produced files


def test_convert_batch_returns_one_result_per_input(monkeypatch, tmp_path, make_record):
    import unmsg.core.pipeline as pipeline

    monkeypatch.setattr(pipeline, "read_msg", lambda path: make_record())
    files = [tmp_path / "a.msg", tmp_path / "b.msg"]
    for f in files:
        f.write_bytes(b"x")

    results = convert_batch(files, tmp_path / "out", ConvertOptions(formats=("md",)))
    assert len(results) == 2
    assert all(isinstance(r, ConvertResult) for r in results)


def test_models_are_usable_directly():
    att = Attachment(name="x.png", data=b"\x89PNG", mime="image/png", cid="c", size=4)
    assert att.is_inline
    assert MsgRecord  # importable type
