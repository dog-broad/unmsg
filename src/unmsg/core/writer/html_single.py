"""Single-file HTML writer: one portable document, images inlined as base64."""

from __future__ import annotations

from typing import ClassVar

from unmsg.core.writer.base import RenderContext, build_html_document, inline_assets


class SingleFileHtmlWriter:
    format_id: ClassVar[str] = "html_single"
    extension: ClassVar[str] = ".single.html"

    def render(self, ctx: RenderContext) -> bytes:
        document = build_html_document(ctx.record, ctx.html_body)
        document = inline_assets(document, ctx.assets)
        return document.encode("utf-8")
