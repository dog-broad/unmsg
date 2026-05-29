"""Format writers and the registry that maps a format id to its writer."""

from __future__ import annotations

from unmsg.core.writer.base import FormatWriter, RenderContext
from unmsg.core.writer.html import HtmlWriter
from unmsg.core.writer.html_single import SingleFileHtmlWriter
from unmsg.core.writer.md import MarkdownWriter

# Format ids implemented in this milestone. Others (txt, json, eml, pdf) arrive
# in later releases and are intentionally absent rather than stubbed.
_WRITERS: dict[str, FormatWriter] = {
    w.format_id: w for w in (MarkdownWriter(), HtmlWriter(), SingleFileHtmlWriter())
}


def get_writer(format_id: str) -> FormatWriter | None:
    """Return the writer for ``format_id``, or ``None`` if not yet supported."""
    return _WRITERS.get(format_id)


def supported_formats() -> tuple[str, ...]:
    return tuple(_WRITERS)


__all__ = [
    "FormatWriter",
    "RenderContext",
    "get_writer",
    "supported_formats",
]
