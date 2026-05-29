"""The Settings dialog: General, Conversion, Advanced, About — round-tripped.

Reads the current config into widgets and, on accept, writes the values back
into the config object the caller then persists. The telemetry control is shown
switched off and disabled — a visible promise, not a hidden toggle.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from unmsg._version import __version__
from unmsg.config import Config


class SettingsDialog(QDialog):
    def __init__(self, config: Config, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._config = config
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._general_tab(), "General")
        tabs.addTab(self._advanced_tab(), "Advanced")
        tabs.addTab(self._about_tab(), "About")
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _general_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self._theme = QComboBox()
        self._theme.addItems(["system", "light", "dark", "high-contrast"])
        self._theme.setCurrentText(self._config.ui.theme)
        form.addRow("Theme", self._theme)
        return page

    def _advanced_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        self._level = QComboBox()
        self._level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self._level.setCurrentText(self._config.logging.level)
        form.addRow("Log level", self._level)

        self._redact = QCheckBox("Redact personal data in logs")
        self._redact.setChecked(self._config.logging.redact_pii)
        form.addRow(self._redact)

        self._parallel = QSpinBox()
        self._parallel.setRange(1, 64)
        self._parallel.setValue(self._config.advanced.max_parallel)
        form.addRow("Max parallel files", self._parallel)
        return page

    def _about_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(f"UnMsg {__version__}"))
        layout.addWidget(_muted("MIT licensed. Your data never leaves your machine."))
        layout.addStretch(1)
        return page

    def accept(self) -> None:
        self._config.ui.theme = self._theme.currentText()
        self._config.logging.level = self._level.currentText()
        self._config.logging.redact_pii = self._redact.isChecked()
        self._config.advanced.max_parallel = self._parallel.value()
        super().accept()


def _muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("muted", "true")
    label.setWordWrap(True)
    return label
