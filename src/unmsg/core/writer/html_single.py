"""Single-file HTML writer: one portable document, images inlined as base64.

Reuses the standard HTML document, then replaces relative asset references with
``data:`` URIs from the rendered assets so the file stands alone.
"""

from __future__ import annotations

import base64
import mimetypes
from typing import ClassVar

from unmsg.core.writer.base import RenderContext, build_html_document


class SingleFileHtmlWriter:
    format_id: ClassVar[str] = "html_single"
    extension: ClassVar[str] = ".single.html"

    def render(self, ctx: RenderContext) -> bytes:
        document = build_html_document(ctx.record, ctx.html_body)
        document = _inline_assets(document, ctx.assets)
        return document.encode("utf-8")


def _inline_assets(document: str, assets: dict[str, bytes]) -> str:
    for relpath, data in assets.items():
        uri = _data_uri(relpath, data)
        for quote in ('"', "'"):
            document = document.replace(
                f"src={quote}{relpath}{quote}", f"src={quote}{uri}{quote}"
            )
    return document


def _data_uri(relpath: str, data: bytes) -> str:
    mime = mimetypes.guess_type(relpath)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
