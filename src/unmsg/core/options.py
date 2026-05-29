"""Conversion options.

A plain frozen dataclass — no pydantic in the core hot path. The application
layer validates user/config input and constructs this.
"""

from __future__ import annotations

from dataclasses import dataclass

from unmsg.core.models import FormatId, InlineMode, OnConflict

DEFAULT_FORMATS: tuple[FormatId, ...] = ("md", "html")
DEFAULT_MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024  # 50 MB, per-attachment cap


@dataclass(slots=True, frozen=True)
class ConvertOptions:
    formats: tuple[FormatId, ...] = DEFAULT_FORMATS
    attachments: bool = True
    inline_images: InlineMode = "extract"
    on_conflict: OnConflict = "rename"
    naming_template: str = "{date}_{subject}"
    max_attachment_bytes: int = DEFAULT_MAX_ATTACHMENT_BYTES
    use_pandoc: bool = False
