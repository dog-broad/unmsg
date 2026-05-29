"""EML writer: reconstruct a faithful, self-contained RFC-822 message.

Inline images are kept as ``cid:`` references in the HTML and attached by
Content-ID so a mail client renders them; a ``text/plain`` alternative is always
present. MIME boundaries are assigned deterministically (and no Message-ID or
wall-clock Date is invented), so the bytes are stable across runs.
"""

from __future__ import annotations

from email.message import EmailMessage
from email.utils import format_datetime
from typing import ClassVar

from unmsg.core.html_cleanup import to_text
from unmsg.core.models import MsgRecord
from unmsg.core.writer.base import RenderContext


class EmlWriter:
    format_id: ClassVar[str] = "eml"
    extension: ClassVar[str] = ".eml"

    def render(self, ctx: RenderContext) -> bytes:
        message = EmailMessage()
        _set_headers(message, ctx.record)

        text_body = ctx.record.body_text.strip() or to_text(ctx.cleaned_html)
        message.set_content(text_body or "")

        if ctx.cleaned_html.strip():
            message.add_alternative(ctx.cleaned_html, subtype="html")
            _attach_inline_images(message, ctx.record)

        _attach_files(message, ctx.record)
        _make_boundaries_deterministic(message)
        return message.as_bytes()


def _set_headers(message: EmailMessage, record: MsgRecord) -> None:
    message["Subject"] = record.subject
    sender = record.sender_email or record.sender_name
    if sender:
        message["From"] = sender
    if record.to:
        message["To"] = ", ".join(record.to)
    if record.cc:
        message["Cc"] = ", ".join(record.cc)
    if record.sent_on is not None:
        message["Date"] = format_datetime(record.sent_on)


def _attach_inline_images(message: EmailMessage, record: MsgRecord) -> None:
    html_part = next(
        (p for p in message.iter_parts() if p.get_content_type() == "text/html"),
        None,
    )
    if not isinstance(html_part, EmailMessage):
        return
    for att in record.attachments:
        if not att.is_inline or att.is_nested_msg or not att.data:
            continue
        maintype, subtype = _split_mime(att.mime, fallback="image/png")
        cid = att.cid.strip().strip("<>") if att.cid else ""
        html_part.add_related(att.data, maintype, subtype, cid=f"<{cid}>")


def _attach_files(message: EmailMessage, record: MsgRecord) -> None:
    for att in record.attachments:
        if att.is_inline or att.is_nested_msg or not att.data:
            continue
        maintype, subtype = _split_mime(att.mime, fallback="application/octet-stream")
        message.add_attachment(
            att.data, maintype=maintype, subtype=subtype, filename=att.name
        )


def _split_mime(mime: str | None, *, fallback: str) -> tuple[str, str]:
    candidate = (mime or "").split(";", 1)[0].strip() or fallback
    if "/" not in candidate:
        candidate = fallback
    maintype, _, subtype = candidate.partition("/")
    return maintype, subtype or "octet-stream"


def _make_boundaries_deterministic(message: EmailMessage) -> None:
    # walk() yields parts in a stable depth-first order; numbering them gives
    # reproducible boundaries instead of the default random ones.
    for index, part in enumerate(message.walk()):
        if part.is_multipart():
            part.set_boundary(f"----=_unmsg_{index}")
