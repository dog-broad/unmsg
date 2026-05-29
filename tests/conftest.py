"""Shared test fixtures and factories."""

from __future__ import annotations

import base64
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from unmsg.core.models import Attachment, MsgRecord

# A real 1x1 PNG, so inline-image handling is exercised with valid bytes.
PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA"
    "60e6kgAAAABJRU5ErkJggg=="
)

SENT = datetime(2024, 3, 15, 9, 32, 0, tzinfo=UTC)


def _record(**over: object) -> MsgRecord:
    base: dict[str, object] = {
        "subject": "Quarterly Report",
        "sender_name": "Alice Example",
        "sender_email": "alice@example.com",
        "to": ["bob@example.com"],
        "cc": [],
        "bcc": [],
        "sent_on": SENT,
        "received_on": None,
        "headers": "From: alice@example.com",
        "body_text": "Hello Bob",
        "body_html": "<html><body><p>Hello <b>Bob</b></p></body></html>",
        "attachments": [],
        "nested": [],
        "is_meeting": False,
        "is_signed": False,
        "raw_path": Path("Quarterly Report.msg"),
    }
    base.update(over)
    return MsgRecord(**base)  # type: ignore[arg-type]


@pytest.fixture
def make_record() -> Callable[..., MsgRecord]:
    return _record


@pytest.fixture
def inline_image() -> Attachment:
    return Attachment(
        name="logo.png",
        data=PNG_1x1,
        mime="image/png",
        cid="image001",
        size=len(PNG_1x1),
        is_nested_msg=False,
    )


@pytest.fixture
def file_attachment() -> Attachment:
    data = b"%PDF-1.4 fake"
    return Attachment(
        name="budget.pdf",
        data=data,
        mime="application/pdf",
        cid=None,
        size=len(data),
        is_nested_msg=False,
    )
