"""Attachment planning: inline vs regular, modes, size cap, dedupe, nesting."""

from __future__ import annotations

from dataclasses import replace

from unmsg.core.attachments import plan_attachments
from unmsg.core.models import Attachment
from unmsg.core.options import ConvertOptions


def test_inline_extracted_to_assets_with_cid_map(inline_image):
    plan = plan_attachments([inline_image], ConvertOptions())
    assert plan.inline_paths == ["assets/inline_image_1.png"]
    assert plan.cid_map["image001"] == "assets/inline_image_1.png"
    assert plan.files["assets/inline_image_1.png"] == inline_image.data


def test_inline_base64_mode_yields_data_uri(inline_image):
    plan = plan_attachments([inline_image], ConvertOptions(inline_images="base64"))
    assert plan.cid_map["image001"].startswith("data:image/png;base64,")
    assert not plan.inline_paths


def test_inline_skip_mode_drops_image(inline_image):
    plan = plan_attachments([inline_image], ConvertOptions(inline_images="skip"))
    assert not plan.files
    assert not plan.cid_map


def test_regular_attachment_saved(file_attachment):
    plan = plan_attachments([file_attachment], ConvertOptions())
    assert plan.regular_paths == ["attachments/budget.pdf"]


def test_regular_skipped_when_disabled(file_attachment):
    plan = plan_attachments([file_attachment], ConvertOptions(attachments=False))
    assert not plan.regular_paths


def test_size_cap_skips_with_warning(file_attachment):
    big = replace(file_attachment, size=10**9)
    plan = plan_attachments([big], ConvertOptions(max_attachment_bytes=1024))
    assert not plan.regular_paths
    assert plan.warnings


def test_duplicate_names_deduped():
    a = Attachment("doc.pdf", b"a", "application/pdf", None, 1)
    b = Attachment("doc.pdf", b"b", "application/pdf", None, 1)
    plan = plan_attachments([a, b], ConvertOptions())
    assert plan.regular_paths == ["attachments/doc.pdf", "attachments/doc_1.pdf"]


def test_nested_msg_attachment_skipped_here():
    nested = Attachment(
        "mail.msg", b"", "application/vnd.ms-outlook", None, 0, is_nested_msg=True
    )
    plan = plan_attachments([nested], ConvertOptions())
    assert not plan.files


def test_unnamed_attachment_gets_extension_from_mime():
    att = Attachment("", b"\x89PNG", "image/png", None, 4)
    plan = plan_attachments([att], ConvertOptions())
    assert plan.regular_paths[0].endswith(".png")
