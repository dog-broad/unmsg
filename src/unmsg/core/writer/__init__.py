"""Format writers and the registry that maps a format id to its writer."""

from __future__ import annotations

from unmsg.core.writer.base import FormatWriter, RenderContext
from unmsg.core.writer.eml import EmlWriter
from unmsg.core.writer.html import HtmlWriter
from unmsg.core.writer.html_single import SingleFileHtmlWriter
from unmsg.core.writer.json_meta import JsonMetadataWriter
from unmsg.core.writer.md import MarkdownWriter
from unmsg.core.writer.txt import TextWriter

# Implemented format ids. PDF arrives in a later release and is intentionally
# absent rather than stubbed.
_WRITERS: dict[str, FormatWriter] = {
    w.format_id: w
    for w in (
        MarkdownWriter(),
        HtmlWriter(),
        SingleFileHtmlWriter(),
        TextWriter(),
        JsonMetadataWriter(),
        EmlWriter(),
    )
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
