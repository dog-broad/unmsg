"""Format writers: front-matter, html document, single-file inlining."""

from __future__ import annotations

import base64

from unmsg.core.writer import get_writer
from unmsg.core.writer.base import RenderContext
from unmsg.core.writer.html_single import SingleFileHtmlWriter


def _ctx(record, **over):
    base = {
        "record": record,
        "markdown_body": "Hello **Bob**\n",
        "html_body": "<p>Hello <b>Bob</b></p>",
        "assets": {},
    }
    base.update(over)
    return RenderContext(**base)


def test_markdown_writer_emits_front_matter(make_record):
    out = get_writer("md").render(_ctx(make_record())).decode("utf-8")
    assert out.startswith("---\n")
    assert 'subject: "Quarterly Report"' in out
    assert 'date: "2024-03-15T09:32:00Z"' in out
    assert "Hello **Bob**" in out


def test_front_matter_escapes_quotes(make_record):
    out = get_writer("md").render(_ctx(make_record(subject='He said "hi"'))).decode()
    assert '\\"hi\\"' in out


def test_html_writer_builds_document(make_record):
    out = get_writer("html").render(_ctx(make_record())).decode("utf-8")
    assert out.startswith("<!DOCTYPE html>")
    assert "<title>Quarterly Report</title>" in out
    assert "alice@example.com" in out


def test_html_falls_back_to_text_when_body_empty(make_record):
    out = get_writer("html").render(_ctx(make_record(), html_body="")).decode()
    assert "<pre>" in out


def test_single_file_inlines_assets(make_record, inline_image):
    png = inline_image.data
    ctx = _ctx(
        make_record(),
        html_body='<img src="assets/inline_image_1.png">',
        assets={"assets/inline_image_1.png": png},
    )
    out = SingleFileHtmlWriter().render(ctx).decode("utf-8")
    assert "data:image/png;base64," in out
    assert 'src="assets/inline_image_1.png"' not in out
    assert base64.b64encode(png).decode("ascii") in out


def test_unsupported_format_returns_none():
    assert get_writer("pdf") is None
