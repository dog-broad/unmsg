"""Locate bundled UI assets (icons) in dev and in a frozen build."""

from __future__ import annotations

from pathlib import Path

_ICONS = Path(__file__).resolve().parent / "resources" / "icons"


def app_icon_svg() -> str:
    """Path to the scalable app icon (used for the window/taskbar)."""
    return str(_ICONS / "unmsg.svg")


def app_icon_ico() -> str:
    """Path to the multi-size Windows icon (used by the installer/exe)."""
    return str(_ICONS / "unmsg.ico")
