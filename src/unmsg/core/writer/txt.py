"""Plain-text writer: a readable header followed by the text body."""

from __future__ import annotations

from typing import ClassVar

from unmsg.core.writer.base import RenderContext, meta_rows


class TextWriter:
    format_id: ClassVar[str] = "txt"
    extension: ClassVar[str] = ".txt"

    def render(self, ctx: RenderContext) -> bytes:
        record = ctx.record
        lines = [f"Subject: {record.subject}".rstrip()]
        lines.extend(f"{label}: {value}" for label, value in meta_rows(record))
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
        lines.append(record.body_text.strip())
        document = "\n".join(lines).rstrip() + "\n"
        return document.encode("utf-8")
