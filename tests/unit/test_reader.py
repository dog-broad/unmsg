"""Reader field-mapping, exercised against a faithful fake ``extract_msg``.

A real Outlook ``.msg`` can only be produced by Outlook, so the binary reader
path is covered here with a stand-in that mimics the library's attribute
surface. This verifies our mapping, address parsing, date normalisation, and
nested-message recursion without committing binary fixtures.
"""

from __future__ import annotations

from datetime import datetime

import extract_msg

from unmsg.core.reader import read_msg


class FakeAttachment:
    def __init__(self, *, data, longFilename="", cid=None, mimetype=None, type="data"):
        self.data = data
        self.longFilename = longFilename
        self.shortFilename = longFilename
        self.cid = cid
        self.mimetype = mimetype
        self.type = type


class FakeMessage:
    def __init__(self, path="", **kw):
        self.subject = kw.get("subject", "Subject")
        self.sender = kw.get("sender", "Alice Example <alice@example.com>")
        self.to = kw.get("to", "bob@example.com; carol@example.com")
        self.cc = kw.get("cc", "")
        self.bcc = kw.get("bcc", "")
        self.date = kw.get("date", datetime(2024, 3, 15, 9, 32, 0))
        self.header = kw.get("header", "From: alice@example.com")
        self.body = kw.get("body", "Plain body")
        self.htmlBody = kw.get("htmlBody", b"<html><body><p>Hi</p></body></html>")
        self.attachments = kw.get("attachments", [])
        self.classType = kw.get("classType", "IPM.Note")
        self.closed = False

    def close(self):
        self.closed = True


def _patch(monkeypatch, factory):
    monkeypatch.setattr(extract_msg, "Message", factory)


def test_maps_core_fields(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    _patch(monkeypatch, lambda p: FakeMessage(p))

    record = read_msg(src)
    assert record.subject == "Subject"
    assert record.sender_name == "Alice Example"
    assert record.sender_email == "alice@example.com"
    assert record.to == ["bob@example.com", "carol@example.com"]
    assert "Hi" in record.body_html


def test_naive_date_normalised_to_utc(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    _patch(monkeypatch, lambda p: FakeMessage(p))
    record = read_msg(src)
    assert record.sent_on is not None
    assert record.sent_on.tzinfo is not None
    assert record.sent_on.strftime("%Y-%m-%dT%H:%M:%SZ") == "2024-03-15T09:32:00Z"


def test_inline_cid_attachment_mapped(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    att = FakeAttachment(
        data=b"PNGDATA", longFilename="logo.png", cid="image001", mimetype="image/png"
    )
    _patch(monkeypatch, lambda p: FakeMessage(p, attachments=[att]))
    record = read_msg(src)
    assert record.attachments[0].cid == "image001"
    assert record.attachments[0].is_inline


def test_meeting_and_signed_flags(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    _patch(monkeypatch, lambda p: FakeMessage(p, classType="IPM.Appointment.Signed"))
    record = read_msg(src)
    assert record.is_meeting
    assert record.is_signed


def test_embedded_message_recursed(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    inner = FakeMessage("", subject="Inner")
    embed = FakeAttachment(data=inner, longFilename="inner.msg", type="msg")
    _patch(monkeypatch, lambda p: FakeMessage(p, attachments=[embed]))
    record = read_msg(src)
    assert len(record.nested) == 1
    assert record.nested[0].subject == "Inner"
    assert record.attachments[0].is_nested_msg


def test_missing_file_raises(tmp_path):
    try:
        read_msg(tmp_path / "nope.msg")
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")


class _GetFilenameAttachment:
    """No long/short filename; exposes a getFilename() method instead."""

    data = b"DATA"
    longFilename = ""
    shortFilename = ""
    cid = None
    mimetype = None
    type = "data"

    def getFilename(self):
        return "from_method.bin"


def test_filename_from_getfilename(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    _patch(
        monkeypatch, lambda p: FakeMessage(p, attachments=[_GetFilenameAttachment()])
    )
    record = read_msg(src)
    assert record.attachments[0].name == "from_method.bin"


def test_undecodable_html_uses_latin1(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    # 0x81 is invalid in utf-8 and undefined in cp1252 -> latin-1 path.
    _patch(monkeypatch, lambda p: FakeMessage(p, htmlBody=b"\x81body"))
    record = read_msg(src)
    assert "body" in record.body_html


def test_no_date_and_empty_recipients(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    _patch(monkeypatch, lambda p: FakeMessage(p, date=None, to="", cc=""))
    record = read_msg(src)
    assert record.sent_on is None
    assert record.to == []


def test_close_is_called_even_if_it_raises(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")

    class Rude(FakeMessage):
        def close(self):
            raise RuntimeError("close blew up")

    _patch(monkeypatch, lambda p: Rude(p))
    record = read_msg(src)  # must not raise
    assert record.subject == "Subject"


class _AltAttachment:
    """Uses alternate attribute spellings the reader must tolerate."""

    data = b"DATA"
    longFilename = ""
    shortFilename = ""
    contentId = "alt-cid"  # not `cid`
    mime = "text/plain"  # not `mimetype`
    type = "data"

    def getFilename(self):
        raise RuntimeError("filename probe failed")


def test_alternate_cid_and_mime_attrs(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    _patch(monkeypatch, lambda p: FakeMessage(p, attachments=[_AltAttachment()]))
    record = read_msg(src)
    att = record.attachments[0]
    assert att.cid == "alt-cid"
    assert att.mime == "text/plain"
    assert att.name == ""  # getFilename raised -> empty; planner numbers it later


def test_smime_signed_detected(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    _patch(monkeypatch, lambda p: FakeMessage(p, classType="IPM.Note.SMIME"))
    record = read_msg(src)
    assert record.is_signed


def test_trailing_nulls_are_stripped(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    att = FakeAttachment(
        data=b"PNG",
        longFilename="image001.png\x00",
        cid="image001@x\x00",
        mimetype="image/png",
    )
    _patch(
        monkeypatch, lambda p: FakeMessage(p, subject="Hello\x00", attachments=[att])
    )
    record = read_msg(src)
    assert record.subject == "Hello"
    assert record.attachments[0].name == "image001.png"
    assert record.attachments[0].cid == "image001@x"


def test_rfc2822_date_string_parsed_to_utc(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    _patch(
        monkeypatch, lambda p: FakeMessage(p, date="Wed, 13 May 2026 01:02:16 +0530")
    )
    record = read_msg(src)
    assert record.sent_on is not None
    assert record.sent_on.strftime("%Y-%m-%dT%H:%M:%SZ") == "2026-05-12T19:32:16Z"


def test_recipients_split_is_quote_aware(monkeypatch, tmp_path):
    src = tmp_path / "m.msg"
    src.write_bytes(b"x")
    raw = '"Jain; Prinse (Cognizant)" <p@x.com>; "Thakur, Ritu (Cognizant)" <r@x.com>'
    _patch(monkeypatch, lambda p: FakeMessage(p, to=raw))
    record = read_msg(src)
    assert record.to == [
        '"Jain; Prinse (Cognizant)" <p@x.com>',
        '"Thakur, Ritu (Cognizant)" <r@x.com>',
    ]
