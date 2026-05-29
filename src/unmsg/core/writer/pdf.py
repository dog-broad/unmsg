"""PDF writer (optional ``[pdf]`` extra).

Renders the message to PDF with xhtml2pdf/reportlab — pure Python, no system
dependencies. The message HTML is reduced to plain, valid markup first
(Outlook's CSS, e.g. ``currentcolor``, defeats simple PDF engines), then styled
with a small print stylesheet. reportlab's invariant mode is enabled so the
bytes are reproducible. The heavy import is lazy: importing this module never
pulls in reportlab.
"""

from __future__ import annotations

import html as _html
import io
from typing import Any, ClassVar

from unmsg.core.html_cleanup import strip_presentation, to_text
from unmsg.core.writer.base import (
    RenderContext,
    WriterUnavailable,
    inline_assets,
    meta_rows,
)

_STYLE = (
    "body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; }"
    "h1 { font-size: 16pt; }"
    "table.meta td { padding-right: 10pt; color: #555555; }"
    "hr { border: 0; border-top: 1px solid #cccccc; }"
    "table { border-collapse: collapse; }"
    "td, th { border: 1px solid #999999; padding: 3pt; }"
)


class PdfWriter:
    format_id: ClassVar[str] = "pdf"
    extension: ClassVar[str] = ".pdf"

    def render(self, ctx: RenderContext) -> bytes:
        pisa = _load_backend()
        document = inline_assets(_pdf_document(ctx), ctx.assets)
        buffer = io.BytesIO()
        pisa.CreatePDF(document, dest=buffer, encoding="utf-8")
        return buffer.getvalue()


def _pdf_document(ctx: RenderContext) -> str:
    record = ctx.record
    body = strip_presentation(ctx.html_body)
    if not body.strip():
        body = (
            f"<pre>{_html.escape(record.body_text or to_text(ctx.cleaned_html))}</pre>"
        )
    rows = "".join(
        f"<tr><td>{_html.escape(label)}</td><td>{_html.escape(value)}</td></tr>"
        for label, value in meta_rows(record)
    )
    subject = _html.escape(record.subject or "(no subject)")
    return (
        "<html><head><style>"
        f"{_STYLE}"
        "</style></head><body>"
        f"<h1>{subject}</h1>"
        f'<table class="meta">{rows}</table><hr/>'
        f"{body}"
        "</body></html>"
    )


def _load_backend() -> Any:
    try:
        import reportlab.rl_config as rl_config
        from xhtml2pdf import pisa
    except ImportError as exc:
        raise WriterUnavailable(
            "PDF output needs the optional 'pdf' feature — install unmsg[pdf]."
        ) from exc
    # Reproducible PDFs: fixed dates and document id instead of wall-clock/random.
    rl_config.invariant = 1
    return pisa
