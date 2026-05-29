"""Config schema: defaults, round-trip, telemetry lock, migration."""

from __future__ import annotations

import json

from unmsg.config import Config, load_config, save_config


def test_defaults_when_no_file(tmp_path):
    cfg = load_config(tmp_path / "missing.json")
    assert cfg.config_version == 1
    assert cfg.output.formats == ["md", "html"]
    assert cfg.ui.theme == "system"
    assert cfg.logging.redact_pii is True


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config()
    cfg.ui.theme = "dark"
    cfg.output.formats = ["md", "txt", "json"]
    save_config(cfg, path)

    loaded = load_config(path)
    assert loaded.ui.theme == "dark"
    assert loaded.output.formats == ["md", "txt", "json"]


def test_legacy_telemetry_field_is_ignored(tmp_path):
    # Old configs may still carry a telemetry flag; it's simply ignored now.
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"advanced": {"telemetry": True}}), encoding="utf-8")
    cfg = load_config(path)
    assert not hasattr(cfg.advanced, "telemetry")


def test_corrupt_file_yields_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not valid json", encoding="utf-8")
    assert load_config(path).output.formats == ["md", "html"]


def test_migration_adds_version(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"ui": {"theme": "light"}}), encoding="utf-8")
    cfg = load_config(path)
    assert cfg.config_version == 1
    assert cfg.ui.theme == "light"


def test_to_convert_options_maps_fields():
    cfg = Config()
    cfg.output.formats = ["md", "html_single"]
    cfg.output.inline_images = "base64"
    opts = cfg.to_convert_options()
    assert opts.formats == ("md", "html_single")
    assert opts.inline_images == "base64"
