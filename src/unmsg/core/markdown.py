"""HTML to Markdown conversion.

Default path is ``markdownify`` (pure Python, no system deps). Pandoc is an
optional enhancement, imported lazily only when explicitly requested and present
on PATH.
"""

from __future__ import annotations

import shutil


def to_markdown(html: str, *, use_pandoc: bool = False) -> str:
    """Convert cleaned HTML to Markdown.

    Falls back to ``markdownify`` whenever pandoc is unavailable, so a missing
    optional dependency never fails a conversion.
    """
    if not html.strip():
        return ""
    if use_pandoc and shutil.which("pandoc"):
        rendered = _via_pandoc(html)
        if rendered is not None:
            return rendered
    return _via_markdownify(html)


def _via_markdownify(html: str) -> str:
    from markdownify import markdownify as _md

    text: str = _md(html, heading_style="ATX", bullets="-")
    return _collapse_blank_lines(text).strip() + "\n"


def _via_pandoc(html: str) -> str | None:
    try:
        import pypandoc
    except ImportError:
        return None
    text: str = pypandoc.convert_text(html, "gfm", format="html")
    return _collapse_blank_lines(text).strip() + "\n"


def _collapse_blank_lines(text: str) -> str:
    out: list[str] = []
    blanks = 0
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped:
            blanks = 0
            out.append(stripped)
        else:
            blanks += 1
            if blanks <= 1:
                out.append("")
    return "\n".join(out)
