"""Writer protocol and shared rendering helpers.

Writers are pure: each turns a :class:`RenderContext` into ``bytes``. The
pipeline owns the actual disk writes, so writers stay trivially testable and
deterministic. Output is always UTF-8 with ``\\n`` line endings — never the
platform default — so bytes match across machines.
"""

from __future__ import annotations

import base64
import html as _html
import mimetypes
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Protocol, runtime_checkable

from unmsg.core.models import MsgRecord


class WriterUnavailable(RuntimeError):
    """Raised when a format's optional dependency isn't installed.

    The message is user-facing; the pipeline surfaces it as a per-format warning
    rather than failing the whole conversion.
    """


@dataclass(slots=True, frozen=True)
class RenderContext:
    record: MsgRecord
    markdown_body: str
    html_body: str  # cleaned + cid-rewritten; asset refs are relative
    assets: dict[str, bytes]  # relpath -> bytes, for single-file inlining
    cleaned_html: str = ""  # cleaned but cid: refs preserved (for the EML writer)


@runtime_checkable
class FormatWriter(Protocol):
    format_id: ClassVar[str]
    extension: ClassVar[str]

    def render(self, ctx: RenderContext) -> bytes: ...


def _iso(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else ""


def _addr(name: str, email: str) -> str:
    name, email = name.strip(), email.strip()
    if name and email:
        return f"{name} <{email}>"
    return email or name


def front_matter(record: MsgRecord) -> str:
    """A deterministic YAML front-matter block (fixed key order)."""
    fields: list[tuple[str, str]] = [
        ("subject", record.subject),
        ("from", _addr(record.sender_name, record.sender_email)),
        ("to", "; ".join(record.to)),
        ("cc", "; ".join(record.cc)),
        ("date", _iso(record.sent_on)),
        ("received", _iso(record.received_on)),
        ("is_meeting", "true" if record.is_meeting else "false"),
        ("is_signed", "true" if record.is_signed else "false"),
        ("attachments", str(len(record.attachments))),
    ]
    lines = ["---"]
    for key, value in fields:
        lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _yaml_scalar(value: str) -> str:
    if value in ("true", "false") or value.isdigit():
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return f'"{escaped}"'


def meta_rows(record: MsgRecord) -> list[tuple[str, str]]:
    rows = [
        ("From", _addr(record.sender_name, record.sender_email)),
        ("To", "; ".join(record.to)),
    ]
    if record.cc:
        rows.append(("Cc", "; ".join(record.cc)))
    if record.sent_on:
        rows.append(("Date", _iso(record.sent_on)))
    return rows


def inline_assets(document: str, assets: dict[str, bytes]) -> str:
    """Replace relative ``src="<relpath>"`` references with ``data:`` URIs."""
    for relpath, data in assets.items():
        mime = mimetypes.guess_type(relpath)[0] or "application/octet-stream"
        uri = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        for quote in ('"', "'"):
            document = document.replace(
                f"src={quote}{relpath}{quote}", f"src={quote}{uri}{quote}"
            )
    return document


def build_html_document(record: MsgRecord, body: str) -> str:
    """Assemble a standalone, readable HTML document (relative asset refs)."""
    safe_subject = _html.escape(record.subject or "(no subject)")
    rows = "\n".join(
        f"      <tr><th>{_html.escape(k)}</th><td>{_html.escape(v)}</td></tr>"
        for k, v in meta_rows(record)
    )
    content = body.strip() or f"<pre>{_html.escape(record.body_text)}</pre>"
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        f"  <title>{safe_subject}</title>\n"
        "  <style>\n"
        "    body { font-family: system-ui, sans-serif; line-height: 1.5;\n"
        "      max-width: 50rem; margin: 2rem auto; padding: 0 1rem; }\n"
        "    table.meta { border-collapse: collapse; margin-bottom: 1.5rem; }\n"
        "    table.meta th { text-align: left; padding-right: 1rem;\n"
        "      vertical-align: top; color: #5c6370; font-weight: 600; }\n"
        "    hr { border: none; border-top: 1px solid #e4e2dc; }\n"
        "  </style>\n</head>\n<body>\n"
        f"  <h1>{safe_subject}</h1>\n"
        f'  <table class="meta">\n{rows}\n  </table>\n'
        "  <hr>\n"
        f"  <article>\n{content}\n  </article>\n"
        "</body>\n</html>\n"
    )
