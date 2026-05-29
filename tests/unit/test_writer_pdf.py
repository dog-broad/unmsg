"""PDF writer: real render, determinism, and graceful missing-dependency."""

from __future__ import annotations

import pytest

from unmsg.core.writer import get_writer
from unmsg.core.writer.base import RenderContext, WriterUnavailable
from unmsg.core.writer.pdf import PdfWriter

xhtml2pdf = pytest.importorskip("xhtml2pdf")


def _ctx(record, **over):
    base = {
        "record": record,
        "markdown_body": "",
        "html_body": "<p>Hello <b>Bob</b></p>",
        "assets": {},
        "cleaned_html": "",
    }
    base.update(over)
    return RenderContext(**base)


def test_pdf_is_rendered(make_record):
    out = PdfWriter().render(_ctx(make_record()))
    assert out[:5] == b"%PDF-"
    assert len(out) > 500


def test_pdf_is_deterministic(make_record):
    ctx = _ctx(make_record())
    assert PdfWriter().render(ctx) == PdfWriter().render(ctx)


def test_pdf_registered():
    assert get_writer("pdf") is not None


def test_missing_dependency_raises_writer_unavailable(monkeypatch, make_record):
    import builtins

    real_import = builtins.__import__

    def block(name, *args, **kwargs):
        if name.startswith("xhtml2pdf") or name.startswith("reportlab"):
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", block)
    with pytest.raises(WriterUnavailable):
        PdfWriter().render(_ctx(make_record()))
