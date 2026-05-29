"""Safe, deterministic names for output folders, files, and attachments.

Filenames coming from a message are never trusted: they are sanitised against
path traversal, reserved device names, control characters, and length before
anything is written. Output names are a pure function of the message and the
template, so the same input always produces the same names.
"""

from __future__ import annotations

import hashlib
import re

from unmsg.core.models import MsgRecord

# Windows reserved device names (case-insensitive), with or without extension.
_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}

_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WS = re.compile(r"\s+")

# Conservative per-component cap. The full path is budgeted separately so the
# deepest output (bundle/<stem>.metadata.json) stays under the platform limit.
MAX_COMPONENT = 80
# Stay well under Windows MAX_PATH (260) without relying on extended-length
# paths, which are not a portable guarantee.
MAX_PATH_BUDGET = 240


def sanitize_component(raw: str, *, fallback: str = "untitled") -> str:
    """Make ``raw`` safe to use as a single path component.

    Strips illegal characters, collapses whitespace, removes a reserved-name
    clash, and trims trailing dots/spaces (which Windows silently drops).
    """
    text = _ILLEGAL.sub(" ", raw)
    text = _WS.sub(" ", text).strip()
    text = text.strip(". ")
    if not text:
        return fallback
    if text.lower() in _RESERVED or text.split(".", 1)[0].lower() in _RESERVED:
        text = f"_{text}"
    if len(text) > MAX_COMPONENT:
        text = _truncate_keeping_ext(text, MAX_COMPONENT)
    return text


def _truncate_keeping_ext(name: str, limit: int) -> str:
    """Truncate ``name`` to ``limit`` chars, preserving a short extension and
    appending a short content hash so distinct long names don't collide."""
    if len(name) <= limit:
        return name
    stem, dot, ext = name.rpartition(".")
    has_ext = bool(dot) and 0 < len(ext) <= 8 and stem != ""
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:8]
    suffix = f"~{digest}"
    if has_ext:
        keep = max(1, limit - len(suffix) - len(ext) - 1)
        return f"{stem[:keep]}{suffix}.{ext}"
    keep = max(1, limit - len(suffix))
    return f"{name[:keep]}{suffix}"


def _short_hash(record: MsgRecord) -> str:
    """A stable 8-char hash of identifying fields — deterministic, no clock."""
    when = record.sent_on or record.received_on
    basis = "␟".join(
        [
            record.subject,
            record.sender_email,
            when.isoformat() if when else "",
            str(len(record.body_text) + len(record.body_html)),
        ]
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:8]


def _tokens(record: MsgRecord) -> dict[str, str]:
    when = record.sent_on or record.received_on
    digest = _short_hash(record)
    return {
        "date": when.strftime("%Y-%m-%d") if when else "undated",
        "time": when.strftime("%H%M%S") if when else "000000",
        "subject": record.subject.strip() or "no-subject",
        "from_name": record.sender_name.strip() or "unknown",
        "from_email": record.sender_email.strip() or "unknown",
        "hash": digest,
        "guid": digest,
    }


def stem_for(record: MsgRecord, template: str) -> str:
    """Expand ``template`` against the record and sanitise the result.

    Unknown tokens are left literal (minus the braces) rather than raising, so
    a user typo degrades gracefully instead of failing a batch.
    """
    tokens = _tokens(record)

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return tokens.get(key, key)

    expanded = re.sub(r"\{(\w+)\}", repl, template)
    return sanitize_component(expanded, fallback=tokens["hash"])


def attachment_name(raw: str, *, index: int, fallback_ext: str = "") -> str:
    """Sanitise an attachment's own filename; fall back to a numbered name."""
    safe = sanitize_component(raw, fallback="")
    if safe:
        return safe
    ext = (
        fallback_ext
        if fallback_ext.startswith(".")
        else (f".{fallback_ext}" if fallback_ext else "")
    )
    return f"attachment_{index}{ext}"


def fit_within_budget(root_len: int, stem: str, longest_ext: str) -> str:
    """Shrink ``stem`` so ``root/stem/stem<longest_ext>`` fits the path budget.

    Accounts for the bundle directory and the longest filename written inside
    it. Truncation is deterministic (a content hash is appended).
    """
    # root_len + sep + stem + sep + stem + longest_ext
    overhead = root_len + 2 + len(longest_ext)
    allowed = MAX_PATH_BUDGET - overhead
    per_component = max(1, allowed // 2)
    if len(stem) <= per_component:
        return stem
    return _truncate_keeping_ext(stem, per_component)
