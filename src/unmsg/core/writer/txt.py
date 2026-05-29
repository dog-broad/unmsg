"""Plain-text writer: a readable header followed by the text body."""

from __future__ import annotations

from typing import ClassVar

from unmsg.core.html_cleanup import to_text
from unmsg.core.writer.base import RenderContext, meta_rows


class TextWriter:
    format_id: ClassVar[str] = "txt"
    extension: ClassVar[str] = ".txt"

    def render(self, ctx: RenderContext) -> bytes:
        record = ctx.record
        # Prefer the sender's plain-text body; many messages are HTML-only, so
        # fall back to text extracted from the HTML rather than writing nothing.
        body = record.body_text.strip() or to_text(ctx.html_body)

        lines = [f"Subject: {record.subject}".rstrip()]
        lines.extend(f"{label}: {value}" for label, value in meta_rows(record))
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
        lines.append(body)
        document = "\n".join(lines).rstrip() + "\n"
        return document.encode("utf-8")
