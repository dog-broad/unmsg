"""User configuration: schema, defaults, load/save, and migration.

Validated with pydantic and versioned so old files upgrade in place. The
telemetry control exists only to be shown switched off — it is forced ``False``
on every load, by design, and there is no code anywhere that would send data.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from unmsg import paths
from unmsg.core.models import FormatId, InlineMode, OnConflict
from unmsg.core.options import ConvertOptions

CONFIG_VERSION = 1


class OutputConfig(BaseModel):
    directory: str = Field(default_factory=lambda: str(paths.default_output_dir()))
    formats: list[FormatId] = Field(default_factory=lambda: ["md", "html"])
    attachments: bool = True
    inline_images: InlineMode = "extract"
    on_conflict: OnConflict = "rename"
    naming_template: str = "{date}_{subject}"


class UIConfig(BaseModel):
    theme: str = "system"  # system | light | dark
    window_width: int = 980
    window_height: int = 680
    last_output_dir: str | None = None
    log_pane_collapsed: bool = True


class LoggingConfig(BaseModel):
    level: str = "INFO"
    redact_pii: bool = True


class AdvancedConfig(BaseModel):
    max_parallel: int = 1
    file_timeout_seconds: int = 0  # 0 = no timeout (until the performance release)
    check_updates: bool = False  # opt-in; the only outbound network call
    telemetry: bool = False  # locked off — see validator below

    @field_validator("telemetry")
    @classmethod
    def _telemetry_is_always_off(cls, _value: bool) -> bool:
        return False


class Config(BaseModel):
    config_version: int = CONFIG_VERSION
    output: OutputConfig = Field(default_factory=OutputConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)

    def to_convert_options(self) -> ConvertOptions:
        return ConvertOptions(
            formats=tuple(self.output.formats),
            attachments=self.output.attachments,
            inline_images=self.output.inline_images,
            on_conflict=self.output.on_conflict,
            naming_template=self.output.naming_template,
        )


def _migrate(raw: dict[str, object]) -> dict[str, object]:
    """Upgrade an older config dict to the current version in place.

    Only version 1 exists today; future versions add branches here.
    """
    raw.setdefault("config_version", CONFIG_VERSION)
    return raw


def load_config(path: Path | None = None) -> Config:
    """Load config from ``path`` (or the platform default).

    A missing or unreadable file yields defaults rather than an error — the app
    should always start.
    """
    target = path or paths.config_file()
    try:
        raw = json.loads(target.read_text("utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return Config()
    if not isinstance(raw, dict):
        return Config()
    try:
        return Config.model_validate(_migrate(raw))
    except ValueError:
        return Config()


def save_config(config: Config, path: Path | None = None) -> Path:
    """Write config atomically; returns the path written."""
    target = path or paths.config_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    text = config.model_dump_json(indent=2)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(target)
    return target
