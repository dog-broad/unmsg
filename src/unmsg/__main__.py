"""``python -m unmsg`` runs the command-line interface."""

from __future__ import annotations

import multiprocessing

from unmsg.cli import app

if __name__ == "__main__":
    multiprocessing.freeze_support()  # safe no-op unless frozen; needed for spawn
    app()
