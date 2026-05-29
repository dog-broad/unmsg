"""Force a headless Qt platform before any Qt import in UI tests."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
