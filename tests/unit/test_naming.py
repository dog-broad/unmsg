"""Naming: sanitisation, templates, traversal defense, length budgeting."""

from __future__ import annotations

from datetime import UTC, datetime

from unmsg.core.naming import (
    MAX_COMPONENT,
    attachment_name,
    fit_within_budget,
    sanitize_component,
    stem_for,
)


def test_sanitize_strips_path_separators_and_traversal():
    assert "/" not in sanitize_component("../../etc/passwd")
    assert "\\" not in sanitize_component("..\\..\\windows\\system32")


def test_sanitize_handles_reserved_device_names():
    assert sanitize_component("CON") == "_CON"
    assert sanitize_component("nul.txt").startswith("_")


def test_sanitize_trims_trailing_dots_and_spaces():
    assert sanitize_component("report. ") == "report"


def test_sanitize_empty_falls_back():
    assert sanitize_component("   ", fallback="x") == "x"
    assert sanitize_component('<>:"/\\|?*') == "untitled"


def test_sanitize_truncates_long_names_keeping_hash():
    out = sanitize_component("A" * 300)
    assert len(out) <= MAX_COMPONENT
    assert "~" in out


def test_stem_uses_date_and_subject(make_record):
    stem = stem_for(make_record(), "{date}_{subject}")
    assert stem == "2024-03-15_Quarterly Report"


def test_stem_empty_subject_falls_back(make_record):
    stem = stem_for(make_record(subject=""), "{date}_{subject}")
    assert stem == "2024-03-15_no-subject"


def test_stem_undated_when_no_dates(make_record):
    stem = stem_for(make_record(sent_on=None, received_on=None), "{date}_{subject}")
    assert stem.startswith("undated_")


def test_stem_unknown_token_is_literal(make_record):
    assert "bogus" in stem_for(make_record(), "{bogus}_{subject}")


def test_stem_hash_is_deterministic(make_record):
    a = stem_for(make_record(), "{hash}")
    b = stem_for(make_record(), "{hash}")
    assert a == b and len(a) == 8


def test_stem_hash_differs_with_received_only(make_record):
    r = make_record(sent_on=None, received_on=datetime(2024, 1, 1, tzinfo=UTC))
    assert stem_for(r, "{date}") == "2024-01-01"


def test_attachment_name_sanitised_or_numbered():
    assert attachment_name("plan.pdf", index=1) == "plan.pdf"
    assert attachment_name("../x", index=2).endswith("x")
    assert attachment_name("   ", index=3, fallback_ext="png") == "attachment_3.png"


def test_fit_within_budget_truncates_for_deep_roots():
    long_root = 200
    fitted = fit_within_budget(long_root, "S" * 100, ".metadata.json")
    assert len(fitted) < 100
