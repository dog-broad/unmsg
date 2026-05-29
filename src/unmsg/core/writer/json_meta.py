"""JSON metadata writer: a stable, machine-readable sidecar.

Keys are written in a fixed order and dates as ISO-8601 UTC, so the output is
byte-stable across runs and machines.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import ClassVar

from unmsg.core.models import MsgRecord
from unmsg.core.writer.base import RenderContext


class JsonMetadataWriter:
    format_id: ClassVar[str] = "json"
    extension: ClassVar[str] = ".metadata.json"

    def render(self, ctx: RenderContext) -> bytes:
        payload = _metadata(ctx.record)
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        return (text + "\n").encode("utf-8")


def _iso(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ") if value else None


def _metadata(record: MsgRecord) -> dict[str, object]:
    return {
        "subject": record.subject,
        "from": {"name": record.sender_name, "email": record.sender_email},
        "to": record.to,
        "cc": record.cc,
        "bcc": record.bcc,
        "sent_on": _iso(record.sent_on),
        "received_on": _iso(record.received_on),
        "is_meeting": record.is_meeting,
        "is_signed": record.is_signed,
        "attachments": [
            {
                "name": att.name,
                "mime": att.mime,
                "size": att.size,
                "inline": att.is_inline,
                "embedded_message": att.is_nested_msg,
            }
            for att in record.attachments
        ],
        "nested_messages": len(record.nested),
    }
