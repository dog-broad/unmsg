"""Core data shapes.

These dataclasses carry data between the reader, the transforms, and the
writers. They hold no behaviour and have no IO — pure shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

Status = Literal["success", "warning", "failed"]
FormatId = Literal["md", "html", "html_single", "txt", "json", "eml", "pdf"]
InlineMode = Literal["extract", "base64", "skip"]
OnConflict = Literal["rename", "overwrite", "skip"]


@dataclass(slots=True, frozen=True)
class Attachment:
    """A file or inline image carried by a message.

    ``data`` holds the full bytes short-term. ``cid`` is set for inline images
    referenced from the HTML body. ``is_nested_msg`` marks an embedded ``.msg``
    (an email attached to an email); such attachments are parsed recursively
    into :attr:`MsgRecord.nested`.
    """

    name: str
    data: bytes
    mime: str | None
    cid: str | None
    size: int
    is_nested_msg: bool = False

    @property
    def is_inline(self) -> bool:
        return self.cid is not None


@dataclass(slots=True)
class MsgRecord:
    """A parsed message, normalised and ready to render.

    ``sent_on`` / ``received_on`` are timezone-aware and normalised to UTC so
    output is identical regardless of the converting machine's locale.
    """

    subject: str
    sender_name: str
    sender_email: str
    to: list[str]
    cc: list[str]
    bcc: list[str]
    sent_on: datetime | None
    received_on: datetime | None
    headers: str
    body_text: str
    body_html: str
    attachments: list[Attachment]
    nested: list[MsgRecord]
    is_meeting: bool
    is_signed: bool
    raw_path: Path


@dataclass(slots=True)
class ConvertResult:
    """The outcome of converting one message.

    ``error`` is already humanised — safe to show a user. Raw exception text
    belongs only in the DEBUG log, never here.
    """

    source: Path
    bundle_dir: Path | None
    output_paths: list[Path]
    attachments_saved: list[Path]
    inline_images_saved: list[Path]
    status: Status
    warnings: list[str]
    error: str | None
    duration_ms: int
    sha256: dict[Path, str] = field(default_factory=dict)
