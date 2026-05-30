"""Read an Outlook ``.msg`` file into a :class:`MsgRecord`.

``extract-msg`` is imported lazily inside :func:`read_msg` so that importing
``unmsg.core`` (and the pure transforms) stays light and does not hard-require
the parser. Field access is defensive: the library's surface has drifted across
versions, so we prefer ``getattr`` with sane fallbacks over brittle attribute
chains. Embedded messages (``.msg`` inside ``.msg``) are parsed recursively.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Any

from unmsg.core.models import Attachment, MsgRecord

_MAX_READ_DEPTH = 5


def read_msg(path: Path | str) -> MsgRecord:
    """Parse ``path`` into a normalised :class:`MsgRecord`."""
    import extract_msg

    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(src)
    message = extract_msg.Message(str(src))  # type: ignore[no-untyped-call,unused-ignore]
    try:
        return _record_from_message(message, src, depth=0)
    finally:
        _safe_close(message)


def _record_from_message(message: Any, path: Path, *, depth: int) -> MsgRecord:
    sender_name, sender_email = parseaddr(_text(getattr(message, "sender", "")))
    attachments, nested = _collect_attachments(message, path, depth)

    return MsgRecord(
        subject=_text(getattr(message, "subject", "")),
        sender_name=sender_name,
        sender_email=sender_email,
        to=_split_addresses(getattr(message, "to", "")),
        cc=_split_addresses(getattr(message, "cc", "")),
        bcc=_split_addresses(getattr(message, "bcc", "")),
        sent_on=_to_utc(getattr(message, "date", None)),
        received_on=None,
        headers=_text(getattr(message, "header", "")),
        body_text=_text(getattr(message, "body", "")),
        body_html=_decode(getattr(message, "htmlBody", None)),
        attachments=attachments,
        nested=nested,
        is_meeting=_is_meeting(message),
        is_signed=_is_signed(message),
        raw_path=path,
    )


def _collect_attachments(
    message: Any, path: Path, depth: int
) -> tuple[list[Attachment], list[MsgRecord]]:
    attachments: list[Attachment] = []
    nested: list[MsgRecord] = []

    for att in getattr(message, "attachments", []) or []:
        embedded = _embedded_message(att)
        if embedded is not None:
            if depth < _MAX_READ_DEPTH:
                nested.append(_record_from_message(embedded, path, depth=depth + 1))
            attachments.append(_nested_marker(att))
            continue
        data = att.data if isinstance(getattr(att, "data", None), bytes) else b""
        name = _attachment_filename(att)
        attachments.append(
            Attachment(
                name=name,
                data=data,
                mime=_mime_of(att),
                cid=_cid_of(att),
                size=len(data),
                is_nested_msg=False,
            )
        )

    return attachments, nested


def _embedded_message(att: Any) -> Any | None:
    data = getattr(att, "data", None)
    if data is not None and data.__class__.__name__ in {"Message", "MessageBase"}:
        return data
    if str(getattr(att, "type", "")).lower() == "msg":
        return data
    return None


def _nested_marker(att: Any) -> Attachment:
    name = _attachment_filename(att) or "embedded-message"
    if not name.lower().endswith(".msg"):
        name = f"{name}.msg"
    return Attachment(
        name=name,
        data=b"",
        mime="application/vnd.ms-outlook",
        cid=None,
        size=0,
        is_nested_msg=True,
    )


def _attachment_filename(att: Any) -> str:
    for attr in ("longFilename", "shortFilename"):
        value = getattr(att, attr, None)
        if value:
            return _text(value)
    getter = getattr(att, "getFilename", None)
    if callable(getter):
        try:
            return _text(getter())
        except Exception:
            return ""
    return ""


def _cid_of(att: Any) -> str | None:
    for attr in ("cid", "contentId", "contendId"):
        value = getattr(att, attr, None)
        if value:
            return _text(value)
    return None


def _mime_of(att: Any) -> str | None:
    value = getattr(att, "mimetype", None) or getattr(att, "mime", None)
    return _text(value) if value else None


def _is_meeting(message: Any) -> bool:
    return (
        "ipm.appointment" in _text(getattr(message, "classType", "")).lower()
        or "meeting" in _text(getattr(message, "classType", "")).lower()
    )


def _is_signed(message: Any) -> bool:
    marker = _text(getattr(message, "classType", "")).lower()
    return "signed" in marker or "smime" in marker


def _to_utc(value: object) -> datetime | None:
    # extract-msg may hand back a datetime or an RFC-2822 string ("Wed, 13 May
    # 2026 01:02:16 +0530"); accept both.
    if isinstance(value, str):
        value = _parse_date(value)
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_date(text: str) -> datetime | None:
    text = text.strip()
    if not text:
        return None
    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None


def _split_addresses(value: object) -> list[str]:
    # Quote-aware split: separators (';' ',' newline) only count outside double
    # quotes, because a display name like "Jain, Prinse (Cognizant)" carries the
    # separator character inside the quoted name.
    text = _text(value)
    parts: list[str] = []
    buffer: list[str] = []
    in_quotes = False
    for char in text:
        if char == '"':
            in_quotes = not in_quotes
            buffer.append(char)
        elif char in ";,\r\n" and not in_quotes:
            parts.append("".join(buffer))
            buffer = []
        else:
            buffer.append(char)
    parts.append("".join(buffer))
    return [part.strip() for part in parts if part.strip()]


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return _decode(value)
    return _strip_nulls(str(value))


def _decode(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _strip_nulls(value)
    if isinstance(value, bytes):
        for encoding in ("utf-8", "cp1252", "latin-1"):
            try:
                return _strip_nulls(value.decode(encoding))
            except UnicodeDecodeError:
                continue
        return _strip_nulls(value.decode("utf-8", errors="replace"))
    return _strip_nulls(str(value))


def _strip_nulls(text: str) -> str:
    # MSG string streams often carry a trailing NUL; a NUL anywhere in a name
    # would also crash any file write. Remove them everywhere.
    return text.replace("\x00", "")


def _safe_close(message: Any) -> None:
    closer = getattr(message, "close", None)
    if callable(closer):
        with contextlib.suppress(Exception):
            closer()
