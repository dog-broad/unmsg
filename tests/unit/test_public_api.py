"""Pin the public API surface.

These tests are the contract for what `import unmsg` exposes. Adding a new
public name requires updating both ``__all__`` and the assertion here so the
change is visible in code review.
"""

from __future__ import annotations

import inspect

import unmsg

EXPECTED_PUBLIC = {
    "Attachment",
    "ConvertOptions",
    "ConvertResult",
    "MsgRecord",
    "__version__",
    "convert_batch",
    "convert_file",
}


def test_public_surface_is_frozen():
    assert set(unmsg.__all__) == EXPECTED_PUBLIC


def test_all_names_are_importable():
    for name in EXPECTED_PUBLIC:
        assert hasattr(unmsg, name), name


def test_convert_file_signature_is_stable():
    params = list(inspect.signature(unmsg.convert_file).parameters)
    assert params[:3] == ["source", "out_root", "options"]


def test_convert_batch_signature_is_stable():
    params = list(inspect.signature(unmsg.convert_batch).parameters)
    assert params[:3] == ["sources", "out_root", "options"]


def test_dataclasses_have_expected_fields():
    """Public data models keep their named fields between releases.

    New optional fields may be added at the tail; existing ones must stay.
    """
    import dataclasses

    must_have: dict[type, set[str]] = {
        unmsg.Attachment: {"name", "data", "mime", "cid", "size"},
        unmsg.ConvertResult: {
            "source",
            "bundle_dir",
            "output_paths",
            "attachments_saved",
            "inline_images_saved",
            "status",
            "warnings",
            "error",
            "duration_ms",
        },
        unmsg.MsgRecord: {"subject", "sender_name", "sender_email"},
        unmsg.ConvertOptions: {"formats", "naming_template", "on_conflict"},
    }
    for cls, required in must_have.items():
        actual = {f.name for f in dataclasses.fields(cls)}
        missing = required - actual
        assert not missing, f"{cls.__name__} missing fields: {missing}"


def test_version_is_string():
    assert isinstance(unmsg.__version__, str)
    assert unmsg.__version__.count(".") >= 1
