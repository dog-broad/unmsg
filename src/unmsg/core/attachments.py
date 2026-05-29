"""Plan where a message's attachments and inline images go.

This module is pure: it computes a plan (relative paths to bytes, plus the
``cid`` rewrite map) without touching disk. The pipeline performs the writes.
Inline images are numbered by order of appearance, so numbering is stable.
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, field

from unmsg.core.models import Attachment
from unmsg.core.naming import attachment_name
from unmsg.core.options import ConvertOptions

ASSETS_DIR = "assets"
ATTACHMENTS_DIR = "attachments"


@dataclass(slots=True)
class AttachmentPlan:
    files: dict[str, bytes] = field(default_factory=dict)
    cid_map: dict[str, str] = field(default_factory=dict)
    inline_paths: list[str] = field(default_factory=list)
    regular_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _ext_for(att: Attachment) -> str:
    _, _, ext = att.name.rpartition(".")
    if ext and att.name != ext and len(ext) <= 8:
        return f".{ext.lower()}"
    if att.mime:
        guessed = mimetypes.guess_extension(att.mime.split(";", 1)[0].strip())
        if guessed:
            return guessed
    return ".bin"


def plan_attachments(
    attachments: list[Attachment], options: ConvertOptions
) -> AttachmentPlan:
    plan = AttachmentPlan()
    inline_index = 0
    regular_index = 0
    used_names: set[str] = set()

    for att in attachments:
        if att.is_nested_msg:
            continue  # embedded messages are converted recursively by the pipeline
        if att.size > options.max_attachment_bytes:
            plan.warnings.append(
                f"Skipped a large attachment ({att.size} bytes) to stay within "
                "the size cap."
            )
            continue

        if att.is_inline:
            _plan_inline(att, options, plan, inline_index)
            if options.inline_images != "skip":
                inline_index += 1
        else:
            if not options.attachments:
                continue
            regular_index += 1
            _plan_regular(att, plan, regular_index, used_names)

    return plan


def _plan_inline(
    att: Attachment, options: ConvertOptions, plan: AttachmentPlan, index: int
) -> None:
    if options.inline_images == "skip":
        return
    assert att.cid is not None
    cid_key = att.cid.strip().strip("<>")
    if options.inline_images == "base64":
        mime = att.mime or "application/octet-stream"
        encoded = base64.b64encode(att.data).decode("ascii")
        plan.cid_map[cid_key] = f"data:{mime};base64,{encoded}"
        return
    relpath = f"{ASSETS_DIR}/inline_image_{index + 1}{_ext_for(att)}"
    plan.files[relpath] = att.data
    plan.inline_paths.append(relpath)
    plan.cid_map[cid_key] = relpath


def _plan_regular(
    att: Attachment, plan: AttachmentPlan, index: int, used: set[str]
) -> None:
    name = attachment_name(att.name, index=index, fallback_ext=_ext_for(att))
    name = _dedupe(name, used)
    used.add(name.lower())
    relpath = f"{ATTACHMENTS_DIR}/{name}"
    plan.files[relpath] = att.data
    plan.regular_paths.append(relpath)


def _dedupe(name: str, used: set[str]) -> str:
    if name.lower() not in used:
        return name
    stem, dot, ext = name.rpartition(".")
    base, suffix = (stem, f".{ext}") if dot else (name, "")
    n = 1
    while f"{base}_{n}{suffix}".lower() in used:
        n += 1
    return f"{base}_{n}{suffix}"
