# UnMsg

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

Early development. The first milestone is a working conversion engine and a
minimal command line; a polished desktop app follows. Watch this space.

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
