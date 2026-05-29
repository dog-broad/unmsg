"""Update check: parsing, version comparison, failure handling (no network)."""

from __future__ import annotations

import json

from unmsg import updates
from unmsg.updates import check_for_update


def _fake(payload: dict) -> updates.Fetcher:
    def fetch(url: str, timeout: float) -> bytes:
        return json.dumps(payload).encode("utf-8")

    return fetch


def test_detects_newer_version(monkeypatch):
    monkeypatch.setattr(updates, "__version__", "0.3.0")
    info = check_for_update(
        fetch=_fake({"tag_name": "v0.9.0", "html_url": "u", "body": "notes"})
    )
    assert info is not None
    assert info.is_newer
    assert info.latest == "0.9.0"
    assert info.notes == "notes"


def test_same_version_is_not_newer(monkeypatch):
    monkeypatch.setattr(updates, "__version__", "0.3.0")
    info = check_for_update(fetch=_fake({"tag_name": "0.3.0"}))
    assert info is not None
    assert not info.is_newer
    assert info.url == updates.RELEASES_PAGE


def test_network_error_returns_none():
    def boom(url: str, timeout: float) -> bytes:
        raise OSError("offline")

    assert check_for_update(fetch=boom) is None


def test_malformed_json_returns_none():
    assert check_for_update(fetch=lambda url, timeout: b"not json") is None


def test_missing_tag_returns_none():
    assert check_for_update(fetch=_fake({"name": "no tag here"})) is None


def test_version_tuple_handles_prefixes_and_junk():
    assert updates._version_tuple("v1.2.3") == (1, 2, 3)
    assert updates._version_tuple("0.3.0a1") == (0, 3, 0)
