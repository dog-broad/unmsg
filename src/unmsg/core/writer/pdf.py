"""PDF writer (optional ``[pdf]`` extra).

Renders the message's HTML to PDF with xhtml2pdf/reportlab — pure Python, no
system dependencies. reportlab's invariant mode is enabled so the bytes are
reproducible (no embedded creation date or random document id). Inline images
are embedded as data URIs so the PDF is self-contained. The heavy import is
lazy: importing this module never pulls in reportlab.
"""

from __future__ import annotations

import io
from typing import Any, ClassVar

from unmsg.core.writer.base import (
    RenderContext,
    WriterUnavailable,
    build_html_document,
    inline_assets,
)


class PdfWriter:
    format_id: ClassVar[str] = "pdf"
    extension: ClassVar[str] = ".pdf"

    def render(self, ctx: RenderContext) -> bytes:
        pisa = _load_backend()
        document = inline_assets(
            build_html_document(ctx.record, ctx.html_body), ctx.assets
        )
        buffer = io.BytesIO()
        pisa.CreatePDF(document, dest=buffer, encoding="utf-8")
        return buffer.getvalue()


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
