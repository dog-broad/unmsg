"""Where UnMsg keeps its config, logs, cache, and default output.

A thin wrapper over ``platformdirs`` so paths are correct on every OS. These are
the only functions that decide locations; nothing else hard-codes a path.
"""

from __future__ import annotations

from pathlib import Path

from platformdirs import PlatformDirs

APP_NAME = "UnMsg"
_dirs = PlatformDirs(appname=APP_NAME, appauthor=APP_NAME)


def config_file() -> Path:
    return Path(_dirs.user_config_dir) / "config.json"


def log_dir() -> Path:
    return Path(_dirs.user_log_dir)


def cache_dir() -> Path:
    return Path(_dirs.user_cache_dir)


def default_output_dir() -> Path:
    """Default place to write conversions: ``~/Documents/UnMsg`` where Documents
    exists, otherwise ``~/UnMsg``."""
    documents = Path.home() / "Documents"
    base = documents if documents.is_dir() else Path.home()
    return base / APP_NAME
