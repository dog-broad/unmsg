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

# Roles mirror the brand's named tokens. A clean near-white window over white
# cards; depth comes from borders, a soft shadow on the drop zone, and the
# selection tint — not a grey wash. `selection` is a faint accent tint.
LIGHT: dict[str, str] = {
    "surface": "#FAFAF8",
    "surface_raised": "#FFFFFF",
    "ink": "#1F2328",
    "ink_muted": "#5C6370",
    "border": "#DAD8D1",
    "selection": "#EAF2EC",
    "accent": "#2F6F4F",
    "accent_contrast": "#FFFFFF",
    "focus": "#3B82F6",
    "error": "#B4232A",
    "warning": "#9A6A00",
    "success": "#2E7D46",
}

DARK: dict[str, str] = {
    "surface": "#161719",
    "surface_raised": "#212327",
    "ink": "#ECECEC",
    "ink_muted": "#9AA0A8",
    "border": "#34373E",
    "selection": "#1F2A24",
    "accent": "#4CAF7D",
    "accent_contrast": "#0E1A13",
    "focus": "#60A5FA",
    "error": "#F1707A",
    "warning": "#E0B341",
    "success": "#6BD68F",
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

_QSS_TEMPLATE = """
QWidget {
    background-color: @surface;
    color: @ink;
    font-size: 14px;
}
QLabel#heading { font-size: 20px; font-weight: 600; }
QLabel[muted="true"] { color: @ink_muted; }

/* ── header & chrome ─────────────────────────────────────────── */
QFrame#header { background-color: @surface; border-bottom: 1px solid @border; }
QLabel#brand { font-size: 20px; font-weight: 600; color: @accent; }
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

/* ── tabs (underline style; text follows the theme) ──────────── */
QTabWidget::pane {
    border: 1px solid @border;
    border-radius: 6px;
    background-color: @surface_raised;
    top: -1px;
}
QTabBar { qproperty-drawBase: 0; }
QTabBar::tab {
    background: transparent;
    color: @ink_muted;
    padding: 7px 16px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:hover { color: @ink; }
QTabBar::tab:selected { color: @ink; border-bottom: 2px solid @accent; }

QCheckBox, QRadioButton { spacing: 8px; }
QTabWidget QWidget { background-color: @surface_raised; }

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
