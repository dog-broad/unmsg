# UnMsg

[![CI](https://github.com/dog-broad/unmsg/actions/workflows/ci.yml/badge.svg)](https://github.com/dog-broad/unmsg/actions/workflows/ci.yml)
[![Docs](https://github.com/dog-broad/unmsg/actions/workflows/docs.yml/badge.svg)](https://dog-broad.github.io/unmsg/)
[![PyPI](https://img.shields.io/pypi/v/unmsg.svg)](https://pypi.org/project/unmsg/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Turn Outlook `.msg` files into clean Markdown, HTML, text, JSON, EML, and PDF —
> with attachments and inline images extracted alongside. Drag, drop, click
> Convert, done.

**UnMsg** is a small, friendly desktop app (and CLI) for getting your email out
of Outlook's `.msg` format and into formats you can actually read, search, and
keep. Everything happens on your machine — your messages never leave it, and
there is no telemetry of any kind.

## Why

Every other option is a brittle script, a paid utility, a sketchy web converter
that wants your email, or one `pip install` away from being your problem. UnMsg
is the thing you can install in two minutes and use forever.

## Status

Pre‑1.0 release line. The conversion core, CLI, and desktop app are all
shipped — current release is on the
[releases page](https://github.com/dog-broad/unmsg/releases). 1.0 will add a
code‑signed Windows installer and best‑effort macOS/Linux artifacts.

## Documentation

Full docs — getting started, CLI reference, desktop app guide, the privacy
statement, and the auto‑generated API reference — live at
**[dog-broad.github.io/unmsg](https://dog-broad.github.io/unmsg/)** (built
from [`docs/`](docs/)).

## Planned features

- Drag-and-drop `.msg` files and folders
- Convert to **Markdown**, **HTML**, **single-file HTML**, **plain text**,
  **JSON metadata**, **EML**, and **PDF/PDF-A**
- Extract attachments and inline images, with `cid:` references rewritten
- Predictable, sortable output folders (`{date}_{subject}` by default)
- A scriptable CLI and a small Python API
- Deterministic output and per-batch manifests for archiving
- Fully offline. No accounts, no uploads, no analytics — ever.

## License

[MIT](LICENSE).
