"""Text and JSON metadata writers."""

from __future__ import annotations

import json

from unmsg.core.writer import get_writer
from unmsg.core.writer.base import RenderContext


def _ctx(record):
    return RenderContext(record=record, markdown_body="", html_body="", assets={})


def _ctx_html(record, html_body):
    return RenderContext(
        record=record, markdown_body="", html_body=html_body, assets={}
    )


def test_txt_writer_has_header_and_body(make_record):
    out = get_writer("txt").render(_ctx(make_record())).decode("utf-8")
    assert out.startswith("Subject: Quarterly Report")
    assert "From: Alice Example <alice@example.com>" in out
    assert "Hello Bob" in out
    assert out.endswith("\n")


def test_txt_falls_back_to_html_text_when_no_plain_body(make_record):
    # HTML-only message: body_text empty, but the HTML carries the content.
    record = make_record(body_text="")
    html = "<p>Dear team,</p><p>The <b>allowance</b> details are attached.</p>"
    out = get_writer("txt").render(_ctx_html(record, html)).decode("utf-8")
    assert "Dear team," in out
    assert "allowance" in out
    assert "<p>" not in out  # tags stripped, not raw HTML


def test_json_writer_is_valid_and_stable(make_record, file_attachment):
    writer = get_writer("json")
    record = make_record(attachments=[file_attachment])
    first = writer.render(_ctx(record))
    second = writer.render(_ctx(record))
    assert first == second  # deterministic

    data = json.loads(first)
    assert data["subject"] == "Quarterly Report"
    assert data["from"]["email"] == "alice@example.com"
    assert data["sent_on"] == "2024-03-15T09:32:00Z"
    assert data["attachments"][0]["name"] == "budget.pdf"
    assert data["attachments"][0]["inline"] is False


def test_json_handles_missing_dates(make_record):
    out = get_writer("json").render(_ctx(make_record(sent_on=None))).decode("utf-8")
    assert json.loads(out)["sent_on"] is None
