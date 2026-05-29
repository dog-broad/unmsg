"""HTML writer: a standalone document with relative asset references."""

from __future__ import annotations

from typing import ClassVar

from unmsg.core.writer.base import RenderContext, build_html_document


class HtmlWriter:
    format_id: ClassVar[str] = "html"
    extension: ClassVar[str] = ".html"

    def render(self, ctx: RenderContext) -> bytes:
        return build_html_document(ctx.record, ctx.html_body).encode("utf-8")
