# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

The first working slice: a pure conversion engine and a minimal command line.
Everything runs locally — nothing is ever sent anywhere.

### Added

- Convert Outlook `.msg` files to **Markdown**, **HTML**, and **single-file
  HTML** (images inlined as base64).
- Extract regular attachments to `attachments/` and inline images to `assets/`,
  rewriting `cid:` references to point at the saved files.
- Recursively unpack messages attached to messages.
- Per-message output folders named `{date}_{subject}` by default, with a
  configurable naming template and collision strategy.
- Safe filenames: protection against path traversal, reserved device names, and
  over-long paths.
- Timestamps normalised to UTC and written as ISO-8601, so output is identical
  across machines and time zones.
- Deterministic output: the same input and options always produce the same
  bytes. Each produced file's SHA-256 is reported.
- A command line: `unmsg convert <paths> -o <out> --format md,html`, with exit
  codes for scripting (`0` success, `1` partial, `2` failed, `3` no input).
- A small Python API: `convert_file`, `convert_batch`, and the data model.
- Friendly, plain-language errors — no stack traces reach the user.

### Notes

- The desktop app is not in this release; a polished GUI comes next.
- `pip install unmsg` installs the core and CLI only. The GUI will be available
  as an optional `unmsg[gui]` extra.

[Unreleased]: https://github.com/dog-broad/unmsg/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dog-broad/unmsg/releases/tag/v0.1.0
