"""The output options panel: destination, formats, attachments, naming."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from unmsg.config import Config
from unmsg.core.models import FormatId, InlineMode
from unmsg.core.options import ConvertOptions

_FORMATS: list[tuple[FormatId, str]] = [
    ("md", "Markdown"),
    ("html", "HTML"),
    ("html_single", "Single-file HTML"),
    ("txt", "Plain text"),
    ("json", "Metadata (JSON)"),
]

_NAMING = [
    "{date}_{subject}",
    "{subject}",
    "{date}_{from_name}_{subject}",
    "{subject}_{hash}",
]


class OptionsPanel(QFrame):
    """Right-hand panel mirroring the conversion options in config."""

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)

        layout.addWidget(_label("Output"))
        self._output = QLineEdit(config.ui.last_output_dir or config.output.directory)
        browse = QPushButton("Browse")
        browse.clicked.connect(self._choose_output)
        row = QHBoxLayout()
        row.addWidget(self._output)
        row.addWidget(browse)
        layout.addLayout(row)

        layout.addWidget(_label("Formats"))
        self._format_boxes: dict[FormatId, QCheckBox] = {}
        for fmt, text in _FORMATS:
            box = QCheckBox(text)
            box.setChecked(fmt in config.output.formats)
            self._format_boxes[fmt] = box
            layout.addWidget(box)

        self._attachments = QCheckBox("Attachments")
        self._attachments.setChecked(config.output.attachments)
        layout.addWidget(self._attachments)

        layout.addWidget(_label("Inline images"))
        self._inline = QComboBox()
        self._inline.addItems(["extract", "base64", "skip"])
        self._inline.setCurrentText(config.output.inline_images)
        layout.addWidget(self._inline)

        layout.addWidget(_label("Naming"))
        self._naming = QComboBox()
        self._naming.setEditable(True)
        self._naming.addItems(_NAMING)
        self._naming.setCurrentText(config.output.naming_template)
        layout.addWidget(self._naming)

        layout.addStretch(1)

    def output_dir(self) -> Path:
        return Path(self._output.text()).expanduser()

    def selected_formats(self) -> tuple[FormatId, ...]:
        return tuple(fmt for fmt, box in self._format_boxes.items() if box.isChecked())

    def to_options(self) -> ConvertOptions:
        inline: InlineMode = self._inline.currentText()  # type: ignore[assignment]
        return ConvertOptions(
            formats=self.selected_formats() or ("md",),
            attachments=self._attachments.isChecked(),
            inline_images=inline,
            naming_template=self._naming.currentText().strip() or "{date}_{subject}",
        )

    def write_into(self, config: Config) -> None:
        config.output.directory = str(self.output_dir())
        config.output.formats = list(self.selected_formats()) or ["md"]
        config.output.attachments = self._attachments.isChecked()
        config.output.inline_images = self._inline.currentText()  # type: ignore[assignment]
        config.output.naming_template = self._naming.currentText().strip()
        config.ui.last_output_dir = str(self.output_dir())

    def _choose_output(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if chosen:
            self._output.setText(chosen)


def _label(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("muted", "true")
    return label
