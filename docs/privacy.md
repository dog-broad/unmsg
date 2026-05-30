# Privacy

**Your messages never leave this machine.** That's the design hinge, not a
marketing line — it's wired into the code.

## What UnMsg does not do

UnMsg ships with **zero telemetry, analytics, or error‑reporting SDKs.** There
is no opt‑in toggle for data collection because there is no data collection.
The app contains no:

- usage analytics or telemetry of any kind,
- error/crash uploading service,
- session or device identifiers,
- third‑party tracking, fonts, or scripts.

The desktop app has **no network indicator** because, in normal use, it makes
no network calls.

## The only two network features

Both are **opt‑in** and clearly named in Settings → **Advanced**:

1. **Update check.** When enabled, the app reads the public releases list to
   tell you that a newer version exists. It sends nothing about you, it
   never downloads or installs anything, and clicking *Download* opens your
   browser. This is the only outbound call in the GUI.

2. **Dependency installer.** A small helper that can `pip install` an
   optional extra (e.g. PDF support) for you. It runs `pip` against the
   public package index when you tap the button — and not otherwise.

Both modules live in dedicated files so the promise is auditable in a
glance.

## Determinism and redaction

- **Deterministic output.** The same `.msg` and the same options produce
  identical bytes — sorted iteration, fixed JSON key order, no wall‑clock
  timestamps embedded in output bodies, stable inline‑image numbering.
- **PII redaction by default.** Logs and crash reports have emails and file
  paths scrubbed before they're written. You can turn redaction off in
  Settings if you need to diagnose a parsing issue and your data is safe to
  expose.
- **Crash reports never leave.** A crash writes a redacted report to a local
  file and points you to the issue tracker — uploading is your choice, not
  ours.

## What gets written, where

| Item | Where | Why |
|------|-------|-----|
| Output bundles | wherever you choose (default: `Documents/UnMsg`) | The converted message |
| App config | OS user config dir (`platformdirs`) | Window size, theme, last folder |
| Logs | OS user log dir | Diagnostics — redacted by default |
| Crash reports | OS user log dir | Local only, never uploaded |

Uninstalling the app does **not** delete the config and log directories —
they are yours to keep or to clean. Delete the directory if you want them
gone.

## Source

The trust claim is verifiable: the entire app is open source at
[github.com/dog-broad/unmsg](https://github.com/dog-broad/unmsg). The two
network modules are short and isolated; the rest of the code does not import
the network at all.
