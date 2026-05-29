"""Task sessions for UnMsg.

Run everything with ``nox``, or a single session with ``nox -s lint``. Sessions
mirror the checks CI runs so "green locally" means "green in CI".
"""

from __future__ import annotations

import nox

nox.options.sessions = ["lint", "typecheck", "imports", "tests"]
PYTHONS = ["3.11", "3.12"]


@nox.session
def lint(session: nox.Session) -> None:
    session.install("ruff")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")


@nox.session
def typecheck(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run("mypy", "src/unmsg/core")


@nox.session
def imports(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run("lint-imports")


@nox.session(python=PYTHONS)
def tests(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run("pytest", "--cov", "--cov-report=term-missing")
