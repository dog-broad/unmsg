"""Markdown writer: YAML front-matter + the converted body."""

from __future__ import annotations

from typing import ClassVar

from unmsg.core.writer.base import RenderContext, front_matter


class MarkdownWriter:
    format_id: ClassVar[str] = "md"
    extension: ClassVar[str] = ".md"

    def render(self, ctx: RenderContext) -> bytes:
        document = front_matter(ctx.record) + "\n" + ctx.markdown_body
        if not document.endswith("\n"):
            document += "\n"
        return document.encode("utf-8")
