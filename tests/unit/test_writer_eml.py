"""EML writer: headers, inline images by Content-ID, attachments, determinism."""

from __future__ import annotations

from email import message_from_bytes

from unmsg.core.writer import get_writer
from unmsg.core.writer.base import RenderContext


def _ctx(record, *, cleaned_html="<p>Hi <b>Bob</b></p>"):
    return RenderContext(
        record=record,
        markdown_body="",
        html_body="",
        assets={},
        cleaned_html=cleaned_html,
    )


def test_eml_has_headers_and_html_and_text(make_record):
    out = get_writer("eml").render(_ctx(make_record()))
    msg = message_from_bytes(out)
    assert msg["Subject"] == "Quarterly Report"
    assert "alice@example.com" in msg["From"]
    assert msg["To"] == "bob@example.com"
    assert "Date" in msg
    types = {part.get_content_type() for part in msg.walk()}
    assert "text/plain" in types
    assert "text/html" in types


def test_eml_inline_image_attached_by_content_id(make_record, inline_image):
    record = make_record(
        attachments=[inline_image],
        body_html='<img src="cid:image001">',
    )
    ctx = _ctx(record, cleaned_html='<p>see</p><img src="cid:image001">')
    out = get_writer("eml").render(ctx)
    msg = message_from_bytes(out)
    cids = [p.get("Content-ID") for p in msg.walk() if p.get("Content-ID")]
    assert "<image001>" in cids
    assert "multipart/related" in {p.get_content_type() for p in msg.walk()}


def test_eml_regular_attachment_included(make_record, file_attachment):
    out = get_writer("eml").render(_ctx(make_record(attachments=[file_attachment])))
    msg = message_from_bytes(out)
    names = [p.get_filename() for p in msg.walk() if p.get_filename()]
    assert "budget.pdf" in names


def test_eml_is_deterministic(make_record, inline_image, file_attachment):
    record = make_record(attachments=[inline_image, file_attachment])
    ctx = _ctx(record)
    assert get_writer("eml").render(ctx) == get_writer("eml").render(ctx)


def test_eml_now_supported_by_registry():
    assert get_writer("eml") is not None
