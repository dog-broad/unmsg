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

# Roles mirror the brand's named tokens (light / dark pairs).
LIGHT: dict[str, str] = {
    "surface": "#FAFAF8",
    "surface_raised": "#FFFFFF",
    "ink": "#1F2328",
    "ink_muted": "#5C6370",
    "border": "#E4E2DC",
    "accent": "#2F6F4F",
    "accent_contrast": "#FFFFFF",
    "focus": "#3B82F6",
    "error": "#B4232A",
    "warning": "#9A6A00",
    "success": "#2E7D46",
}

DARK: dict[str, str] = {
    "surface": "#1A1B1E",
    "surface_raised": "#25262B",
    "ink": "#ECECEC",
    "ink_muted": "#9AA0A8",
    "border": "#34363B",
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
    padding: 4px 8px;
}
QLineEdit:focus, QComboBox:focus { border: 2px solid @focus; }

QPlainTextEdit#logPane { font-family: "JetBrains Mono", Consolas, monospace; }
"""


def build_qss(tokens: dict[str, str]) -> str:
    """Substitute ``@token`` placeholders in the template with token values."""
    qss = _QSS_TEMPLATE
    for name, value in tokens.items():
        qss = qss.replace(f"@{name}", value)
    return qss.strip() + "\n"


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
