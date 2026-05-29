# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.7]

More colour, used meaningfully.

### Added

- Each file row's status line is now coloured by state — green when done, amber
  for a warning, red for a failure, accent while converting — matching its dot.
- A small brand mark and an accent strip in the header, and an accent-coloured
  heading on the empty-state drop zone.

## [0.5.6]

A clean restyle to a Tailwind-like look, with colored format badges.

### Changed

- Reworked the desktop palette as a Tailwind-like slate system — clean white
  surfaces (slate-900 in dark) separated by crisp borders. This reverts the
  earlier grey canvas, the tint behind row text, the accent wordmark, and the
  drop-zone shadow.
- File-type indicators are now **per-format colored badges** — Markdown, HTML,
  single-file HTML, text, JSON, EML, and PDF each get a distinct colour — so the
  output formats are identifiable at a glance, in every theme.
- The themed tab bar (from 0.5.3) is retained.

## [0.5.5]

### Changed

- File rows no longer get a tinted background behind the text — only the
  format badges are filled. Cleaner, less busy.
- The options bar's chevron direction is corrected (points up when collapsed,
  down when expanded).

## [0.5.4]

### Changed

- Reverted the grey window background introduced in 0.5.2 — the app is a clean
  near-white again; panels are separated by borders and a soft shadow on the
  drop zone rather than a grey wash.
- Format indicators are now compact Tailwind-style badges (lightly rounded, soft
  tint) instead of full-rounded capsules.

## [0.5.3]

### Fixed

- Settings tab labels were invisible in dark and high-contrast themes (black text
  on a dark background); tabs now use the theme's text colour with an accent
  underline on the active tab.
- Theme colours were mis-applied where one token name is a prefix of another
  (e.g. muted text, raised surfaces, button-text-on-accent): the stylesheet now
  substitutes the longest names first, so every element gets its intended colour.

### Changed

- Format indicators on each row are now filled, rounded **pills** in the brand
  tint — clearer and easier to scan than the previous thin outlines.

## [0.5.2]

A visual depth pass: the window no longer reads as flat white-on-white.

### Changed

- Clear surface hierarchy — a cool grey window behind white cards, with stronger
  borders and a soft shadow under the drop zone, so panels actually separate.
- Hovered and selected file rows get a faint green tint, with hairline separators
  between rows.
- The wordmark is now in the brand green.
- Comboboxes use a crisp, theme-aware chevron instead of the old default arrow;
  menus and dropdown popups are styled to match.

## [0.5.1]

A ground-up rethink of the desktop window — calmer, clearer, and more honest
about what it's doing.

### Changed

- The window is now a single, calm column instead of a control panel. There is
  always exactly **one primary action** that changes with the moment —
  **Convert → Cancel → Open output** — so the next step is never in doubt.
- Output options collapse into a **one-line summary bar** that expands only when
  you want it; sensible defaults mean most people never open it.
- Each file row now shows the **message's identity** — once converted, its
  output name (date and subject) — with a coloured status dot and small chips
  for the formats produced, instead of a bare filename.
- Conversion progress is a **slim line under the header**, not a heavy bar.
- The privacy promise lives in the header, always visible.
- The empty state says what UnMsg produces (Markdown, HTML, PDF, …).

## [0.5.0]

Performance, resilience, accessibility — and PDF.

### Added

- **PDF output** (optional `unmsg[pdf]` extra) — pure-Python and deterministic;
  renders a clean, best-effort PDF from the message.
- **Parallel conversion** — `--jobs N` converts across worker processes.
- **Per-file timeout** — `--timeout S` stops a single stuck message (the worker
  is terminated) without taking the rest of the batch down.
- **Resume** — `--resume` skips messages already converted, verified by matching
  each output's checksum against the manifest; skipped entries are carried
  forward.
- **File search/filter** in the desktop app's file list.
- A **high-contrast theme**.

### Changed

- A format that fails or whose optional dependency is missing now degrades to a
  warning for that one format — the other formats still convert.
- Removed the (disabled) telemetry control from Settings: the app collects
  nothing, so it shows no such UI.

### Fixed

- PDF renders reliably from real Outlook HTML (its modern CSS is reduced to
  plain markup first).
- Command-line output no longer errors when redirected to a file on Windows.

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

[Unreleased]: https://github.com/dog-broad/unmsg/compare/v0.5.7...HEAD
[0.5.7]: https://github.com/dog-broad/unmsg/compare/v0.5.6...v0.5.7
[0.5.6]: https://github.com/dog-broad/unmsg/compare/v0.5.5...v0.5.6
[0.5.5]: https://github.com/dog-broad/unmsg/compare/v0.5.4...v0.5.5
[0.5.4]: https://github.com/dog-broad/unmsg/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/dog-broad/unmsg/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/dog-broad/unmsg/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/dog-broad/unmsg/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/dog-broad/unmsg/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/dog-broad/unmsg/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/dog-broad/unmsg/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/dog-broad/unmsg/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/dog-broad/unmsg/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dog-broad/unmsg/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dog-broad/unmsg/releases/tag/v0.1.0
