# Contributing to UnMsg

Thanks for being here. UnMsg is small enough that most contributions are
straightforward — read this once and you'll be set.

## What we're optimising for

**Trust and privacy win ties.** UnMsg's promise is that your messages never
leave your machine. Anything that compromises that — telemetry, analytics,
error‑reporting SDKs, surprising network calls — won't land. The two
opt‑in network features (update check, dependency installer) live in
dedicated modules so the promise stays auditable.

A close second: **deterministic output**. The same `.msg` and the same
options must produce the same bytes. Sorted iteration, fixed JSON key order,
no wall‑clock timestamps embedded in the output, stable inline‑image
numbering.

## Dev setup

```bash
git clone https://github.com/dog-broad/unmsg.git
cd unmsg
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -e ".[gui,pdf,dev,docs]"
```

That gives you everything: the conversion core, the GUI extras, PDF
rendering, the test/lint/type toolchain, and the docs builder.

## The local check‑list

Run these and they'll match what CI runs:

```bash
nox              # all sessions (lint, types, imports, tests on 3.11 + 3.12)

# or individually:
ruff check .
ruff format --check .
mypy src/unmsg/core         # strict on core
lint-imports                 # core ↛ ui/cli is enforced
pytest --cov=unmsg           # ≥ 90% required to pass
mkdocs build --strict        # docs site
```

CI runs `pytest` with `QT_QPA_PLATFORM=offscreen`; `pytest‑qt` sets that
for you automatically. The `nox tests` session installs the GUI extras so
the desktop tests actually run.

## Code conventions

- **Python 3.11+**. PySide6 (Qt 6) for the GUI, typer for the CLI,
  pydantic v2 for config, platformdirs for OS dirs.
- **`mypy --strict` on `core/`** must stay clean. Public functions and
  dataclass fields are fully annotated. No bare `Any` where a real type
  exists; no implicit `Optional`.
- **`core/` never imports from `ui/` or `cli`** — enforced by
  `import‑linter` in CI. Core has zero import‑time side effects; IO only at
  reader/writer edges; pure transforms between.
- **Comment *why*, never *what*.** If a comment restates well‑named code,
  delete the comment or rename the code.
- **Never trust message‑supplied filenames** — sanitise for path traversal,
  reserved names, and length before any write. Use the helpers in
  `core/naming.py`.
- **No dead code, no commented‑out blocks.** Git remembers.
- **No `TODO` without a matching tracking item.** Untracked TODOs lie about
  the project's state.

Formatter and linter are `ruff` — run `ruff format` and `ruff check --fix`
before opening a PR; don't hand‑fight the formatter.

## Commit style

Conventional commits: `type: imperative subject`, lowercase type, subject
**≤72 chars**, no trailing period.

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`,
`perf`, `style`.

One logical change per commit; it should build and pass on its own.

## Pull requests

- Open against `main`.
- A short description of the change and (if user‑facing) a one‑line
  CHANGELOG entry under **Unreleased**.
- CI must pass (lint, types, import contracts, tests across Ubuntu, Windows,
  macOS × Python 3.11 + 3.12, coverage ≥ 90%).

If you're not sure whether something fits the project, open an issue first
— happy to talk it through before you write code.

## Reporting bugs / asking for help

[Issues](https://github.com/dog-broad/unmsg/issues). Include the OS, the
Python version, the UnMsg version (`unmsg --version`), and — if it's a
parsing problem and you can share — a redacted sample `.msg` or a
description of what the message contains (HTML body? embedded `.msg`?
attachment with a tricky name?). Logs go to the OS user log directory with
emails/paths redacted by default; including the relevant chunk is helpful.

## Security

If you find a security issue, please **don't open a public issue**. Email
the maintainer (address on the GitHub profile) instead. We'll work it out
privately and credit you in the fix.
