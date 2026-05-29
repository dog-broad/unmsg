"""Theme token/QSS generation (Qt-free)."""

from __future__ import annotations

from pathlib import Path

from unmsg.ui.theme import (
    DARK,
    HIGH_CONTRAST,
    LIGHT,
    build_qss,
    chevron_icon_path,
    tokens_for,
)


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


def test_all_themes_have_a_selection_token():
    for tokens in (LIGHT, DARK, HIGH_CONTRAST):
        assert "selection" in tokens


def test_borders_are_visible_against_surface():
    # differentiation comes from borders, not a grey canvas
    assert LIGHT["border"] != LIGHT["surface"]
    assert DARK["border"] != DARK["surface"]


def test_badge_palette_is_per_format_and_theme_aware():
    from unmsg.ui.theme import badge_palette

    light = badge_palette("light")
    dark = badge_palette("dark")
    # each format has a distinct colour; light and dark differ
    assert light["pdf"] != light["md"] != light["html"]
    assert light["pdf"] != dark["pdf"]
    # every implemented format is covered
    for fmt in ("md", "html", "html_single", "txt", "json", "eml", "pdf"):
        bg, fg = light[fmt]
        assert bg.startswith("#") and fg.startswith("#")


def test_high_contrast_badges_are_uniform():
    from unmsg.ui.theme import badge_palette

    hc = badge_palette("high-contrast")
    assert len(set(hc.values())) == 1  # one legible style


def test_chevron_icon_generated_and_tinted(tmp_path, monkeypatch):
    import unmsg.paths as paths

    monkeypatch.setattr(paths, "cache_dir", lambda: tmp_path)
    down = chevron_icon_path("#5C6370")
    up = chevron_icon_path("#5C6370", up=True)
    assert down.endswith(".svg") and up.endswith(".svg")
    assert down != up
    body = Path(down).read_text("utf-8")
    assert "#5C6370" in body and "<svg" in body


def test_build_qss_resolves_chevron_into_combobox(monkeypatch, tmp_path):
    import unmsg.paths as paths

    monkeypatch.setattr(paths, "cache_dir", lambda: tmp_path)
    qss = build_qss(LIGHT)
    assert "@chevron" not in qss
    assert "down-arrow" in qss
    assert ".svg" in qss


def test_color_accents_present_in_qss(monkeypatch, tmp_path):
    import unmsg.paths as paths

    monkeypatch.setattr(paths, "cache_dir", lambda: tmp_path)
    qss = build_qss(LIGHT)
    assert "QLabel#appMark" in qss  # coloured brand mark
    assert "QLabel#dropHeading" in qss  # accent empty-state heading
    assert "border-top: 3px solid" in qss  # accent top strip


def test_tabs_are_themed_so_text_is_visible(monkeypatch, tmp_path):
    import unmsg.paths as paths

    monkeypatch.setattr(paths, "cache_dir", lambda: tmp_path)
    for tokens in (LIGHT, DARK, HIGH_CONTRAST):
        qss = build_qss(tokens)
        assert "QTabBar::tab" in qss
        # tab text uses theme ink colours, never a hard-coded black
        assert tokens["ink"] in qss
        assert tokens["ink_muted"] in qss
