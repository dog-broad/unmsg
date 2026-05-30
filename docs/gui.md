# Desktop app

UnMsg's desktop window is a calm, single‑column flow. There is always
**exactly one primary action** — *Convert → Cancel → Open output* — so the
next step is never in doubt.

## The window

- **Drop zone.** The empty‑state invitation. Drag `.msg` files or folders in,
  or click to browse.
- **File list.** Each row shows the message's identity — once converted, its
  output bundle name (date and subject) — with a coloured status dot and
  small chips for the formats produced.
- **Options bar.** A one‑line summary that expands only when you want it.
  Sensible defaults mean most people never open it.
- **Action.** *Convert* turns into *Cancel* while running, and *Open output*
  when done. A slim progress strip under the header carries the "working"
  feedback.
- **Log pane.** Collapsed by default. Expand it if you want to see what
  happened in detail. Emails and paths are scrubbed before they appear here.

## Themes

Light, dark, and a high‑contrast theme — pick from **Settings → General**, or
let the app follow the OS. The brand colour is a calm green; the focus ring
is a distinct blue so keyboard users can always see where they are.

## Right‑click on a `.msg`

The Windows installer adds **Convert with UnMsg** to the right‑click menu of
`.msg` files and a **Send To → UnMsg** target. Both open the app with those
files queued and ready to convert.

## What the app never does

- No telemetry. No analytics. No error‑reporting SDK.
- No accounts, no sign‑in, no cloud.
- No background uploads — even crash reports stay on disk and are never sent.
- No fake urgency or buried "off" switches. The privacy promise is in plain
  words on the **Help / About** screen.

See the [Privacy](privacy.md) page for the full statement.
