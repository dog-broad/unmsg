# UnMsg

> **Right‑click → UnMsg → it just works.**

UnMsg turns Outlook `.msg` files into clean, readable formats — **Markdown,
HTML, single‑file HTML, plain text, JSON metadata, EML, and PDF** — with
attachments and inline images extracted alongside.

Everything happens on your machine. There is **no telemetry, no analytics, no
network call** outside the two clearly‑labelled opt‑in features (update check
and dependency installer). Your messages never leave.

## Why UnMsg

- **Trustworthy by construction.** Deterministic output (same input → same
  bytes), PII redacted in logs and crash reports by default, no SDKs that
  phone home.
- **One thing, well.** A drop zone, an action button, and your files come out.
  No marketing tour. No accounts.
- **Three ways to use it.** A Windows installer with right‑click integration,
  a cross‑platform [command line](cli.md), and a stable Python
  [API](api.md) for scripters and archivists.

## What you get out

Every `.msg` becomes a bundle directory named after the message — by default
`{date}_{subject}` — containing the formats you asked for plus
`attachments/` and `assets/` (inline images, with `cid:` references rewritten
to point at the saved files).

```text
2024-03-15_Quarterly Report/
├── 2024-03-15_Quarterly Report.md
├── 2024-03-15_Quarterly Report.html
├── 2024-03-15_Quarterly Report.pdf
├── 2024-03-15_Quarterly Report.metadata.json
├── attachments/
│   └── budget.pdf
└── assets/
    └── image-001.png
```

## Get going

- [Getting started](getting-started.md) — install, drop, convert.
- [Command line](cli.md) — for batches, scripts, and pipelines.
- [Desktop app](gui.md) — the calm window with the drop zone.
- [API reference](api.md) — embed UnMsg in your own Python.
- [Privacy](privacy.md) — what UnMsg does, and what it deliberately *doesn't*.
