"""Theme: named design tokens turned into Qt stylesheet (QSS) at runtime.

The tokens are the single source of truth for colour and are substituted into a
QSS template. Switching theme swaps the token set and re-applies — there is no
second hand-written stylesheet to drift. Token/QSS generation here is Qt-free
and unit-tested; only :func:`apply_theme` touches ``QApplication``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

# A Tailwind-like neutral slate scale on white (light) / slate-900 (dark),
# separated by clearly-visible borders. `selection` is for menu/combobox
# highlight only — never a background behind list-row text.
LIGHT: dict[str, str] = {
    "surface": "#FFFFFF",
    "surface_raised": "#FFFFFF",
    "ink": "#1E293B",
    "ink_muted": "#64748B",
    "border": "#E2E8F0",
    "selection": "#F1F5F9",
    "accent": "#2F6F4F",
    "accent_contrast": "#FFFFFF",
    "focus": "#3B82F6",
    "error": "#DC2626",
    "warning": "#D97706",
    "success": "#16A34A",
}

DARK: dict[str, str] = {
    "surface": "#0F172A",
    "surface_raised": "#1E293B",
    "ink": "#E2E8F0",
    "ink_muted": "#94A3B8",
    "border": "#334155",
    "selection": "#334155",
    "accent": "#34D399",
    "accent_contrast": "#052E1B",
    "focus": "#60A5FA",
    "error": "#F87171",
    "warning": "#FBBF24",
    "success": "#4ADE80",
}

# Maximum-contrast set: pure black/white with a vivid accent and a distinct
# focus colour. Status colours stay saturated and legible on black.
HIGH_CONTRAST: dict[str, str] = {
    "surface": "#000000",
    "surface_raised": "#000000",
    "ink": "#FFFFFF",
    "ink_muted": "#FFFFFF",
    "border": "#FFFFFF",
    "selection": "#333300",
    "accent": "#FFFF00",
    "accent_contrast": "#000000",
    "focus": "#00FFFF",
    "error": "#FF5555",
    "warning": "#FFD400",
    "success": "#00FF7F",
}

# Per-format badge colours (bg, text) — Tailwind -100/-700 (light) and a darker
# pairing (dark). High-contrast uses one legible style for all formats.
_BADGES_LIGHT: dict[str, tuple[str, str]] = {
    "md": ("#F1F5F9", "#475569"),
    "html": ("#E0F2FE", "#0369A1"),
    "html_single": ("#E0E7FF", "#4338CA"),
    "txt": ("#F4F4F5", "#52525B"),
    "json": ("#FEF3C7", "#B45309"),
    "eml": ("#EDE9FE", "#6D28D9"),
    "pdf": ("#FFE4E6", "#BE123C"),
}
_BADGES_DARK: dict[str, tuple[str, str]] = {
    "md": ("#334155", "#CBD5E1"),
    "html": ("#0C4A6E", "#7DD3FC"),
    "html_single": ("#312E81", "#A5B4FC"),
    "txt": ("#3F3F46", "#D4D4D8"),
    "json": ("#78350F", "#FCD34D"),
    "eml": ("#4C1D95", "#C4B5FD"),
    "pdf": ("#881337", "#FDA4AF"),
}
_BADGE_HC: tuple[str, str] = ("#3A3A00", "#FFFF00")


def badge_palette(
    theme: str, *, system_is_dark: bool = False
) -> dict[str, tuple[str, str]]:
    """Per-format (bg, text) badge colours for the active theme."""
    if theme == "high-contrast":
        return dict.fromkeys(_BADGES_LIGHT, _BADGE_HC)
    if theme == "dark" or (theme == "system" and system_is_dark):
        return _BADGES_DARK
    return _BADGES_LIGHT


_QSS_TEMPLATE = """
QWidget {
    background-color: @surface;
    color: @ink;
    font-size: 14px;
}
QLabel#heading { font-size: 20px; font-weight: 600; }
QLabel[muted="true"] { color: @ink_muted; }

/* ── header & chrome ─────────────────────────────────────────── */
QFrame#header {
    background-color: @surface;
    border-top: 3px solid @accent;
    border-bottom: 1px solid @border;
}
QLabel#appMark {
    background-color: @accent;
    color: @accent_contrast;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 700;
}
QLabel#brand { font-size: 20px; font-weight: 600; color: @ink; }
QLabel#trustLine { color: @ink_muted; font-size: 12px; }
QFrame#actionBar { background-color: @surface; border-top: 1px solid @border; }
QLabel#statusLabel, QLabel#countLabel { color: @ink_muted; }
QFrame#updateBanner {
    background-color: @surface_raised; border-bottom: 1px solid @border;
}

/* ── slim top progress line ──────────────────────────────────── */
QProgressBar#topProgress { background-color: @surface; border: none; }
QProgressBar#topProgress::chunk { background-color: @accent; }

/* ── options summary bar (expands the panel) ─────────────────── */
QPushButton#optionsBar {
    text-align: left;
    background-color: @surface;
    border: none;
    border-top: 1px solid @border;
    color: @ink_muted;
    padding: 10px 24px;
    font-size: 13px;
}
QPushButton#optionsBar:hover { color: @ink; }
QPushButton#optionsBar:focus { color: @ink; }

QFrame#card, QPlainTextEdit {
    background-color: @surface_raised;
    border: 1px solid @border;
    border-radius: 6px;
}
QListWidget { background-color: @surface; border: none; outline: none; }

#dropZone {
    background-color: @surface_raised;
    border: 2px dashed @border;
    border-radius: 10px;
    color: @ink_muted;
}
#dropZone[dragActive="true"] {
    border: 2px solid @accent;
    color: @ink;
}
QLabel#dropHeading { color: @accent; font-size: 16px; font-weight: 600; }
QLabel#dropPrompt { color: @ink_muted; }

/* ── buttons ─────────────────────────────────────────────────── */
QPushButton {
    background-color: @surface_raised;
    border: 1px solid @border;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover { border-color: @accent; }
QPushButton:focus { border: 2px solid @focus; }

QPushButton#cta {
    background-color: @accent;
    color: @accent_contrast;
    border: none;
    border-radius: 6px;
    padding: 8px 22px;
    font-weight: 600;
}
QPushButton#cta:disabled { background-color: @border; color: @ink_muted; }

QPushButton#ghost {
    background-color: transparent;
    border: none;
    color: @ink_muted;
    padding: 6px 10px;
}
QPushButton#ghost:hover { color: @accent; }
QPushButton#ghost:focus { color: @ink; border: none; }

QLineEdit, QComboBox {
    background-color: @surface_raised;
    border: 1px solid @border;
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: @selection;
    selection-color: @ink;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid @focus; }
QComboBox:hover { border-color: @accent; }
QComboBox { padding-right: 26px; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow { image: url(@chevron); width: 12px; height: 12px; }
QComboBox QAbstractItemView {
    background-color: @surface_raised;
    border: 1px solid @border;
    border-radius: 6px;
    padding: 4px;
    outline: none;
    selection-background-color: @selection;
    selection-color: @ink;
}

QMenu { background-color: @surface_raised; border: 1px solid @border; padding: 4px; }
QMenu::item { padding: 6px 18px; border-radius: 4px; }
QMenu::item:selected { background-color: @selection; color: @ink; }

/* ── tabs (underline style; one divider, no boxed pane) ──────── */
QTabWidget::pane {
    border: none;
    border-top: 1px solid @border;
}
QTabBar { qproperty-drawBase: 0; background: transparent; }
QTabBar::tab {
    background: transparent;
    color: @ink_muted;
    padding: 7px 16px;
    margin-right: 4px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;  /* sit the underline on the pane's divider */
}
QTabBar::tab:hover { color: @ink; }
QTabBar::tab:selected { color: @ink; border-bottom: 2px solid @accent; }

QCheckBox, QRadioButton { spacing: 8px; }

QPlainTextEdit#logPane { font-family: "JetBrains Mono", Consolas, monospace; }
"""


def build_qss(tokens: dict[str, str]) -> str:
    """Substitute ``@token`` placeholders in the template with token values.

    ``@chevron`` is replaced with the path to a small SVG drop-down arrow tinted
    with ``ink_muted`` (generated and cached per colour).
    """
    qss = _QSS_TEMPLATE.replace("@chevron", chevron_icon_path(tokens["ink_muted"]))
    # Substitute longest names first so e.g. `@ink` doesn't clobber `@ink_muted`
    # (a shorter token name is a prefix of a longer one).
    for name in sorted(tokens, key=len, reverse=True):
        qss = qss.replace(f"@{name}", tokens[name])
    return qss.strip() + "\n"


def chevron_icon_path(color: str, *, up: bool = False) -> str:
    """Return a filesystem path (forward-slashed for QSS) to a chevron SVG tinted
    ``color``, generating it in the cache the first time. ``up`` flips it."""
    from unmsg import paths

    cache = paths.cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    facing = "up" if up else "down"
    target = cache / f"chevron-{facing}-{color.lstrip('#')}.svg"
    if not target.exists():
        path = "M2.5 7.5 L6 4 L9.5 7.5" if up else "M2.5 4.5 L6 8 L9.5 4.5"
        target.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
            f'viewBox="0 0 12 12"><path d="{path}" fill="none" '
            f'stroke="{color}" stroke-width="1.6" stroke-linecap="round" '
            'stroke-linejoin="round"/></svg>',
            encoding="utf-8",
        )
    return target.as_posix()


def tokens_for(theme: str, *, system_is_dark: bool) -> dict[str, str]:
    """Pick the token set for a theme name (``system`` follows the OS)."""
    if theme == "high-contrast":
        return HIGH_CONTRAST
    if theme == "dark":
        return DARK
    if theme == "light":
        return LIGHT
    return DARK if system_is_dark else LIGHT


def _system_is_dark(app: QApplication) -> bool:
    try:
        from PySide6.QtCore import Qt

        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except (AttributeError, ImportError):
        return False


def apply_theme(app: QApplication, theme: str = "system") -> None:
    """Apply the chosen theme to a running application."""
    tokens = tokens_for(theme, system_is_dark=_system_is_dark(app))
    app.setStyleSheet(build_qss(tokens))
