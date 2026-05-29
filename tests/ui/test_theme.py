"""Theme token/QSS generation (Qt-free)."""

from __future__ import annotations

from unmsg.ui.theme import DARK, HIGH_CONTRAST, LIGHT, build_qss, tokens_for


def test_build_qss_substitutes_tokens():
    qss = build_qss(LIGHT)
    assert "@surface" not in qss
    assert LIGHT["accent"] in qss
    assert "#dropZone" in qss


def test_tokens_for_explicit_themes():
    assert tokens_for("light", system_is_dark=True) is LIGHT
    assert tokens_for("dark", system_is_dark=False) is DARK
    assert tokens_for("high-contrast", system_is_dark=False) is HIGH_CONTRAST


def test_tokens_for_system_follows_os():
    assert tokens_for("system", system_is_dark=True) is DARK
    assert tokens_for("system", system_is_dark=False) is LIGHT


def test_all_themes_share_the_same_tokens():
    assert set(LIGHT) == set(DARK) == set(HIGH_CONTRAST)


def test_high_contrast_qss_builds():
    qss = build_qss(HIGH_CONTRAST)
    assert "@" not in qss.replace("@token", "")  # no leftover placeholders
    assert HIGH_CONTRAST["focus"] in qss
