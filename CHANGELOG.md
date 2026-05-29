# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0]

For scripters and archivists: a fuller command line, a stable Python API, batch
manifests with checksums, and EML output.

### Added

- **EML output** — reconstructs a self-contained `.eml` (multipart/related with a
  plain-text alternative); inline images are preserved by Content-ID so they
  render in a mail client.
- **Per-batch manifest** — `manifest.json` written at the output root by default
  (`--no-manifest` to skip), listing each message's outputs with SHA-256, using
  relative paths and no timestamp so identical runs produce identical manifests.
- **More CLI options** — `--naming` (output template), `--on-conflict`
  (rename / overwrite / skip), and `--manifest/--no-manifest`. Exit codes remain
  `0` success, `1` partial, `2` failed, `3` no input.
- **Documented, stable Python API** — `convert_file`, `convert_batch`,
  `ConvertOptions`, `ConvertResult`, and the data model, importable from `unmsg`.

## [0.3.2]

### Fixed

- Plain-text output was empty for HTML-only messages (those with no text body).
  The text format now derives readable text from the HTML when there's no
  plain-text part, so the `.txt` file contains the message body.

## [0.3.1]

Fixes found by converting a real Outlook message.

### Fixed

- Messages whose fields carried trailing NUL characters (common in `.msg`
  string data) no longer crash conversion; subjects, attachment names, and
  inline-image references are cleaned.
- Send/receive dates provided as text are now parsed, so output folders are
  dated correctly instead of falling back to "undated".
- Recipient lists are split correctly when display names contain `;` or `,`
  (e.g. "Surname, Given (Org)") — each person is one entry with the right
  address.
- A problem while writing output now shows a friendly message instead of a raw
  error.

### Changed

- Version reporting now reflects the released version.

## [0.3.0]

Ready for a non-technical Windows user: a real installer, a gentle first run, and
honest diagnostics — all still fully local.

### Added

- A Windows installer built with PyInstaller + Inno Setup: a single setup `.exe`
  with a Start-menu shortcut and optional desktop shortcut, Send To entry, and a
  "Convert with UnMsg" entry on the `.msg` right-click menu.
- A first-run welcome screen that teaches the drop-and-convert gesture.
- Combined Help/About with quick-start steps and the privacy promise.
- An opt-in update check (off by default) that reads the public releases list and
  shows a dismissible banner; "Download" opens your browser. It never downloads
  or installs anything, and it's the only outbound network call in the app.
- A crash reporter that writes a redacted report to disk (emails and paths
  removed) and points you to the issue tracker — never uploading anything.

### Notes

- Releases are unsigned for now: SmartScreen shows a warning — click
  **More info → Run anyway**. Code signing is planned for 1.0.

## [0.2.0]

The desktop app arrives: drag, drop, click Convert, done — with a calm, themed
interface. Still fully local, still no telemetry.

### Added

- A PySide6 desktop application (`unmsg-gui`): a drop zone that teaches the empty
  state, a file list with live per-row status (queued, working, done, warning,
  failed) and a right-click menu (show in Explorer, show source, copy error,
  remove), an output options panel, a progress strip with Convert / Cancel /
  Open Output, and a collapsible log pane.
- Light and dark themes generated from a single set of design tokens; a "system"
  option follows the OS.
- Conversion runs on a background thread so the window stays responsive; Cancel
  stops cleanly between files (no half-written output).
- Settings dialog (General / Advanced / About) with values saved between runs;
  window size and last output folder are remembered. The telemetry control is
  shown switched off and disabled — a visible promise.
- Two more output formats: **plain text** and **JSON metadata**.
- Logs and error details redact emails and file paths by default.

### Notes

- The GUI installs with the optional extra: `pip install "unmsg[gui]"`.

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

[Unreleased]: https://github.com/dog-broad/unmsg/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/dog-broad/unmsg/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/dog-broad/unmsg/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/dog-broad/unmsg/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/dog-broad/unmsg/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dog-broad/unmsg/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dog-broad/unmsg/releases/tag/v0.1.0
